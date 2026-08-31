"""Render a :class:`~dqflow.result.ValidationResult` as readable text.

This is a presentation layer with no engine dependencies. ``dq validate`` uses it
for its default output; the stable, machine-readable representation stays
:meth:`ValidationResult.to_dict`. The renderer groups checks (schema, columns,
table rules, cross-column rules), shows per-group pass/fail counts, and appends a
bounded sample of offending values and a failure rate to each failing check.
"""

from __future__ import annotations

import enum
import os
from typing import Any

from dqflow.result import CheckResult, ValidationResult

__all__ = ["Verbosity", "render_result", "resolve_color"]

# Check-name prefixes (``<kind>:<subject>``) that describe a single column.
_COLUMN_CHECK_KINDS = ("not_null", "min", "max", "allowed", "unique", "pattern")

_PASS = "✔"  # ✔
_FAIL = "✘"  # ✘
_DOT = "·"  # ·

_ANSI = {
    "red": "\033[31m",
    "green": "\033[32m",
    "dim": "\033[2m",
    "bold": "\033[1m",
}
_RESET = "\033[0m"


class Verbosity(enum.Enum):
    """How much of a validation result :func:`render_result` prints."""

    QUIET = "quiet"
    NORMAL = "normal"
    VERBOSE = "verbose"


class _Style:
    """Wrap text in an ANSI colour, or return it unchanged when colour is off."""

    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled

    def __call__(self, text: str, color: str) -> str:
        if not self.enabled or color not in _ANSI:
            return text
        return f"{_ANSI[color]}{text}{_RESET}"


def resolve_color(flag: bool | None, *, isatty: bool) -> bool:
    """Decide whether to emit colour.

    An explicit ``--color/--no-color`` flag wins. Otherwise colour is on only for
    a TTY and is always suppressed when the ``NO_COLOR`` environment variable is
    set (see https://no-color.org).
    """
    if flag is not None:
        return flag
    if os.environ.get("NO_COLOR") is not None:
        return False
    return isatty


def render_result(
    result: ValidationResult,
    *,
    row_count: int | None = None,
    verbosity: Verbosity = Verbosity.NORMAL,
    color: bool = False,
) -> str:
    """Return the text ``dq validate`` prints for ``result``.

    Args:
        result: The validation result to render.
        row_count: Number of rows validated, shown in the header when given.
        verbosity: ``QUIET`` prints only failing checks, ``NORMAL`` adds a
            per-group pass summary, ``VERBOSE`` lists every check.
        color: Whether to emit ANSI colour codes.
    """
    style = _Style(color)
    passed = sum(1 for c in result.checks if c.passed)
    failed = len(result.checks) - passed

    groups = _group_checks(result.checks)
    sections = [
        (
            "Schema",
            groups.schema,
            _flat_section(groups.schema, verbosity, style, strip_prefix=True),
        ),
        ("Columns", _flatten(groups.columns), _column_section(groups.columns, verbosity, style)),
        ("Table rules", groups.rules, _flat_section(groups.rules, verbosity, style)),
        (
            "Cross-column rules",
            groups.cross_column,
            _flat_section(groups.cross_column, verbosity, style),
        ),
    ]

    lines = [_header(result.contract_name, passed, failed, len(result.checks), row_count, style)]
    for title, checks, block in sections:
        if not checks or (not block and verbosity is Verbosity.QUIET):
            continue
        lines.append("")
        lines.append(f"  {style(title, 'bold')}  {_group_count(checks, style)}")
        lines.extend(block)

    if failed or verbosity is not Verbosity.QUIET:
        lines.append("")
        lines.append("  " + _footer(passed, failed, style))
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Grouping
# --------------------------------------------------------------------------- #


class _Groups:
    def __init__(self) -> None:
        self.schema: list[CheckResult] = []
        self.columns: dict[str, list[CheckResult]] = {}
        self.rules: list[CheckResult] = []
        self.cross_column: list[CheckResult] = []


def _group_checks(checks: list[CheckResult]) -> _Groups:
    groups = _Groups()
    for check in checks:
        kind, subject = _kind_and_subject(check)
        if kind == "column_exists":
            groups.schema.append(check)
        elif kind in _COLUMN_CHECK_KINDS:
            groups.columns.setdefault(subject, []).append(check)
        elif kind == "cross_column":
            groups.cross_column.append(check)
        else:  # "rule" and any future top-level kind
            groups.rules.append(check)
    return groups


def _kind_and_subject(check: CheckResult) -> tuple[str, str]:
    kind, _, subject = check.name.partition(":")
    return kind, subject


def _flatten(columns: dict[str, list[CheckResult]]) -> list[CheckResult]:
    return [check for checks in columns.values() for check in checks]


def _group_count(checks: list[CheckResult], style: _Style) -> str:
    total = len(checks)
    failed = sum(1 for c in checks if not c.passed)
    if failed:
        return style(f"{failed}/{total} failed", "red")
    return style(f"{total}/{total} passed", "dim")


# --------------------------------------------------------------------------- #
# Sections
# --------------------------------------------------------------------------- #


def _flat_section(
    checks: list[CheckResult],
    verbosity: Verbosity,
    style: _Style,
    *,
    strip_prefix: bool = False,
) -> list[str]:
    """Render a flat list of checks (schema, table rules, cross-column rules).

    Returns only the check lines; the group's pass/fail count is rendered by the
    caller in the section header. ``NORMAL`` shows just the failures, ``VERBOSE``
    every check.
    """
    if not checks:
        return []
    shown = checks if verbosity is Verbosity.VERBOSE else [c for c in checks if not c.passed]
    width = max((len(_kind_and_subject(c)[1]) for c in shown), default=0)
    return [_flat_line(c, style, width, strip_prefix) for c in shown]


def _flat_line(check: CheckResult, style: _Style, width: int, strip_prefix: bool) -> str:
    label = _kind_and_subject(check)[1]
    mark = style(_PASS, "green") if check.passed else style(_FAIL, "red")
    prefix = f"Column '{label}' " if strip_prefix else ""
    detail = _detail(check, strip_prefix=prefix, boilerplate=f"Rule '{label}' failed")
    line = f"    {mark} {label.ljust(width)}".rstrip()
    return f"{line}  {detail}" if detail else line


def _column_section(
    columns: dict[str, list[CheckResult]], verbosity: Verbosity, style: _Style
) -> list[str]:
    """Render column checks, grouped under each column name.

    ``NORMAL`` shows only columns with a failure (and only their failing checks),
    followed by a one-line note for the columns that passed cleanly. ``VERBOSE``
    shows every column and check.
    """
    if not columns:
        return []

    failing = {n: cs for n, cs in columns.items() if any(not c.passed for c in cs)}
    shown = columns if verbosity is Verbosity.VERBOSE else failing
    if not shown:
        return []

    name_width = max(len(n) for n in shown)
    kind_width = max(len(_kind_and_subject(c)[0]) for cs in shown.values() for c in cs)

    lines: list[str] = []
    for name, checks in shown.items():
        rows = checks if verbosity is Verbosity.VERBOSE else [c for c in checks if not c.passed]
        for i, check in enumerate(rows):
            head = name.ljust(name_width) if i == 0 else " " * name_width
            kind = _kind_and_subject(check)[0]
            mark = style(_PASS, "green") if check.passed else style(_FAIL, "red")
            detail = _detail(check, strip_prefix=f"Column '{name}' ")
            line = f"    {head}  {mark} {kind.ljust(kind_width)}"
            lines.append(f"{line}  {detail}".rstrip() if detail else line.rstrip())

    clean = len(columns) - len(failing)
    if verbosity is Verbosity.NORMAL and clean:
        note = f"{clean} more {_plural(clean, 'column')} passed"
        lines.append(f"    {style(_PASS, 'green')} {style(note, 'dim')}")
    return lines


# --------------------------------------------------------------------------- #
# Detail text
# --------------------------------------------------------------------------- #


def _detail(check: CheckResult, *, strip_prefix: str = "", boilerplate: str = "") -> str:
    """Compose the trailing detail for a failing check.

    The engine ``message`` carries the expectation and the absolute magnitude;
    this appends the failure rate as a percentage and a bounded sample of
    offending values — information the message deliberately leaves out.
    """
    if check.passed:
        return ""

    message = "" if check.message == boilerplate else check.message
    if strip_prefix and message.startswith(strip_prefix):
        message = message[len(strip_prefix) :]

    pct = _pct(_first(check.details, "violating_rate", "failing_rate", "null_rate"))
    if pct:
        message = f"{message} ({pct})" if message else f"({pct})"

    sample = _first(check.details, "sample_invalid_values", "sample_duplicate_values")
    if sample:
        listed = "e.g. " + ", ".join(_fmt_value(v) for v in sample)
        message = f"{message}  {_DOT}  {listed}" if message else listed
    return message


def _first(details: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in details:
            return details[key]
    return None


def _fmt_value(value: Any) -> str:
    return repr(value) if isinstance(value, str) else str(value)


def _pct(value: Any) -> str:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
        return ""
    pct = value * 100
    return "<0.1%" if pct < 0.1 else f"{pct:.1f}%"


# --------------------------------------------------------------------------- #
# Header / footer
# --------------------------------------------------------------------------- #


def _header(
    name: str,
    passed: int,
    failed: int,
    total: int,
    row_count: int | None,
    style: _Style,
) -> str:
    if failed:
        status = style(f"{failed} of {total} checks failed", "red")
    else:
        status = style(f"{passed}/{total} checks passed", "green")
    suffix = "" if row_count is None else f" on {row_count:,} {_plural(row_count, 'row')}"
    return f"{style(name, 'bold')} {_DOT} {status}{suffix}"


def _plural(n: int, noun: str) -> str:
    return noun if n == 1 else f"{noun}s"


def _footer(passed: int, failed: int, style: _Style) -> str:
    return (
        f"{style(f'{passed} passed', 'green' if passed else 'dim')} {_DOT} "
        f"{style(f'{failed} failed', 'red' if failed else 'dim')}"
    )

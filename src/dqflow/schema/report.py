"""Render :class:`~dqflow.schema.errors.Diagnostic` lists as readable text.

Presentation only — the machine-readable form is ``Diagnostic.to_dict`` and the
``dq lint --output json`` payload. Styled to match :mod:`dqflow.diff` /
:mod:`dqflow.report`.
"""

from __future__ import annotations

from dqflow.schema.errors import ERROR, Diagnostic


def format_diagnostics(source: str, diagnostics: list[Diagnostic]) -> str:
    """Return a grouped, aligned summary of ``diagnostics`` for ``source``."""
    errors = [d for d in diagnostics if d.severity == ERROR]
    warnings = [d for d in diagnostics if d.severity != ERROR]

    if not diagnostics:
        return f"{source}: OK"

    counts = []
    if errors:
        counts.append(f"{len(errors)} error{'s' if len(errors) != 1 else ''}")
    if warnings:
        counts.append(f"{len(warnings)} warning{'s' if len(warnings) != 1 else ''}")
    lines = [f"{source}: {', '.join(counts)}", ""]

    rendered = [(_label(d), _location(d), d.message, d.code) for d in diagnostics]
    label_w = max(len(label) for label, _, _, _ in rendered)
    loc_w = max(len(loc) for _, loc, _, _ in rendered)
    for label, loc, message, code in rendered:
        lines.append(f"  {label.ljust(label_w)}  {loc.ljust(loc_w)}  {message}  [{code}]")

    return "\n".join(lines)


def _label(d: Diagnostic) -> str:
    return "ERROR" if d.severity == ERROR else "WARN"


def _location(d: Diagnostic) -> str:
    where = d.path or "(root)"
    return f"{where}:{d.line}" if d.line is not None else where

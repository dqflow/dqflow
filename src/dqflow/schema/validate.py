"""Structural validation of a contract document — the engine behind ``dq lint``.

:func:`lint_contract_data` walks an already-parsed contract mapping and returns
:class:`~dqflow.schema.errors.Diagnostic` records; it performs no I/O and imports
no engine. :func:`lint_contract_file` adds YAML reading (raising
:class:`~dqflow.schema.errors.ContractParseError` on a syntax error) and
line-number tracking.

The checks mirror what :meth:`dqflow.contract.Contract.from_yaml` and the
``Column`` / ``CrossColumnRule`` constructors would otherwise fail on — but with
a document path and, where available, a line number instead of a traceback.
"""

from __future__ import annotations

import contextlib
import re
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from dqflow.column import SUPPORTED_OPS
from dqflow.rules import RuleError, evaluate_rule
from dqflow.schema.errors import ERROR, WARNING, ContractParseError, Diagnostic
from dqflow.schema.version import check_version

#: Accepted top-level keys. ``metadata`` is the escape hatch for arbitrary data.
KNOWN_TOP_LEVEL: frozenset[str] = frozenset(
    {
        "schema_version",
        "$schema",
        "name",
        "description",
        "columns",
        "rules",
        "cross_column_rules",
        "metadata",
    }
)

#: Accepted keys on a column mapping. ``type`` is the legacy alias for ``dtype``.
#: ``custom`` is Python-only and deliberately excluded.
KNOWN_COLUMN_FIELDS: frozenset[str] = frozenset(
    {
        "dtype",
        "type",
        "not_null",
        "min",
        "max",
        "allowed",
        "freshness_minutes",
        "unique",
        "pattern",
        "description",
        "metadata",
    }
)

#: Accepted keys on a cross-column rule mapping. Callable ``check`` is Python-only.
KNOWN_CROSS_COLUMN_FIELDS: frozenset[str] = frozenset(
    {"name", "left", "op", "right", "error_message"}
)

# Values acceptable as a bare constraint value (min / max / an allowed entry).
# ``date`` also covers ``datetime``; YAML loads timestamps as those.
_SCALAR = (str, int, float, bool, date)


# --------------------------------------------------------------------------- #
# Line-number-aware YAML loading
# --------------------------------------------------------------------------- #


class _LineDict(dict):  # type: ignore[type-arg]
    """A ``dict`` that remembers the source line of the mapping and of each key."""

    def __init__(self) -> None:
        super().__init__()
        self.__line__: int | None = None
        self.__marks__: dict[Any, int] = {}


class _LineList(list):  # type: ignore[type-arg]
    """A ``list`` that remembers the source line of the sequence and each item."""

    def __init__(self) -> None:
        super().__init__()
        self.__line__: int | None = None
        self.__marks__: list[int] = []


class _MarkedLoader(yaml.SafeLoader):
    """``SafeLoader`` that yields :class:`_LineDict` / :class:`_LineList`."""


def _construct_marked_map(loader: Any, node: yaml.Node) -> Any:
    data = _LineDict()
    data.__line__ = node.start_mark.line + 1
    yield data
    if not isinstance(node, yaml.MappingNode):  # pragma: no cover - malformed tree
        return
    loader.flatten_mapping(node)
    marks: dict[Any, int] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=True)
        data[key] = loader.construct_object(value_node, deep=True)
        with contextlib.suppress(TypeError):  # unhashable key — pragma: no cover
            marks[key] = key_node.start_mark.line + 1
    data.__marks__ = marks


def _construct_marked_seq(loader: Any, node: yaml.Node) -> Any:
    data = _LineList()
    data.__line__ = node.start_mark.line + 1
    yield data
    if not isinstance(node, yaml.SequenceNode):  # pragma: no cover - malformed tree
        return
    data.__marks__ = [child.start_mark.line + 1 for child in node.value]
    data.extend(loader.construct_object(child, deep=True) for child in node.value)


_MarkedLoader.add_constructor("tag:yaml.org,2002:map", _construct_marked_map)
_MarkedLoader.add_constructor("tag:yaml.org,2002:seq", _construct_marked_seq)

# The marked containers are plain dict/list subclasses; teach SafeDumper to emit
# them like their bases so a parsed contract still round-trips through to_yaml().
yaml.SafeDumper.add_representer(_LineDict, yaml.SafeDumper.represent_dict)
yaml.SafeDumper.add_representer(_LineList, yaml.SafeDumper.represent_list)


def parse_contract_yaml(text: str, *, source: str | None = None) -> Any:
    """Parse ``text`` as YAML, tracking line numbers.

    Raises:
        ContractParseError: If ``text`` is not valid YAML.
    """
    try:
        return yaml.load(text, Loader=_MarkedLoader)
    except yaml.YAMLError as exc:
        where = f" in {source}" if source else ""
        raise ContractParseError(f"could not parse contract{where}: {exc}") from exc


def _line_of(container: Any, key: Any = None) -> int | None:
    if isinstance(container, _LineDict) and key is not None:
        return container.__marks__.get(key)
    if isinstance(container, _LineList) and isinstance(key, int):
        marks = container.__marks__
        return marks[key] if 0 <= key < len(marks) else container.__line__
    line = getattr(container, "__line__", None)
    return line if isinstance(line, int) else None


# --------------------------------------------------------------------------- #
# Path helpers
# --------------------------------------------------------------------------- #


def _child(prefix: str, key: str) -> str:
    return f"{prefix}.{key}" if prefix else key


def _item(prefix: str, index: int) -> str:
    return f"{prefix}[{index}]"


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #


def lint_contract_file(path: str | Path) -> list[Diagnostic]:
    """Read, parse and validate the contract at ``path``.

    Raises:
        ContractParseError: If the file is not valid YAML.

    Returns:
        Every :class:`Diagnostic` found, errors and warnings, in document order.
    """
    path = Path(path)
    data = parse_contract_yaml(path.read_text(), source=str(path))
    return lint_contract_data(data)


def lint_contract_data(data: Any) -> list[Diagnostic]:
    """Validate an already-parsed contract mapping. Pure; performs no I/O."""
    if not isinstance(data, dict):
        got = type(data).__name__
        return [
            Diagnostic(
                ERROR,
                "not-a-mapping",
                f"a contract must be a mapping at the top level, got {got}",
                path="",
                line=_line_of(data),
            )
        ]

    diagnostics: list[Diagnostic] = []
    diagnostics.extend(check_version(data.get("schema_version")))
    diagnostics.extend(_check_unknown_keys(data, KNOWN_TOP_LEVEL, prefix=""))
    diagnostics.extend(_check_top_level_types(data))
    diagnostics.extend(_check_identity(data))
    diagnostics.extend(_check_columns(data.get("columns")))
    diagnostics.extend(_check_rules(data.get("rules")))
    diagnostics.extend(_check_cross_column_rules(data.get("cross_column_rules")))
    diagnostics.extend(_check_emptiness(data))
    return diagnostics


# --------------------------------------------------------------------------- #
# Checks
# --------------------------------------------------------------------------- #


def _check_unknown_keys(
    mapping: dict[Any, Any], known: frozenset[str], *, prefix: str
) -> list[Diagnostic]:
    out: list[Diagnostic] = []
    for key in mapping:
        if not isinstance(key, str) or key not in known:
            out.append(
                Diagnostic(
                    ERROR,
                    "unknown-field",
                    f"unknown field {key!r}; expected one of {', '.join(sorted(known))}",
                    path=_child(prefix, str(key)),
                    line=_line_of(mapping, key),
                )
            )
    return out


def _wrong_type(
    mapping: dict[Any, Any], key: str, expected: str, *, prefix: str
) -> Diagnostic | None:
    if key not in mapping:
        return None
    value = mapping[key]
    checks = {
        "string": lambda v: isinstance(v, str),
        "boolean": lambda v: isinstance(v, bool),
        "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
        "list": lambda v: isinstance(v, list),
        "mapping": lambda v: isinstance(v, dict),
        "scalar": lambda v: v is None or (isinstance(v, _SCALAR)),
    }
    if checks[expected](value):
        return None
    return Diagnostic(
        ERROR,
        "wrong-type",
        f"{key!r} must be {'a' if expected != 'integer' else 'an'} {expected}, "
        f"got {type(value).__name__}",
        path=_child(prefix, key),
        line=_line_of(mapping, key),
    )


def _check_top_level_types(data: dict[Any, Any]) -> list[Diagnostic]:
    specs = {
        "$schema": "string",
        "name": "string",
        "description": "string",
        "columns": "mapping",
        "rules": "list",
        "cross_column_rules": "list",
        "metadata": "mapping",
    }
    return [
        d for key, exp in specs.items() if (d := _wrong_type(data, key, exp, prefix="")) is not None
    ]


def _check_identity(data: dict[Any, Any]) -> list[Diagnostic]:
    if "name" in data:
        return []
    return [
        Diagnostic(
            WARNING,
            "missing-name",
            "no name; the file stem will be used",
            path="",
            line=_line_of(data),
        )
    ]


def _check_emptiness(data: dict[Any, Any]) -> list[Diagnostic]:
    if data.get("columns") or data.get("rules") or data.get("cross_column_rules"):
        return []
    return [
        Diagnostic(
            WARNING,
            "empty-contract",
            "contract declares no columns, rules or cross-column rules",
            path="",
            line=_line_of(data),
        )
    ]


def _check_columns(columns: Any) -> list[Diagnostic]:
    if columns is None:
        return []
    if not isinstance(columns, dict):
        return []  # already reported by _check_top_level_types

    out: list[Diagnostic] = []
    for name, spec in columns.items():
        path = _child("columns", str(name))
        if spec is None or isinstance(spec, _SCALAR):
            continue  # shorthand: `col: string` — a bare dtype, always valid
        if not isinstance(spec, dict):
            out.append(
                Diagnostic(
                    ERROR,
                    "not-a-mapping",
                    f"column {name!r} must be a mapping or a dtype name, got {type(spec).__name__}",
                    path=path,
                    line=_line_of(columns, name),
                )
            )
            continue
        out.extend(_check_column_spec(name, spec, path))
    return out


def _check_column_spec(name: Any, spec: dict[Any, Any], path: str) -> list[Diagnostic]:
    out: list[Diagnostic] = []
    out.extend(_check_unknown_keys(spec, KNOWN_COLUMN_FIELDS, prefix=path))

    for key, exp in (
        ("dtype", "string"),
        ("type", "string"),
        ("not_null", "boolean"),
        ("unique", "boolean"),
        ("min", "scalar"),
        ("max", "scalar"),
        ("allowed", "list"),
        ("freshness_minutes", "integer"),
        ("pattern", "string"),
        ("description", "string"),
        ("metadata", "mapping"),
    ):
        d = _wrong_type(spec, key, exp, prefix=path)
        if d is not None:
            out.append(d)

    if "dtype" not in spec and "type" not in spec:
        out.append(
            Diagnostic(
                WARNING,
                "missing-column-dtype",
                f"column {name!r} has no dtype; it will default to string",
                path=path,
                line=_line_of(spec),
            )
        )

    lo, hi = spec.get("min"), spec.get("max")
    if isinstance(lo, _SCALAR) and isinstance(hi, _SCALAR) and not isinstance(lo, bool):
        try:
            contradictory = lo > hi  # type: ignore[operator]
        except TypeError:
            contradictory = False
        if contradictory:
            out.append(
                Diagnostic(
                    ERROR,
                    "min-greater-than-max",
                    f"min ({lo}) is greater than max ({hi})",
                    path=_child(path, "min"),
                    line=_line_of(spec, "min"),
                )
            )

    pattern = spec.get("pattern")
    if isinstance(pattern, str):
        try:
            re.compile(pattern)
        except re.error as exc:
            out.append(
                Diagnostic(
                    ERROR,
                    "invalid-regex",
                    f"pattern is not a valid regular expression: {exc}",
                    path=_child(path, "pattern"),
                    line=_line_of(spec, "pattern"),
                )
            )

    allowed = spec.get("allowed")
    if isinstance(allowed, list) and not allowed:
        out.append(
            Diagnostic(
                WARNING,
                "empty-allowed",
                "allowed is an empty list; every non-null value will fail",
                path=_child(path, "allowed"),
                line=_line_of(spec, "allowed"),
            )
        )

    return out


def _check_rules(rules: Any) -> list[Diagnostic]:
    if rules is None:
        return []
    if not isinstance(rules, list):
        return []  # already reported by _check_top_level_types

    out: list[Diagnostic] = []
    seen: set[str] = set()
    for index, rule in enumerate(rules):
        path = _item("rules", index)
        line = _line_of(rules, index)
        if not isinstance(rule, str):
            out.append(
                Diagnostic(
                    ERROR,
                    "wrong-type",
                    f"a table rule must be a string, got {type(rule).__name__}",
                    path=path,
                    line=line,
                )
            )
            continue
        if rule in seen:
            out.append(
                Diagnostic(
                    WARNING,
                    "duplicate-rule",
                    f"table rule {rule!r} is repeated",
                    path=path,
                    line=line,
                )
            )
        seen.add(rule)
        error = _rule_error(rule)
        if error is not None:
            out.append(
                Diagnostic(ERROR, "invalid-rule", f"{rule!r}: {error}", path=path, line=line)
            )
    return out


def _rule_error(rule: str) -> str | None:
    try:
        evaluate_rule(rule, row_count=0, null_rate=lambda _c: 0.0, unique_count=lambda _c: 0)
    except RuleError as exc:
        return str(exc)
    except Exception as exc:  # noqa: BLE001 - any evaluation failure means a broken rule
        return f"rule could not be evaluated: {exc}"
    return None


def _check_cross_column_rules(rules: Any) -> list[Diagnostic]:
    if rules is None:
        return []
    if not isinstance(rules, list):
        return []

    out: list[Diagnostic] = []
    seen: set[str] = set()
    for index, rule in enumerate(rules):
        path = _item("cross_column_rules", index)
        line = _line_of(rules, index)
        if not isinstance(rule, dict):
            out.append(
                Diagnostic(
                    ERROR,
                    "not-a-mapping",
                    f"a cross-column rule must be a mapping, got {type(rule).__name__}",
                    path=path,
                    line=line,
                )
            )
            continue

        out.extend(_check_unknown_keys(rule, KNOWN_CROSS_COLUMN_FIELDS, prefix=path))

        name = rule.get("name")
        if not isinstance(name, str) or not name:
            out.append(
                Diagnostic(
                    ERROR,
                    "incomplete-cross-column-rule",
                    "cross-column rule needs a 'name'",
                    path=path,
                    line=line,
                )
            )
        elif name in seen:
            out.append(
                Diagnostic(
                    ERROR,
                    "duplicate-cross-column-rule-name",
                    f"cross-column rule name {name!r} is used more than once",
                    path=_child(path, "name"),
                    line=_line_of(rule, "name"),
                )
            )
        else:
            seen.add(name)

        missing = [f for f in ("left", "op", "right") if rule.get(f) is None]
        if missing:
            out.append(
                Diagnostic(
                    ERROR,
                    "incomplete-cross-column-rule",
                    f"cross-column rule is missing {', '.join(missing)} "
                    "(callable rules cannot be expressed in YAML)",
                    path=path,
                    line=line,
                )
            )

        op = rule.get("op")
        if isinstance(op, str) and op not in SUPPORTED_OPS:
            out.append(
                Diagnostic(
                    ERROR,
                    "invalid-operator",
                    f"unsupported op {op!r}; expected one of {', '.join(sorted(SUPPORTED_OPS))}",
                    path=_child(path, "op"),
                    line=_line_of(rule, "op"),
                )
            )

    return out

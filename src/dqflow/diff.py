"""Compare two contract versions and classify each change.

The public entry point is :func:`diff_contracts`; the ``dq diff`` CLI command
wraps it. A change is **breaking** when data that conformed to the old contract
may violate the new one, judged from the contract's *declared intent*. This is
independent of which constraints an engine enforces today, so ``dtype`` and
``freshness_minutes`` changes are classified too (see the guide for the
enforcement caveat).
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

from dqflow.column import CrossColumnRule
from dqflow.contract import Contract, _dtype_to_str, column_to_dict

__all__ = ["ContractChange", "ContractDiff", "diff_contracts"]

BREAKING = "breaking"
NON_BREAKING = "non_breaking"

# dtype changes (old -> new, as normalized strings) that only widen the set of
# accepted values and therefore cannot reject previously-valid data.
_DTYPE_WIDENINGS: frozenset[tuple[str, str]] = frozenset({("integer", "float")})

# Order in which column fields are compared and reported.
_FIELD_ORDER: tuple[str, ...] = (
    "dtype",
    "not_null",
    "unique",
    "min",
    "max",
    "allowed",
    "pattern",
    "freshness_minutes",
)


@dataclass(frozen=True)
class ContractChange:
    """One classified difference between two contracts.

    Attributes:
        kind: Stable machine token — one of ``column_added``, ``column_removed``,
            ``field_added``, ``field_removed``, ``field_changed``,
            ``table_rule_added``, ``table_rule_removed``,
            ``cross_column_rule_added``, ``cross_column_rule_removed``,
            ``cross_column_rule_changed``.
        classification: ``"breaking"`` or ``"non_breaking"`` for data producers.
        reason: Short human-readable explanation.
        column: Affected column name, or ``None`` for table-level and
            cross-column changes.
        attribute: Affected field name for ``field_*`` kinds
            (``dtype``/``not_null``/``min``/…), otherwise ``None``.
        old: Previous value (``None`` means the field or object was absent).
        new: New value (``None`` means the field or object was removed).
    """

    kind: str
    classification: str
    reason: str
    column: str | None = None
    attribute: str | None = None
    old: Any = None
    new: Any = None

    @property
    def breaking(self) -> bool:
        """Whether this change is classified as breaking."""
        return self.classification == BREAKING

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation of this change."""
        return {
            "kind": self.kind,
            "classification": self.classification,
            "reason": self.reason,
            "column": self.column,
            "attribute": self.attribute,
            "old": _jsonify(self.old),
            "new": _jsonify(self.new),
        }


@dataclass
class ContractDiff:
    """The full set of classified changes between two contracts.

    Attributes:
        old_name: Name of the previous contract.
        new_name: Name of the updated contract.
        changes: Every difference, in a stable source order (columns in new-
            contract order, then table rules, then cross-column rules).
    """

    old_name: str
    new_name: str
    changes: list[ContractChange] = field(default_factory=list)

    @property
    def breaking_changes(self) -> list[ContractChange]:
        """Breaking changes, in source order."""
        return [c for c in self.changes if c.breaking]

    @property
    def non_breaking_changes(self) -> list[ContractChange]:
        """Non-breaking changes, in source order."""
        return [c for c in self.changes if not c.breaking]

    @property
    def has_breaking(self) -> bool:
        """Whether any change is breaking."""
        return any(c.breaking for c in self.changes)

    @property
    def is_empty(self) -> bool:
        """Whether the two contracts are equivalent (no changes)."""
        return not self.changes

    def to_dict(self) -> dict[str, Any]:
        """Return the stable, documented JSON representation of this diff."""
        breaking = sum(1 for c in self.changes if c.breaking)
        return {
            "old_contract": self.old_name,
            "new_contract": self.new_name,
            "summary": {
                "total": len(self.changes),
                "breaking": breaking,
                "non_breaking": len(self.changes) - breaking,
            },
            "has_breaking": self.has_breaking,
            "changes": [c.to_dict() for c in self.changes],
        }

    def render_text(self) -> str:
        """Return the human-readable, severity-grouped summary."""
        return _render_text(self)


def diff_contracts(
    old: Contract | str | Path,
    new: Contract | str | Path,
) -> ContractDiff:
    """Compare two contracts and classify every difference.

    Args:
        old: The previous contract, or a path/str to a YAML contract loaded with
            :meth:`Contract.from_yaml`.
        new: The updated contract, or a path/str to a YAML contract.

    Returns:
        A :class:`ContractDiff` whose ``changes`` are each classified
        ``"breaking"`` or ``"non_breaking"`` for data producers.
    """
    old_c = _as_contract(old)
    new_c = _as_contract(new)

    changes: list[ContractChange] = []
    changes.extend(_diff_columns(old_c, new_c))
    changes.extend(_diff_table_rules(old_c, new_c))
    changes.extend(_diff_cross_column_rules(old_c, new_c))

    return ContractDiff(old_name=old_c.name, new_name=new_c.name, changes=changes)


def _as_contract(value: Contract | str | Path) -> Contract:
    if isinstance(value, Contract):
        return value
    return Contract.from_yaml(value)


# --------------------------------------------------------------------------- #
# Columns
# --------------------------------------------------------------------------- #


def _diff_columns(old_c: Contract, new_c: Contract) -> list[ContractChange]:
    changes: list[ContractChange] = []

    ordered = list(new_c.columns) + [n for n in old_c.columns if n not in new_c.columns]

    for name in ordered:
        old_col = old_c.columns.get(name)
        new_col = new_c.columns.get(name)

        if old_col is None and new_col is not None:
            if new_col.not_null:
                classification, reason = BREAKING, "new column requires non-null values"
            elif new_col.unique:
                classification, reason = BREAKING, "new column requires unique values"
            else:
                classification, reason = NON_BREAKING, "new nullable column"
            changes.append(
                ContractChange(
                    kind="column_added",
                    classification=classification,
                    reason=reason,
                    column=name,
                    new=column_to_dict(new_col),
                )
            )
        elif old_col is not None and new_col is None:
            changes.append(
                ContractChange(
                    kind="column_removed",
                    classification=NON_BREAKING,
                    reason="column is no longer required",
                    column=name,
                    old=column_to_dict(old_col),
                )
            )
        elif old_col is not None and new_col is not None:
            for attr in _FIELD_ORDER:
                change = _FIELD_HANDLERS[attr](
                    name,
                    _field_value(old_col, attr),
                    _field_value(new_col, attr),
                )
                if change is not None:
                    changes.append(change)

    return changes


def _field_value(col: Any, attr: str) -> Any:
    if attr == "dtype":
        return _dtype_to_str(col.dtype)
    return getattr(col, attr)


def _diff_dtype(name: str, old: Any, new: Any) -> ContractChange | None:
    if old == new:
        return None
    if (old, new) in _DTYPE_WIDENINGS:
        classification, reason = NON_BREAKING, "widened dtype"
    else:
        classification, reason = BREAKING, "narrowed or incompatible dtype"
    return ContractChange(
        kind="field_changed",
        classification=classification,
        reason=reason,
        column=name,
        attribute="dtype",
        old=old,
        new=new,
    )


def _diff_flag(
    name: str,
    attr: str,
    old: Any,
    new: Any,
    *,
    add_reason: str,
    remove_reason: str,
) -> ContractChange | None:
    old_b, new_b = bool(old), bool(new)
    if old_b == new_b:
        return None
    if new_b:
        return ContractChange(
            kind="field_added",
            classification=BREAKING,
            reason=add_reason,
            column=name,
            attribute=attr,
            old=False,
            new=True,
        )
    return ContractChange(
        kind="field_removed",
        classification=NON_BREAKING,
        reason=remove_reason,
        column=name,
        attribute=attr,
        old=True,
        new=False,
    )


def _diff_not_null(name: str, old: Any, new: Any) -> ContractChange | None:
    return _diff_flag(
        name,
        "not_null",
        old,
        new,
        add_reason="column no longer allows nulls",
        remove_reason="column now allows nulls",
    )


def _diff_unique(name: str, old: Any, new: Any) -> ContractChange | None:
    return _diff_flag(
        name,
        "unique",
        old,
        new,
        add_reason="values must now be unique",
        remove_reason="uniqueness requirement removed",
    )


def _diff_bound(
    name: str,
    attr: str,
    old: Any,
    new: Any,
    *,
    added_reason: str,
    removed_reason: str,
    stricter_reason: str,
    looser_reason: str,
    is_stricter: Callable[[Any, Any], bool],
) -> ContractChange | None:
    if old is None and new is None:
        return None
    if old is None:
        return ContractChange(
            kind="field_added",
            classification=BREAKING,
            reason=added_reason,
            column=name,
            attribute=attr,
            old=None,
            new=new,
        )
    if new is None:
        return ContractChange(
            kind="field_removed",
            classification=NON_BREAKING,
            reason=removed_reason,
            column=name,
            attribute=attr,
            old=old,
            new=None,
        )
    if old == new:
        return None
    try:
        stricter = bool(is_stricter(old, new))
    except TypeError:
        return ContractChange(
            kind="field_changed",
            classification=BREAKING,
            reason=f"{attr} bound changed",
            column=name,
            attribute=attr,
            old=old,
            new=new,
        )
    return ContractChange(
        kind="field_changed",
        classification=BREAKING if stricter else NON_BREAKING,
        reason=stricter_reason if stricter else looser_reason,
        column=name,
        attribute=attr,
        old=old,
        new=new,
    )


def _diff_min(name: str, old: Any, new: Any) -> ContractChange | None:
    return _diff_bound(
        name,
        "min",
        old,
        new,
        added_reason="added a lower bound",
        removed_reason="removed the lower bound",
        stricter_reason="stricter lower bound",
        looser_reason="relaxed lower bound",
        is_stricter=lambda o, n: n > o,
    )


def _diff_max(name: str, old: Any, new: Any) -> ContractChange | None:
    return _diff_bound(
        name,
        "max",
        old,
        new,
        added_reason="added an upper bound",
        removed_reason="removed the upper bound",
        stricter_reason="stricter upper bound",
        looser_reason="relaxed upper bound",
        is_stricter=lambda o, n: n < o,
    )


def _diff_freshness(name: str, old: Any, new: Any) -> ContractChange | None:
    return _diff_bound(
        name,
        "freshness_minutes",
        old,
        new,
        added_reason="added a freshness limit",
        removed_reason="removed the freshness limit",
        stricter_reason="stricter freshness limit",
        looser_reason="relaxed freshness limit",
        is_stricter=lambda o, n: n < o,
    )


def _diff_allowed(name: str, old: Any, new: Any) -> ContractChange | None:
    if old is None and new is None:
        return None
    if old is None:
        return ContractChange(
            kind="field_added",
            classification=BREAKING,
            reason="values now restricted to an allowed set",
            column=name,
            attribute="allowed",
            old=None,
            new=_sorted_safe(new),
        )
    if new is None:
        return ContractChange(
            kind="field_removed",
            classification=NON_BREAKING,
            reason="allowed-set restriction removed",
            column=name,
            attribute="allowed",
            old=_sorted_safe(old),
            new=None,
        )

    old_list, new_list = list(old), list(new)
    try:
        old_set, new_set = set(old_list), set(new_list)
    except TypeError:
        if old_list == new_list:
            return None
        return ContractChange(
            kind="field_changed",
            classification=BREAKING,
            reason="allowed set changed",
            column=name,
            attribute="allowed",
            old=old_list,
            new=new_list,
        )

    if old_set == new_set:
        return None

    removed = old_set - new_set
    added = new_set - old_set
    if removed:
        classification = BREAKING
        reason = "narrowed allowed set" if not added else "allowed set changed"
    else:
        classification = NON_BREAKING
        reason = "widened allowed set"

    return ContractChange(
        kind="field_changed",
        classification=classification,
        reason=reason,
        column=name,
        attribute="allowed",
        old=_sorted_safe(old_set),
        new=_sorted_safe(new_set),
    )


def _diff_pattern(name: str, old: Any, new: Any) -> ContractChange | None:
    if old == new:
        return None
    if old is None:
        return ContractChange(
            kind="field_added",
            classification=BREAKING,
            reason="new pattern constraint",
            column=name,
            attribute="pattern",
            old=None,
            new=new,
        )
    if new is None:
        return ContractChange(
            kind="field_removed",
            classification=NON_BREAKING,
            reason="pattern constraint removed",
            column=name,
            attribute="pattern",
            old=old,
            new=None,
        )
    return ContractChange(
        kind="field_changed",
        classification=BREAKING,
        reason="pattern changed",
        column=name,
        attribute="pattern",
        old=old,
        new=new,
    )


_FIELD_HANDLERS: dict[str, Callable[[str, Any, Any], ContractChange | None]] = {
    "dtype": _diff_dtype,
    "not_null": _diff_not_null,
    "unique": _diff_unique,
    "min": _diff_min,
    "max": _diff_max,
    "allowed": _diff_allowed,
    "pattern": _diff_pattern,
    "freshness_minutes": _diff_freshness,
}


# --------------------------------------------------------------------------- #
# Table rules
# --------------------------------------------------------------------------- #


def _diff_table_rules(old_c: Contract, new_c: Contract) -> list[ContractChange]:
    removed = Counter(old_c.rules) - Counter(new_c.rules)
    added = Counter(new_c.rules) - Counter(old_c.rules)

    changes: list[ContractChange] = []

    seen: Counter[str] = Counter()
    for rule in old_c.rules:
        if seen[rule] < removed[rule]:
            seen[rule] += 1
            changes.append(
                ContractChange(
                    kind="table_rule_removed",
                    classification=NON_BREAKING,
                    reason="table rule removed",
                    old=rule,
                )
            )

    seen = Counter()
    for rule in new_c.rules:
        if seen[rule] < added[rule]:
            seen[rule] += 1
            changes.append(
                ContractChange(
                    kind="table_rule_added",
                    classification=BREAKING,
                    reason="new table rule",
                    new=rule,
                )
            )

    return changes


# --------------------------------------------------------------------------- #
# Cross-column rules
# --------------------------------------------------------------------------- #


def _diff_cross_column_rules(old_c: Contract, new_c: Contract) -> list[ContractChange]:
    old_by_name = {r.name: r for r in old_c.cross_column_rules}
    new_by_name = {r.name: r for r in new_c.cross_column_rules}

    ordered = [r.name for r in new_c.cross_column_rules] + [
        r.name for r in old_c.cross_column_rules if r.name not in new_by_name
    ]

    changes: list[ContractChange] = []
    for cname in ordered:
        old_r = old_by_name.get(cname)
        new_r = new_by_name.get(cname)

        if old_r is None and new_r is not None:
            changes.append(
                ContractChange(
                    kind="cross_column_rule_added",
                    classification=BREAKING,
                    reason="new cross-column rule",
                    new=_cross_rule_dict(new_r),
                )
            )
        elif old_r is not None and new_r is None:
            changes.append(
                ContractChange(
                    kind="cross_column_rule_removed",
                    classification=NON_BREAKING,
                    reason="cross-column rule removed",
                    old=_cross_rule_dict(old_r),
                )
            )
        elif old_r is not None and new_r is not None and _cross_rule_changed(old_r, new_r):
            changes.append(
                ContractChange(
                    kind="cross_column_rule_changed",
                    classification=BREAKING,
                    reason="cross-column rule redefined",
                    old=_cross_rule_dict(old_r),
                    new=_cross_rule_dict(new_r),
                )
            )

    return changes


def _cross_rule_dict(rule: CrossColumnRule) -> dict[str, Any]:
    if rule.check is not None:
        return {"name": rule.name, "check": "<callable>"}
    return {"name": rule.name, "left": rule.left, "op": rule.op, "right": rule.right}


def _cross_rule_changed(old: CrossColumnRule, new: CrossColumnRule) -> bool:
    if old.check is not None or new.check is not None:
        return old.check is not new.check
    return (old.left, old.op, old.right) != (new.left, new.op, new.right)


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #


def _render_text(diff: ContractDiff) -> str:
    same_name = diff.old_name == diff.new_name
    label = diff.new_name if same_name else f"{diff.old_name} -> {diff.new_name}"

    if diff.is_empty:
        return f"{label}: no changes"

    total = len(diff.changes)
    breaking = diff.breaking_changes
    non_breaking = diff.non_breaking_changes
    plural = "change" if total == 1 else "changes"
    count = f"{len(breaking)} breaking" if breaking else "no breaking changes"

    lines = [f"{label}: {total} {plural} ({count})"]

    for title, group in (("BREAKING", breaking), ("non-breaking", non_breaking)):
        if not group:
            continue
        rendered = [(_describe(c), c.reason) for c in group]
        width = max(len(desc) for desc, _ in rendered)
        lines.append("")
        lines.append(f"  {title}")
        lines.extend(f"    {desc.ljust(width)}  ({reason})" for desc, reason in rendered)

    return "\n".join(lines)


def _describe(change: ContractChange) -> str:
    sym = _symbol(change.kind)
    kind = change.kind

    if kind == "column_added":
        return f'{sym} column "{change.column}" ({_column_summary(change.new)})'
    if kind == "column_removed":
        return f'{sym} column "{change.column}"'
    if kind in {"field_added", "field_removed", "field_changed"}:
        return f'{sym} column "{change.column}" {_field_phrase(change)}'
    if kind == "table_rule_added":
        return f"{sym} rule: {change.new}"
    if kind == "table_rule_removed":
        return f"{sym} rule: {change.old}"

    payload = change.new if change.new is not None else change.old
    rule_name = payload["name"] if isinstance(payload, dict) else "?"
    if kind == "cross_column_rule_changed":
        return f'{sym} cross-column rule "{rule_name}" redefined'
    return f'{sym} cross-column rule "{rule_name}"'


def _symbol(kind: str) -> str:
    if kind.endswith("_added"):
        return "+"
    if kind.endswith("_removed"):
        return "-"
    return "~"


def _column_summary(col_dict: Any) -> str:
    if not isinstance(col_dict, dict):
        return "?"
    parts = [str(col_dict.get("dtype", "?"))]
    if col_dict.get("not_null"):
        parts.append("not null")
    if col_dict.get("unique"):
        parts.append("unique")
    return ", ".join(parts)


def _field_phrase(change: ContractChange) -> str:
    attr = change.attribute or ""

    if attr in {"not_null", "unique"}:
        return "not null" if attr == "not_null" else "unique"
    if attr == "allowed":
        return f"allowed: {_allowed_delta(change.old, change.new)}"
    if change.kind == "field_added":
        return f"{attr}: {_fmt(change.new)}"
    if change.kind == "field_removed":
        return f"{attr} removed (was {_fmt(change.old)})"
    return f"{attr}: {_fmt(change.old)} -> {_fmt(change.new)}"


def _allowed_delta(old: Any, new: Any) -> str:
    if old is None:
        return "[" + ", ".join(_fmt(v) for v in new) + "]"
    if new is None:
        return "removed (was [" + ", ".join(_fmt(v) for v in old) + "])"

    added = [v for v in new if v not in old]
    removed = [v for v in old if v not in new]
    bits = []
    if added:
        bits.append("+[" + ", ".join(_fmt(v) for v in added) + "]")
    if removed:
        bits.append("-[" + ", ".join(_fmt(v) for v in removed) + "]")
    return " ".join(bits) if bits else "changed"


def _fmt(value: Any) -> str:
    if value is None:
        return "none"
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _sorted_safe(values: Any) -> list[Any]:
    try:
        return sorted(values)
    except TypeError:
        return sorted(values, key=str)


def _jsonify(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _jsonify(v) for k, v in value.items()}
    if isinstance(value, set):
        return [_jsonify(v) for v in _sorted_safe(value)]
    if isinstance(value, (list, tuple)):
        return [_jsonify(v) for v in value]
    if hasattr(value, "item"):
        return value.item()
    return value

"""Tests for contract diffing and breaking-change classification."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from dqflow import Column, Contract, CrossColumnRule
from dqflow.diff import ContractChange, diff_contracts


def _diff_one(old_col: Column, new_col: Column) -> ContractChange:
    """Diff two single-column contracts and return the only change."""
    old = Contract(name="t", columns={"c": old_col})
    new = Contract(name="t", columns={"c": new_col})
    changes = diff_contracts(old, new).changes
    assert len(changes) == 1, changes
    return changes[0]


def _classify(old_col: Column, new_col: Column) -> str:
    return _diff_one(old_col, new_col).classification


class TestNoChanges:
    def test_identical_contracts_have_no_changes(self) -> None:
        c = Contract(
            name="orders",
            columns={"id": Column(str, not_null=True), "amount": Column(float, min=0)},
            rules=["row_count > 0"],
        )
        result = diff_contracts(c, c)
        assert result.is_empty
        assert not result.has_breaking
        assert result.changes == []

    def test_equivalent_numeric_bounds_are_not_a_change(self) -> None:
        assert diff_contracts(
            Contract(name="t", columns={"c": Column(float, min=0)}),
            Contract(name="t", columns={"c": Column(float, min=0.0)}),
        ).is_empty


class TestColumnAddRemove:
    def test_new_nullable_column_is_non_breaking(self) -> None:
        old = Contract(name="t", columns={"a": Column(str)})
        new = Contract(name="t", columns={"a": Column(str), "b": Column(float)})
        (change,) = diff_contracts(old, new).changes
        assert change.kind == "column_added"
        assert change.classification == "non_breaking"
        assert change.column == "b"
        assert change.new == {"dtype": "float"}

    def test_new_not_null_column_is_breaking(self) -> None:
        old = Contract(name="t", columns={"a": Column(str)})
        new = Contract(name="t", columns={"a": Column(str), "b": Column(str, not_null=True)})
        (change,) = diff_contracts(old, new).changes
        assert change.kind == "column_added"
        assert change.breaking

    def test_new_unique_column_is_breaking(self) -> None:
        old = Contract(name="t", columns={"a": Column(str)})
        new = Contract(name="t", columns={"a": Column(str), "b": Column(str, unique=True)})
        (change,) = diff_contracts(old, new).changes
        assert change.breaking

    def test_removed_column_is_non_breaking(self) -> None:
        old = Contract(name="t", columns={"a": Column(str), "b": Column(str)})
        new = Contract(name="t", columns={"a": Column(str)})
        (change,) = diff_contracts(old, new).changes
        assert change.kind == "column_removed"
        assert change.classification == "non_breaking"
        assert change.old == {"dtype": "string"}


class TestDtype:
    def test_integer_to_float_is_non_breaking(self) -> None:
        assert _classify(Column(int), Column(float)) == "non_breaking"

    def test_float_to_integer_is_breaking(self) -> None:
        assert _classify(Column(float), Column(int)) == "breaking"

    def test_string_to_integer_is_breaking(self) -> None:
        change = _diff_one(Column(str), Column(int))
        assert change.attribute == "dtype"
        assert change.old == "string"
        assert change.new == "integer"
        assert change.breaking


class TestFlags:
    def test_adding_not_null_is_breaking(self) -> None:
        change = _diff_one(Column(str), Column(str, not_null=True))
        assert change.kind == "field_added"
        assert change.attribute == "not_null"
        assert change.old is False
        assert change.new is True
        assert change.breaking

    def test_removing_not_null_is_non_breaking(self) -> None:
        change = _diff_one(Column(str, not_null=True), Column(str))
        assert change.kind == "field_removed"
        assert change.classification == "non_breaking"

    def test_adding_unique_is_breaking(self) -> None:
        assert _diff_one(Column(str), Column(str, unique=True)).breaking

    def test_removing_unique_is_non_breaking(self) -> None:
        assert _diff_one(Column(str, unique=True), Column(str)).classification == "non_breaking"


class TestNumericBounds:
    @pytest.mark.parametrize(
        ("old_col", "new_col", "expected", "kind"),
        [
            (Column(float), Column(float, min=0), "breaking", "field_added"),
            (Column(float, min=0), Column(float), "non_breaking", "field_removed"),
            (Column(float, min=0), Column(float, min=10), "breaking", "field_changed"),
            (Column(float, min=10), Column(float, min=0), "non_breaking", "field_changed"),
        ],
    )
    def test_min(self, old_col: Column, new_col: Column, expected: str, kind: str) -> None:
        change = _diff_one(old_col, new_col)
        assert change.attribute == "min"
        assert change.classification == expected
        assert change.kind == kind

    @pytest.mark.parametrize(
        ("old_col", "new_col", "expected", "kind"),
        [
            (Column(float), Column(float, max=100), "breaking", "field_added"),
            (Column(float, max=100), Column(float), "non_breaking", "field_removed"),
            (Column(float, max=100), Column(float, max=50), "breaking", "field_changed"),
            (Column(float, max=50), Column(float, max=100), "non_breaking", "field_changed"),
        ],
    )
    def test_max(self, old_col: Column, new_col: Column, expected: str, kind: str) -> None:
        change = _diff_one(old_col, new_col)
        assert change.attribute == "max"
        assert change.classification == expected
        assert change.kind == kind

    def test_incomparable_bound_change_is_breaking(self) -> None:
        # dtype flips from numeric to timestamp alongside the bound
        old = Contract(name="t", columns={"c": Column(int, min=0)})
        new = Contract(name="t", columns={"c": Column("timestamp", min=datetime(2026, 1, 1))})
        changes = {c.attribute: c for c in diff_contracts(old, new).changes}
        assert changes["min"].breaking


class TestAllowed:
    def test_adding_allowed_set_is_breaking(self) -> None:
        change = _diff_one(Column(str), Column(str, allowed=["A", "B"]))
        assert change.kind == "field_added"
        assert change.breaking

    def test_removing_allowed_set_is_non_breaking(self) -> None:
        change = _diff_one(Column(str, allowed=["A", "B"]), Column(str))
        assert change.kind == "field_removed"
        assert change.classification == "non_breaking"

    def test_widening_allowed_set_is_non_breaking(self) -> None:
        change = _diff_one(Column(str, allowed=["A", "B"]), Column(str, allowed=["A", "B", "C"]))
        assert change.classification == "non_breaking"
        assert change.reason == "widened allowed set"

    def test_narrowing_allowed_set_is_breaking(self) -> None:
        change = _diff_one(Column(str, allowed=["A", "B", "C"]), Column(str, allowed=["A", "B"]))
        assert change.breaking
        assert change.reason == "narrowed allowed set"

    def test_mixed_allowed_change_is_breaking(self) -> None:
        change = _diff_one(Column(str, allowed=["A", "B"]), Column(str, allowed=["B", "C"]))
        assert change.breaking

    def test_allowed_order_only_is_not_a_change(self) -> None:
        assert diff_contracts(
            Contract(name="t", columns={"c": Column(str, allowed=["A", "B"])}),
            Contract(name="t", columns={"c": Column(str, allowed=["B", "A"])}),
        ).is_empty


class TestPattern:
    def test_adding_pattern_is_breaking(self) -> None:
        assert _diff_one(Column(str), Column(str, pattern=r"^\d+$")).breaking

    def test_removing_pattern_is_non_breaking(self) -> None:
        change = _diff_one(Column(str, pattern=r"^\d+$"), Column(str))
        assert change.classification == "non_breaking"

    def test_changing_pattern_is_breaking(self) -> None:
        change = _diff_one(Column(str, pattern=r"^\d+$"), Column(str, pattern=r"^\d{3}$"))
        assert change.kind == "field_changed"
        assert change.breaking


class TestFreshness:
    @pytest.mark.parametrize(
        ("old_col", "new_col", "expected"),
        [
            (Column("timestamp"), Column("timestamp", freshness_minutes=60), "breaking"),
            (Column("timestamp", freshness_minutes=60), Column("timestamp"), "non_breaking"),
            (
                Column("timestamp", freshness_minutes=60),
                Column("timestamp", freshness_minutes=30),
                "breaking",
            ),
            (
                Column("timestamp", freshness_minutes=30),
                Column("timestamp", freshness_minutes=60),
                "non_breaking",
            ),
        ],
    )
    def test_freshness(self, old_col: Column, new_col: Column, expected: str) -> None:
        assert _diff_one(old_col, new_col).classification == expected


class TestTableRules:
    def test_added_rule_is_breaking(self) -> None:
        old = Contract(name="t", rules=["row_count > 0"])
        new = Contract(name="t", rules=["row_count > 0", "row_count < 100"])
        (change,) = diff_contracts(old, new).changes
        assert change.kind == "table_rule_added"
        assert change.new == "row_count < 100"
        assert change.breaking

    def test_removed_rule_is_non_breaking(self) -> None:
        old = Contract(name="t", rules=["row_count > 0", "row_count < 100"])
        new = Contract(name="t", rules=["row_count > 0"])
        (change,) = diff_contracts(old, new).changes
        assert change.kind == "table_rule_removed"
        assert change.classification == "non_breaking"

    def test_reworded_rule_is_a_remove_and_an_add(self) -> None:
        old = Contract(name="t", rules=["null_rate('a') < 0.5"])
        new = Contract(name="t", rules=["null_rate('a') < 0.2"])
        kinds = sorted(c.kind for c in diff_contracts(old, new).changes)
        assert kinds == ["table_rule_added", "table_rule_removed"]


class TestCrossColumnRules:
    def _rule(self, right: str = "created_at") -> CrossColumnRule:
        return CrossColumnRule(name="ordering", left="shipped_at", op=">=", right=right)

    def test_added_rule_is_breaking(self) -> None:
        old = Contract(name="t")
        new = Contract(name="t", cross_column_rules=[self._rule()])
        (change,) = diff_contracts(old, new).changes
        assert change.kind == "cross_column_rule_added"
        assert change.breaking

    def test_removed_rule_is_non_breaking(self) -> None:
        old = Contract(name="t", cross_column_rules=[self._rule()])
        new = Contract(name="t")
        (change,) = diff_contracts(old, new).changes
        assert change.kind == "cross_column_rule_removed"
        assert change.classification == "non_breaking"

    def test_redefined_rule_is_breaking(self) -> None:
        old = Contract(name="t", cross_column_rules=[self._rule(right="created_at")])
        new = Contract(name="t", cross_column_rules=[self._rule(right="ordered_at")])
        (change,) = diff_contracts(old, new).changes
        assert change.kind == "cross_column_rule_changed"
        assert change.breaking

    def test_error_message_only_change_is_ignored(self) -> None:
        old = Contract(
            name="t",
            cross_column_rules=[CrossColumnRule(name="r", left="a", op=">=", right="b")],
        )
        new = Contract(
            name="t",
            cross_column_rules=[
                CrossColumnRule(name="r", left="a", op=">=", right="b", error_message="changed")
            ],
        )
        assert diff_contracts(old, new).is_empty


class TestOutput:
    def _sample(self) -> tuple[Contract, Contract]:
        old = Contract(
            name="orders",
            columns={
                "amount": Column(float, min=0),
                "currency": Column(str, allowed=["USD", "EUR"]),
                "ts": Column("timestamp", min=datetime(2026, 1, 1)),
            },
        )
        new = Contract(
            name="orders",
            columns={
                "amount": Column(float, min=10),
                "currency": Column(str, allowed=["USD", "EUR", "JPY"]),
                "ts": Column("timestamp", min=datetime(2026, 6, 1)),
                "discount": Column(float),
            },
        )
        return old, new

    def test_to_dict_schema_is_stable(self) -> None:
        result = diff_contracts(*self._sample())
        data = result.to_dict()
        assert set(data) == {
            "old_contract",
            "new_contract",
            "summary",
            "has_breaking",
            "changes",
        }
        assert set(data["summary"]) == {"total", "breaking", "non_breaking"}
        assert data["summary"]["total"] == len(data["changes"])
        for change in data["changes"]:
            assert set(change) == {
                "kind",
                "classification",
                "reason",
                "column",
                "attribute",
                "old",
                "new",
            }
            assert change["classification"] in {"breaking", "non_breaking"}

    def test_to_dict_is_json_serializable_including_datetimes(self) -> None:
        result = diff_contracts(*self._sample())
        dumped = json.dumps(result.to_dict())
        assert "2026-06-01" in dumped

    def test_render_text_groups_by_severity(self) -> None:
        text = diff_contracts(*self._sample()).render_text()
        assert text.startswith("orders: 4 changes (2 breaking)")
        assert "  BREAKING" in text
        assert "  non-breaking" in text
        assert "stricter lower bound" in text

    def test_render_text_no_changes(self) -> None:
        c = Contract(name="orders", columns={"a": Column(str)})
        assert diff_contracts(c, c).render_text() == "orders: no changes"

    def test_contract_rename_is_reflected(self) -> None:
        old = Contract(name="orders_v1", columns={"a": Column(str)})
        new = Contract(name="orders_v2", columns={"a": Column(str)})
        result = diff_contracts(old, new)
        assert result.old_name == "orders_v1"
        assert result.new_name == "orders_v2"
        assert result.is_empty
        assert result.render_text() == "orders_v1 -> orders_v2: no changes"


class TestInputTypes:
    def test_accepts_yaml_paths(self, tmp_path: Path) -> None:
        old_path = tmp_path / "v1.yaml"
        new_path = tmp_path / "v2.yaml"
        Contract(name="orders", columns={"amount": Column(float, min=0)}).to_yaml(old_path)
        Contract(name="orders", columns={"amount": Column(float, min=5)}).to_yaml(new_path)

        result = diff_contracts(old_path, new_path)
        assert result.has_breaking
        assert diff_contracts(str(old_path), str(new_path)).has_breaking

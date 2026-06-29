"""Tests for cross-column validation rules."""

from __future__ import annotations

import pandas as pd
import polars as pl
import pytest

from dqflow import Column, Contract, CrossColumnRule
from dqflow.engines.pandas import PandasEngine
from dqflow.engines.polars import PolarsEngine


class TestCrossColumnRuleValidation:
    """CrossColumnRule raises on invalid construction."""

    def test_must_provide_check_or_structured(self) -> None:
        with pytest.raises(ValueError, match="provide either"):
            CrossColumnRule(name="bad")

    def test_cannot_provide_both(self) -> None:
        with pytest.raises(ValueError, match="not both"):
            CrossColumnRule(
                name="bad",
                check=lambda df: df["a"] > df["b"],
                left="a",
                op=">",
                right="b",
            )

    def test_unknown_op_raises(self) -> None:
        with pytest.raises(ValueError, match="[Uu]nsupported op"):
            CrossColumnRule(name="bad", left="a", op="??", right="b")

    def test_right_zero_is_valid(self) -> None:
        rule = CrossColumnRule(name="positive", left="amount", op=">", right=0)
        assert rule.right == 0


class TestStructuredRulePandas:
    """Structured cross-column rules evaluated by PandasEngine."""

    def _contract(self, *rules: CrossColumnRule) -> Contract:
        return Contract(
            name="test",
            columns={"start": Column(int), "end": Column(int)},
            cross_column_rules=list(rules),
        )

    def test_passes_when_all_rows_satisfy(self) -> None:
        df = pd.DataFrame({"start": [1, 2, 3], "end": [4, 5, 6]})
        result = self._contract(
            CrossColumnRule(name="end_after_start", left="end", op=">=", right="start")
        ).validate(df)

        check = next(c for c in result.checks if c.name == "cross_column:end_after_start")
        assert check.passed
        assert check.details["failing_rows"] == 0

    def test_fails_and_counts_failing_rows(self) -> None:
        df = pd.DataFrame({"start": [1, 5, 3], "end": [4, 2, 6]})
        result = self._contract(
            CrossColumnRule(
                name="end_after_start",
                left="end",
                op=">=",
                right="start",
                error_message="end must be >= start",
            )
        ).validate(df)

        check = next(c for c in result.checks if c.name == "cross_column:end_after_start")
        assert not check.passed
        assert check.details["failing_rows"] == 1
        assert check.message == "end must be >= start"

    def test_right_as_literal_value(self) -> None:
        df = pd.DataFrame({"start": [1, 2, 3], "end": [10, -1, 5]})
        contract = Contract(
            name="test",
            columns={"end": Column(int)},
            cross_column_rules=[CrossColumnRule(name="positive_end", left="end", op=">", right=0)],
        )
        result = contract.validate(df)
        check = next(c for c in result.checks if c.name == "cross_column:positive_end")
        assert not check.passed
        assert check.details["failing_rows"] == 1

    def test_all_operators(self) -> None:
        df = pd.DataFrame({"a": [5], "b": [5]})
        contract = Contract(name="test", columns={"a": Column(int), "b": Column(int)})

        for op, expected in [
            (">=", True),
            ("<=", True),
            ("==", True),
            ("!=", False),
            (">", False),
            ("<", False),
        ]:
            contract.cross_column_rules = [
                CrossColumnRule(name="check", left="a", op=op, right="b")
            ]
            result = contract.validate(df)
            check = next(c for c in result.checks if c.name == "cross_column:check")
            assert check.passed == expected, f"op={op!r} expected passed={expected}"

    def test_missing_column_returns_failed_check(self) -> None:
        df = pd.DataFrame({"start": [1, 2, 3]})
        contract = Contract(
            name="test",
            columns={"start": Column(int)},
            cross_column_rules=[
                CrossColumnRule(name="bad", left="nonexistent", op=">", right="start")
            ],
        )
        result = contract.validate(df)
        check = next(c for c in result.checks if c.name == "cross_column:bad")
        assert not check.passed
        assert "nonexistent" in check.message


class TestCallableRulePandas:
    """Callable cross-column rules evaluated by PandasEngine."""

    def test_callable_passes(self) -> None:
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        contract = Contract(
            name="test",
            columns={"a": Column(int), "b": Column(int)},
            cross_column_rules=[CrossColumnRule(name="b_gt_a", check=lambda d: d["b"] > d["a"])],
        )
        result = contract.validate(df)
        check = next(c for c in result.checks if c.name == "cross_column:b_gt_a")
        assert check.passed
        assert check.details["failing_rows"] == 0

    def test_callable_fails_with_correct_count(self) -> None:
        df = pd.DataFrame({"a": [1, 10, 3], "b": [4, 5, 6]})
        contract = Contract(
            name="test",
            columns={"a": Column(int), "b": Column(int)},
            cross_column_rules=[
                CrossColumnRule(
                    name="b_gt_a",
                    check=lambda d: d["b"] > d["a"],
                    error_message="b must be greater than a",
                )
            ],
        )
        result = contract.validate(df)
        check = next(c for c in result.checks if c.name == "cross_column:b_gt_a")
        assert not check.passed
        assert check.details["failing_rows"] == 1
        assert check.message == "b must be greater than a"


class TestCrossColumnEngineConsistency:
    """PandasEngine and PolarsEngine produce identical CheckResult structures."""

    def test_structured_rule_consistency(self) -> None:
        rule = CrossColumnRule(
            name="end_after_start",
            left="end",
            op=">=",
            right="start",
            error_message="end must be >= start",
        )
        contract = Contract(
            name="test",
            columns={"start": Column(int), "end": Column(int)},
            cross_column_rules=[rule],
        )

        pdf = pd.DataFrame({"start": [1, 5, 3], "end": [4, 2, 6]})
        pldf = pl.DataFrame({"start": [1, 5, 3], "end": [4, 2, 6]})

        pandas_result = PandasEngine().validate(pdf, contract)
        polars_result = PolarsEngine().validate(pldf, contract)

        p_check = next(c for c in pandas_result.checks if c.name == "cross_column:end_after_start")
        pl_check = next(c for c in polars_result.checks if c.name == "cross_column:end_after_start")

        assert p_check.passed == pl_check.passed
        assert p_check.message == pl_check.message
        assert p_check.details["failing_rows"] == pl_check.details["failing_rows"]

    def test_literal_right_consistency(self) -> None:
        contract = Contract(
            name="test",
            columns={"amount": Column(float)},
            cross_column_rules=[CrossColumnRule(name="positive", left="amount", op=">", right=0)],
        )
        pdf = pd.DataFrame({"amount": [10.0, -5.0, 20.0]})
        pldf = pl.DataFrame({"amount": [10.0, -5.0, 20.0]})

        p_check = next(
            c
            for c in PandasEngine().validate(pdf, contract).checks
            if c.name == "cross_column:positive"
        )
        pl_check = next(
            c
            for c in PolarsEngine().validate(pldf, contract).checks
            if c.name == "cross_column:positive"
        )

        assert p_check.passed == pl_check.passed
        assert p_check.details["failing_rows"] == pl_check.details["failing_rows"]


class TestCrossColumnRuleYaml:
    """YAML serialization and deserialization of cross_column_rules."""

    def test_from_yaml(self, tmp_path: pytest.TempPathFactory) -> None:
        yaml_content = """\
name: orders
columns:
  start_date:
    dtype: integer
  end_date:
    dtype: integer
cross_column_rules:
  - name: end_after_start
    left: end_date
    op: ">="
    right: start_date
    error_message: "end_date must not precede start_date"
"""
        f = tmp_path / "contract.yaml"  # type: ignore[operator]
        f.write_text(yaml_content)

        contract = Contract.from_yaml(f)
        assert len(contract.cross_column_rules) == 1
        rule = contract.cross_column_rules[0]
        assert rule.name == "end_after_start"
        assert rule.left == "end_date"
        assert rule.op == ">="
        assert rule.right == "start_date"
        assert rule.error_message == "end_date must not precede start_date"

    def test_from_yaml_literal_right(self, tmp_path: pytest.TempPathFactory) -> None:
        yaml_content = """\
name: orders
columns:
  amount:
    dtype: float
cross_column_rules:
  - name: positive_amount
    left: amount
    op: ">"
    right: 0
"""
        f = tmp_path / "contract.yaml"  # type: ignore[operator]
        f.write_text(yaml_content)

        contract = Contract.from_yaml(f)
        assert contract.cross_column_rules[0].right == 0

    def test_to_yaml_round_trip(self, tmp_path: pytest.TempPathFactory) -> None:
        contract = Contract(
            name="orders",
            columns={"start": Column(int), "end": Column(int)},
            cross_column_rules=[
                CrossColumnRule(
                    name="end_after_start",
                    left="end",
                    op=">=",
                    right="start",
                    error_message="end must be >= start",
                )
            ],
        )
        path = tmp_path / "out.yaml"  # type: ignore[operator]
        contract.to_yaml(path)
        reloaded = Contract.from_yaml(path)

        assert len(reloaded.cross_column_rules) == 1
        r = reloaded.cross_column_rules[0]
        assert r.name == "end_after_start"
        assert r.left == "end"
        assert r.op == ">="
        assert r.right == "start"
        assert r.error_message == "end must be >= start"

    def test_callable_rules_not_serialized(self, tmp_path: pytest.TempPathFactory) -> None:
        contract = Contract(
            name="test",
            columns={"a": Column(int), "b": Column(int)},
            cross_column_rules=[
                CrossColumnRule(name="callable_rule", check=lambda d: d["a"] > d["b"]),
                CrossColumnRule(name="structured_rule", left="a", op=">", right="b"),
            ],
        )
        path = tmp_path / "out.yaml"  # type: ignore[operator]
        contract.to_yaml(path)
        reloaded = Contract.from_yaml(path)

        assert len(reloaded.cross_column_rules) == 1
        assert reloaded.cross_column_rules[0].name == "structured_rule"

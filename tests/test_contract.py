"""Tests for Contract class."""

import pandas as pd

from dqflow import Contract


class TestContract:
    """Tests for Contract definition and validation."""

    def test_basic_contract(self) -> None:
        contract = Contract(name="test")
        assert contract.name == "test"
        assert contract.columns == {}
        assert contract.rules == []

    def test_contract_with_columns(self, sample_contract: Contract) -> None:
        assert sample_contract.name == "orders"
        assert "order_id" in sample_contract.columns
        assert "amount" in sample_contract.columns
        assert "currency" in sample_contract.columns

    def test_validate_passing(self, sample_contract: Contract, sample_df: pd.DataFrame) -> None:
        result = sample_contract.validate(sample_df)
        assert result.ok is True
        assert result.contract_name == "orders"

    def test_validate_missing_column(self, sample_contract: Contract) -> None:
        df = pd.DataFrame({"order_id": ["A001"]})
        result = sample_contract.validate(df)
        assert result.ok is False
        assert any("amount" in c.name and not c.passed for c in result.checks)

    def test_validate_null_violation(
        self, sample_contract: Contract, df_with_violations: pd.DataFrame
    ) -> None:
        result = sample_contract.validate(df_with_violations)
        assert result.ok is False
        failed_names = [c.name for c in result.failed_checks]
        assert "not_null:order_id" in failed_names

    def test_validate_min_violation(
        self, sample_contract: Contract, df_with_violations: pd.DataFrame
    ) -> None:
        result = sample_contract.validate(df_with_violations)
        failed_names = [c.name for c in result.failed_checks]
        assert "min:amount" in failed_names

    def test_validate_allowed_violation(
        self, sample_contract: Contract, df_with_violations: pd.DataFrame
    ) -> None:
        result = sample_contract.validate(df_with_violations)
        failed_names = [c.name for c in result.failed_checks]
        assert "allowed:currency" in failed_names


# (parallel validation regression test)
class TestParallelValidation:
    """Ensure parallel validation does not change correctness."""

    def test_parallel_column_validation_consistency(
        self, sample_contract: Contract, sample_df: pd.DataFrame
    ) -> None:

        from dqflow.engines.pandas import PandasEngine

        engine = PandasEngine()

        result1 = engine.validate(sample_df, sample_contract)
        result2 = engine.validate(sample_df, sample_contract)

        # Core correctness checks
        assert result1.ok == result2.ok
        assert result1.contract_name == result2.contract_name
        assert len(result1.checks) == len(result2.checks)

        # Compare check names (order-independent)
        assert sorted(c.name for c in result1.checks) == sorted(c.name for c in result2.checks)

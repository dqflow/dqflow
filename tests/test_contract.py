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


class TestParallelValidation:
    """Ensure sequential vs parallel execution produces identical results."""

    def test_parallel_vs_sequential_consistency(
        self,
        sample_contract: Contract,
        sample_df: pd.DataFrame,
    ) -> None:

        from dqflow.engines.pandas import PandasEngine

        engine = PandasEngine()

        result_seq = engine.validate(
            sample_df,
            sample_contract,
            parallel=False,
        )

        result_par = engine.validate(
            sample_df,
            sample_contract,
            parallel=True,
        )

        assert result_seq.ok == result_par.ok
        assert result_seq.contract_name == result_par.contract_name

        # Same number of checks
        assert len(result_seq.checks) == len(result_par.checks)

        seq_names = sorted(c.name for c in result_seq.checks)
        par_names = sorted(c.name for c in result_par.checks)

        assert seq_names == par_names

        seq_map = {c.name: c.passed for c in result_seq.checks}
        par_map = {c.name: c.passed for c in result_par.checks}

        assert seq_map == par_map

"""Tests for Contract class."""

from pathlib import Path

import pandas as pd
import pytest

from dqflow import Contract
from dqflow.schema import (
    SCHEMA_VERSION,
    ContractParseError,
    ContractSchemaError,
    ContractVersionError,
)


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
    """The ``parallel`` context flag must not change results (real parallelism is #22)."""

    def test_parallel_vs_sequential_consistency(
        self,
        sample_contract: Contract,
        sample_df: pd.DataFrame,
    ) -> None:
        from dqflow.engines.pandas import PandasEngine
        from dqflow.execution.context import ExecutionContext

        engine = PandasEngine()

        result_seq = engine.validate(
            sample_df,
            sample_contract,
            context=ExecutionContext(parallel=False),
        )

        result_par = engine.validate(
            sample_df,
            sample_contract,
            context=ExecutionContext(parallel=True),
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


class TestFromYamlValidation:
    """``Contract.from_yaml`` validates against the schema before construction."""

    def _write(self, tmp_path: Path, text: str) -> Path:
        path = tmp_path / "contract.yaml"
        path.write_text(text)
        return path

    def test_valid_contract_loads(self, tmp_path: Path) -> None:
        path = self._write(
            tmp_path,
            'schema_version: "1.0"\nname: orders\ncolumns:\n  id: {dtype: string}\n',
        )
        contract = Contract.from_yaml(path)
        assert contract.name == "orders"
        assert "id" in contract.columns

    def test_contract_without_schema_version_still_loads(self, tmp_path: Path) -> None:
        path = self._write(tmp_path, "name: orders\ncolumns:\n  id: {dtype: string}\n")
        assert Contract.from_yaml(path).name == "orders"

    def test_malformed_yaml_raises_parse_error(self, tmp_path: Path) -> None:
        path = self._write(tmp_path, "name: orders\ncolumns: {a: [1, 2\n")
        with pytest.raises(ContractParseError):
            Contract.from_yaml(path)

    def test_structural_error_raises_schema_error_with_diagnostics(self, tmp_path: Path) -> None:
        path = self._write(
            tmp_path,
            'schema_version: "1.0"\nname: orders\ncolumns:\n'
            "  amount: {dtype: float, min: 10, max: 1, bogus: 1}\n",
        )
        with pytest.raises(ContractSchemaError) as excinfo:
            Contract.from_yaml(path)
        codes = {d.code for d in excinfo.value.diagnostics}
        assert {"min-greater-than-max", "unknown-field"} <= codes
        assert all(d.is_error for d in excinfo.value.diagnostics)

    def test_unsupported_version_raises_version_error(self, tmp_path: Path) -> None:
        path = self._write(
            tmp_path, 'schema_version: "2.0"\nname: orders\ncolumns:\n  a: {dtype: string}\n'
        )
        with pytest.raises(ContractVersionError):
            Contract.from_yaml(path)


class TestToYamlSchemaVersion:
    def test_to_yaml_declares_schema_version(self, tmp_path: Path) -> None:
        from dqflow import Column

        path = tmp_path / "out.yaml"
        Contract(name="orders", columns={"a": Column(str)}).to_yaml(path)
        text = path.read_text()
        assert text.splitlines()[0] == f"schema_version: '{SCHEMA_VERSION}'"

    def test_round_trip_through_yaml(self, tmp_path: Path) -> None:
        from dqflow import Column

        original = Contract(
            name="orders",
            columns={"a": Column(str, not_null=True)},
            rules=["row_count > 0"],
        )
        path = tmp_path / "rt.yaml"
        original.to_yaml(path)
        reloaded = Contract.from_yaml(path)
        assert reloaded.name == original.name
        assert list(reloaded.columns) == list(original.columns)
        assert reloaded.rules == original.rules

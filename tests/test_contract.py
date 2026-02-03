"""Tests for Contract class."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from dqflow import Contract
from dqflow.column import Column


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


class TestContractYAML:
    """Tests for YAML serialization."""

    def test_from_yaml(self) -> None:
        with TemporaryDirectory() as tmpdir:
            yaml_content = """
name: orders
columns:
  order_id:
    type: string
    not_null: true
  amount:
    type: float
    min: 0
rules:
  - row_count > 0
"""
            path = Path(tmpdir) / "contract.yaml"
            path.write_text(yaml_content)

            contract = Contract.from_yaml(path)
            assert contract.name == "orders"
            assert "order_id" in contract.columns
            assert contract.columns["order_id"].not_null is True
            assert contract.columns["amount"].min == 0
            assert "row_count > 0" in contract.rules

    def test_to_yaml(self, sample_contract: Contract) -> None:
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "output.yaml"
            sample_contract.to_yaml(path)

            loaded = Contract.from_yaml(path)
            assert loaded.name == sample_contract.name
            assert set(loaded.columns.keys()) == set(sample_contract.columns.keys())

    def test_roundtrip(self, sample_contract: Contract) -> None:
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "roundtrip.yaml"
            sample_contract.to_yaml(path)
            loaded = Contract.from_yaml(path)

            assert loaded.name == sample_contract.name
            assert loaded.rules == sample_contract.rules
            for col_name, col in sample_contract.columns.items():
                assert col_name in loaded.columns
                loaded_col = loaded.columns[col_name]
                assert loaded_col.not_null == col.not_null
                assert loaded_col.min == col.min
                assert loaded_col.max == col.max


class TestValidationResult:
    """Tests for validation result output."""

    def test_summary(self, sample_contract: Contract, sample_df: pd.DataFrame) -> None:
        result = sample_contract.validate(sample_df)
        summary = result.summary()
        assert "orders" in summary
        assert "passed" in summary

    def test_to_dict(self, sample_contract: Contract, sample_df: pd.DataFrame) -> None:
        result = sample_contract.validate(sample_df)
        d = result.to_dict()
        assert d["contract_name"] == "orders"
        assert d["ok"] is True
        assert "checks" in d
        assert isinstance(d["checks"], list)

    def test_failed_checks(
        self, sample_contract: Contract, df_with_violations: pd.DataFrame
    ) -> None:
        result = sample_contract.validate(df_with_violations)
        assert len(result.failed_checks) > 0
        for check in result.failed_checks:
            assert not check.passed


class TestCustomChecks:
    """Tests for custom validation functions."""

    def test_custom_check_passing(self) -> None:
        """Test custom check that passes validation."""

        def is_positive(value: float) -> bool:
            return value > 0

        contract = Contract(
            name="test",
            columns={
                "value": Column(float, custom=is_positive),
            },
        )

        df = pd.DataFrame({"value": [1.0, 2.5, 10.0]})
        result = contract.validate(df)

        assert result.ok
        custom_checks = [c for c in result.checks if "custom:value" in c.name]
        assert len(custom_checks) == 1
        assert custom_checks[0].passed

    def test_custom_check_failing(self) -> None:
        """Test custom check that fails validation."""

        def is_email(value: str) -> bool:
            return "@" in str(value) and "." in str(value)

        contract = Contract(
            name="test",
            columns={
                "email": Column(str, custom=is_email),
            },
        )

        df = pd.DataFrame({"email": ["user@example.com", "invalid-email", "test@domain.org"]})
        result = contract.validate(df)

        assert not result.ok
        custom_checks = [c for c in result.checks if "custom:email" in c.name]
        assert len(custom_checks) == 1
        assert not custom_checks[0].passed
        assert "1" in custom_checks[0].message  # 1 value failed

    def test_custom_check_lambda(self) -> None:
        """Test custom check using lambda function."""
        contract = Contract(
            name="test",
            columns={
                "age": Column(int, custom=lambda x: 18 <= x <= 100),
            },
        )

        df = pd.DataFrame({"age": [25, 30, 150, 45]})  # 150 is out of range
        result = contract.validate(df)

        assert not result.ok
        custom_checks = [c for c in result.checks if "custom:age" in c.name]
        assert len(custom_checks) == 1
        assert not custom_checks[0].passed

    def test_custom_check_with_other_constraints(self) -> None:
        """Test custom check combined with other constraints."""

        def is_even(value: int) -> bool:
            return value % 2 == 0

        contract = Contract(
            name="test",
            columns={
                "count": Column(int, not_null=True, min=0, max=100, custom=is_even),
            },
        )

        df = pd.DataFrame({"count": [2, 4, 6, 8]})
        result = contract.validate(df)

        assert result.ok
        # Check that all constraints passed
        assert any("not_null:count" in c.name and c.passed for c in result.checks)
        assert any("min:count" in c.name and c.passed for c in result.checks)
        assert any("max:count" in c.name and c.passed for c in result.checks)
        assert any("custom:count" in c.name and c.passed for c in result.checks)

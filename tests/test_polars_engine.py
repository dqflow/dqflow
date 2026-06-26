"""Tests for PolarsEngine."""

from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest

pl = pytest.importorskip("polars")

from dqflow import Column, Contract  # noqa: E402
from dqflow.engines.pandas import PandasEngine  # noqa: E402
from dqflow.engines.polars import PolarsEngine  # noqa: E402


@pytest.fixture
def engine() -> PolarsEngine:
    return PolarsEngine()


@pytest.fixture
def sample_pl_df() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "order_id": ["A001", "A002", "A003"],
            "amount": [100.0, 250.5, 75.0],
            "currency": ["USD", "EUR", "USD"],
            "created_at": [
                datetime.now(timezone.utc) - timedelta(minutes=30),
                datetime.now(timezone.utc) - timedelta(minutes=20),
                datetime.now(timezone.utc) - timedelta(minutes=10),
            ],
        }
    )


@pytest.fixture
def sample_contract() -> Contract:
    return Contract(
        name="orders",
        columns={
            "order_id": Column(str, not_null=True),
            "amount": Column(float, min=0),
            "currency": Column(str, allowed=["USD", "EUR"]),
        },
        rules=["row_count > 0"],
    )


@pytest.fixture
def violations_pl_df() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "order_id": ["A001", None, "A003"],
            "amount": [100.0, -50.0, 75.0],
            "currency": ["USD", "GBP", "USD"],
        }
    )


class TestPolarsEngineBasic:
    def test_validate_passing(
        self, engine: PolarsEngine, sample_pl_df: pl.DataFrame, sample_contract: Contract
    ) -> None:
        result = engine.validate(sample_pl_df, sample_contract)
        assert result.ok is True
        assert result.contract_name == "orders"

    def test_validate_missing_column(self, engine: PolarsEngine, sample_contract: Contract) -> None:
        df = pl.DataFrame({"order_id": ["A001"]})
        result = engine.validate(df, sample_contract)
        assert result.ok is False
        assert any("amount" in c.name and not c.passed for c in result.checks)

    def test_validate_null_violation(
        self,
        engine: PolarsEngine,
        sample_contract: Contract,
        violations_pl_df: pl.DataFrame,
    ) -> None:
        result = engine.validate(violations_pl_df, sample_contract)
        assert result.ok is False
        assert "not_null:order_id" in [c.name for c in result.failed_checks]

    def test_validate_min_violation(
        self,
        engine: PolarsEngine,
        sample_contract: Contract,
        violations_pl_df: pl.DataFrame,
    ) -> None:
        result = engine.validate(violations_pl_df, sample_contract)
        assert "min:amount" in [c.name for c in result.failed_checks]

    def test_validate_allowed_violation(
        self,
        engine: PolarsEngine,
        sample_contract: Contract,
        violations_pl_df: pl.DataFrame,
    ) -> None:
        result = engine.validate(violations_pl_df, sample_contract)
        assert "allowed:currency" in [c.name for c in result.failed_checks]

    def test_validate_rule(self, engine: PolarsEngine, sample_pl_df: pl.DataFrame) -> None:
        contract = Contract(name="test", rules=["row_count > 0", "row_count > 100"])
        result = engine.validate(sample_pl_df, contract)
        check_map = {c.name: c.passed for c in result.checks}
        assert check_map["rule:row_count > 0"] is True
        assert check_map["rule:row_count > 100"] is False


class TestPolarsEngineConstraints:
    def test_max_constraint_passing(self, engine: PolarsEngine) -> None:
        df = pl.DataFrame({"score": [10.0, 20.0, 30.0]})
        contract = Contract(name="test", columns={"score": Column(float, max=50.0)})
        result = engine.validate(df, contract)
        assert result.ok is True

    def test_max_constraint_failing(self, engine: PolarsEngine) -> None:
        df = pl.DataFrame({"score": [10.0, 20.0, 100.0]})
        contract = Contract(name="test", columns={"score": Column(float, max=50.0)})
        result = engine.validate(df, contract)
        assert "max:score" in [c.name for c in result.failed_checks]

    def test_unique_constraint_passing(self, engine: PolarsEngine) -> None:
        df = pl.DataFrame({"id": [1, 2, 3]})
        contract = Contract(name="test", columns={"id": Column(int, unique=True)})
        result = engine.validate(df, contract)
        assert result.ok is True

    def test_unique_constraint_failing(self, engine: PolarsEngine) -> None:
        df = pl.DataFrame({"id": [1, 2, 2]})
        contract = Contract(name="test", columns={"id": Column(int, unique=True)})
        result = engine.validate(df, contract)
        assert "unique:id" in [c.name for c in result.failed_checks]

    def test_pattern_constraint_passing(self, engine: PolarsEngine) -> None:
        df = pl.DataFrame({"code": ["A001", "A002", "A003"]})
        contract = Contract(name="test", columns={"code": Column(str, pattern=r"A\d{3}")})
        result = engine.validate(df, contract)
        assert result.ok is True

    def test_pattern_constraint_failing(self, engine: PolarsEngine) -> None:
        df = pl.DataFrame({"code": ["A001", "B999", "X123"]})
        contract = Contract(name="test", columns={"code": Column(str, pattern=r"A\d{3}")})
        result = engine.validate(df, contract)
        assert "pattern:code" in [c.name for c in result.failed_checks]
        detail = next(c for c in result.checks if c.name == "pattern:code")
        assert detail.details["invalid_count"] == 2

    def test_custom_constraint_passing(self, engine: PolarsEngine) -> None:
        df = pl.DataFrame({"amount": [10.0, 20.0, 30.0]})
        contract = Contract(name="test", columns={"amount": Column(float, custom=lambda x: x > 0)})
        result = engine.validate(df, contract)
        assert result.ok is True

    def test_custom_constraint_failing(self, engine: PolarsEngine) -> None:
        df = pl.DataFrame({"amount": [10.0, -5.0, 30.0]})
        contract = Contract(name="test", columns={"amount": Column(float, custom=lambda x: x > 0)})
        result = engine.validate(df, contract)
        assert "custom:amount" in [c.name for c in result.failed_checks]

    def test_freshness_passing(self, engine: PolarsEngine) -> None:
        df = pl.DataFrame(
            {
                "ts": [
                    datetime.now(timezone.utc) - timedelta(minutes=5),
                    datetime.now(timezone.utc) - timedelta(minutes=2),
                ]
            }
        )
        contract = Contract(name="test", columns={"ts": Column(datetime, freshness_minutes=60)})
        result = engine.validate(df, contract)
        assert result.ok is True

    def test_freshness_failing(self, engine: PolarsEngine) -> None:
        df = pl.DataFrame(
            {
                "ts": [
                    datetime.now(timezone.utc) - timedelta(hours=3),
                    datetime.now(timezone.utc) - timedelta(hours=2),
                ]
            }
        )
        contract = Contract(name="test", columns={"ts": Column(datetime, freshness_minutes=60)})
        result = engine.validate(df, contract)
        assert "freshness:ts" in [c.name for c in result.failed_checks]


class TestPolarsEngineLazyFrame:
    def test_accepts_lazyframe(
        self, engine: PolarsEngine, sample_pl_df: pl.DataFrame, sample_contract: Contract
    ) -> None:
        lazy_df = sample_pl_df.lazy()
        result = engine.validate(lazy_df, sample_contract)
        assert result.ok is True
        assert result.contract_name == "orders"

    def test_lazyframe_violations(
        self, engine: PolarsEngine, violations_pl_df: pl.DataFrame, sample_contract: Contract
    ) -> None:
        result = engine.validate(violations_pl_df.lazy(), sample_contract)
        assert result.ok is False
        failed_names = [c.name for c in result.failed_checks]
        assert "not_null:order_id" in failed_names
        assert "min:amount" in failed_names
        assert "allowed:currency" in failed_names


class TestCrossEngineConsistency:
    """Ensure PolarsEngine produces the same check outcomes as PandasEngine."""

    def test_passing_contract_consistency(self, sample_contract: Contract) -> None:
        pd_df = pd.DataFrame(
            {
                "order_id": ["A001", "A002", "A003"],
                "amount": [100.0, 250.5, 75.0],
                "currency": ["USD", "EUR", "USD"],
            }
        )
        pl_df = pl.from_pandas(pd_df)

        pandas_result = PandasEngine().validate(pd_df, sample_contract)
        polars_result = PolarsEngine().validate(pl_df, sample_contract)

        assert pandas_result.ok == polars_result.ok

        pandas_map = {c.name: c.passed for c in pandas_result.checks}
        polars_map = {c.name: c.passed for c in polars_result.checks}
        assert pandas_map == polars_map

    def test_violations_consistency(self, sample_contract: Contract) -> None:
        pd_df = pd.DataFrame(
            {
                "order_id": ["A001", None, "A003"],
                "amount": [100.0, -50.0, 75.0],
                "currency": ["USD", "GBP", "USD"],
            }
        )
        pl_df = pl.from_pandas(pd_df)

        pandas_result = PandasEngine().validate(pd_df, sample_contract)
        polars_result = PolarsEngine().validate(pl_df, sample_contract)

        pandas_failed = {c.name for c in pandas_result.failed_checks}
        polars_failed = {c.name for c in polars_result.failed_checks}
        assert pandas_failed == polars_failed

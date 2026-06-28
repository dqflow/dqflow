"""Tests for PolarsEngine"""

from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest

pl = pytest.importorskip("polars")

from dqflow import Column, Contract
from dqflow.engines.pandas import PandasEngine
from dqflow.engines.polars import PolarsEngine


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

    def test_validate_passing(self, engine, sample_pl_df, sample_contract):
        result = engine.validate(sample_pl_df, sample_contract, context={})
        assert result.contract_name == "orders"

    def test_validate_missing_column(self, engine, sample_contract):
        df = pl.DataFrame({"order_id": ["A001"]})

        result = engine.validate(df, sample_contract, context={})

        assert any("amount" in c.name and not c.passed for c in result.checks)

    def test_validate_rule(self, engine, sample_pl_df):
        contract = Contract(
            name="test",
            columns={
                "order_id": Column(str, not_null=True),
            },
            rules=["row_count > 0", "row_count > 100"],
        )

        result = engine.validate(sample_pl_df, contract, context={})

        check_map = {c.name: c.passed for c in result.checks}

        assert check_map["rule:row_count > 0"] is True
        assert check_map["rule:row_count > 100"] is False


class TestPolarsEngineConstraints:

    def test_max_constraint_failing(self, engine):
        df = pl.DataFrame({"score": [10.0, 20.0, 100.0]})

        contract = Contract(
            name="test",
            columns={"score": Column(float, max=50.0)},
        )

        result = engine.validate(df, contract, context={})

        assert "max:score" in [c.name for c in result.checks]


class TestCrossEngineConsistency:

    def test_passing_contract_consistency(self, sample_contract):
        pd_df = pd.DataFrame(
            {
                "order_id": ["A001", "A002", "A003"],
                "amount": [100.0, 250.5, 75.0],
                "currency": ["USD", "EUR", "USD"],
            }
        )

        pl_df = pl.from_pandas(pd_df)

        pandas_result = PandasEngine().validate(pd_df, sample_contract, context={})
        polars_result = PolarsEngine().validate(pl_df, sample_contract, context={})

        assert pandas_result.contract_name == polars_result.contract_name

        pandas_map = {c.name: c.passed for c in pandas_result.checks}
        polars_map = {c.name: c.passed for c in polars_result.checks}

        assert pandas_map == polars_map

    def test_violations_consistency(self, sample_contract):
        pd_df = pd.DataFrame(
            {
                "order_id": ["A001", None, "A003"],
                "amount": [100.0, -50.0, 75.0],
                "currency": ["USD", "GBP", "USD"],
            }
        )

        pl_df = pl.from_pandas(pd_df)

        pandas_result = PandasEngine().validate(pd_df, sample_contract, context={})
        polars_result = PolarsEngine().validate(pl_df, sample_contract, context={})

        pandas_failed = {c.name for c in pandas_result.checks if not c.passed}
        polars_failed = {c.name for c in polars_result.checks if not c.passed}

        assert pandas_failed == polars_failed
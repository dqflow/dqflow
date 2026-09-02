"""Regression tests for PandasEngine optimization."""

from __future__ import annotations

import pandas as pd

from dqflow.column import Column, CrossColumnRule
from dqflow.contract import Contract
from dqflow.engines.pandas import PandasEngine, PandasStatsCache


def test_not_null_validation_regression() -> None:
    """Ensure not_null validation behaves correctly."""

    df = pd.DataFrame(
        {
            "customer_id": [1, 2, None],
        }
    )

    contract = Contract(
        name="not_null_test",
        columns={
            "customer_id": Column(
                dtype=int,
                not_null=True,
            )
        },
    )

    result = PandasEngine().validate(
        df,
        contract,
    )

    check = next(c for c in result.checks if c.name == "not_null:customer_id")

    assert check.passed is False
    assert check.details["null_count"] == 1


def test_min_max_validation_regression() -> None:
    """Ensure min and max validations still work."""

    df = pd.DataFrame(
        {
            "age": [10, 20, 30],
        }
    )

    contract = Contract(
        name="range_test",
        columns={
            "age": Column(
                dtype=int,
                min=18,
                max=65,
            )
        },
    )

    result = PandasEngine().validate(
        df,
        contract,
    )

    checks = {check.name: check for check in result.checks}

    assert checks["min:age"].passed is False
    assert checks["max:age"].passed is True


def test_allowed_values_validation_regression() -> None:
    """Ensure allowed values validation works."""

    df = pd.DataFrame(
        {
            "status": ["active", "inactive", "unknown"],
        }
    )

    contract = Contract(
        name="allowed_test",
        columns={
            "status": Column(
                dtype=str,
                allowed=[
                    "active",
                    "inactive",
                ],
            )
        },
    )

    result = PandasEngine().validate(
        df,
        contract,
    )

    check = next(c for c in result.checks if c.name == "allowed:status")

    assert check.passed is False
    assert "unknown" in check.details["invalid_values"]


def test_unique_validation_regression() -> None:
    """Ensure duplicate detection still works."""

    df = pd.DataFrame(
        {
            "id": [1, 2, 2, 3],
        }
    )

    contract = Contract(
        name="unique_test",
        columns={
            "id": Column(
                dtype=int,
                unique=True,
            )
        },
    )

    result = PandasEngine().validate(
        df,
        contract,
    )

    check = next(c for c in result.checks if c.name == "unique:id")

    assert check.passed is False
    assert check.details["duplicate_count"] == 2


def test_missing_column_regression() -> None:
    """Ensure missing columns are reported."""

    df = pd.DataFrame(
        {
            "name": ["Alice"],
        }
    )

    contract = Contract(
        name="missing_column_test",
        columns={
            "age": Column(
                dtype=int,
                not_null=True,
            )
        },
    )

    result = PandasEngine().validate(
        df,
        contract,
    )

    check = next(c for c in result.checks if c.name == "column_exists:age")

    assert check.passed is False


def test_stats_cache_regression() -> None:
    """Ensure statistics cache returns expected values."""

    df = pd.DataFrame(
        {
            "value": [1, 2, None, 4],
        }
    )

    cache = PandasStatsCache(df)

    assert cache.row_count == 4
    assert cache.unique_count("value") == 4  # NaN counts as a distinct value
    assert cache.null_rate("value") == 0.25


def test_custom_rule_regression() -> None:
    """Ensure contract rules still evaluate correctly."""

    df = pd.DataFrame(
        {
            "value": [1, 2, 3],
        }
    )

    contract = Contract(
        name="rule_test",
        columns={
            "value": Column(
                dtype=int,
            )
        },
        rules=[
            "row_count == 3",
        ],
    )

    result = PandasEngine().validate(
        df,
        contract,
    )

    check = next(c for c in result.checks if c.name == "rule:row_count == 3")

    assert check.passed is True


def test_failing_checks_carry_samples_and_rates() -> None:
    """New reporting details: rates, row counts, and bounded value samples."""

    df = pd.DataFrame(
        {
            "order_id": ["A1", "A1", None, "A4"],
            "amount": [10.0, -5.0, -1.0, 20.0],
            "currency": ["USD", "GBP", "JPY", "USD"],
        }
    )
    contract = Contract(
        name="orders",
        columns={
            "order_id": Column(str, not_null=True, unique=True),
            "amount": Column(float, min=0),
            "currency": Column(str, allowed=["USD", "EUR"]),
        },
    )

    checks = {c.name: c for c in PandasEngine().validate(df, contract).checks}

    assert checks["not_null:order_id"].details["null_rate"] == 0.25
    assert checks["min:amount"].details["violating_rows"] == 2
    assert checks["min:amount"].details["violating_rate"] == 0.5
    assert checks["min:amount"].message == "Column 'amount' has 2 values below the minimum 0"
    assert checks["allowed:currency"].details["sample_invalid_values"] == ["GBP", "JPY"]
    # invalid_values is sorted, so pandas and Polars agree regardless of hash seed.
    assert checks["allowed:currency"].details["invalid_values"] == ["GBP", "JPY"]
    assert checks["allowed:currency"].details["violating_rows"] == 2
    assert checks["unique:order_id"].details["sample_duplicate_values"] == ["A1"]


def test_value_samples_are_bounded() -> None:
    df = pd.DataFrame({"code": [f"x{i}" for i in range(50)]})
    contract = Contract(name="t", columns={"code": Column(str, allowed=["ok"])})

    check = next(
        c for c in PandasEngine().validate(df, contract).checks if c.name == "allowed:code"
    )

    assert check.details["invalid_value_count"] == 50
    assert len(check.details["sample_invalid_values"]) == 5


def test_to_dict_keys_are_stable() -> None:
    """The JSON schema is unchanged except for the added ``details`` fields."""

    df = pd.DataFrame({"amount": [-1.0]})
    contract = Contract(name="t", columns={"amount": Column(float, min=0)})

    payload = PandasEngine().validate(df, contract).to_dict()

    assert set(payload) == {
        "contract_name",
        "ok",
        "total_checks",
        "passed",
        "failed",
        "checks",
    }
    assert set(payload["checks"][0]) == {"name", "passed", "message", "details"}


def test_cross_column_rule_regression() -> None:
    """Ensure cross-column validation still works."""

    df = pd.DataFrame(
        {
            "start": [1, 5],
            "end": [2, 3],
        }
    )

    contract = Contract(
        name="cross_column_test",
        columns={
            "start": Column(dtype=int),
            "end": Column(dtype=int),
        },
        cross_column_rules=[
            CrossColumnRule(
                name="start_less_than_end",
                left="start",
                op="<=",
                right="end",
            )
        ],
    )

    result = PandasEngine().validate(
        df,
        contract,
    )

    check = next(c for c in result.checks if c.name == "cross_column:start_less_than_end")

    assert check.passed is False
    assert check.details["failing_rows"] == 1

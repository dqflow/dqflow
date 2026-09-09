import pandas as pd
import polars as pl

from dqflow.contract import Contract
from dqflow.engines.pandas import PandasEngine
from dqflow.engines.polars import PolarsEngine


def normalize(result):
    """
    Convert ValidationResult into deterministic structure for comparison.
    """

    return [
        {
            "name": c.name,
            "passed": c.passed,
            "message": c.message,
            "details": c.details,
        }
        for c in result.checks
    ]


def test_pandas_and_polars_engine_output_match_simple_case():
    contract = Contract(
        name="consistency_test",
        columns={
            "a": {"dtype": int, "not_null": True},
            "b": {"dtype": int, "min": 0},
        },
        rules=[],
    )

    df_pd = pd.DataFrame({"a": [1, 2, 3], "b": [0, 1, 2]})
    df_pl = pl.DataFrame({"a": [1, 2, 3], "b": [0, 1, 2]})

    pandas_result = PandasEngine().validate(df_pd, contract)
    polars_result = PolarsEngine().validate(df_pl, contract)

    assert normalize(pandas_result) == normalize(polars_result)


def test_engine_output_match_with_missing_column():
    contract = Contract(
        name="missing_column_test",
        columns={
            "a": {"dtype": int},
            "missing": {"dtype": int},
        },
        rules=[],
    )

    df_pd = pd.DataFrame({"a": [1, 2, 3]})
    df_pl = pl.DataFrame({"a": [1, 2, 3]})

    pandas_result = PandasEngine().validate(df_pd, contract)
    polars_result = PolarsEngine().validate(df_pl, contract)

    assert normalize(pandas_result) == normalize(polars_result)


def test_engine_output_match_with_rules():
    contract = Contract(
        name="rule_test",
        columns={
            "a": {"dtype": int},
        },
        rules=["row_count == 3", "unique_count('a') == 3"],
    )

    df_pd = pd.DataFrame({"a": [1, 2, 3]})
    df_pl = pl.DataFrame({"a": [1, 2, 3]})

    pandas_result = PandasEngine().validate(df_pd, contract)
    polars_result = PolarsEngine().validate(df_pl, contract)

    assert normalize(pandas_result) == normalize(polars_result)


def test_engine_output_match_with_violations_and_samples():
    contract = Contract(
        name="violations",
        columns={
            "amount": {"dtype": float, "min": 0, "max": 100},
            "currency": {"dtype": str, "allowed": ["USD", "EUR"]},
            "order_id": {"dtype": str, "unique": True},
        },
    )
    data = {
        "amount": [-5.0, 50.0, 250.0],
        "currency": ["USD", "GBP", "JPY"],
        "order_id": ["A", "A", "B"],
    }

    pandas_result = PandasEngine().validate(pd.DataFrame(data), contract)
    polars_result = PolarsEngine().validate(pl.DataFrame(data), contract)

    assert normalize(pandas_result) == normalize(polars_result)


def test_engine_output_match_with_pattern_and_nullable_unique():
    contract = Contract(
        name="string_constraints",
        columns={
            "code": {"dtype": str, "pattern": r"^[A-Z]{2}$"},
            "optional_id": {"dtype": int, "unique": True},
        },
    )
    data = {"code": ["US", "invalid"], "optional_id": [1, None]}

    pandas_result = PandasEngine().validate(pd.DataFrame(data), contract)
    polars_result = PolarsEngine().validate(pl.DataFrame(data), contract)

    assert normalize(pandas_result) == normalize(polars_result)


def test_pattern_is_a_full_match_not_a_search_on_both_engines():
    # An unanchored pattern must still reject partial matches. A substring-search
    # primitive (Polars' str.contains) would wrongly pass "abc123" for r"\d{3}".
    contract = Contract(name="p", columns={"s": {"dtype": str, "pattern": r"\d{3}"}})
    data = {"s": ["123", "abc123", "12", "x123x", "123\n"]}

    pandas_result = PandasEngine().validate(pd.DataFrame(data), contract)
    polars_result = PolarsEngine().validate(pl.DataFrame(data), contract)

    assert normalize(pandas_result) == normalize(polars_result)
    (pattern_check,) = [c for c in pandas_result.checks if c.name == "pattern:s"]
    assert not pattern_check.passed
    assert pattern_check.details["invalid_count"] == 4  # only "123" matches in full


def test_pattern_with_top_level_alternation_matches_in_full_on_both_engines():
    contract = Contract(name="p", columns={"s": {"dtype": str, "pattern": r"yes|no"}})
    data = {"s": ["yes", "no", "nope", "ayes"]}

    pandas_result = PandasEngine().validate(pd.DataFrame(data), contract)
    polars_result = PolarsEngine().validate(pl.DataFrame(data), contract)

    assert normalize(pandas_result) == normalize(polars_result)
    (pattern_check,) = [c for c in polars_result.checks if c.name == "pattern:s"]
    assert pattern_check.details["invalid_count"] == 2  # "nope", "ayes"

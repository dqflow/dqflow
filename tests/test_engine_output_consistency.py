import pandas as pd
import polars as pl

from dqflow.engines.pandas import PandasEngine
from dqflow.engines.polars import PolarsEngine
from dqflow.contract import Contract


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
        rules=[]
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
        rules=[]
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
        rules=[
            "row_count == 3",
            "unique_count('a') == 3"
        ]
    )

    df_pd = pd.DataFrame({"a": [1, 2, 3]})
    df_pl = pl.DataFrame({"a": [1, 2, 3]})

    pandas_result = PandasEngine().validate(df_pd, contract)
    polars_result = PolarsEngine().validate(df_pl, contract)

    assert normalize(pandas_result) == normalize(polars_result)
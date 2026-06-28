import pandas as pd
import polars as pl

from dqflow.engines.pandas import PandasEngine
from dqflow.engines.polars import PolarsEngine
from dqflow.contract import Contract
from dqflow.column import Column


def build_contract():
    return Contract(
        name="test_contract",
        columns={
            "age": Column(min=0, max=120, not_null=True),
            "name": Column(not_null=True),
        },
        rules=[
            "row_count > 0",
        ],
    )


def normalize_result(result):
    """
    Converts ValidationResult into a deterministic comparable structure.
    """

    return {
        "contract_name": result.contract_name,
        "checks": sorted(
            [
                {
                    "name": c.name,
                    "passed": c.passed,
                    "message": c.message,
                }
                for c in result.checks
            ],
            key=lambda x: x["name"],
        ),
    }


def test_engine_output_structure_identical():
    """
    Ensures both engines produce identical ValidationResult structure.
    """

    data = pd.DataFrame(
        {
            "age": [10, 20, 30],
            "name": ["a", "b", "c"],
        }
    )

    pandas_engine = PandasEngine()
    polars_engine = PolarsEngine()

    spec = build_contract()

    pandas_result = pandas_engine.validate(data, spec, context={})
    polars_result = polars_engine.validate(pl.from_pandas(data), spec, context={})

    assert normalize_result(pandas_result) == normalize_result(polars_result)
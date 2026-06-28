import pandas as pd
import polars as pl

from dqflow.engines.pandas import PandasEngine
from dqflow.engines.polars import PolarsEngine
from dqflow.contract import Contract
from dqflow.column import Column


def test_column_check_naming_consistency():
    """
    Ensures both engines use identical check naming conventions.
    """

    spec = Contract(
        name="lock_test",
        columns={
            "x": Column(not_null=True),
        },
        rules=[],
    )

    data = pd.DataFrame({"x": [1, 2, 3]})

    pandas_engine = PandasEngine()
    polars_engine = PolarsEngine()

    p_result = pandas_engine.validate(data, spec, context={})
    pl_result = polars_engine.validate(pl.from_pandas(data), spec, context={})

    p_names = {c.name for c in p_result.checks}
    pl_names = {c.name for c in pl_result.checks}

    assert p_names == pl_names
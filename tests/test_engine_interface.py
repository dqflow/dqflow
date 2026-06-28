import inspect
import pandas as pd
import polars as pl

from dqflow.engines.pandas import PandasEngine
from dqflow.engines.polars import PolarsEngine
from dqflow.contract import Contract
from dqflow.result import ValidationResult


def test_engine_validate_signature_is_consistent():
    pandas_sig = inspect.signature(PandasEngine.validate)
    polars_sig = inspect.signature(PolarsEngine.validate)

    # Both must have identical parameter names (excluding self)
    assert list(pandas_sig.parameters.keys()) == list(polars_sig.parameters.keys())


def test_engine_validate_returns_validation_result():
    contract = Contract(name="test")

    df_pd = pd.DataFrame({"a": [1, 2, 3]})
    df_pl = pl.DataFrame({"a": [1, 2, 3]})

    pandas_result = PandasEngine().validate(df_pd, contract)
    polars_result = PolarsEngine().validate(df_pl, contract)

    assert isinstance(pandas_result, ValidationResult)
    assert isinstance(polars_result, ValidationResult)
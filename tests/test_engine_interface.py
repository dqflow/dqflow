import inspect

from dqflow.engines.pandas import PandasEngine
from dqflow.engines.polars import PolarsEngine
from dqflow.contract import Contract


def test_engine_signature_consistency():
    """
    Ensures both engines follow the strict contract:

    validate(data, spec, context)
    """

    pandas_sig = inspect.signature(PandasEngine.validate)
    polars_sig = inspect.signature(PolarsEngine.validate)

    expected_params = ["self", "data", "spec", "context"]

    assert list(pandas_sig.parameters.keys()) == expected_params
    assert list(polars_sig.parameters.keys()) == expected_params


def test_no_kwargs_allowed():
    """
    Prevents regression back to flexible kwargs-based API.
    """

    pandas_sig = inspect.signature(PandasEngine.validate)
    polars_sig = inspect.signature(PolarsEngine.validate)

    for sig in (pandas_sig, polars_sig):
        assert "kwargs" not in sig.parameters
        assert not any(
            p.kind == inspect.Parameter.VAR_KEYWORD
            for p in sig.parameters.values()
        )
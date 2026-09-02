"""Contract is decoupled from concrete engines (issue #17)."""

from __future__ import annotations

import subprocess
import sys

import pandas as pd
import polars as pl
import pytest

from dqflow import Column, Contract
from dqflow.engines import (
    UnknownEngineError,
    available_engines,
    get_engine,
    register_engine,
)
from dqflow.engines.base import Engine
from dqflow.engines.pandas import PandasEngine
from dqflow.engines.polars import PolarsEngine
from dqflow.result import ValidationResult


@pytest.fixture
def contract() -> Contract:
    return Contract(
        name="orders",
        columns={"order_id": Column(str, not_null=True), "amount": Column(float, min=0)},
        rules=["row_count > 0"],
    )


class TestEngineInjection:
    def test_defaults_to_pandas(self, contract: Contract) -> None:
        result = contract.validate(pd.DataFrame({"order_id": ["A"], "amount": [1.0]}))
        assert isinstance(result, ValidationResult)
        assert result.ok

    def test_accepts_engine_instance(self, contract: Contract) -> None:
        result = contract.validate(
            pl.DataFrame({"order_id": ["A"], "amount": [1.0]}), engine=PolarsEngine()
        )
        assert result.ok

    def test_accepts_engine_name(self, contract: Contract) -> None:
        result = contract.validate(
            pl.DataFrame({"order_id": ["A"], "amount": [1.0]}), engine="polars"
        )
        assert result.ok

    def test_pandas_name_matches_default(self, contract: Contract) -> None:
        df = pd.DataFrame({"order_id": ["A", "B"], "amount": [1.0, 2.0]})
        assert contract.validate(df).to_dict() == contract.validate(df, engine="pandas").to_dict()


class TestRegistry:
    def test_get_engine_types(self) -> None:
        assert isinstance(get_engine(), PandasEngine)
        assert isinstance(get_engine("pandas"), PandasEngine)
        assert isinstance(get_engine("polars"), PolarsEngine)

    def test_get_engine_is_case_insensitive(self) -> None:
        assert isinstance(get_engine("Polars"), PolarsEngine)

    def test_unknown_engine_raises(self) -> None:
        with pytest.raises(UnknownEngineError, match="nope"):
            get_engine("nope")

    def test_available_engines_lists_builtins(self) -> None:
        assert {"pandas", "polars"} <= set(available_engines())

    def test_register_custom_engine(self, contract: Contract) -> None:
        class RecordingEngine(Engine):
            def validate(self, data: object, contract: object, **kw: object) -> ValidationResult:
                return ValidationResult(contract_name="custom")

        register_engine("recording", RecordingEngine)
        try:
            assert isinstance(get_engine("recording"), RecordingEngine)
            assert contract.validate(object(), engine="recording").contract_name == "custom"
        finally:
            from dqflow.engines.registry import _REGISTRY

            _REGISTRY.pop("recording", None)


def test_importing_dqflow_does_not_import_engine_modules() -> None:
    """``import dqflow`` must not eagerly import pandas/polars engine modules."""
    code = (
        "import sys, dqflow; "
        "assert 'dqflow.engines.pandas' not in sys.modules, 'pandas engine imported'; "
        "assert 'dqflow.engines.polars' not in sys.modules, 'polars engine imported'"
    )
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr

"""ExecutionContext: runtime configuration for a validation run (issue #15)."""

from __future__ import annotations

import dataclasses

import pandas as pd
import polars as pl
import pytest

from dqflow import Column, Contract, ExecutionContext
from dqflow.engines.pandas import PandasEngine, PandasStatsCache
from dqflow.engines.polars import PolarsEngine
from dqflow.engines.registry import UnknownEngineError


@pytest.fixture
def contract() -> Contract:
    return Contract(
        name="orders",
        columns={"order_id": Column(str, not_null=True), "amount": Column(float, min=0)},
        rules=["row_count > 0", "null_rate('amount') < 0.5"],
    )


class TestDefaults:
    def test_default_field_values(self) -> None:
        ctx = ExecutionContext()
        assert ctx.engine == "pandas"
        assert ctx.parallel is False
        assert ctx.max_workers is None
        assert ctx.cache is True
        assert ctx.strict is False
        assert ctx.fail_fast is False

    def test_is_frozen(self) -> None:
        ctx = ExecutionContext()
        with pytest.raises(dataclasses.FrozenInstanceError):
            ctx.engine = "polars"  # type: ignore[misc]


class TestResolveEngine:
    def test_resolves_builtin_engines(self) -> None:
        assert isinstance(ExecutionContext().resolve_engine(), PandasEngine)
        assert isinstance(ExecutionContext(engine="pandas").resolve_engine(), PandasEngine)
        assert isinstance(ExecutionContext(engine="polars").resolve_engine(), PolarsEngine)

    def test_unknown_engine_raises(self) -> None:
        with pytest.raises(UnknownEngineError, match="nope"):
            ExecutionContext(engine="nope").resolve_engine()


class TestContextPropagation:
    def test_validate_with_context_selects_engine(self, contract: Contract) -> None:
        df = pl.DataFrame({"order_id": ["A"], "amount": [1.0]})
        result = contract.validate(df, context=ExecutionContext(engine="polars"))
        assert result.ok

    def test_engine_and_context_are_mutually_exclusive(self, contract: Contract) -> None:
        with pytest.raises(TypeError, match="not both"):
            contract.validate(
                pd.DataFrame({"order_id": ["A"], "amount": [1.0]}),
                engine="pandas",
                context=ExecutionContext(),
            )

    def test_reserved_flags_do_not_change_results(self, contract: Contract) -> None:
        df = pd.DataFrame({"order_id": ["A", "B"], "amount": [1.0, 2.0]})
        baseline = contract.validate(df, context=ExecutionContext())
        with_flags = contract.validate(
            df,
            context=ExecutionContext(parallel=True, max_workers=4, strict=True, fail_fast=True),
        )
        assert baseline.to_dict() == with_flags.to_dict()


class TestCacheToggle:
    def test_cache_flag_reaches_the_stats_cache(self) -> None:
        from dqflow.engines.pandas import _Run

        df = pd.DataFrame({"a": [1, 2, 3]})
        assert _Run(df, cache=True).stats._memoize is True
        assert _Run(df, cache=False).stats._memoize is False

    def test_disabled_cache_produces_identical_results(self, contract: Contract) -> None:
        df = pd.DataFrame({"order_id": ["A", "B", None], "amount": [1.0, 2.0, 3.0]})
        cached = contract.validate(df, context=ExecutionContext(cache=True))
        uncached = contract.validate(df, context=ExecutionContext(cache=False))
        assert cached.to_dict() == uncached.to_dict()

    def test_non_memoizing_cache_recomputes(self) -> None:
        calls = {"n": 0}

        class _Spy(PandasStatsCache):
            def _compute_unique_count(self, column: str) -> int:
                calls["n"] += 1
                return super()._compute_unique_count(column)

        df = pd.DataFrame({"a": [1, 1, 2]})
        cache = _Spy(df, memoize=False)
        cache.unique_count("a")
        cache.unique_count("a")
        assert calls["n"] == 2


def test_public_api_exports() -> None:
    import dqflow

    expected = {
        "Engine",
        "ExecutionContext",
        "StatsCache",
        "ValidationSpec",
        "available_engines",
        "evaluate_rule",
        "get_engine",
        "register_engine",
    }
    assert expected <= set(dqflow.__all__)
    for name in expected:
        assert hasattr(dqflow, name)

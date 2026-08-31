"""Shared StatsCache abstraction (issue #21)."""

from __future__ import annotations

import pandas as pd
import polars as pl
import pytest

from dqflow.cache import StatsCache
from dqflow.engines.pandas import PandasStatsCache
from dqflow.engines.polars import PolarsStatsCache

_DATA = {"a": [1, 2, 3, None], "b": ["x", "x", "y", "z"], "c": [1.0, 1.0, 1.0, 1.0]}


def _caches() -> list[StatsCache]:
    return [PandasStatsCache(pd.DataFrame(_DATA)), PolarsStatsCache(pl.DataFrame(_DATA))]


@pytest.fixture(params=_caches(), ids=["pandas", "polars"])
def cache(request: pytest.FixtureRequest) -> StatsCache:
    return request.param


class TestStatistics:
    def test_row_count(self, cache: StatsCache) -> None:
        assert cache.row_count == 4

    def test_null_rate(self, cache: StatsCache) -> None:
        assert cache.null_rate("a") == 0.25
        assert cache.null_rate("b") == 0.0

    def test_unique_count(self, cache: StatsCache) -> None:
        assert cache.unique_count("b") == 3
        assert cache.unique_count("c") == 1
        assert cache.unique_count("a") == 4  # null counts as a distinct value

    def test_missing_column_reports_zero(self, cache: StatsCache) -> None:
        assert cache.null_rate("nope") == 0.0
        assert cache.unique_count("nope") == 0


def test_pandas_and_polars_caches_agree() -> None:
    pandas_cache, polars_cache = _caches()
    for col in _DATA:
        assert pandas_cache.null_rate(col) == polars_cache.null_rate(col)
        assert pandas_cache.unique_count(col) == polars_cache.unique_count(col)


class _CountingCache(StatsCache):
    def __init__(self) -> None:
        super().__init__({"a", "b"})
        self.calls: dict[str, int] = {"row_count": 0, "null_count": 0, "unique_count": 0}

    def _compute_row_count(self) -> int:
        self.calls["row_count"] += 1
        return 10

    def _compute_null_count(self, column: str) -> int:
        self.calls["null_count"] += 1
        return 2

    def _compute_unique_count(self, column: str) -> int:
        self.calls["unique_count"] += 1
        return 5


class TestLazinessAndMemoization:
    def test_nothing_is_computed_until_asked(self) -> None:
        cache = _CountingCache()
        assert cache.calls == {"row_count": 0, "null_count": 0, "unique_count": 0}

    def test_each_statistic_is_computed_at_most_once(self) -> None:
        cache = _CountingCache()
        for _ in range(3):
            cache.null_rate("a")  # touches row_count + null_count("a")
            cache.unique_count("a")
        assert cache.calls == {"row_count": 1, "null_count": 1, "unique_count": 1}

    def test_untouched_column_is_never_scanned(self) -> None:
        cache = _CountingCache()
        cache.null_rate("a")
        assert cache.calls["null_count"] == 1  # "b" never computed

    def test_missing_column_short_circuits_before_computing(self) -> None:
        cache = _CountingCache()
        cache.unique_count("missing")
        assert cache.calls["unique_count"] == 0


class TestEmptyFrame:
    @pytest.mark.parametrize(
        "empty",
        [pd.DataFrame({"a": []}), pl.DataFrame({"a": []})],
        ids=["pandas", "polars"],
    )
    def test_null_rate_is_zero_not_a_zero_division(self, empty: object) -> None:
        cache: StatsCache = (
            PandasStatsCache(empty)  # type: ignore[arg-type]
            if isinstance(empty, pd.DataFrame)
            else PolarsStatsCache(empty)  # type: ignore[arg-type]
        )
        assert cache.row_count == 0
        assert cache.null_rate("a") == 0.0

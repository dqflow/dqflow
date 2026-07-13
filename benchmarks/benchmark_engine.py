"""Benchmark PandasEngine vs PolarsEngine performance."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import pandas as pd

from dqflow.column import Column
from dqflow.contract import Contract
from dqflow.engines.pandas import PandasEngine

try:
    import polars as pl

    from dqflow.engines.polars import PolarsEngine

    POLARS_AVAILABLE = True

except ImportError:
    POLARS_AVAILABLE = False


@dataclass
class BenchmarkResult:
    """Benchmark execution result."""

    engine: str
    rows: int
    columns: int
    execution_time: float


def create_dataset(
    rows: int = 100_000,
    columns: int = 10,
) -> pd.DataFrame:
    """Create synthetic benchmark dataset."""

    data: dict[str, Any] = {}

    for index in range(columns):
        data[f"column_{index}"] = range(rows)

    return pd.DataFrame(data)


def create_contract(
    columns: int,
) -> Contract:
    """Create benchmark validation contract."""

    column_definitions = {}

    for index in range(columns):
        column_definitions[f"column_{index}"] = Column(
            dtype=int,
            not_null=True,
        )

    return Contract(
        name="benchmark",
        columns=column_definitions,
    )


def benchmark_engine(
    engine: Any,
    data: Any,
    contract: Contract,
    name: str,
    runs: int = 5,
) -> BenchmarkResult:
    """Measure engine validation performance."""

    timings: list[float] = []

    # Warm-up execution
    engine.validate(
        data,
        contract,
    )

    for _ in range(runs):
        start = time.perf_counter()

        engine.validate(
            data,
            contract,
        )

        end = time.perf_counter()

        timings.append(end - start)

    return BenchmarkResult(
        engine=name,
        rows=len(data),
        columns=len(contract.columns),
        execution_time=sum(timings) / len(timings),
    )


def run_benchmark(
    rows: int = 100_000,
    columns: int = 10,
) -> list[BenchmarkResult]:
    """Run benchmark suite."""

    pandas_df = create_dataset(
        rows,
        columns,
    )

    contract = create_contract(
        columns,
    )

    results: list[BenchmarkResult] = []

    results.append(
        benchmark_engine(
            PandasEngine(),
            pandas_df,
            contract,
            "pandas",
        )
    )

    if POLARS_AVAILABLE:
        results.append(
            benchmark_engine(
                PolarsEngine(),
                pl.from_pandas(pandas_df),
                contract,
                "polars",
            )
        )

    return results


def print_results(
    results: list[BenchmarkResult],
) -> None:
    """Print benchmark output."""

    print("\nBenchmark Results")
    print("-" * 50)

    for result in results:
        print(
            f"{result.engine:<10}{result.rows:<12}{result.columns:<12}{result.execution_time:.5f}s"
        )


if __name__ == "__main__":
    print_results(run_benchmark())

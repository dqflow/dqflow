"""Benchmark PandasEngine vs PolarsEngine performance."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import pandas as pd

from dqflow import Column, Contract
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
    """Create validation contract."""

    contract = Contract(
        name="benchmark",
    )

    for index in range(columns):
        contract.add_column(
            Column(
                name=f"column_{index}",
                not_null=True,
            )
        )

    return contract


def benchmark_engine(
    engine: Any,
    data: Any,
    contract: Contract,
    name: str,
    runs: int = 5,
) -> BenchmarkResult:
    """Benchmark validation engine."""

    timings: list[float] = []

    # Warm-up
    engine.validate(data, contract)

    for _ in range(runs):
        start = time.perf_counter()

        engine.validate(data, contract)

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
    """Run pandas and polars benchmarks."""

    pandas_df = create_dataset(rows, columns)

    contract = create_contract(columns)

    results = []

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
    """Display benchmark results."""

    print("\nBenchmark Results")
    print("-" * 50)

    for result in results:
        print(
            f"{result.engine:<10}"
            f"{result.rows:<12}"
            f"{result.columns:<12}"
            f"{result.execution_time:.5f}s"
        )


if __name__ == "__main__":
    benchmark_results = run_benchmark()

    print_results(
        benchmark_results,
    )
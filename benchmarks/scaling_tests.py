"""Scaling benchmarks for dqflow engines."""

from __future__ import annotations

from benchmarks.benchmark_engine import run_benchmark


def run_scaling_tests() -> None:
    """Run benchmarks across different dataset sizes."""

    sizes = [
        1_000,
        10_000,
        100_000,
    ]

    print("\nScaling Benchmark")
    print("=" * 60)

    for size in sizes:
        print(f"\nRows: {size}")

        results = run_benchmark(
            rows=size,
            columns=10,
        )

        for result in results:
            print(f"{result.engine}: {result.execution_time:.5f}s")


if __name__ == "__main__":
    run_scaling_tests()

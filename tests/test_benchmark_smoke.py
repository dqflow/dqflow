"""Smoke tests for benchmark framework."""

from benchmarks.benchmark_engine import run_benchmark


def test_benchmark_runs_successfully() -> None:
    """Ensure benchmark executes."""

    results = run_benchmark(
        rows=100,
        columns=3,
    )

    assert len(results) >= 1


def test_benchmark_output_structure() -> None:
    """Ensure benchmark output is valid."""

    results = run_benchmark(
        rows=100,
        columns=3,
    )

    result = results[0]

    assert result.engine
    assert result.rows == 100
    assert result.columns == 3
    assert result.execution_time >= 0

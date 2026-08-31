"""Smoke tests for the runnable documentation examples."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]


@pytest.mark.parametrize(
    ("script", "expected"),
    [
        ("pandas-etl/pipeline.py", "published 3 valid orders"),
        ("polars-pipeline/pipeline.py", "validated 3 Polars rows"),
        ("ci-validation/validate.py", "11/11 checks passed"),
        (
            "infer-refine/infer_and_validate.py",
            "reviewed the inferred draft and validated the curated contract",
        ),
    ],
)
def test_runnable_example(script: str, expected: str) -> None:
    completed = subprocess.run(
        [sys.executable, ROOT / "examples" / script],
        check=True,
        capture_output=True,
        text=True,
    )

    assert expected in completed.stdout

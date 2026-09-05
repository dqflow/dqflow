"""Smoke tests for the runnable documentation examples."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]


@pytest.mark.parametrize(
    ("script", "expected", "exit_code"),
    [
        ("pandas-etl/pipeline.py", "published 3 valid orders", 0),
        ("polars-pipeline/pipeline.py", "validated 3 Polars rows", 0),
        ("ci-validation/validate.py", "11/11 checks passed", 0),
        (
            "infer-refine/infer_and_validate.py",
            "reviewed the inferred draft and validated the curated contract",
            0,
        ),
        (
            "contract-diff/diff.py",
            "blocked: 1 breaking change(s) for data producers",
            1,
        ),
    ],
)
def test_runnable_example(script: str, expected: str, exit_code: int) -> None:
    completed = subprocess.run(
        [sys.executable, ROOT / "examples" / script],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == exit_code
    assert expected in completed.stdout

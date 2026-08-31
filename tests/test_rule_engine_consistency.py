"""The pandas and Polars engines evaluate table rules identically (issue #18)."""

from __future__ import annotations

import pandas as pd
import polars as pl
import pytest

from dqflow import Column, Contract
from dqflow.engines.pandas import PandasEngine
from dqflow.engines.polars import PolarsEngine

_DATA = {"a": [1, 2, 3, None], "b": ["x", "x", "y", "z"]}


def _rule_check(rules: list[str], engine: object, frame: object) -> dict[str, object]:
    contract = Contract(name="t", columns={"a": Column(int), "b": Column(str)}, rules=rules)
    result = engine.validate(frame, contract)  # type: ignore[attr-defined]
    return {c.name: (c.passed, c.message) for c in result.checks if c.name.startswith("rule:")}


@pytest.mark.parametrize(
    "rule",
    [
        "row_count == 4",
        "row_count > 100",
        "null_rate('a') == 0.25",
        "unique_count('b') == 3",
        "row_count > 0 and null_rate('a') < 0.5",
        "nonsense expression (",
        "unknown_name > 1",
        "row_count < 'x'",
    ],
)
def test_pandas_and_polars_agree_on_each_rule(rule: str) -> None:
    pandas_out = _rule_check([rule], PandasEngine(), pd.DataFrame(_DATA))
    polars_out = _rule_check([rule], PolarsEngine(), pl.DataFrame(_DATA))
    assert pandas_out == polars_out


def test_evaluation_errors_become_failed_checks_not_exceptions() -> None:
    for engine, frame in (
        (PandasEngine(), pd.DataFrame(_DATA)),
        (PolarsEngine(), pl.DataFrame(_DATA)),
    ):
        out = _rule_check(["row_count < 'x'"], engine, frame)
        ((passed, message),) = out.values()
        assert passed is False
        assert message.startswith("Failed to evaluate rule: ")

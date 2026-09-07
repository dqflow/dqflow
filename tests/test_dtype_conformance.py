"""Cross-engine conformance tests for declared logical dtypes (issue #51)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import polars as pl
import pytest

from dqflow import Column, Contract
from dqflow.engines.pandas import PandasEngine
from dqflow.engines.polars import PolarsEngine
from dqflow.report import render_result
from dqflow.schema import lint_contract_data


def _results(expected: type | str, values: list[Any]):
    contract = Contract(name="types", columns={"value": Column(expected)})
    return (
        PandasEngine().validate(pd.DataFrame({"value": values}), contract),
        PolarsEngine().validate(pl.DataFrame({"value": values}), contract),
    )


def _dtype_check(result: Any):
    return next(check for check in result.checks if check.name == "dtype:value")


@pytest.mark.parametrize(
    ("expected", "values", "actual"),
    [
        (int, [1, 2], "integer"),
        (float, [1.5, 2.25], "float"),
        (str, ["a", "b"], "string"),
        (bool, [True, False], "boolean"),
        ("timestamp", [datetime(2026, 1, 1, tzinfo=UTC)], "timestamp"),
    ],
)
def test_supported_logical_dtypes_pass_in_both_engines(
    expected: type | str, values: list[Any], actual: str
) -> None:
    for result in _results(expected, values):
        check = _dtype_check(result)
        assert check.passed is True
        assert check.message == ""
        assert check.details == {"expected_dtype": actual, "actual_dtype": actual}


def test_incompatible_dtype_has_identical_diagnostics() -> None:
    pandas_result, polars_result = _results(int, ["1", "2"])
    pandas_check = _dtype_check(pandas_result)
    polars_check = _dtype_check(polars_result)

    assert pandas_check == polars_check
    assert pandas_check.passed is False
    assert pandas_check.message == "Column 'value' has dtype 'string'; expected 'integer'"
    assert pandas_check.details == {"expected_dtype": "integer", "actual_dtype": "string"}
    assert "has dtype 'string'; expected 'integer'" in render_result(pandas_result)
    assert pandas_result.to_dict()["checks"][1]["details"] == pandas_check.details


def test_integer_data_satisfies_float_declaration() -> None:
    for result in _results(float, [1, 2]):
        check = _dtype_check(result)
        assert check.passed is True
        assert check.details["actual_dtype"] == "integer"


def test_nullable_integer_promotion_is_normalized_across_engines() -> None:
    pandas_result, polars_result = _results(int, [1, None, 2])
    assert _dtype_check(pandas_result) == _dtype_check(polars_result)
    assert _dtype_check(pandas_result).passed is True
    assert _dtype_check(pandas_result).details["actual_dtype"] == "integer"


@pytest.mark.parametrize("expected", [int, float, str, bool, "timestamp"])
def test_all_null_column_is_dtype_compatible(expected: type | str) -> None:
    for result in _results(expected, [None, None]):
        check = _dtype_check(result)
        assert check.passed is True
        assert check.details["actual_dtype"] == "null"


def test_missing_column_emits_only_existence_failure() -> None:
    contract = Contract(name="missing", columns={"missing": Column(int)})
    for frame, engine in (
        (pd.DataFrame({"other": [1]}), PandasEngine()),
        (pl.DataFrame({"other": [1]}), PolarsEngine()),
    ):
        result = engine.validate(frame, contract)
        assert [check.name for check in result.checks] == ["column_exists:missing"]


def test_dtype_failure_skips_dependent_column_constraints() -> None:
    contract = Contract(name="guard", columns={"value": Column(int, min=0, not_null=True)})
    for frame, engine in (
        (pd.DataFrame({"value": ["bad"]}), PandasEngine()),
        (pl.DataFrame({"value": ["bad"]}), PolarsEngine()),
    ):
        result = engine.validate(frame, contract)
        assert [check.name for check in result.checks] == ["column_exists:value", "dtype:value"]
        assert result.failed_checks == [_dtype_check(result)]


def test_native_width_variants_are_compatible() -> None:
    contract = Contract(name="widths", columns={"value": Column(int)})
    pandas_result = PandasEngine().validate(
        pd.DataFrame({"value": pd.Series([1, 2], dtype="uint8")}), contract
    )
    polars_result = PolarsEngine().validate(
        pl.DataFrame({"value": pl.Series([1, 2], dtype=pl.Int16)}), contract
    )
    assert _dtype_check(pandas_result).passed is True
    assert _dtype_check(polars_result).passed is True


def test_backend_native_variants_have_identical_logical_results() -> None:
    contract = Contract(
        name="variants",
        columns={
            "integer": Column(int),
            "float": Column(float),
            "string": Column(str),
            "boolean": Column(bool),
            "timestamp": Column("timestamp"),
        },
    )
    pandas_frame = pd.DataFrame(
        {
            "integer": pd.Series([1, None], dtype="Int32"),
            "float": pd.Series([1.5, None], dtype="Float32"),
            "string": pd.Series(["x", None], dtype="string"),
            "boolean": pd.Series([True, None], dtype="boolean"),
            "timestamp": pd.to_datetime(["2026-01-01T00:00:00Z", None]),
        }
    )
    polars_frame = pl.DataFrame(
        {
            "integer": pl.Series([1, None], dtype=pl.UInt16),
            "float": pl.Series([1.5, None], dtype=pl.Float32),
            "string": pl.Series(["x", None], dtype=pl.String),
            "boolean": pl.Series([True, None], dtype=pl.Boolean),
            "timestamp": pl.Series(
                [datetime(2026, 1, 1, tzinfo=UTC), None],
                dtype=pl.Datetime(time_zone="UTC"),
            ),
        }
    )

    pandas_checks = PandasEngine().validate(pandas_frame, contract).checks
    polars_checks = PolarsEngine().validate(polars_frame, contract).checks
    assert pandas_checks == polars_checks


def test_yaml_legacy_alias_and_shorthand_still_load(tmp_path: Path) -> None:
    path = tmp_path / "contract.yaml"
    path.write_text('schema_version: "1.0"\nname: aliases\ncolumns:\n  a: {type: int}\n  b: str\n')
    contract = Contract.from_yaml(path)
    assert contract.columns["a"].dtype == "int"
    assert contract.columns["b"].dtype == "str"
    assert contract.validate(pd.DataFrame({"a": [1], "b": ["x"]})).ok


def test_unknown_dtype_warns_but_remains_loadable(tmp_path: Path) -> None:
    data = {"schema_version": "1.0", "name": "x", "columns": {"a": "decimal128"}}
    diagnostics = lint_contract_data(data)
    assert [item.code for item in diagnostics] == ["unsupported-dtype"]

    path = tmp_path / "contract.yaml"
    path.write_text('schema_version: "1.0"\nname: x\ncolumns:\n  a: decimal128\n')
    contract = Contract.from_yaml(path)
    result = contract.validate(pd.DataFrame({"a": [1]}))
    check = next(item for item in result.checks if item.name == "dtype:a")
    assert check.passed is False

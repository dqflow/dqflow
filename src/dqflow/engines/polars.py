"""Polars validation engine."""

from __future__ import annotations

from typing import Any

try:
    import polars as pl
except ImportError as exc:
    raise ImportError(
        "polars is required for PolarsEngine. Install with: pip install dqflow[polars]"
    ) from exc

from dqflow.column import Column
from dqflow.contract import Contract
from dqflow.engines.base import Engine
from dqflow.result import CheckResult, ValidationResult


class PolarsEngine(Engine):
    """Validation engine for Polars DataFrames."""

    def validate(
        self,
        data: pl.DataFrame | pl.LazyFrame,
        contract: Contract,
        context: dict[str, Any] | None = None,
    ) -> ValidationResult:

        context = context or {}

        if isinstance(data, pl.LazyFrame):
            data = data.collect()

        result = ValidationResult(contract_name=contract.name)

        cache = self._build_stats_cache(data)


        # Column existence checks
        for col_name in contract.columns:
            if col_name not in data.columns:
                result.checks.append(
                    CheckResult(
                        name=f"column_exists:{col_name}",
                        passed=False,
                        message=f"Column '{col_name}' not found in DataFrame",
                    )
                )
            else:
                result.checks.append(
                    CheckResult(
                        name=f"column_exists:{col_name}",
                        passed=True,
                        message="",
                    )
                )

      
        # Column validation
        for col_name, col_def in contract.columns.items():
            if col_name not in data.columns:
                continue

            result.checks.extend(
                self._validate_column(
                    data[col_name],
                    col_name,
                    col_def,
                )
            )

      
        # Rule evaluation
        for rule in contract.rules:
            result.checks.append(
                self._evaluate_rule(
                    data,
                    rule,
                    cache,
                    context,
                )
            )

        return result

    def _validate_column(
        self,
        series: pl.Series,
        col_name: str,
        col_def: Column,
    ) -> list[CheckResult]:

        checks: list[CheckResult] = []

        if col_def.not_null:
            null_count = series.null_count()

            checks.append(
                CheckResult(
                    name=f"not_null:{col_name}",
                    passed=null_count == 0,
                    message=(
                        f"Found {null_count} null values"
                        if null_count > 0
                        else ""
                    ),
                    details={"null_count": null_count},
                )
            )

        if col_def.min is not None:
            min_val = series.min()
            passed = min_val is None or min_val >= col_def.min

            checks.append(
                CheckResult(
                    name=f"min:{col_name}",
                    passed=bool(passed),
                    message=(
                        f"Minimum value {min_val} is below {col_def.min}"
                        if not passed
                        else ""
                    ),
                )
            )

        if col_def.max is not None:
            max_val = series.max()
            passed = max_val is None or max_val <= col_def.max

            checks.append(
                CheckResult(
                    name=f"max:{col_name}",
                    passed=bool(passed),
                    message=(
                        f"Maximum value {max_val} exceeds {col_def.max}"
                        if not passed
                        else ""
                    ),
                )
            )

        if col_def.allowed is not None:
            invalid = (
                set(series.drop_nulls().unique().to_list())
                - set(col_def.allowed)
            )

            checks.append(
                CheckResult(
                    name=f"allowed:{col_name}",
                    passed=len(invalid) == 0,
                    message=(
                        f"Found invalid values: {invalid}"
                        if invalid
                        else ""
                    ),
                    details={"invalid_values": list(invalid)},
                )
            )

        return checks

    def _build_stats_cache(
        self,
        data: pl.DataFrame,
    ) -> dict[str, dict[str, float | int]]:

        row_count = len(data)

        return {
            col: {
                "null_rate": (
                    data[col].null_count() / row_count
                    if row_count
                    else 0.0
                ),
                "unique_count": data[col].n_unique(),
                "row_count": row_count,
            }
            for col in data.columns
        }

    def _evaluate_rule(
        self,
        data: pl.DataFrame,
        rule: str,
        cache: dict[str, dict[str, float | int]],
        context: dict[str, Any],
    ) -> CheckResult:

        try:
            result = self._parse_and_evaluate(data, rule, cache, context)

            return CheckResult(
                name=f"rule:{rule}",
                passed=bool(result),
                message="" if result else f"Rule '{rule}' failed",
            )

        except Exception as exc:
            return CheckResult(
                name=f"rule:{rule}",
                passed=False,
                message=f"Failed to evaluate rule: {exc}",
            )

    def _parse_and_evaluate(
        self,
        data: pl.DataFrame,
        rule: str,
        cache: dict[str, dict[str, float | int]],
        context: dict[str, Any],
    ) -> Any:

        eval_context = {
            "row_count": len(data),
            "null_rate": lambda col: cache.get(col, {}).get("null_rate", 0),
            "unique_count": lambda col: cache.get(col, {}).get("unique_count", 0),
            **context,
        }

        return eval(rule, {"__builtins__": {}}, eval_context)
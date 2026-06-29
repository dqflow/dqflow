"""Polars validation engine."""

from __future__ import annotations

import operator as _op
from collections.abc import Callable
from typing import Any

import polars as pl

from dqflow.column import Column, CrossColumnRule
from dqflow.contract import Contract
from dqflow.engines.base import Engine
from dqflow.result import CheckResult, ValidationResult

_OPS: dict[str, Callable[[Any, Any], Any]] = {
    ">=": _op.ge,
    "<=": _op.le,
    ">": _op.gt,
    "<": _op.lt,
    "==": _op.eq,
    "!=": _op.ne,
}


class PolarsEngine(Engine):
    """Validation engine for Polars DataFrames."""

    def validate(
        self,
        data: pl.DataFrame | pl.LazyFrame,
        contract: Contract,
        **kwargs: Any,
    ) -> ValidationResult:
        if isinstance(data, pl.LazyFrame):
            data = data.collect()

        df = data  # normalize

        result = ValidationResult(contract_name=contract.name)
        cache = self._build_stats_cache(df)

        # 1. COLUMN EXISTENCE CHECKS
        for col_name in contract.columns:
            exists = col_name in df.columns

            result.checks.append(
                CheckResult(
                    name=f"column_exists:{col_name}",
                    passed=exists,
                    message=("" if exists else f"Column '{col_name}' not found in DataFrame"),
                )
            )

        # 2. COLUMN VALIDATION CHECKS
        for col_name, col_def in contract.columns.items():
            if col_name not in df.columns:
                continue

            result.checks.extend(self._validate_column(df[col_name], col_name, col_def))

        # 3. RULES
        for rule in contract.rules:
            result.checks.append(self._evaluate_rule(df, rule, cache))

        # 4. CROSS-COLUMN RULES
        for cc_rule in contract.cross_column_rules:
            result.checks.append(self._evaluate_cross_column_rule(df, cc_rule))

        return result

    # COLUMN VALIDATION

    def _validate_column(
        self,
        series: pl.Series,
        col_name: str,
        col_def: Column,
    ) -> list[CheckResult]:
        checks: list[CheckResult] = []

        # NOT NULL
        if col_def.not_null:
            null_count = series.null_count()
            checks.append(
                CheckResult(
                    name=f"not_null:{col_name}",
                    passed=null_count == 0,
                    message=f"Found {null_count} null values" if null_count > 0 else "",
                    details={"null_count": null_count},
                )
            )

        # MIN
        if col_def.min is not None:
            min_val = series.min()
            passed = min_val is None or min_val >= col_def.min

            checks.append(
                CheckResult(
                    name=f"min:{col_name}",
                    passed=bool(passed),
                    message=(
                        f"Minimum value {min_val} is below {col_def.min}" if not passed else ""
                    ),
                    details={"actual_min": float(min_val) if min_val is not None else None},
                )
            )

        # MAX
        if col_def.max is not None:
            max_val = series.max()
            passed = max_val is None or max_val <= col_def.max

            checks.append(
                CheckResult(
                    name=f"max:{col_name}",
                    passed=bool(passed),
                    message=(
                        f"Maximum value {max_val} exceeds {col_def.max}" if not passed else ""
                    ),
                    details={"actual_max": float(max_val) if max_val is not None else None},
                )
            )

        # ALLOWED VALUES
        if col_def.allowed is not None:
            invalid = set(series.drop_nulls().unique().to_list()) - set(col_def.allowed)

            checks.append(
                CheckResult(
                    name=f"allowed:{col_name}",
                    passed=len(invalid) == 0,
                    message=f"Found invalid values: {invalid}" if invalid else "",
                    details={"invalid_values": list(invalid)},
                )
            )

        # UNIQUE
        if col_def.unique:
            duplicate_count = int(series.is_duplicated().sum())

            checks.append(
                CheckResult(
                    name=f"unique:{col_name}",
                    passed=duplicate_count == 0,
                    message=(
                        f"Found {duplicate_count} duplicate values" if duplicate_count > 0 else ""
                    ),
                    details={"duplicate_count": duplicate_count},
                )
            )

        return checks

    # STATS CACHE

    def _build_stats_cache(self, df: pl.DataFrame) -> dict[str, dict[str, float | int]]:
        return {
            col: {
                "null_rate": df[col].null_count() / len(df) if len(df) > 0 else 0.0,
                "unique_count": df[col].n_unique(),
                "row_count": len(df),
            }
            for col in df.columns
        }

    # RULE ENGINE

    def _evaluate_rule(
        self,
        df: pl.DataFrame,
        rule: str,
        cache: dict[str, dict[str, float | int]],
    ) -> CheckResult:
        try:
            context = {
                "row_count": len(df),
                "null_rate": lambda c: cache.get(c, {}).get("null_rate", 0),
                "unique_count": lambda c: cache.get(c, {}).get("unique_count", 0),
            }

            result = eval(rule, {"__builtins__": {}}, context)

            return CheckResult(
                name=f"rule:{rule}",
                passed=bool(result),
                message="" if result else f"Rule '{rule}' failed",
            )

        except Exception as e:
            return CheckResult(
                name=f"rule:{rule}",
                passed=False,
                message=f"Failed to evaluate rule: {e}",
            )

    def _evaluate_cross_column_rule(
        self,
        df: pl.DataFrame,
        rule: CrossColumnRule,
    ) -> CheckResult:
        try:
            if rule.check is not None:
                mask: Any = rule.check(df)
            else:
                assert rule.left is not None and rule.op is not None
                left_series = df[rule.left]
                right_val: Any = (
                    df[rule.right]
                    if isinstance(rule.right, str) and rule.right in df.columns
                    else rule.right
                )
                mask = _OPS[rule.op](left_series, right_val)

            failing_rows = int((~mask).sum())
            passed = failing_rows == 0
            return CheckResult(
                name=f"cross_column:{rule.name}",
                passed=passed,
                message=rule.error_message if not passed else "",
                details={"failing_rows": failing_rows},
            )
        except Exception as e:
            return CheckResult(
                name=f"cross_column:{rule.name}",
                passed=False,
                message=f"Failed to evaluate cross-column rule '{rule.name}': {e}",
            )

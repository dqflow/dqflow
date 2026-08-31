"""Polars validation engine."""

from __future__ import annotations

import operator as _op
from collections.abc import Callable
from typing import Any, cast

import polars as pl

from dqflow.column import Column, CrossColumnRule
from dqflow.contract import Contract
from dqflow.engines.base import Engine, count_noun, rate, sample_values
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
    """Execute contracts against Polars DataFrames or LazyFrames.

    LazyFrames are currently collected before checks run, so validation is not
    streaming or lazy yet.
    """

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
                    message=("" if exists else f"Column '{col_name}' is missing from the data"),
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
        total = len(series)

        # NOT NULL
        if col_def.not_null:
            null_count = series.null_count()
            checks.append(
                CheckResult(
                    name=f"not_null:{col_name}",
                    passed=null_count == 0,
                    message=(
                        f"Column '{col_name}' has {count_noun(null_count, 'null value')}"
                        if null_count > 0
                        else ""
                    ),
                    details={
                        "null_count": null_count,
                        "null_rate": rate(null_count, total),
                    },
                )
            )

        # MIN
        if col_def.min is not None:
            min_val = cast("float | None", series.min())
            passed = min_val is None or min_val >= col_def.min
            below = 0 if passed else int((series < col_def.min).sum())

            checks.append(
                CheckResult(
                    name=f"min:{col_name}",
                    passed=bool(passed),
                    message=(
                        ""
                        if passed
                        else f"Column '{col_name}' has {count_noun(below, 'value')} "
                        f"below the minimum {col_def.min}"
                    ),
                    details={
                        "actual_min": min_val,
                        "violating_rows": below,
                        "violating_rate": rate(below, total),
                    },
                )
            )

        # MAX
        if col_def.max is not None:
            max_val = cast("float | None", series.max())
            passed = max_val is None or max_val <= col_def.max
            above = 0 if passed else int((series > col_def.max).sum())

            checks.append(
                CheckResult(
                    name=f"max:{col_name}",
                    passed=bool(passed),
                    message=(
                        ""
                        if passed
                        else f"Column '{col_name}' has {count_noun(above, 'value')} "
                        f"above the maximum {col_def.max}"
                    ),
                    details={
                        "actual_max": max_val,
                        "violating_rows": above,
                        "violating_rate": rate(above, total),
                    },
                )
            )

        # ALLOWED VALUES
        if col_def.allowed is not None:
            invalid = set(series.drop_nulls().unique().to_list()) - set(col_def.allowed)
            sample = sample_values(invalid)
            violating = int(series.is_in(list(invalid)).sum())

            checks.append(
                CheckResult(
                    name=f"allowed:{col_name}",
                    passed=len(invalid) == 0,
                    message=(
                        f"Column '{col_name}' has {count_noun(violating, 'value')} "
                        f"outside the allowed set"
                        if invalid
                        else ""
                    ),
                    details={
                        "invalid_values": list(invalid),
                        "sample_invalid_values": sample,
                        "invalid_value_count": len(invalid),
                        "violating_rows": violating,
                        "violating_rate": rate(violating, total),
                    },
                )
            )

        # UNIQUE
        if col_def.unique:
            non_null = series.drop_nulls()
            duplicated_mask = non_null.is_duplicated()
            duplicate_count = int(duplicated_mask.sum())
            sample = sample_values(non_null.filter(duplicated_mask).to_list())

            checks.append(
                CheckResult(
                    name=f"unique:{col_name}",
                    passed=duplicate_count == 0,
                    message=(
                        f"Column '{col_name}' has {count_noun(duplicate_count, 'non-unique value')}"
                        if duplicate_count > 0
                        else ""
                    ),
                    details={
                        "duplicate_count": duplicate_count,
                        "sample_duplicate_values": sample,
                        "violating_rate": rate(duplicate_count, total),
                    },
                )
            )

        if col_def.pattern is not None:
            non_null = series.drop_nulls().cast(pl.String)
            mismatch_mask = ~non_null.str.contains(col_def.pattern)
            invalid_count = int(mismatch_mask.sum())
            sample = sample_values(non_null.filter(mismatch_mask).to_list())

            checks.append(
                CheckResult(
                    name=f"pattern:{col_name}",
                    passed=invalid_count == 0,
                    message=(
                        f"Column '{col_name}' has {count_noun(invalid_count, 'value')} "
                        f"not matching {col_def.pattern!r}"
                        if invalid_count
                        else ""
                    ),
                    details={
                        "invalid_count": invalid_count,
                        "sample_invalid_values": sample,
                        "violating_rate": rate(invalid_count, total),
                    },
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
                details={
                    "failing_rows": failing_rows,
                    "failing_rate": rate(failing_rows, len(df)),
                },
            )
        except Exception as e:
            return CheckResult(
                name=f"cross_column:{rule.name}",
                passed=False,
                message=f"Failed to evaluate cross-column rule '{rule.name}': {e}",
            )

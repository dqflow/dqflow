"""Pandas validation engine."""

from __future__ import annotations

import operator as _op
from collections.abc import Callable
from datetime import date, datetime
from typing import Any

import pandas as pd

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


class PandasEngine(Engine):
    """Execute contracts against in-memory pandas DataFrames."""

    def validate(
        self,
        data: pd.DataFrame,
        contract: Contract,
        **kwargs: Any,
    ) -> ValidationResult:
        df = data

        result = ValidationResult(
            contract_name=contract.name,
        )

        existing_columns = set(df.columns)

        # Only create cache when rules need it
        cache = self._build_stats_cache(df) if contract.rules else {}

        # Backward compatibility
        _ = kwargs.get("parallel", False)
        _ = kwargs.get("max_workers")

        column_data = df

        # Column existence checks
        for col_name in contract.columns:
            exists = col_name in existing_columns

            result.checks.append(
                CheckResult(
                    name=f"column_exists:{col_name}",
                    passed=exists,
                    message=("" if exists else f"Column '{col_name}' is missing from the data"),
                )
            )

        # Column validation
        for col_name, col_def in contract.columns.items():
            if col_name not in existing_columns:
                continue

            result.checks.extend(
                self._validate_column(
                    column_data[col_name],
                    col_name,
                    col_def,
                )
            )

        # Rules
        for rule in contract.rules:
            result.checks.append(
                self._evaluate_rule(
                    df,
                    rule,
                    cache,
                )
            )

        # Cross-column rules
        for cross_rule in contract.cross_column_rules:
            result.checks.append(
                self._evaluate_cross_column_rule(
                    df,
                    cross_rule,
                )
            )

        return result

    def _validate_column(
        self,
        series: pd.Series,
        col_name: str,
        col_def: Column,
    ) -> list[CheckResult]:
        checks: list[CheckResult] = []
        total = len(series)

        if col_def.not_null:
            null_count = int(series.isna().sum())

            checks.append(
                CheckResult(
                    name=f"not_null:{col_name}",
                    passed=null_count == 0,
                    message=(
                        f"Column '{col_name}' has {count_noun(null_count, 'null value')}"
                        if null_count
                        else ""
                    ),
                    details={
                        "null_count": null_count,
                        "null_rate": rate(null_count, total),
                    },
                )
            )

        if col_def.min is not None:
            min_val = series.min()
            passed = pd.isna(min_val) or min_val >= col_def.min
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
                        "actual_min": _result_value(min_val),
                        "violating_rows": below,
                        "violating_rate": rate(below, total),
                    },
                )
            )

        if col_def.max is not None:
            max_val = series.max()
            passed = pd.isna(max_val) or max_val <= col_def.max
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
                        "actual_max": _result_value(max_val),
                        "violating_rows": above,
                        "violating_rate": rate(above, total),
                    },
                )
            )

        if col_def.allowed is not None:
            invalid = set(series.dropna().unique()) - set(col_def.allowed)
            sample = sample_values(invalid)
            violating = int(series.isin(list(invalid)).sum())

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

        if col_def.unique:
            duplicated_mask = series.dropna().duplicated(keep=False)
            duplicate_count = int(duplicated_mask.sum())
            sample = sample_values(series.dropna()[duplicated_mask])

            checks.append(
                CheckResult(
                    name=f"unique:{col_name}",
                    passed=duplicate_count == 0,
                    message=(
                        f"Column '{col_name}' has {count_noun(duplicate_count, 'non-unique value')}"
                        if duplicate_count
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
            non_null = series.dropna().astype("string")
            mismatch_mask = ~non_null.str.fullmatch(col_def.pattern, na=False)
            invalid_count = int(mismatch_mask.sum())
            sample = sample_values(non_null[mismatch_mask])

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

    def _build_stats_cache(
        self,
        df: pd.DataFrame,
    ) -> dict[str, dict[str, float | int]]:
        """
        Build statistics cache.

        Required by regression tests.
        """

        cache: dict[str, dict[str, float | int]] = {}

        row_count = len(df)

        for column in df.columns:
            series = df[column]

            cache[column] = {
                "null_rate": float(series.isna().mean()),
                "unique_count": int(series.nunique(dropna=False)),
                "row_count": row_count,
            }

        return cache

    def _evaluate_rule(
        self,
        df: pd.DataFrame,
        rule: str,
        cache: dict[str, dict[str, float | int]],
    ) -> CheckResult:
        try:
            context = {
                "row_count": len(df),
                "null_rate": lambda c: cache.get(c, {}).get(
                    "null_rate",
                    0,
                ),
                "unique_count": lambda c: cache.get(c, {}).get(
                    "unique_count",
                    0,
                ),
            }

            result = eval(
                rule,
                {"__builtins__": {}},
                context,
            )

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
        df: pd.DataFrame,
        rule: CrossColumnRule,
    ) -> CheckResult:
        try:
            if rule.check is not None:
                mask: Any = rule.check(df)

            else:
                assert rule.left is not None and rule.op is not None

                left_series = df[rule.left]

                right_value = (
                    df[rule.right]
                    if (isinstance(rule.right, str) and rule.right in df.columns)
                    else rule.right
                )

                mask = _OPS[rule.op](
                    left_series,
                    right_value,
                )

            failing_rows = int((~mask).sum())

            return CheckResult(
                name=f"cross_column:{rule.name}",
                passed=failing_rows == 0,
                message=(rule.error_message if failing_rows else ""),
                details={
                    "failing_rows": failing_rows,
                    "failing_rate": rate(failing_rows, len(df)),
                },
            )

        except Exception as e:
            return CheckResult(
                name=f"cross_column:{rule.name}",
                passed=False,
                message=(f"Failed to evaluate cross-column rule '{rule.name}': {e}"),
            )


def _result_value(value: Any) -> float | int | str | None:
    """Convert pandas scalars to JSON-safe validation details."""
    if pd.isna(value):
        return None
    if isinstance(value, (pd.Timestamp, datetime, date)):
        return value.isoformat()
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, (float, int, str)):
        return value
    return str(value)

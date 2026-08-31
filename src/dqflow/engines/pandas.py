"""Pandas validation engine."""

from __future__ import annotations

import operator as _op
from collections.abc import Callable
from datetime import date, datetime
from typing import Any

import pandas as pd

from dqflow.contract import Contract
from dqflow.engines.base import (
    SAMPLE_LIMIT,
    Engine,
    allowed_message,
    cross_column_error_message,
    max_message,
    min_message,
    missing_column_message,
    not_null_message,
    pattern_message,
    rate,
    rule_error_message,
    rule_failed_message,
    sorted_values,
    unique_message,
)
from dqflow.result import CheckResult, ValidationResult
from dqflow.rules import evaluate_rule
from dqflow.spec import CheckSpec, ValidationSpec

_OPS: dict[str, Callable[[Any, Any], Any]] = {
    ">=": _op.ge,
    "<=": _op.le,
    ">": _op.gt,
    "<": _op.lt,
    "==": _op.eq,
    "!=": _op.ne,
}


class _Run:
    """Per-``validate`` state: the frame plus a lazily built stats cache."""

    def __init__(self, df: pd.DataFrame) -> None:
        self.df = df
        self.columns = set(df.columns)
        self._stats: dict[str, dict[str, float | int]] | None = None

    @property
    def stats(self) -> dict[str, dict[str, float | int]]:
        if self._stats is None:
            self._stats = _compute_stats_cache(self.df)
        return self._stats


class PandasEngine(Engine):
    """Execute contracts against in-memory pandas DataFrames."""

    def validate(
        self,
        data: pd.DataFrame,
        contract: Contract | ValidationSpec,
        **kwargs: Any,
    ) -> ValidationResult:
        spec = (
            contract
            if isinstance(contract, ValidationSpec)
            else ValidationSpec.from_contract(contract)
        )

        # Accepted for backward compatibility; execution is always sequential.
        _ = kwargs.get("parallel", False)
        _ = kwargs.get("max_workers")

        run = _Run(data)
        handlers: dict[str, Callable[[_Run, CheckSpec], CheckResult | None]] = {
            "column_exists": self._check_column_exists,
            "not_null": self._check_not_null,
            "min": self._check_min,
            "max": self._check_max,
            "allowed": self._check_allowed,
            "unique": self._check_unique,
            "pattern": self._check_pattern,
            "rule": self._check_rule,
            "cross_column": self._check_cross_column,
        }

        result = ValidationResult(contract_name=spec.contract_name)
        for check in spec.checks:
            outcome = handlers[check.kind](run, check)
            if outcome is not None:
                result.checks.append(outcome)
        return result

    # --- schema ----------------------------------------------------------

    def _check_column_exists(self, run: _Run, check: CheckSpec) -> CheckResult:
        exists = check.target in run.columns
        return CheckResult(
            name=check.name,
            passed=exists,
            message="" if exists else missing_column_message(check.target),
        )

    # --- column constraints (skipped when the column is absent) ---------

    def _check_not_null(self, run: _Run, check: CheckSpec) -> CheckResult | None:
        if check.target not in run.columns:
            return None
        series = run.df[check.target]
        total = len(series)
        null_count = int(series.isna().sum())

        return CheckResult(
            name=check.name,
            passed=null_count == 0,
            message=not_null_message(check.target, null_count),
            details={
                "null_count": null_count,
                "null_rate": rate(null_count, total),
            },
        )

    def _check_min(self, run: _Run, check: CheckSpec) -> CheckResult | None:
        if check.target not in run.columns:
            return None
        series = run.df[check.target]
        total = len(series)
        minimum = check.params["min"]

        min_val = series.min()
        passed = pd.isna(min_val) or min_val >= minimum
        below = 0 if passed else int((series < minimum).sum())

        return CheckResult(
            name=check.name,
            passed=bool(passed),
            message=min_message(check.target, below, minimum),
            details={
                "actual_min": _result_value(min_val),
                "violating_rows": below,
                "violating_rate": rate(below, total),
            },
        )

    def _check_max(self, run: _Run, check: CheckSpec) -> CheckResult | None:
        if check.target not in run.columns:
            return None
        series = run.df[check.target]
        total = len(series)
        maximum = check.params["max"]

        max_val = series.max()
        passed = pd.isna(max_val) or max_val <= maximum
        above = 0 if passed else int((series > maximum).sum())

        return CheckResult(
            name=check.name,
            passed=bool(passed),
            message=max_message(check.target, above, maximum),
            details={
                "actual_max": _result_value(max_val),
                "violating_rows": above,
                "violating_rate": rate(above, total),
            },
        )

    def _check_allowed(self, run: _Run, check: CheckSpec) -> CheckResult | None:
        if check.target not in run.columns:
            return None
        series = run.df[check.target]
        total = len(series)
        allowed = check.params["allowed"]

        invalid = set(series.dropna().unique()) - set(allowed)
        invalid_values = sorted_values(invalid)
        violating = int(series.isin(invalid_values).sum())

        return CheckResult(
            name=check.name,
            passed=len(invalid) == 0,
            message=allowed_message(check.target, violating, has_invalid=bool(invalid)),
            details={
                "invalid_values": invalid_values,
                "sample_invalid_values": invalid_values[:SAMPLE_LIMIT],
                "invalid_value_count": len(invalid),
                "violating_rows": violating,
                "violating_rate": rate(violating, total),
            },
        )

    def _check_unique(self, run: _Run, check: CheckSpec) -> CheckResult | None:
        if check.target not in run.columns:
            return None
        series = run.df[check.target]
        total = len(series)

        duplicated_mask = series.dropna().duplicated(keep=False)
        duplicate_count = int(duplicated_mask.sum())
        sample = sorted_values(series.dropna()[duplicated_mask], limit=SAMPLE_LIMIT)

        return CheckResult(
            name=check.name,
            passed=duplicate_count == 0,
            message=unique_message(check.target, duplicate_count),
            details={
                "duplicate_count": duplicate_count,
                "sample_duplicate_values": sample,
                "violating_rate": rate(duplicate_count, total),
            },
        )

    def _check_pattern(self, run: _Run, check: CheckSpec) -> CheckResult | None:
        if check.target not in run.columns:
            return None
        series = run.df[check.target]
        total = len(series)
        pattern = check.params["pattern"]

        non_null = series.dropna().astype("string")
        mismatch_mask = ~non_null.str.fullmatch(pattern, na=False)
        invalid_count = int(mismatch_mask.sum())
        sample = sorted_values(non_null[mismatch_mask], limit=SAMPLE_LIMIT)

        return CheckResult(
            name=check.name,
            passed=invalid_count == 0,
            message=pattern_message(check.target, invalid_count, pattern),
            details={
                "invalid_count": invalid_count,
                "sample_invalid_values": sample,
                "violating_rate": rate(invalid_count, total),
            },
        )

    # --- table & cross-column rules ------------------------------------

    def _check_rule(self, run: _Run, check: CheckSpec) -> CheckResult:
        expression = check.params["expression"]
        cache = run.stats
        try:
            passed = evaluate_rule(
                expression,
                row_count=len(run.df),
                null_rate=lambda c: float(cache.get(c, {}).get("null_rate", 0.0)),
                unique_count=lambda c: cache.get(c, {}).get("unique_count", 0),
            )
        except Exception as exc:  # noqa: BLE001 - evaluation errors become failed checks
            return CheckResult(name=check.name, passed=False, message=rule_error_message(exc))

        return CheckResult(
            name=check.name,
            passed=passed,
            message="" if passed else rule_failed_message(expression),
        )

    def _check_cross_column(self, run: _Run, check: CheckSpec) -> CheckResult:
        rule = check.params["rule"]
        df = run.df
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
                mask = _OPS[rule.op](left_series, right_value)

            failing_rows = int((~mask).sum())
        except Exception as exc:  # noqa: BLE001 - evaluation errors become failed checks
            return CheckResult(
                name=check.name,
                passed=False,
                message=cross_column_error_message(rule.name, exc),
            )

        return CheckResult(
            name=check.name,
            passed=failing_rows == 0,
            message=rule.error_message if failing_rows else "",
            details={
                "failing_rows": failing_rows,
                "failing_rate": rate(failing_rows, len(df)),
            },
        )

    def _build_stats_cache(self, df: pd.DataFrame) -> dict[str, dict[str, float | int]]:
        """Backward-compatible alias for :func:`_compute_stats_cache` (issue #21)."""
        return _compute_stats_cache(df)


def _compute_stats_cache(df: pd.DataFrame) -> dict[str, dict[str, float | int]]:
    """Build the per-column statistics used by table-rule expressions."""
    row_count = len(df)
    return {
        column: {
            "null_rate": float(df[column].isna().mean()),
            "unique_count": int(df[column].nunique(dropna=False)),
            "row_count": row_count,
        }
        for column in df.columns
    }


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

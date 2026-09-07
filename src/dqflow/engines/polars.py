"""Polars validation engine."""

from __future__ import annotations

import operator as _op
from collections.abc import Callable
from typing import Any, cast

import polars as pl

from dqflow.cache import StatsCache
from dqflow.contract import Contract
from dqflow.dtypes import dtype_details, dtypes_compatible
from dqflow.engines.base import (
    SAMPLE_LIMIT,
    Engine,
    allowed_message,
    cross_column_error_message,
    dtype_message,
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
from dqflow.execution.context import ExecutionContext
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


class PolarsStatsCache(StatsCache):
    """:class:`~dqflow.cache.StatsCache` backed by a Polars DataFrame."""

    def __init__(self, df: pl.DataFrame, *, memoize: bool = True) -> None:
        super().__init__(df.columns, memoize=memoize)
        self._df = df

    def _compute_row_count(self) -> int:
        return len(self._df)

    def _compute_null_count(self, column: str) -> int:
        return int(self._df[column].null_count())

    def _compute_unique_count(self, column: str) -> int:
        return int(self._df[column].n_unique())


class _Run:
    """Per-``validate`` state: the frame plus a lazily built stats cache."""

    def __init__(self, df: pl.DataFrame, *, cache: bool = True) -> None:
        self.df = df
        self.columns = set(df.columns)
        self._cache = cache
        self._stats: StatsCache | None = None
        self.invalid_dtype_columns: set[str] = set()

    @property
    def stats(self) -> StatsCache:
        if self._stats is None:
            self._stats = PolarsStatsCache(self.df, memoize=self._cache)
        return self._stats


class PolarsEngine(Engine):
    """Execute contracts against Polars DataFrames or LazyFrames.

    LazyFrames are currently collected before checks run, so validation is not
    streaming or lazy yet.
    """

    def validate(
        self,
        data: pl.DataFrame | pl.LazyFrame,
        contract: Contract | ValidationSpec,
        *,
        context: ExecutionContext | None = None,
    ) -> ValidationResult:
        if context is None:
            context = ExecutionContext()

        if isinstance(data, pl.LazyFrame):
            data = data.collect()

        spec = (
            contract
            if isinstance(contract, ValidationSpec)
            else ValidationSpec.from_contract(contract)
        )

        run = _Run(data, cache=context.cache)
        handlers: dict[str, Callable[[_Run, CheckSpec], CheckResult | None]] = {
            "column_exists": self._check_column_exists,
            "dtype": self._check_dtype,
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

    def _check_dtype(self, run: _Run, check: CheckSpec) -> CheckResult | None:
        if check.target not in run.columns:
            return None
        expected = check.params["expected_dtype"]
        actual = _logical_dtype(run.df[check.target])
        passed = dtypes_compatible(expected, actual)
        if not passed:
            run.invalid_dtype_columns.add(check.target)
        return CheckResult(
            name=check.name,
            passed=passed,
            message=dtype_message(check.target, expected, actual, passed=passed),
            details=dtype_details(expected, actual),
        )

    @staticmethod
    def _column_usable(run: _Run, column: str) -> bool:
        return column in run.columns and column not in run.invalid_dtype_columns

    def _check_not_null(self, run: _Run, check: CheckSpec) -> CheckResult | None:
        if not self._column_usable(run, check.target):
            return None
        series = run.df[check.target]
        total = len(series)
        null_count = series.null_count()

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
        if not self._column_usable(run, check.target):
            return None
        series = run.df[check.target]
        total = len(series)
        minimum = check.params["min"]

        min_val = cast("float | None", series.min())
        passed = min_val is None or min_val >= minimum
        below = 0 if passed else int((series < minimum).sum())

        return CheckResult(
            name=check.name,
            passed=bool(passed),
            message=min_message(check.target, below, minimum),
            details={
                "actual_min": min_val,
                "violating_rows": below,
                "violating_rate": rate(below, total),
            },
        )

    def _check_max(self, run: _Run, check: CheckSpec) -> CheckResult | None:
        if not self._column_usable(run, check.target):
            return None
        series = run.df[check.target]
        total = len(series)
        maximum = check.params["max"]

        max_val = cast("float | None", series.max())
        passed = max_val is None or max_val <= maximum
        above = 0 if passed else int((series > maximum).sum())

        return CheckResult(
            name=check.name,
            passed=bool(passed),
            message=max_message(check.target, above, maximum),
            details={
                "actual_max": max_val,
                "violating_rows": above,
                "violating_rate": rate(above, total),
            },
        )

    def _check_allowed(self, run: _Run, check: CheckSpec) -> CheckResult | None:
        if not self._column_usable(run, check.target):
            return None
        series = run.df[check.target]
        total = len(series)
        allowed = check.params["allowed"]

        invalid = set(series.drop_nulls().unique().to_list()) - set(allowed)
        invalid_values = sorted_values(invalid)
        violating = int(series.is_in(invalid_values).sum())

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
        if not self._column_usable(run, check.target):
            return None
        series = run.df[check.target]
        total = len(series)

        non_null = series.drop_nulls()
        duplicated_mask = non_null.is_duplicated()
        duplicate_count = int(duplicated_mask.sum())
        sample = sorted_values(non_null.filter(duplicated_mask).to_list(), limit=SAMPLE_LIMIT)

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
        if not self._column_usable(run, check.target):
            return None
        series = run.df[check.target]
        total = len(series)
        pattern = check.params["pattern"]

        non_null = series.drop_nulls().cast(pl.String)
        mismatch_mask = ~non_null.str.contains(pattern)
        invalid_count = int(mismatch_mask.sum())
        sample = sorted_values(non_null.filter(mismatch_mask).to_list(), limit=SAMPLE_LIMIT)

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
        stats = run.stats
        try:
            passed = evaluate_rule(
                expression,
                row_count=stats.row_count,
                null_rate=stats.null_rate,
                unique_count=stats.unique_count,
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
                right_val: Any = (
                    df[rule.right]
                    if isinstance(rule.right, str) and rule.right in df.columns
                    else rule.right
                )
                mask = _OPS[rule.op](left_series, right_val)

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


def _logical_dtype(series: pl.Series) -> str:
    """Map a Polars Series to dqflow's backend-independent logical dtype."""
    non_null = series.drop_nulls()
    if len(non_null) == 0:
        return "null"

    dtype = series.dtype
    integer_types = {
        pl.Int8,
        pl.Int16,
        pl.Int32,
        pl.Int64,
        pl.UInt8,
        pl.UInt16,
        pl.UInt32,
        pl.UInt64,
    }
    if dtype == pl.Boolean:
        return "boolean"
    if dtype in integer_types:
        return "integer"
    if dtype in {pl.Float32, pl.Float64}:
        if series.null_count() and bool(((non_null % 1) == 0).all()):
            return "integer"
        return "float"
    if dtype in {pl.String, pl.Categorical, pl.Enum}:
        return "string"
    if dtype == pl.Date or isinstance(dtype, pl.Datetime):
        return "timestamp"
    return str(dtype).lower()

"""Pandas validation engine."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd

from dqflow.column import Column
from dqflow.contract import Contract
from dqflow.engines.base import Engine
from dqflow.result import CheckResult, ValidationResult


class PandasEngine(Engine):
    """Validation engine for pandas DataFrames."""

    def validate(
        self,
        df: pd.DataFrame,
        contract: Contract,
        parallel: bool = False,
        max_workers: int | None = None,
    ) -> ValidationResult:
        """
        Validate a DataFrame against a contract.

        Args:
            df: input DataFrame
            contract: validation contract
            parallel: whether to run column validation in parallel
            max_workers: optional worker limit for thread pool
        """
        result = ValidationResult(contract_name=contract.name)
        cache = self._build_stats_cache(df)

        for col_name in contract.columns:
            if col_name not in df.columns:
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

        if parallel:
            column_checks = self._validate_columns_parallel(df, contract, max_workers=max_workers)
        else:
            column_checks = self._validate_columns_sequential(df, contract)

        result.checks.extend(column_checks)

        for rule in contract.rules:
            result.checks.append(self._evaluate_rule(df, rule, cache))

        return result

    def _validate_columns_sequential(
        self,
        df: pd.DataFrame,
        contract: Contract,
    ) -> list[CheckResult]:
        """Original sequential execution (baseline)."""
        results: list[CheckResult] = []

        for col_name, col_def in contract.columns.items():
            if col_name not in df.columns:
                continue

            results.extend(
                self._validate_column(
                    df[col_name],
                    col_name,
                    col_def,
                )
            )

        return results

    def _validate_columns_parallel(
        self,
        df: pd.DataFrame,
        contract: Contract,
        max_workers: int | None = None,
    ) -> list[CheckResult]:
        """Parallel column validation using threads."""

        results: list[CheckResult] = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    self._validate_column_safe,
                    df,
                    col_name,
                    col_def,
                ): col_name
                for col_name, col_def in contract.columns.items()
                if col_name in df.columns
            }

            for future in as_completed(futures):
                results.extend(future.result())

        return results

    def _validate_column_safe(
        self,
        df: pd.DataFrame,
        col_name: str,
        col_def: Column,
    ) -> list[CheckResult]:
        """
        Thread-safe wrapper for column validation.

        Ensures no shared mutable state is accessed.
        """
        return self._validate_column(df[col_name], col_name, col_def)

    def _validate_column(
        self,
        series: pd.Series,
        col_name: str,
        col_def: Column,
    ) -> list[CheckResult]:

        checks: list[CheckResult] = []

        if col_def.not_null:
            null_count = series.isna().sum()
            checks.append(
                CheckResult(
                    name=f"not_null:{col_name}",
                    passed=null_count == 0,
                    message=f"Found {null_count} null values" if null_count > 0 else "",
                    details={"null_count": int(null_count)},
                )
            )

        if col_def.min is not None:
            min_val = series.min()
            passed = pd.isna(min_val) or min_val >= col_def.min

            checks.append(
                CheckResult(
                    name=f"min:{col_name}",
                    passed=bool(passed),
                    message=(
                        f"Minimum value {min_val} is below {col_def.min}" if not passed else ""
                    ),
                    details={"actual_min": float(min_val) if pd.notna(min_val) else None},
                )
            )

        if col_def.max is not None:
            max_val = series.max()
            passed = pd.isna(max_val) or max_val <= col_def.max

            checks.append(
                CheckResult(
                    name=f"max:{col_name}",
                    passed=bool(passed),
                    message=(
                        f"Maximum value {max_val} exceeds {col_def.max}" if not passed else ""
                    ),
                    details={"actual_max": float(max_val) if pd.notna(max_val) else None},
                )
            )

        if col_def.allowed is not None:
            allowed_set = set(col_def.allowed)
            unique_vals = set(series.dropna().unique())
            invalid = unique_vals - allowed_set

            checks.append(
                CheckResult(
                    name=f"allowed:{col_name}",
                    passed=len(invalid) == 0,
                    message=f"Found invalid values: {invalid}" if invalid else "",
                    details={"invalid_values": list(invalid)},
                )
            )

        if col_def.freshness_minutes is not None:
            checks.append(self._check_freshness(series, col_name, col_def.freshness_minutes))

        if col_def.unique:
            duplicate_count = int(series.duplicated(keep=False).sum())
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

        if col_def.pattern is not None:
            non_null = series.dropna()
            matches = non_null.astype(str).str.match(col_def.pattern, na=False)
            invalid_count = int((~matches).sum())

            checks.append(
                CheckResult(
                    name=f"pattern:{col_name}",
                    passed=invalid_count == 0,
                    message=(
                        f"{invalid_count} values do not match pattern '{col_def.pattern}'"
                        if invalid_count > 0
                        else ""
                    ),
                    details={
                        "invalid_count": invalid_count,
                        "pattern": col_def.pattern,
                    },
                )
            )

        if col_def.custom is not None:
            try:
                results = series.apply(col_def.custom)
                passed_count = int(results.sum())
                total_count = len(series)

                checks.append(
                    CheckResult(
                        name=f"custom:{col_name}",
                        passed=passed_count == total_count,
                        message=(
                            f"{total_count - passed_count} values failed custom check"
                            if passed_count != total_count
                            else ""
                        ),
                        details={
                            "passed": passed_count,
                            "total": total_count,
                        },
                    )
                )

            except Exception as exc:
                checks.append(
                    CheckResult(
                        name=f"custom:{col_name}",
                        passed=False,
                        message=f"Custom check raised exception: {exc}",
                    )
                )

        return checks

    def _check_freshness(
        self,
        series: pd.Series,
        col_name: str,
        freshness_minutes: int,
    ) -> CheckResult:

        try:
            ts_series = pd.to_datetime(series)
            max_ts = ts_series.max()

            if pd.isna(max_ts):
                return CheckResult(
                    name=f"freshness:{col_name}",
                    passed=False,
                    message="No valid timestamps found",
                )

            now = datetime.now(timezone.utc)

            if max_ts.tzinfo is None:
                max_ts = max_ts.replace(tzinfo=timezone.utc)

            age = now - max_ts
            threshold = timedelta(minutes=freshness_minutes)

            passed = age <= threshold

            return CheckResult(
                name=f"freshness:{col_name}",
                passed=passed,
                message=(f"Data is {age} old, threshold is {threshold}" if not passed else ""),
                details={
                    "max_timestamp": max_ts.isoformat(),
                    "age_minutes": age.total_seconds() / 60,
                },
            )

        except Exception as e:
            return CheckResult(
                name=f"freshness:{col_name}",
                passed=False,
                message=f"Failed to check freshness: {e}",
            )

    def _build_stats_cache(
        self,
        df: pd.DataFrame,
    ) -> dict[str, dict[str, float | int]]:

        row_count = len(df)

        return {
            col: {
                "null_rate": df[col].isna().mean(),
                "unique_count": df[col].nunique(dropna=False),
                "row_count": row_count,
            }
            for col in df.columns
        }

    def _evaluate_rule(
        self,
        df: pd.DataFrame,
        rule: str,
        cache: dict[str, dict[str, float | int]],
    ) -> CheckResult:

        try:
            result = self._parse_and_evaluate(df, rule, cache)

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

    def _parse_and_evaluate(
        self,
        df: pd.DataFrame,
        rule: str,
        cache: dict[str, dict[str, float | int]],
    ) -> Any:

        context = {
            "row_count": len(df),
            "null_rate": lambda col: cache.get(col, {}).get("null_rate", 0),
            "unique_count": lambda col: cache.get(col, {}).get("unique_count", 0),
            "duplicate_rate": lambda col: (
                (cache.get(col, {}).get("row_count", 0) - cache.get(col, {}).get("unique_count", 0))
                / cache.get(col, {}).get("row_count", 1)
                if cache.get(col)
                else 0
            ),
        }

        return eval(rule, {"__builtins__": {}}, context)

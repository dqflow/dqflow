"""Pandas validation engine."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd

from dqflow.column import Column
from dqflow.contract import Contract
from dqflow.engines.base import Engine
from dqflow.result import CheckResult, ValidationResult


class PandasEngine(Engine):
    """Validation engine for pandas DataFrames."""

    def validate(self, df: pd.DataFrame, contract: Contract) -> ValidationResult:
        """Validate a DataFrame against a contract."""
        result = ValidationResult(contract_name=contract.name)

        # Column existence checks
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
                result.checks.append(CheckResult(name=f"column_exists:{col_name}", passed=True))

        # Column-level checks
        for col_name, col_def in contract.columns.items():
            if col_name not in df.columns:
                continue
            result.checks.extend(self._validate_column(df[col_name], col_name, col_def))

        # Table-level rules
        for rule in contract.rules:
            result.checks.append(self._evaluate_rule(df, rule))

        return result

    def _validate_column(
        self, series: pd.Series, col_name: str, col_def: Column
    ) -> list[CheckResult]:
        """Validate a single column."""
        checks = []

        # Not null check
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

        # Min check
        if col_def.min is not None:
            min_val = series.min()
            passed = pd.isna(min_val) or min_val >= col_def.min
            checks.append(
                CheckResult(
                    name=f"min:{col_name}",
                    passed=bool(passed),
                    message=f"Minimum value {min_val} is below {col_def.min}" if not passed else "",
                    details={"actual_min": float(min_val) if pd.notna(min_val) else None},
                )
            )

        # Max check
        if col_def.max is not None:
            max_val = series.max()
            passed = pd.isna(max_val) or max_val <= col_def.max
            checks.append(
                CheckResult(
                    name=f"max:{col_name}",
                    passed=bool(passed),
                    message=f"Maximum value {max_val} exceeds {col_def.max}" if not passed else "",
                    details={"actual_max": float(max_val) if pd.notna(max_val) else None},
                )
            )

        # Allowed values check
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

        # Freshness check
        if col_def.freshness_minutes is not None:
            checks.append(self._check_freshness(series, col_name, col_def.freshness_minutes))

        return checks

    def _check_freshness(
        self, series: pd.Series, col_name: str, freshness_minutes: int
    ) -> CheckResult:
        """Check if timestamp column has recent data."""
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
                message=f"Data is {age} old, threshold is {threshold}" if not passed else "",
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

    def _evaluate_rule(self, df: pd.DataFrame, rule: str) -> CheckResult:
        """Evaluate a table-level rule."""
        try:
            result = self._parse_and_evaluate(df, rule)
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

    def _parse_and_evaluate(self, df: pd.DataFrame, rule: str) -> Any:
        """Parse and evaluate a rule expression."""
        # Simple rule parser - extend as needed
        context = {
            "row_count": len(df),
            "null_rate": lambda col: df[col].isna().mean() if col in df.columns else 1.0,
            "unique_count": lambda col: df[col].nunique() if col in df.columns else 0,
            "duplicate_rate": lambda col: (
                1 - (df[col].nunique() / len(df)) if col in df.columns and len(df) > 0 else 0
            ),
        }
        return eval(rule, {"__builtins__": {}}, context)

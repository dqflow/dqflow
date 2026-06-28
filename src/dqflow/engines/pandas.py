"""Pandas validation engine."""

from __future__ import annotations

import pandas as pd

from dqflow.column import Column
from dqflow.contract import Contract
from dqflow.engines.base import Engine
from dqflow.result import CheckResult, ValidationResult


class PandasEngine(Engine):
    """Validation engine for pandas DataFrames."""

    def validate(
        self,
        data: pd.DataFrame,
        contract: Contract,
        **kwargs,
    ) -> ValidationResult:

        df = data  # normalize name for internal use

        result = ValidationResult(contract_name=contract.name)
        cache = self._build_stats_cache(df)

        # Backward compatibility (ignored but accepted)
        _ = kwargs.get("parallel", False)
        _ = kwargs.get("max_workers")

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

        return result

    # COLUMN VALIDATION

    def _validate_column(
        self,
        series: pd.Series,
        col_name: str,
        col_def: Column,
    ) -> list[CheckResult]:

        checks: list[CheckResult] = []

        # NOT NULL
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

        # MIN
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

        # MAX
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

        # ALLOWED VALUES
        if col_def.allowed is not None:
            invalid = set(series.dropna().unique()) - set(col_def.allowed)

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

        return checks

    # STATS CACHE

    def _build_stats_cache(self, df: pd.DataFrame) -> dict[str, dict[str, float | int]]:
        return {
            col: {
                "null_rate": df[col].isna().mean(),
                "unique_count": df[col].nunique(dropna=False),
                "row_count": len(df),
            }
            for col in df.columns
        }

    # RULE ENGINE

    def _evaluate_rule(
        self,
        df: pd.DataFrame,
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

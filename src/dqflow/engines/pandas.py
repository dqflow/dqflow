"""Pandas validation engine."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
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
        data: pd.DataFrame,
        spec: Contract,  # standardized (matches PolarsEngine + tests)
        context: dict[str, Any] | None = None,
    ) -> ValidationResult:
        """
        Validate a pandas DataFrame against a contract.
        """

        context = context or {}

        parallel = context.get("parallel", False)
        max_workers = context.get("max_workers")

        result = ValidationResult(contract_name=spec.name)

        cache = self._build_stats_cache(data)


        # Column existence checks
        for col_name in spec.columns:
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
        if parallel:
            column_checks = self._validate_columns_parallel(
                data,
                spec,
                max_workers=max_workers,
            )
        else:
            column_checks = self._validate_columns_sequential(
                data,
                spec,
            )

        result.checks.extend(column_checks)


        # Rule evaluation
        for rule in spec.rules:
            result.checks.append(
                self._evaluate_rule(
                    data,
                    rule,
                    cache,
                    context,
                )
            )

        return result


    # Column validation (sequential)
    def _validate_columns_sequential(
        self,
        data: pd.DataFrame,
        spec: Contract,
    ) -> list[CheckResult]:

        results: list[CheckResult] = []

        for col_name, col_def in spec.columns.items():
            if col_name not in data.columns:
                continue

            results.extend(
                self._validate_column(
                    data[col_name],
                    col_name,
                    col_def,
                )
            )

        return results


    # Column validation (parallel)
    def _validate_columns_parallel(
        self,
        data: pd.DataFrame,
        spec: Contract,
        max_workers: int | None = None,
    ) -> list[CheckResult]:

        results: list[CheckResult] = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    self._validate_column_safe,
                    data,
                    col_name,
                    col_def,
                ): col_name
                for col_name, col_def in spec.columns.items()
                if col_name in data.columns
            }

            for future in as_completed(futures):
                results.extend(future.result())

        return results

    def _validate_column_safe(
        self,
        data: pd.DataFrame,
        col_name: str,
        col_def: Column,
    ) -> list[CheckResult]:

        return self._validate_column(
            data[col_name],
            col_name,
            col_def,
        )


    # Column-level checks
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
                    message=(
                        f"Found {null_count} null values"
                        if null_count > 0
                        else ""
                    ),
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
                        f"Minimum value {min_val} is below {col_def.min}"
                        if not passed
                        else ""
                    ),
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
                        f"Maximum value {max_val} exceeds {col_def.max}"
                        if not passed
                        else ""
                    ),
                )
            )

        # ALLOWED VALUES
        if col_def.allowed is not None:
            invalid = set(series.dropna().unique()) - set(col_def.allowed)

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

   
    # Stats cache
    def _build_stats_cache(
        self,
        data: pd.DataFrame,
    ) -> dict[str, dict[str, float | int]]:

        row_count = len(data)

        return {
            col: {
                "null_rate": data[col].isna().mean(),
                "unique_count": data[col].nunique(dropna=False),
                "row_count": row_count,
            }
            for col in data.columns
        }

 
    # Rule evaluation
    def _evaluate_rule(
        self,
        data: pd.DataFrame,
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
        data: pd.DataFrame,
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
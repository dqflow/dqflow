"""Infer useful draft contracts from pandas dataframes."""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any

import pandas as pd

from dqflow.column import Column
from dqflow.contract import Contract

EMAIL_PATTERN = r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$"
UUID_PATTERN = (
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-"
    r"[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
)
ISO_DATE_PATTERN = r"^\d{4}-\d{2}-\d{2}$"

_COMMON_PATTERNS = (EMAIL_PATTERN, UUID_PATTERN, ISO_DATE_PATTERN)


def infer_contract(
    df: pd.DataFrame,
    name: str = "inferred",
    *,
    infer_ranges: bool = True,
    max_allowed_cardinality: int = 20,
) -> Contract:
    """Infer a draft contract from the observed values in ``df``.

    The result describes only the supplied sample. Callers should review the
    generated constraints before treating them as a durable specification.

    Args:
        df: Source pandas DataFrame or representative sample.
        name: Name for the inferred contract.
        infer_ranges: Whether to infer observed numeric and datetime bounds.
        max_allowed_cardinality: Maximum distinct string/category values that
            can become an ``allowed`` constraint. Set to zero to disable it.

    Returns:
        A draft contract preserving source column order.

    Raises:
        ValueError: If ``max_allowed_cardinality`` is negative.
    """
    if max_allowed_cardinality < 0:
        raise ValueError("max_allowed_cardinality must be non-negative")

    columns: dict[str, Column] = {}
    for name_, series in df.items():
        non_null = series.dropna()
        dtype = _infer_dtype(series)
        column = Column(
            dtype=dtype,
            not_null=not series.isna().any(),
            unique=not non_null.empty and not non_null.duplicated().any(),
        )

        if infer_ranges and not non_null.empty and _supports_ranges(series):
            column.min = _python_scalar(non_null.min())
            column.max = _python_scalar(non_null.max())

        if _supports_allowed_values(series) and not non_null.empty:
            values = [_python_scalar(value) for value in non_null.unique()]
            if len(values) <= max_allowed_cardinality:
                column.allowed = sorted(values, key=str)

        if _supports_patterns(series) and not non_null.empty:
            column.pattern = _infer_pattern(non_null)

        columns[str(name_)] = column

    return Contract(name=name, columns=columns)


def inference_header(
    source: str,
    row_count: int,
    *,
    inferred_at: datetime | None = None,
) -> str:
    """Build the provenance comment placed above an inferred YAML contract.

    Args:
        source: Human-readable source file name.
        row_count: Number of observed rows.
        inferred_at: Optional timestamp, primarily for deterministic output.

    Returns:
        Two lines of provenance and review guidance.
    """
    timestamp = inferred_at or datetime.now().astimezone()
    safe_source = " ".join(source.splitlines())
    return (
        f"inferred by `dq infer` from {safe_source} ({row_count:,} rows) "
        f"on {timestamp.isoformat(timespec='seconds')}\n"
        "review before committing — inference is a starting point, not a spec"
    )


def _infer_dtype(series: pd.Series) -> type | str:
    dtype = series.dtype
    if pd.api.types.is_bool_dtype(dtype):
        return bool
    if pd.api.types.is_integer_dtype(dtype):
        return int
    if pd.api.types.is_float_dtype(dtype):
        return float
    if pd.api.types.is_datetime64_any_dtype(dtype):
        return "timestamp"
    return str


def _supports_ranges(series: pd.Series) -> bool:
    dtype = series.dtype
    return bool(
        not pd.api.types.is_bool_dtype(dtype)
        and (pd.api.types.is_numeric_dtype(dtype) or pd.api.types.is_datetime64_any_dtype(dtype))
    )


def _supports_allowed_values(series: pd.Series) -> bool:
    dtype = series.dtype
    return bool(
        isinstance(dtype, pd.CategoricalDtype)
        or pd.api.types.is_object_dtype(dtype)
        or pd.api.types.is_string_dtype(dtype)
    )


def _supports_patterns(series: pd.Series) -> bool:
    return bool(
        pd.api.types.is_object_dtype(series.dtype) or pd.api.types.is_string_dtype(series.dtype)
    )


def _infer_pattern(series: pd.Series) -> str | None:
    values = series.tolist()
    if not all(isinstance(value, str) for value in values):
        return None
    for pattern in _COMMON_PATTERNS:
        if all(re.fullmatch(pattern, value) is not None for value in values):
            return pattern
    return None


def _python_scalar(value: Any) -> Any:
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    if isinstance(value, (datetime, date)):
        return value
    if hasattr(value, "item"):
        return value.item()
    return value

"""Contract definition and validation orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from dqflow.column import Column
from dqflow.result import ValidationResult

if TYPE_CHECKING:
    pass


def _ensure_column(col_def: Any) -> Column:
    """
    Normalize column definition into Column object.

    Supports both:
    - {"type": ...}  (CLI / YAML legacy)
    - {"dtype": ...} (internal standard)
    """
    if isinstance(col_def, Column):
        return col_def

    if isinstance(col_def, dict):
        col_def = col_def.copy()

        # Accept BOTH formats safely
        dtype = col_def.pop("dtype", None)
        if dtype is None:
            dtype = col_def.pop("type", str)

        return Column(dtype=dtype, **col_def)

    return Column(dtype=col_def)


@dataclass
class Contract:
    """Data quality contract defining expectations for a dataset."""

    name: str
    columns: dict[str, Column] = field(default_factory=dict)
    rules: list[str] = field(default_factory=list)
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Ensure all columns are normalized into Column objects."""
        self.columns = {name: _ensure_column(col) for name, col in self.columns.items()}

    def validate(self, df: Any, engine: Any | None = None) -> ValidationResult:
        """Validate dataset using an engine (defaults to PandasEngine)."""
        if engine is None:
            from dqflow.engines.pandas import PandasEngine

            engine = PandasEngine()

        return engine.validate(df, self)

    @classmethod
    def from_yaml(cls, path: str | Path) -> Contract:
        """Load contract from YAML file."""
        path = Path(path)

        with path.open() as f:
            data = yaml.safe_load(f)

        columns = {
            name: _ensure_column(col_def) for name, col_def in data.get("columns", {}).items()
        }

        return cls(
            name=data.get("name", path.stem),
            columns=columns,
            rules=data.get("rules", []),
            description=data.get("description", ""),
            metadata=data.get("metadata", {}),
        )

    def to_yaml(self, path: str | Path) -> None:
        """Save contract to YAML file."""
        path = Path(path)

        columns_data: dict[str, Any] = {}

        for col_name, col in self.columns.items():
            col_dict: dict[str, Any] = {
                # STANDARDIZED OUTPUT FORMAT
                "dtype": _dtype_to_str(col.dtype)
            }

            if col.not_null:
                col_dict["not_null"] = True
            if col.min is not None:
                col_dict["min"] = col.min
            if col.max is not None:
                col_dict["max"] = col.max
            if col.allowed is not None:
                col_dict["allowed"] = list(col.allowed)
            if col.freshness_minutes is not None:
                col_dict["freshness_minutes"] = col.freshness_minutes
            if col.unique:
                col_dict["unique"] = True
            if col.pattern is not None:
                col_dict["pattern"] = col.pattern

            columns_data[col_name] = col_dict

        data = {
            "name": self.name,
            "columns": columns_data,
        }

        if self.rules:
            data["rules"] = self.rules
        if self.description:
            data["description"] = self.description

        with path.open("w") as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)


def _dtype_to_str(dtype: type | str) -> str:
    """Convert dtype to string representation."""
    if isinstance(dtype, str):
        return dtype
    if dtype is str:
        return "string"
    if dtype is int:
        return "integer"
    if dtype is float:
        return "float"
    if dtype is bool:
        return "boolean"
    return str(dtype)

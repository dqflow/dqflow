"""Contract definition and validation orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from dqflow.column import Column, CrossColumnRule
from dqflow.engines.registry import get_engine
from dqflow.result import ValidationResult
from dqflow.spec import ValidationSpec

if TYPE_CHECKING:
    from dqflow.engines.base import Engine


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
    """Define and execute data-quality expectations for a dataset.

    Attributes:
        name: Contract name included in validation results.
        columns: Mapping of required column names to column definitions. Plain
            types and dictionaries are normalized to :class:`Column` objects.
        rules: Table-rule expressions using ``row_count``, ``null_rate()``, and
            ``unique_count()``.
        cross_column_rules: Structured or callable row-wise rules.
        description: Human-readable contract description.
        metadata: User-defined metadata stored with the Python contract.
    """

    name: str
    columns: dict[str, Column] = field(default_factory=dict)
    rules: list[str] = field(default_factory=list)
    cross_column_rules: list[CrossColumnRule] = field(default_factory=list)
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Ensure all columns are normalized into Column objects."""
        self.columns = {name: _ensure_column(col) for name, col in self.columns.items()}

    def validate(self, df: Any, engine: Engine | str | None = None) -> ValidationResult:
        """Validate a DataFrame and return every generated check.

        Args:
            df: DataFrame supported by the selected engine.
            engine: An :class:`~dqflow.engines.base.Engine` instance, a
                registered engine name (``"pandas"`` or ``"polars"``), or
                ``None`` to use the default pandas engine.

        Returns:
            A structured result whose ``ok`` property is true only when every
            check passes.
        """
        if engine is None or isinstance(engine, str):
            engine = get_engine(engine)

        return engine.validate(df, ValidationSpec.from_contract(self))

    @classmethod
    def from_yaml(cls, path: str | Path) -> Contract:
        """Load a contract from a YAML file.

        Args:
            path: Path to the YAML contract.

        Returns:
            The parsed and normalized contract.
        """
        path = Path(path)

        with path.open() as f:
            data = yaml.safe_load(f)

        columns = {
            name: _ensure_column(col_def) for name, col_def in data.get("columns", {}).items()
        }

        cross_column_rules = [
            CrossColumnRule(
                name=r["name"],
                error_message=r.get("error_message", ""),
                left=r.get("left"),
                op=r.get("op"),
                right=r.get("right"),
            )
            for r in data.get("cross_column_rules", [])
        ]

        return cls(
            name=data.get("name", path.stem),
            columns=columns,
            rules=data.get("rules", []),
            cross_column_rules=cross_column_rules,
            description=data.get("description", ""),
            metadata=data.get("metadata", {}),
        )

    def to_yaml(self, path: str | Path, *, header: str | None = None) -> None:
        """Write the serializable portion of this contract as YAML.

        Callable cross-column rules and arbitrary metadata on ``Column`` are not
        serialized. Each line in ``header`` is written as a YAML comment.

        Args:
            path: Destination path.
            header: Optional provenance text to place above the YAML document.
        """
        path = Path(path)

        columns_data: dict[str, Any] = {
            col_name: column_to_dict(col) for col_name, col in self.columns.items()
        }

        data: dict[str, Any] = {
            "name": self.name,
            "columns": columns_data,
        }

        if self.rules:
            data["rules"] = self.rules

        serializable_cross = [r for r in self.cross_column_rules if r.check is None]
        if serializable_cross:
            cross_data = []
            for r in serializable_cross:
                rule_dict: dict[str, Any] = {
                    "name": r.name,
                    "left": r.left,
                    "op": r.op,
                    "right": r.right,
                }
                if r.error_message:
                    rule_dict["error_message"] = r.error_message
                cross_data.append(rule_dict)
            data["cross_column_rules"] = cross_data

        if self.description:
            data["description"] = self.description

        with path.open("w") as f:
            if header:
                for line in header.splitlines():
                    f.write(f"# {line}\n")
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


def column_to_dict(col: Column) -> dict[str, Any]:
    """Return the serializable, validation-affecting fields of a column.

    Only fields the engines act on are included: ``dtype`` plus any set
    constraint. ``description``, ``metadata``, and callable ``custom`` are
    omitted, matching :meth:`Contract.to_yaml`. Used for YAML output and by
    :func:`dqflow.diff.diff_contracts`.
    """
    col_dict: dict[str, Any] = {"dtype": _dtype_to_str(col.dtype)}

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

    return col_dict

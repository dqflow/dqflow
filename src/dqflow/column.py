"""Column definition and validation logic."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any

SUPPORTED_OPS: frozenset[str] = frozenset({">=", "<=", ">", "<", "==", "!="})


@dataclass
class CrossColumnRule:
    """Row-level validation rule that compares two columns or a column against a literal."""

    name: str
    error_message: str = ""
    check: Callable[[Any], Any] | None = None
    left: str | None = None
    op: str | None = None
    right: str | int | float | None = None

    def __post_init__(self) -> None:
        has_callable = self.check is not None
        has_structured = self.left is not None and self.op is not None and self.right is not None

        if has_callable and has_structured:
            raise ValueError(
                f"CrossColumnRule '{self.name}': provide either 'check' or "
                f"'left'/'op'/'right', not both."
            )
        if not has_callable and not has_structured:
            raise ValueError(
                f"CrossColumnRule '{self.name}': provide either 'check' or "
                f"all of 'left', 'op', 'right'."
            )
        if has_structured and self.op not in SUPPORTED_OPS:
            raise ValueError(
                f"CrossColumnRule '{self.name}': unsupported op '{self.op}'. "
                f"Must be one of: {sorted(SUPPORTED_OPS)}"
            )


@dataclass
class Column:
    """Define expectations for a single column."""

    dtype: type | str
    not_null: bool = False
    min: float | None = None
    max: float | None = None
    allowed: Sequence[Any] | None = None
    freshness_minutes: int | None = None
    unique: bool = False
    pattern: str | None = None
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    custom: Callable[[Any], bool] | None = None

    def __post_init__(self) -> None:
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError(f"min ({self.min}) cannot be greater than max ({self.max})")

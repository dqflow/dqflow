"""Column definition and validation logic."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Column:
    """Define expectations for a single column."""

    dtype: type | str
    not_null: bool = False
    min: float | None = None
    max: float | None = None
    allowed: Sequence[Any] | None = None
    freshness_minutes: int | None = None
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError(f"min ({self.min}) cannot be greater than max ({self.max})")

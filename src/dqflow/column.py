"""Column definition and validation logic."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any

SUPPORTED_OPS: frozenset[str] = frozenset({">=", "<=", ">", "<", "==", "!="})


@dataclass
class CrossColumnRule:
    """Validate a row-wise relationship between columns or values.

    Supply either ``check`` or all three structured fields ``left``, ``op``, and
    ``right``. A callable receives the complete DataFrame and must return a
    boolean mask with one value per row. Structured rules can be serialized to
    YAML; callable rules are Python-only.

    Attributes:
        name: Stable name used in the resulting check identifier.
        error_message: Message returned when at least one row fails.
        check: Callable accepting a pandas or Polars DataFrame and returning a
            boolean mask.
        left: Name of the left-hand column for a structured rule.
        op: Comparison operator: ``>=``, ``<=``, ``>``, ``<``, ``==``, or ``!=``.
        right: Right-hand column name or literal value.

    Raises:
        ValueError: If the callable and structured forms are mixed, required
            structured fields are missing, or the operator is unsupported.
    """

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
    """Declare constraints and metadata for one required column.

    The current pandas and Polars engines enforce ``not_null``, ``min``,
    ``max``, ``allowed``, ``unique``, and ``pattern``. They preserve but do not
    yet enforce ``dtype``, ``freshness_minutes``, or ``custom``.

    Attributes:
        dtype: Declared Python type or string type name. Currently descriptive.
        not_null: Fail when the column contains null values.
        min: Inclusive minimum value.
        max: Inclusive maximum value.
        allowed: Sequence of permitted non-null values.
        freshness_minutes: Declared maximum timestamp age. Not yet enforced.
        unique: Require non-null values to be distinct.
        pattern: Regular expression applied to every non-null string value.
        description: Human-readable description.
        metadata: User-defined metadata preserved on the contract.
        custom: Declared custom column callable. Not yet invoked by engines.

    Raises:
        ValueError: If ``min`` is greater than ``max``.
    """

    dtype: type | str
    not_null: bool = False
    min: Any | None = None
    max: Any | None = None
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

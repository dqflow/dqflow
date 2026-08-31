from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

from dqflow.result import ValidationResult

if TYPE_CHECKING:
    from dqflow.contract import Contract
    from dqflow.spec import ValidationSpec

#: Maximum number of offending values attached to a failing ``CheckResult``.
SAMPLE_LIMIT = 5


class Engine(ABC):
    """Abstract interface implemented by DataFrame validation engines."""

    @abstractmethod
    def validate(
        self,
        data: Any,
        contract: Contract | ValidationSpec,
        **kwargs: Any,
    ) -> ValidationResult:
        """Validate data against a contract.

        Args:
            data: Engine-specific DataFrame object.
            contract: A :class:`~dqflow.contract.Contract` or an already-compiled
                :class:`~dqflow.spec.ValidationSpec`. A contract is compiled once
                on entry; engines execute the spec.
            **kwargs: Optional engine-specific execution settings.

        Returns:
            Engine-independent validation result.
        """
        ...


def sorted_values(values: Iterable[Any], *, limit: int | None = None) -> list[Any]:
    """Return the distinct ``values`` in a deterministic, JSON-safe order.

    Engines call this so the offending-value lists they attach to a
    :class:`~dqflow.result.CheckResult` are identical across pandas and Polars
    (their raw ``set`` iteration order is not). Values that are not mutually
    comparable fall back to ``repr`` order; ``limit`` bounds the result.
    """
    distinct = list(dict.fromkeys(values))
    try:
        distinct.sort()
    except TypeError:
        distinct.sort(key=repr)
    if limit is not None:
        distinct = distinct[:limit]
    return [v.item() if hasattr(v, "item") else v for v in distinct]


def rate(count: int, total: int) -> float:
    """Return ``count / total`` as a float, or ``0.0`` when ``total`` is zero."""
    return float(count / total) if total else 0.0


def count_noun(count: int, noun: str) -> str:
    """Return ``"1 value"`` / ``"3 values"`` — ``noun`` pluralised with a bare ``s``."""
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"


# --- Failure messages -------------------------------------------------------
#
# One definition per check, shared by every engine so pandas and Polars emit
# byte-identical ``CheckResult.message`` strings. Each returns ``""`` when the
# check passed (the ``count`` / flag argument is zero / false).


def missing_column_message(col: str) -> str:
    """Message for a ``column_exists`` check."""
    return f"Column '{col}' is missing from the data"


def not_null_message(col: str, null_count: int) -> str:
    if not null_count:
        return ""
    return f"Column '{col}' has {count_noun(null_count, 'null value')}"


def min_message(col: str, below: int, minimum: Any) -> str:
    if not below:
        return ""
    return f"Column '{col}' has {count_noun(below, 'value')} below the minimum {minimum}"


def max_message(col: str, above: int, maximum: Any) -> str:
    if not above:
        return ""
    return f"Column '{col}' has {count_noun(above, 'value')} above the maximum {maximum}"


def allowed_message(col: str, violating: int, *, has_invalid: bool) -> str:
    if not has_invalid:
        return ""
    return f"Column '{col}' has {count_noun(violating, 'value')} outside the allowed set"


def unique_message(col: str, duplicate_count: int) -> str:
    if not duplicate_count:
        return ""
    return f"Column '{col}' has {count_noun(duplicate_count, 'non-unique value')}"


def pattern_message(col: str, invalid_count: int, pattern: str) -> str:
    if not invalid_count:
        return ""
    return f"Column '{col}' has {count_noun(invalid_count, 'value')} not matching {pattern!r}"


def rule_failed_message(expression: str) -> str:
    return f"Rule '{expression}' failed"


def rule_error_message(exc: object) -> str:
    return f"Failed to evaluate rule: {exc}"


def cross_column_error_message(name: str, exc: object) -> str:
    return f"Failed to evaluate cross-column rule '{name}': {exc}"

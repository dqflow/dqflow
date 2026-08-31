from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any

from dqflow.contract import Contract
from dqflow.result import ValidationResult

#: Maximum number of offending values attached to a failing ``CheckResult``.
SAMPLE_LIMIT = 5


class Engine(ABC):
    """Abstract interface implemented by DataFrame validation engines."""

    @abstractmethod
    def validate(
        self,
        data: Any,
        contract: Contract,
        **kwargs: Any,
    ) -> ValidationResult:
        """Validate data against a contract.

        Args:
            data: Engine-specific DataFrame object.
            contract: Contract to execute.
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

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


def sample_values(values: Iterable[Any], limit: int = SAMPLE_LIMIT) -> list[Any]:
    """Return up to ``limit`` distinct values in a deterministic, JSON-safe order.

    Engines call this to attach a bounded sample of offending values to a
    :class:`~dqflow.result.CheckResult` so the CLI can show *which* values failed
    a check. Sorting keeps pandas and Polars output identical; values that are
    not mutually comparable fall back to ``repr`` order.
    """
    distinct = list(dict.fromkeys(values))
    try:
        distinct.sort()
    except TypeError:
        distinct.sort(key=repr)
    return [v.item() if hasattr(v, "item") else v for v in distinct[:limit]]


def rate(count: int, total: int) -> float:
    """Return ``count / total`` as a float, or ``0.0`` when ``total`` is zero."""
    return float(count / total) if total else 0.0


def count_noun(count: int, noun: str) -> str:
    """Return ``"1 value"`` / ``"3 values"`` — ``noun`` pluralised with a bare ``s``."""
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"

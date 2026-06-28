"""Abstract base engine."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from dqflow.contract import Contract
    from dqflow.result import ValidationResult


class Engine(ABC):
    """Abstract base class for validation engines."""

    @abstractmethod
    def validate(
        self,
        data: Any,
        spec: Contract,
        context: dict[str, Any] | None = None,
    ) -> ValidationResult:
        """
        Validate data against a specification.

        Args:
            data:
                Input dataset to validate.

            spec:
                Validation specification (contract).

            context:
                Runtime execution context / options.

        Returns:
            ValidationResult containing validation outcomes.
        """
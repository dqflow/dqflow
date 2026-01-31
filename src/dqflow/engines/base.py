"""Abstract base engine."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from dqflow.contract import Contract
    from dqflow.result import ValidationResult


class Engine(ABC):
    """Abstract base class for validation engines."""

    @abstractmethod
    def validate(self, data: Any, contract: Contract) -> ValidationResult:
        """Validate data against a contract."""
        ...

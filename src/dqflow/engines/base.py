"""Abstract base engine."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from dqflow.contract import Contract
from dqflow.result import ValidationResult


class Engine(ABC):
    """Abstract base class for validation engines."""

    @abstractmethod
    def validate(self, data: Any, contract: Contract) -> ValidationResult:
        """
        Validate data against a contract.

        Must return identical ValidationResult structure across all engines.
        """
        raise NotImplementedError
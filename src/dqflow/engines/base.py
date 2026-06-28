from abc import ABC, abstractmethod
from typing import Any

from dqflow.contract import Contract
from dqflow.result import ValidationResult


class Engine(ABC):
    @abstractmethod
    def validate(
        self,
        data: Any,
        contract: Contract,
        **kwargs: Any,
    ) -> ValidationResult:
        """Validate data against a contract."""
        ...

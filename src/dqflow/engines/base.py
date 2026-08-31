from abc import ABC, abstractmethod
from typing import Any

from dqflow.contract import Contract
from dqflow.result import ValidationResult


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

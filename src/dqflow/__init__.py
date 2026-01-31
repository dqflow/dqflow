"""dqflow - Lightweight, contract-first data quality engine."""

from dqflow.column import Column
from dqflow.contract import Contract
from dqflow.result import ValidationResult

__version__ = "0.1.2"
__all__ = ["Contract", "Column", "ValidationResult"]

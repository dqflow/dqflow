"""dqflow - Lightweight, contract-first data quality engine."""

from dqflow.column import Column
from dqflow.contract import Contract
from dqflow.result import ValidationResult

__version__ = "0.2.0"
__all__ = ["Contract", "Column", "ValidationResult"]

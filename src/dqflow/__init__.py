"""dqflow - Lightweight, contract-first data quality engine."""

from dqflow.column import Column, CrossColumnRule
from dqflow.contract import Contract
from dqflow.diff import ContractChange, ContractDiff, diff_contracts
from dqflow.inference import infer_contract
from dqflow.result import ValidationResult

__version__ = "0.3.0"
__all__ = [
    "Column",
    "Contract",
    "ContractChange",
    "ContractDiff",
    "CrossColumnRule",
    "ValidationResult",
    "diff_contracts",
    "infer_contract",
]

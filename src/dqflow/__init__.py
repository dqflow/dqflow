"""dqflow - Lightweight, contract-first data quality engine."""

from dqflow.cache import StatsCache
from dqflow.column import Column, CrossColumnRule
from dqflow.contract import Contract
from dqflow.diff import ContractChange, ContractDiff, diff_contracts
from dqflow.engines import available_engines, get_engine, register_engine
from dqflow.engines.base import Engine
from dqflow.execution import ExecutionContext
from dqflow.inference import infer_contract
from dqflow.result import ValidationResult
from dqflow.rules import evaluate_rule
from dqflow.spec import ValidationSpec

__version__ = "0.4.0"
__all__ = [
    "Column",
    "Contract",
    "ContractChange",
    "ContractDiff",
    "CrossColumnRule",
    "Engine",
    "ExecutionContext",
    "StatsCache",
    "ValidationResult",
    "ValidationSpec",
    "available_engines",
    "diff_contracts",
    "evaluate_rule",
    "get_engine",
    "infer_contract",
    "register_engine",
]

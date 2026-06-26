"""Validation engines."""

from dqflow.engines.base import Engine
from dqflow.engines.pandas import PandasEngine

__all__ = ["Engine", "PandasEngine"]

try:
    from dqflow.engines.polars import PolarsEngine

    __all__ = [*__all__, "PolarsEngine"]
except ImportError:
    pass

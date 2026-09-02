"""Engine registry: resolve an :class:`~dqflow.engines.base.Engine` by name.

This module is deliberately light — importing it does not import pandas, Polars,
or any concrete engine. The engine modules are imported lazily inside
:func:`get_engine` so ``import dqflow`` stays cheap and :mod:`dqflow.contract`
can depend on the registry without depending on an engine.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dqflow.engines.base import Engine

#: Name used when no engine is requested.
DEFAULT_ENGINE = "pandas"

EngineFactory = Callable[[], "Engine"]


class UnknownEngineError(ValueError):
    """Raised when an engine name is not registered."""


def _pandas_engine() -> Engine:
    from dqflow.engines.pandas import PandasEngine

    return PandasEngine()


def _polars_engine() -> Engine:
    try:
        from dqflow.engines.polars import PolarsEngine
    except ImportError as exc:  # pragma: no cover - exercised via message only
        raise ImportError(
            "The 'polars' engine requires the optional Polars dependency. "
            'Install it with: pip install "dqflow[polars]"'
        ) from exc

    return PolarsEngine()


_REGISTRY: dict[str, EngineFactory] = {
    "pandas": _pandas_engine,
    "polars": _polars_engine,
}


def register_engine(name: str, factory: EngineFactory) -> None:
    """Register ``factory`` under ``name`` for later :func:`get_engine` lookups.

    Args:
        name: Lower-case identifier, e.g. ``"spark"``.
        factory: Zero-argument callable returning a fresh engine instance.
    """
    _REGISTRY[name.lower()] = factory


def available_engines() -> list[str]:
    """Return the registered engine names in sorted order."""
    return sorted(_REGISTRY)


def get_engine(name: str | None = None) -> Engine:
    """Return a new engine instance for ``name``.

    Args:
        name: Registered engine name. ``None`` selects :data:`DEFAULT_ENGINE`.

    Returns:
        A fresh :class:`~dqflow.engines.base.Engine`.

    Raises:
        UnknownEngineError: If ``name`` is not registered.
        ImportError: If the engine's optional dependency is missing.
    """
    key = (name or DEFAULT_ENGINE).lower()

    try:
        factory = _REGISTRY[key]
    except KeyError:
        raise UnknownEngineError(
            f"Unknown engine {name!r}. Available engines: {', '.join(available_engines())}"
        ) from None

    return factory()

"""ExecutionContext: the runtime configuration for a single validation run.

A :class:`~dqflow.contract.Contract` says *what* a dataset must look like and a
:class:`~dqflow.spec.ValidationSpec` is its compiled form. ``ExecutionContext`` is
the third axis — *how* a run executes: which engine, whether table-rule
statistics are cached, and (reserved) execution-mode flags. It is the single
place later performance and integration work configures a run instead of
threading ad-hoc keyword arguments through every layer.

Only ``engine`` and ``cache`` change behaviour today. ``parallel`` /
``max_workers`` / ``strict`` / ``fail_fast`` are carried but not yet acted on —
see the class docstring.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from dqflow.engines.registry import DEFAULT_ENGINE, get_engine

if TYPE_CHECKING:
    from dqflow.engines.base import Engine


@dataclass(frozen=True)
class ExecutionContext:
    """Runtime configuration for one :meth:`~dqflow.contract.Contract.validate` call.

    Attributes:
        engine: Registered engine name to run the contract with
            (``"pandas"`` / ``"polars"``). Resolved through the engine registry
            by :meth:`resolve_engine`.
        parallel: Reserved. Accepted and carried but not yet acted on — execution
            is always sequential today
            ([#22](https://github.com/dqflow/dqflow/issues/22)).
        max_workers: Reserved companion to ``parallel``; no effect yet.
        cache: When true (default), table-rule statistics are memoised for the
            run so a column referenced by several rules is scanned once. Set to
            false to recompute every statistic on access.
        strict: Reserved execution-mode flag; no effect yet
            ([#44](https://github.com/dqflow/dqflow/issues/44)).
        fail_fast: Reserved execution-mode flag; no effect yet. Unrelated to the
            ``dq validate --fail-fast`` option, which only controls the process
            exit code.
    """

    engine: str = DEFAULT_ENGINE
    parallel: bool = False
    max_workers: int | None = None
    cache: bool = True
    strict: bool = False
    fail_fast: bool = False

    def resolve_engine(self) -> Engine:
        """Return a fresh engine instance for :attr:`engine` via the registry.

        Raises:
            UnknownEngineError: If :attr:`engine` is not registered.
            ImportError: If the engine's optional dependency is missing.
        """
        return get_engine(self.engine)

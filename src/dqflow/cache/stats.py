"""Shared column-statistics cache used by table-rule evaluation.

Table rules need three statistics — ``row_count``, ``null_rate(col)`` and
``unique_count(col)``. :class:`StatsCache` is the engine-agnostic half: it
memoizes every statistic (so a column referenced by several rules is scanned
once) and derives ``null_rate`` from the null count and row count. Each engine
subclasses it with three primitives that actually read its DataFrame.

The cache is lazy — nothing is computed until a rule asks for it — and scoped to
a single ``validate()`` call. A statistic for a column the data does not contain
is reported as zero, matching the previous per-engine behaviour.

Memoisation can be turned off (``memoize=False``, driven by
``ExecutionContext(cache=False)``): every statistic is then recomputed on each
access. Cache *size* limits remain future work.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable


class StatsCache(ABC):
    """Lazily computed, memoized column statistics for one ``validate()`` call.

    Subclasses implement :meth:`_compute_row_count`,
    :meth:`_compute_null_count`, and :meth:`_compute_unique_count`.
    """

    def __init__(self, columns: Iterable[str], *, memoize: bool = True) -> None:
        self._memoize = memoize
        self._known = frozenset(columns)
        self._row_count: int | None = None
        self._null_counts: dict[str, int] = {}
        self._unique_counts: dict[str, int] = {}

    # --- primitives implemented per engine -----------------------------

    @abstractmethod
    def _compute_row_count(self) -> int: ...

    @abstractmethod
    def _compute_null_count(self, column: str) -> int: ...

    @abstractmethod
    def _compute_unique_count(self, column: str) -> int: ...

    # --- memoized public statistics -----------------------------------

    @property
    def row_count(self) -> int:
        if not self._memoize:
            return self._compute_row_count()
        if self._row_count is None:
            self._row_count = self._compute_row_count()
        return self._row_count

    def null_count(self, column: str) -> int:
        if column not in self._known:
            return 0
        if not self._memoize:
            return self._compute_null_count(column)
        if column not in self._null_counts:
            self._null_counts[column] = self._compute_null_count(column)
        return self._null_counts[column]

    def unique_count(self, column: str) -> int:
        if column not in self._known:
            return 0
        if not self._memoize:
            return self._compute_unique_count(column)
        if column not in self._unique_counts:
            self._unique_counts[column] = self._compute_unique_count(column)
        return self._unique_counts[column]

    def null_rate(self, column: str) -> float:
        total = self.row_count
        return self.null_count(column) / total if total else 0.0

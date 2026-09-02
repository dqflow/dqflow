"""ValidationSpec: the engine-agnostic intermediate representation.

A :class:`~dqflow.contract.Contract` describes *what* a dataset must look like.
:class:`ValidationSpec` is its compiled form: a flat, ordered tuple of
:class:`CheckSpec` entries that every engine executes the same way. Compiling the
contract once — in :meth:`ValidationSpec.from_contract` — is the only place a
:class:`~dqflow.column.Column` is inspected; engines never read ``Column`` fields
directly.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from dqflow.contract import Contract

#: Check kinds an engine must handle. ``column_exists`` always yields a result;
#: the per-column constraint kinds are skipped at runtime when their column is
#: missing from the data.
CHECK_KINDS: frozenset[str] = frozenset(
    {
        "column_exists",
        "not_null",
        "min",
        "max",
        "allowed",
        "unique",
        "pattern",
        "rule",
        "cross_column",
    },
)


@dataclass(frozen=True)
class CheckSpec:
    """One atomic check for an engine to execute.

    Attributes:
        kind: One of :data:`CHECK_KINDS`.
        target: Column name, table-rule expression, or cross-column rule name.
        name: The stable :class:`~dqflow.result.CheckResult` identifier, e.g.
            ``"min:amount"`` — precomputed so engines never build identifiers.
        params: Kind-specific parameters (``{"min": 0}``, ``{"pattern": "..."}``,
            ``{"expression": "row_count > 0"}``, ``{"rule": CrossColumnRule(...)}``).
    """

    kind: str
    target: str
    name: str
    params: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ValidationSpec:
    """A contract compiled into an ordered, engine-agnostic list of checks.

    Attributes:
        contract_name: Name carried onto the :class:`~dqflow.result.ValidationResult`.
        checks: Checks in canonical execution order — every ``column_exists``
            first, then per-column constraints (in ``Column`` field order), then
            table rules, then cross-column rules.
    """

    contract_name: str
    checks: tuple[CheckSpec, ...] = ()

    @classmethod
    def from_contract(cls, contract: Contract) -> ValidationSpec:
        """Compile ``contract`` into a :class:`ValidationSpec`."""
        checks: list[CheckSpec] = []

        for col_name in contract.columns:
            checks.append(CheckSpec("column_exists", col_name, f"column_exists:{col_name}"))

        for col_name, column in contract.columns.items():
            checks.extend(_column_checks(col_name, column))

        for rule in contract.rules:
            checks.append(CheckSpec("rule", rule, f"rule:{rule}", {"expression": rule}))

        for cross_rule in contract.cross_column_rules:
            checks.append(
                CheckSpec(
                    "cross_column",
                    cross_rule.name,
                    f"cross_column:{cross_rule.name}",
                    {"rule": cross_rule},
                )
            )

        return cls(contract_name=contract.name, checks=tuple(checks))


def _column_checks(name: str, column: Any) -> Iterator[CheckSpec]:
    """Yield the constraint checks declared on one column, in field order."""
    if column.not_null:
        yield CheckSpec("not_null", name, f"not_null:{name}")
    if column.min is not None:
        yield CheckSpec("min", name, f"min:{name}", {"min": column.min})
    if column.max is not None:
        yield CheckSpec("max", name, f"max:{name}", {"max": column.max})
    if column.allowed is not None:
        yield CheckSpec("allowed", name, f"allowed:{name}", {"allowed": tuple(column.allowed)})
    if column.unique:
        yield CheckSpec("unique", name, f"unique:{name}")
    if column.pattern is not None:
        yield CheckSpec("pattern", name, f"pattern:{name}", {"pattern": column.pattern})

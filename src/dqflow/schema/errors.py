"""Typed exceptions and the :class:`Diagnostic` record for contract loading.

``dqflow`` distinguishes three failure modes when reading a YAML contract:

* :class:`ContractParseError` — the file is not valid YAML.
* :class:`ContractSchemaError` — the YAML parsed but the contract is
  structurally wrong (unknown field, wrong type, contradictory bounds, …). It
  carries a list of :class:`Diagnostic` records, each with a ``path`` into the
  document.
* :class:`ContractVersionError` — the ``schema_version`` is not one this
  release understands.

All three derive from :class:`ContractError`, so callers that only care that a
contract failed to load can catch the base class.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

ERROR = "error"
WARNING = "warning"


@dataclass(frozen=True)
class Diagnostic:
    """One problem found in a contract document.

    Attributes:
        severity: ``"error"`` (the contract cannot be loaded) or ``"warning"``
            (loadable, but probably not intended).
        code: Stable kebab-case token, e.g. ``"unknown-field"``. Safe to branch
            on; the human ``message`` is not.
        message: Human-readable, actionable description.
        path: Location in the document — ``"columns.amount.min"``,
            ``"rules[2]"``, or ``""`` for the document root.
        line: 1-based line in the source file when known, else ``None``.
    """

    severity: str
    code: str
    message: str
    path: str = ""
    line: int | None = None

    @property
    def is_error(self) -> bool:
        """Whether this diagnostic is error severity."""
        return self.severity == ERROR

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable representation."""
        return {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "path": self.path,
            "line": self.line,
        }

    def __str__(self) -> str:
        where = self.path or "(root)"
        location = f"{where}:{self.line}" if self.line is not None else where
        return f"{self.severity}: {location}: {self.message} [{self.code}]"


class ContractError(Exception):
    """Base class for every contract-loading failure."""


class ContractParseError(ContractError):
    """The contract file could not be parsed as YAML."""


class ContractSchemaError(ContractError):
    """The contract parsed but is structurally invalid.

    Attributes:
        diagnostics: The error-severity :class:`Diagnostic` records that caused
            the failure (warnings are not included here).
        source: The contract file path, when loaded from one.
    """

    def __init__(self, diagnostics: list[Diagnostic], *, source: str | None = None) -> None:
        self.diagnostics = diagnostics
        self.source = source
        super().__init__(self._render())

    def _render(self) -> str:
        head = f"invalid contract {self.source}" if self.source else "invalid contract"
        count = len(self.diagnostics)
        head += f": {count} error{'s' if count != 1 else ''}"
        lines = [head]
        for d in self.diagnostics:
            where = d.path or "(root)"
            location = f"{where}:{d.line}" if d.line is not None else where
            lines.append(f"  {location}: {d.message} [{d.code}]")
        return "\n".join(lines)


class ContractVersionError(ContractError):
    """The contract's ``schema_version`` is not supported by this dqflow release."""

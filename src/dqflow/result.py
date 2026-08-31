"""Validation result structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def _to_native(obj: Any) -> Any:
    """Convert numpy types to native Python types for JSON serialization."""
    if hasattr(obj, "item"):  # numpy scalar
        return obj.item()
    if isinstance(obj, dict):
        return {k: _to_native(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_native(v) for v in obj]
    if isinstance(obj, set):
        return [_to_native(v) for v in obj]
    return obj


@dataclass
class CheckResult:
    """Represent one schema, column, table, or cross-column check.

    Attributes:
        name: Stable check identifier such as ``not_null:order_id``.
        passed: Whether the check passed.
        message: Human-readable failure detail; empty for passing checks.
        details: Structured values useful for logs and reports.
    """

    name: str
    passed: bool
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Aggregate all checks produced while validating one contract.

    Attributes:
        contract_name: Name of the validated contract.
        checks: Checks in engine execution order.
    """

    contract_name: str
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """Return whether every check passed."""
        return all(check.passed for check in self.checks)

    @property
    def failed_checks(self) -> list[CheckResult]:
        """Return failed checks in execution order."""
        return [check for check in self.checks if not check.passed]

    def summary(self) -> str:
        """Return a compact text summary including every failed check."""
        total = len(self.checks)
        passed = sum(1 for c in self.checks if c.passed)
        failed = total - passed

        lines = [f"Contract '{self.contract_name}': {passed}/{total} checks passed"]

        if failed > 0:
            lines.append("Failed checks:")
            for check in self.failed_checks:
                lines.append(f"  - {check.name}: {check.message}")

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation of this result."""
        return {
            "contract_name": self.contract_name,
            "ok": bool(self.ok),
            "total_checks": len(self.checks),
            "passed": sum(1 for c in self.checks if c.passed),
            "failed": sum(1 for c in self.checks if not c.passed),
            "checks": [
                {
                    "name": c.name,
                    "passed": bool(c.passed),
                    "message": c.message,
                    "details": _to_native(c.details),
                }
                for c in self.checks
            ],
        }

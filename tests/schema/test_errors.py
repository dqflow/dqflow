"""Tests for the typed exceptions and the Diagnostic record."""

from __future__ import annotations

from dqflow.schema import ContractError, ContractSchemaError, Diagnostic


def test_diagnostic_to_dict_is_json_shaped() -> None:
    d = Diagnostic("error", "unknown-field", "unknown field 'x'", "columns.a.x", 7)
    assert d.to_dict() == {
        "severity": "error",
        "code": "unknown-field",
        "message": "unknown field 'x'",
        "path": "columns.a.x",
        "line": 7,
    }


def test_diagnostic_str_includes_location_and_code() -> None:
    assert "columns.a:3" in str(Diagnostic("error", "c", "m", "columns.a", 3))
    assert "(root)" in str(Diagnostic("warning", "c", "m", ""))


def test_contract_schema_error_renders_every_diagnostic() -> None:
    exc = ContractSchemaError(
        [
            Diagnostic("error", "unknown-field", "unknown field 'x'", "columns.a.x", 4),
            Diagnostic("error", "invalid-regex", "bad pattern", "columns.b.pattern", 9),
        ],
        source="orders.yaml",
    )
    message = str(exc)
    assert "orders.yaml" in message
    assert "2 errors" in message
    assert "columns.a.x:4" in message
    assert "columns.b.pattern:9" in message
    assert isinstance(exc, ContractError)


def test_contract_schema_error_keeps_diagnostics_accessible() -> None:
    diags = [Diagnostic("error", "unknown-field", "m", "p")]
    exc = ContractSchemaError(diags, source="c.yaml")
    assert exc.diagnostics == diags
    assert exc.source == "c.yaml"

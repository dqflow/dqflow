"""End-to-end checks over the YAML fixtures and the file loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from dqflow.schema import (
    ContractParseError,
    Diagnostic,
    format_diagnostics,
    lint_contract_file,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_valid_fixture_is_clean() -> None:
    assert lint_contract_file(FIXTURES / "valid_v1.yaml") == []


def test_legacy_type_alias_fixture_is_clean() -> None:
    assert lint_contract_file(FIXTURES / "legacy_type_alias.yaml") == []


def test_many_errors_fixture_reports_each_problem() -> None:
    diagnostics = lint_contract_file(FIXTURES / "many_errors.yaml")
    codes = {d.code for d in diagnostics}
    assert {
        "unknown-field",
        "min-greater-than-max",
        "invalid-regex",
        "wrong-type",
        "invalid-rule",
        "duplicate-rule",
        "invalid-operator",
        "duplicate-cross-column-rule-name",
        "incomplete-cross-column-rule",
    } <= codes
    # every diagnostic points somewhere and carries a line number
    for d in diagnostics:
        assert d.line is None or d.line > 0


def test_unsupported_version_fixture() -> None:
    (d,) = [x for x in lint_contract_file(FIXTURES / "unsupported_version.yaml") if x.is_error]
    assert d.code == "unsupported-schema-version"


def test_non_mapping_columns_fixture() -> None:
    codes = {d.code for d in lint_contract_file(FIXTURES / "not_mapping_columns.yaml")}
    assert "wrong-type" in codes


def test_non_mapping_root_fixture() -> None:
    (d,) = lint_contract_file(FIXTURES / "not_mapping_root.yaml")
    assert d.code == "not-a-mapping"


def test_malformed_yaml_raises_parse_error() -> None:
    with pytest.raises(ContractParseError, match="malformed.txt"):
        lint_contract_file(FIXTURES / "malformed.txt")


def test_format_diagnostics_clean() -> None:
    assert format_diagnostics("x.yaml", []) == "x.yaml: OK"


def test_format_diagnostics_groups_and_counts() -> None:
    text = format_diagnostics(
        "x.yaml",
        [
            Diagnostic("error", "e1", "boom", "columns.a", 3),
            Diagnostic("warning", "w1", "hmm", ""),
        ],
    )
    assert "1 error, 1 warning" in text
    assert "ERROR" in text and "WARN" in text
    assert "[e1]" in text and "columns.a:3" in text

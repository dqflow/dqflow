"""Unit tests for :func:`dqflow.schema.lint_contract_data` — one per code."""

from __future__ import annotations

import dataclasses

import pytest

from dqflow.column import Column
from dqflow.schema import lint_contract_data
from dqflow.schema.validate import KNOWN_COLUMN_FIELDS


def _codes(data: object) -> list[str]:
    return [d.code for d in lint_contract_data(data)]


def _errors(data: object) -> list[str]:
    return [d.code for d in lint_contract_data(data) if d.is_error]


class TestClean:
    def test_a_valid_contract_has_no_diagnostics(self) -> None:
        data = {
            "schema_version": "1.0",
            "name": "orders",
            "columns": {
                "id": {"dtype": "string", "not_null": True, "unique": True},
                "amount": {"dtype": "float", "min": 0, "max": 10, "pattern": r"\d+"},
                "ccy": {"dtype": "string", "allowed": ["USD", "EUR"]},
            },
            "rules": ["row_count > 0", "null_rate('amount') < 0.1"],
            "cross_column_rules": [{"name": "r", "left": "a", "op": ">", "right": 0}],
        }
        assert lint_contract_data(data) == []

    def test_legacy_type_alias_is_accepted(self) -> None:
        data = {"schema_version": "1.0", "name": "x", "columns": {"a": {"type": "string"}}}
        assert lint_contract_data(data) == []

    def test_bare_dtype_shorthand_is_accepted(self) -> None:
        data = {"schema_version": "1.0", "name": "x", "columns": {"a": "string"}}
        assert lint_contract_data(data) == []


class TestErrors:
    def test_not_a_mapping_root(self) -> None:
        assert _errors(["a", "list"]) == ["not-a-mapping"]

    def test_unknown_top_level_field(self) -> None:
        data = {"schema_version": "1.0", "name": "x", "columns": {"a": {"dtype": "s"}}, "extra": 1}
        assert "unknown-field" in _errors(data)

    def test_unknown_column_field(self) -> None:
        data = {"schema_version": "1.0", "name": "x", "columns": {"a": {"dtype": "s", "wat": 1}}}
        assert "unknown-field" in _errors(data)

    def test_wrong_type_not_null(self) -> None:
        data = {
            "schema_version": "1.0",
            "name": "x",
            "columns": {"a": {"dtype": "s", "not_null": "yes"}},
        }
        assert "wrong-type" in _errors(data)

    def test_schema_key_must_be_a_string(self) -> None:
        data = {"$schema": ["nope"], "name": "x", "columns": {"a": {"dtype": "s"}}}
        assert "wrong-type" in _errors(data)

    def test_schema_key_is_otherwise_accepted(self) -> None:
        data = {
            "$schema": "https://dqflow.github.io/dqflow/schema/contract-1.0.json",
            "schema_version": "1.0",
            "name": "x",
            "columns": {"a": {"dtype": "s"}},
        }
        assert lint_contract_data(data) == []

    def test_wrong_type_rules_not_a_list(self) -> None:
        data = {
            "schema_version": "1.0",
            "name": "x",
            "columns": {"a": {"dtype": "s"}},
            "rules": "row_count > 0",
        }
        assert "wrong-type" in _errors(data)

    def test_min_greater_than_max(self) -> None:
        data = {
            "schema_version": "1.0",
            "name": "x",
            "columns": {"a": {"dtype": "int", "min": 5, "max": 1}},
        }
        assert "min-greater-than-max" in _errors(data)

    def test_invalid_regex(self) -> None:
        data = {
            "schema_version": "1.0",
            "name": "x",
            "columns": {"a": {"dtype": "s", "pattern": "([a-z"}},
        }
        assert "invalid-regex" in _errors(data)

    def test_invalid_rule(self) -> None:
        data = {
            "schema_version": "1.0",
            "name": "x",
            "columns": {"a": {"dtype": "s"}},
            "rules": ["import os"],
        }
        assert "invalid-rule" in _errors(data)

    def test_invalid_operator(self) -> None:
        data = {
            "schema_version": "1.0",
            "name": "x",
            "columns": {"a": {"dtype": "s"}},
            "cross_column_rules": [{"name": "r", "left": "a", "op": "~=", "right": "b"}],
        }
        assert "invalid-operator" in _errors(data)

    def test_incomplete_cross_column_rule(self) -> None:
        data = {
            "schema_version": "1.0",
            "name": "x",
            "columns": {"a": {"dtype": "s"}},
            "cross_column_rules": [{"name": "r", "left": "a"}],
        }
        assert "incomplete-cross-column-rule" in _errors(data)

    def test_duplicate_cross_column_rule_name(self) -> None:
        data = {
            "schema_version": "1.0",
            "name": "x",
            "columns": {"a": {"dtype": "s"}},
            "cross_column_rules": [
                {"name": "r", "left": "a", "op": ">", "right": 0},
                {"name": "r", "left": "b", "op": ">", "right": 0},
            ],
        }
        assert "duplicate-cross-column-rule-name" in _errors(data)


class TestWarnings:
    def test_missing_schema_version(self) -> None:
        data = {"name": "x", "columns": {"a": {"dtype": "s"}}}
        assert "missing-schema-version" in _codes(data)
        assert _errors(data) == []

    def test_missing_name(self) -> None:
        data = {"schema_version": "1.0", "columns": {"a": {"dtype": "s"}}}
        assert "missing-name" in _codes(data)

    def test_missing_column_dtype(self) -> None:
        data = {"schema_version": "1.0", "name": "x", "columns": {"a": {"not_null": True}}}
        assert "missing-column-dtype" in _codes(data)

    def test_empty_contract(self) -> None:
        assert "empty-contract" in _codes({"schema_version": "1.0", "name": "x"})

    def test_empty_allowed(self) -> None:
        data = {
            "schema_version": "1.0",
            "name": "x",
            "columns": {"a": {"dtype": "s", "allowed": []}},
        }
        assert "empty-allowed" in _codes(data)

    def test_duplicate_rule(self) -> None:
        data = {
            "schema_version": "1.0",
            "name": "x",
            "columns": {"a": {"dtype": "s"}},
            "rules": ["row_count > 0", "row_count > 0"],
        }
        codes = _codes(data)
        assert "duplicate-rule" in codes
        assert _errors(data) == []


def test_known_column_fields_stay_in_sync_with_the_dataclass() -> None:
    """Every serialisable ``Column`` field must be recognised by the linter."""
    dataclass_fields = {f.name for f in dataclasses.fields(Column)}
    python_only = {"custom"}
    expected = (dataclass_fields - python_only) | {"type"}  # "type" is the legacy alias
    assert expected == KNOWN_COLUMN_FIELDS


@pytest.mark.parametrize(
    ("value", "code"),
    [
        ("1.0", None),
        ("1.5", "newer-schema-minor"),
        ("2.0", "unsupported-schema-version"),
        ("nope", "unsupported-schema-version"),
    ],
)
def test_schema_version_values(value: str, code: str | None) -> None:
    data = {"schema_version": value, "name": "x", "columns": {"a": {"dtype": "s"}}}
    codes = _codes(data)
    if code is None:
        assert not any(c.startswith(("unsupported-", "newer-", "missing-schema")) for c in codes)
    else:
        assert code in codes

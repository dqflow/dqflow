"""The published JSON Schema: validity, packaging, and agreement with the linter.

`dq lint` is authoritative; the JSON Schema is a subset for editor tooling. The
agreement checks therefore assert *one direction* — the schema never rejects a
contract the linter accepts — plus that both pass the known-good fixtures.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import pytest
import yaml

from dqflow.schema import (
    CONTRACT_SCHEMA_FILENAME,
    SCHEMA_VERSION,
    contract_json_schema,
    lint_contract_data,
)
from dqflow.schema.published import CONTRACT_SCHEMA_URI, contract_schema_text

jsonschema = pytest.importorskip("jsonschema")

FIXTURES = Path(__file__).parent / "fixtures"
_SCHEMA = contract_json_schema()


def _json_safe(value: object) -> object:
    """Project a YAML-parsed contract onto its JSON form (dates -> ISO strings)."""
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    return value


def _schema_valid(data: object) -> bool:
    validator = jsonschema.Draft202012Validator(_SCHEMA)
    return validator.is_valid(_json_safe(data))


def _linter_ok(data: object) -> bool:
    return not any(d.is_error for d in lint_contract_data(data))


class TestSchemaItself:
    def test_filename_matches_version(self) -> None:
        expected = f"contract-{SCHEMA_VERSION}.json"
        assert expected == CONTRACT_SCHEMA_FILENAME

    def test_packaged_file_is_readable_and_matches_accessor(self) -> None:
        assert json.loads(contract_schema_text()) == _SCHEMA

    def test_id_matches_published_uri(self) -> None:
        assert _SCHEMA["$id"] == CONTRACT_SCHEMA_URI

    def test_is_a_valid_2020_12_schema(self) -> None:
        jsonschema.Draft202012Validator.check_schema(_SCHEMA)


class TestAgreement:
    @pytest.mark.parametrize("name", ["valid_v1.yaml", "legacy_type_alias.yaml"])
    def test_known_good_fixtures_pass_both(self, name: str) -> None:
        data = yaml.safe_load((FIXTURES / name).read_text())
        assert _schema_valid(data)
        assert _linter_ok(data)

    def test_many_errors_fixture_fails_the_schema_too(self) -> None:
        data = yaml.safe_load((FIXTURES / "many_errors.yaml").read_text())
        assert not _schema_valid(data)
        assert not _linter_ok(data)

    @pytest.mark.parametrize(
        "name",
        ["valid_v1.yaml", "legacy_type_alias.yaml", "many_errors.yaml", "not_mapping_columns.yaml"],
    )
    def test_schema_is_never_stricter_than_the_linter(self, name: str) -> None:
        data = yaml.safe_load((FIXTURES / name).read_text())
        if not _schema_valid(data):
            assert not _linter_ok(data), f"{name}: schema rejects it but the linter does not"


def test_cli_schema_command_prints_valid_json() -> None:
    from click.testing import CliRunner

    from dqflow.cli import main

    result = CliRunner().invoke(main, ["schema"])
    assert result.exit_code == 0
    assert json.loads(result.output)["$id"] == CONTRACT_SCHEMA_URI

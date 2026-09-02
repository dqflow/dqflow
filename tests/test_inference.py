"""Tests for contract inference."""

from datetime import datetime
from pathlib import Path

import pandas as pd

from dqflow.contract import Contract
from dqflow.inference import (
    EMAIL_PATTERN,
    ISO_DATE_PATTERN,
    UUID_PATTERN,
    infer_contract,
    inference_header,
)


def test_infer_contract_adds_supported_constraints() -> None:
    df = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "status": ["new", "done", "new"],
            "email": ["a@example.com", "b@example.com", "a@example.com"],
            "amount": [1.5, 3.0, 2.0],
            "created_at": pd.to_datetime(
                ["2026-08-01T00:00:00", "2026-08-02T00:00:00", "2026-08-03T00:00:00"]
            ),
        }
    )

    contract = infer_contract(df, name="orders")

    assert contract.name == "orders"
    assert contract.columns["id"].not_null is True
    assert contract.columns["id"].unique is True
    assert contract.columns["status"].allowed == ["done", "new"]
    assert contract.columns["email"].pattern is not None
    assert contract.columns["amount"].min == 1.5
    assert contract.columns["amount"].max == 3.0
    assert contract.columns["created_at"].min == datetime(2026, 8, 1)
    assert contract.columns["created_at"].max == datetime(2026, 8, 3)
    assert contract.validate(df).ok is True


def test_infer_contract_options_disable_ranges_and_limit_allowed() -> None:
    df = pd.DataFrame({"category": ["a", "b", "c", "a"], "value": [1, 2, 3, 4]})

    contract = infer_contract(
        df,
        infer_ranges=False,
        max_allowed_cardinality=2,
    )

    assert contract.columns["category"].allowed is None
    assert contract.columns["value"].min is None
    assert contract.columns["value"].max is None


def test_infer_contract_recognizes_common_string_patterns() -> None:
    df = pd.DataFrame(
        {
            "email": ["a@example.com", "person+tag@example.co.uk"],
            "uuid": [
                "123e4567-e89b-12d3-a456-426614174000",
                "c73bcdcc-2669-4bf6-81d3-e4ae73fb11fd",
            ],
            "date": ["2026-08-01", "2026-08-31"],
        }
    )

    contract = infer_contract(df)

    assert contract.columns["email"].pattern == EMAIL_PATTERN
    assert contract.columns["uuid"].pattern == UUID_PATTERN
    assert contract.columns["date"].pattern == ISO_DATE_PATTERN


def test_inferred_contract_validates_its_source_with_nulls() -> None:
    df = pd.DataFrame({"optional_id": [1.0, None, 2.0], "status": ["a", "a", "b"]})

    contract = infer_contract(df)

    assert contract.columns["optional_id"].unique is True
    assert contract.validate(df).ok is True


def test_inferred_datetime_ranges_round_trip_through_yaml(tmp_path: Path) -> None:
    path = tmp_path / "events.yaml"
    df = pd.DataFrame(
        {"occurred_at": pd.to_datetime(["2026-08-01T10:00:00", "2026-08-02T11:00:00"])}
    )
    inferred = infer_contract(df, name="events")

    inferred.to_yaml(path)
    loaded = Contract.from_yaml(path)

    assert loaded.validate(df).ok is True


def test_inferred_contract_yaml_declares_a_schema_version(tmp_path: Path) -> None:
    from dqflow.schema import SCHEMA_VERSION, lint_contract_file

    path = tmp_path / "c.yaml"
    df = pd.DataFrame({"id": [1, 2, 3], "name": ["a", "b", "c"]})
    infer_contract(df, name="c").to_yaml(path)

    assert f"schema_version: '{SCHEMA_VERSION}'" in path.read_text()
    assert lint_contract_file(path) == []


def test_inference_header_records_provenance() -> None:
    header = inference_header(
        "data/orders.csv",
        1_000,
        inferred_at=datetime(2026, 8, 28, 12, 30, 0),
    )

    assert header == (
        "inferred by `dq infer` from data/orders.csv (1,000 rows) "
        "on 2026-08-28T12:30:00\n"
        "review before committing — inference is a starting point, not a spec"
    )

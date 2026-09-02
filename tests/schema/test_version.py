"""Tests for the schema-version compatibility policy."""

from __future__ import annotations

import pytest

from dqflow.schema.version import SCHEMA_VERSION, check_version


def test_current_version_is_clean() -> None:
    assert check_version(SCHEMA_VERSION) == []


def test_missing_version_warns() -> None:
    (d,) = check_version(None)
    assert d.severity == "warning"
    assert d.code == "missing-schema-version"


@pytest.mark.parametrize("value", ["1.0"])
def test_supported_minor_is_clean(value: str) -> None:
    assert check_version(value) == []


def test_newer_minor_same_major_warns() -> None:
    (d,) = check_version("1.99")
    assert d.severity == "warning"
    assert d.code == "newer-schema-minor"


@pytest.mark.parametrize("value", ["2.0", "0.9", "3.1"])
def test_different_major_is_an_error(value: str) -> None:
    (d,) = check_version(value)
    assert d.is_error
    assert d.code == "unsupported-schema-version"


@pytest.mark.parametrize("value", ["nope", "1", "1.2.3", "1.x", ""])
def test_unparseable_version_is_an_error(value: str) -> None:
    (d,) = check_version(value)
    assert d.is_error
    assert d.code == "unsupported-schema-version"


def test_non_string_version_is_an_error() -> None:
    (d,) = check_version(1.0)
    assert d.is_error

"""Tests for Column class."""

import pytest

from dqflow import Column


class TestColumn:
    """Tests for Column definition."""

    def test_basic_column(self) -> None:
        col = Column(dtype=str)
        assert col.dtype is str
        assert col.not_null is False
        assert col.min is None
        assert col.max is None
        assert col.allowed is None

    def test_column_with_constraints(self) -> None:
        col = Column(
            dtype=float,
            not_null=True,
            min=0,
            max=1000,
            allowed=None,
        )
        assert col.dtype is float
        assert col.not_null is True
        assert col.min == 0
        assert col.max == 1000

    def test_column_with_allowed_values(self) -> None:
        col = Column(dtype=str, allowed=["USD", "EUR", "GBP"])
        assert col.allowed == ["USD", "EUR", "GBP"]

    def test_column_with_freshness(self) -> None:
        col = Column(dtype="timestamp", freshness_minutes=60)
        assert col.freshness_minutes == 60

    def test_column_min_max_validation(self) -> None:
        with pytest.raises(ValueError, match="min.*cannot be greater than max"):
            Column(dtype=float, min=100, max=10)

    def test_column_with_metadata(self) -> None:
        col = Column(
            dtype=str,
            description="Customer identifier",
            metadata={"source": "crm"},
        )
        assert col.description == "Customer identifier"
        assert col.metadata == {"source": "crm"}

"""Pytest fixtures for dqflow tests."""

from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest

from dqflow import Column, Contract


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Sample DataFrame for testing."""
    return pd.DataFrame(
        {
            "order_id": ["A001", "A002", "A003"],
            "amount": [100.0, 250.5, 75.0],
            "currency": ["USD", "EUR", "USD"],
            "created_at": pd.to_datetime(
                [
                    datetime.now(timezone.utc) - timedelta(minutes=30),
                    datetime.now(timezone.utc) - timedelta(minutes=20),
                    datetime.now(timezone.utc) - timedelta(minutes=10),
                ]
            ),
        }
    )


@pytest.fixture
def sample_contract() -> Contract:
    """Sample contract for testing."""
    return Contract(
        name="orders",
        columns={
            "order_id": Column(str, not_null=True),
            "amount": Column(float, min=0),
            "currency": Column(str, allowed=["USD", "EUR"]),
        },
        rules=["row_count > 0"],
    )


@pytest.fixture
def df_with_nulls() -> pd.DataFrame:
    """DataFrame with null values for testing."""
    return pd.DataFrame(
        {
            "id": [1, 2, None],
            "name": ["Alice", None, "Charlie"],
        }
    )


@pytest.fixture
def df_with_violations() -> pd.DataFrame:
    """DataFrame that violates common constraints."""
    return pd.DataFrame(
        {
            "order_id": ["A001", None, "A003"],
            "amount": [100.0, -50.0, 75.0],
            "currency": ["USD", "GBP", "USD"],  # GBP not allowed
        }
    )

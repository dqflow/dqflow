"""Tests for PandasEngine"""

import pandas as pd

import pytest

from dqflow import Column, Contract
from dqflow.engines.pandas import PandasEngine


@pytest.fixture
def engine():
    return PandasEngine()


@pytest.fixture
def sample_df():
    return pd.DataFrame(
        {
            "order_id": ["A001", "A002", "A003"],
            "amount": [100.0, 250.5, 75.0],
            "currency": ["USD", "EUR", "USD"],
        }
    )


@pytest.fixture
def contract():
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
def violations_df():
    return pd.DataFrame(
        {
            "order_id": ["A001", None, "A003"],
            "amount": [100.0, -50.0, 75.0],
            "currency": ["USD", "GBP", "USD"],
        }
    )
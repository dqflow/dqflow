"""Engine Conformance Harness (Issue 6 enforcement layer)."""

from __future__ import annotations

import inspect

import pandas as pd
import pytest

from dqflow import Column, Contract
from dqflow.engines.pandas import PandasEngine
from dqflow.engines.polars import PolarsEngine

pl = pytest.importorskip("polars")


# Engine Registry
ENGINES = [
    ("pandas", PandasEngine),
    ("polars", PolarsEngine),
]


# Shared Contracts
@pytest.fixture
def base_contract() -> Contract:
    return Contract(
        name="orders",
        columns={
            "order_id": Column(str, not_null=True),
            "amount": Column(float, min=0),
            "currency": Column(str, allowed=["USD", "EUR"]),
        },
        rules=[
            "row_count > 0",
        ],
    )


# Shared Datasets
@pytest.fixture
def clean_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "order_id": ["A001", "A002", "A003"],
            "amount": [100.0, 250.5, 75.0],
            "currency": ["USD", "EUR", "USD"],
        }
    )


@pytest.fixture
def dirty_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "order_id": ["A001", None, "A003"],
            "amount": [100.0, -50.0, 75.0],
            "currency": ["USD", "GBP", "USD"],
        }
    )


# Engine Runner
def run_engine(engine_cls, data, spec: Contract):
    """
    Normalizes execution across engines.
    Handles format differences (Pandas vs Polars).
    """

    engine = engine_cls()

    # Polars expects Polars DataFrame
    if engine_cls.__name__ == "PolarsEngine":
        data = pl.from_pandas(data)

    return engine.validate(data, spec, context={})


# 1. Interface Compliance
def test_all_engines_follow_validate_interface():
    """
    Ensures strict compliance:
    validate(data, spec, context)
    """

    expected_signature = ["self", "data", "spec", "context"]

    for name, engine_cls in ENGINES:
        sig = inspect.signature(engine_cls.validate)

        assert list(sig.parameters.keys()) == expected_signature, (
            f"{name} engine signature mismatch: {sig}"
        )

        assert not any(
            p.kind == inspect.Parameter.VAR_KEYWORD
            for p in sig.parameters.values()
        ), (
            f"{name} engine must not use **kwargs"
        )


# 2. Clean Data Consistency
def test_all_engines_pass_clean_data(base_contract, clean_data):
    """
    All engines must produce identical success behavior.
    """

    results = {}

    for name, engine_cls in ENGINES:
        results[name] = run_engine(engine_cls, clean_data, base_contract)

    assert all(r.ok for r in results.values())

    reference = results["pandas"]

    for name, result in results.items():
        assert result.contract_name == reference.contract_name
        assert len(result.checks) == len(reference.checks), (
            f"{name} check count mismatch"
        )


# 3. Dirty Data Consistency
def test_all_engines_fail_consistently(base_contract, dirty_data):
    """
    All engines must detect the same failures.
    """

    results = {}

    for name, engine_cls in ENGINES:
        results[name] = run_engine(engine_cls, dirty_data, base_contract)

    assert all(not r.ok for r in results.values())

    failed_sets = {
        name: {c.name for c in r.checks if not c.passed}
        for name, r in results.items()
    }

    reference = next(iter(failed_sets.values()))

    for name, failed in failed_sets.items():
        assert failed == reference, f"{name} failed checks mismatch"


# 4. Rule Evaluation Consistency
def test_rule_evaluation_consistency(base_contract, clean_data):
    """
    Ensures rule engine behaves identically across engines.
    """

    for name, engine_cls in ENGINES:
        result = run_engine(engine_cls, clean_data, base_contract)

        rule_checks = [
            c for c in result.checks
            if c.name.startswith("rule:")
        ]

        assert len(rule_checks) > 0, f"{name} missing rule checks"
        assert all(c.passed for c in rule_checks), (
            f"{name} rule evaluation failed unexpectedly"
        )


# 5. Structural Stability Test (Regression Guard)
def test_validation_result_structure_stable(base_contract, clean_data):
    """
    Ensures ValidationResult structure remains stable across engines.
    """

    results = [
        run_engine(engine_cls, clean_data, base_contract)
        for _, engine_cls in ENGINES
    ]

    reference = results[0]

    for result in results[1:]:
        assert result.contract_name == reference.contract_name

        # FIXED: removed type() comparison (E721 safe fix)
        assert len(result.checks) == len(reference.checks)

        assert all(
            hasattr(c, "name") and hasattr(c, "passed")
            for c in result.checks
        )


# 6. Column-Level Determinism Check
def test_column_level_determinism(base_contract, clean_data):
    """
    Ensures both engines produce identical column check names.
    """

    results = {}

    for name, engine_cls in ENGINES:
        results[name] = run_engine(engine_cls, clean_data, base_contract)

    column_checks = {
        name: {
            c.name
            for c in result.checks
            if "column_exists" in c.name
        }
        for name, result in results.items()
    }

    reference = next(iter(column_checks.values()))

    for name, checks in column_checks.items():
        assert checks == reference, (
            f"{name} column checks mismatch"
        )
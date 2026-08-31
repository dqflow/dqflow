"""ValidationSpec compilation (issue #16)."""

from __future__ import annotations

import dataclasses

import pandas as pd
import polars as pl
import pytest

from dqflow import Column, Contract
from dqflow.column import CrossColumnRule
from dqflow.engines.pandas import PandasEngine
from dqflow.engines.polars import PolarsEngine
from dqflow.spec import CheckSpec, ValidationSpec


def _names(spec: ValidationSpec) -> list[str]:
    return [c.name for c in spec.checks]


class TestFromContract:
    def test_column_constraints_map_to_checks(self) -> None:
        contract = Contract(
            name="orders",
            columns={
                "order_id": Column(str, not_null=True, unique=True),
                "amount": Column(float, min=0, max=100),
                "currency": Column(str, allowed=["USD", "EUR"]),
                "code": Column(str, pattern=r"^[A-Z]{2}$"),
            },
        )
        spec = ValidationSpec.from_contract(contract)

        assert spec.contract_name == "orders"
        assert _names(spec) == [
            "column_exists:order_id",
            "column_exists:amount",
            "column_exists:currency",
            "column_exists:code",
            "not_null:order_id",
            "unique:order_id",
            "min:amount",
            "max:amount",
            "allowed:currency",
            "pattern:code",
        ]

    def test_check_params_carry_the_constraint_value(self) -> None:
        contract = Contract(
            name="c",
            columns={"amount": Column(float, min=0, max=100, allowed=[1, 2], pattern="x")},
        )
        by_kind = {c.kind: c for c in ValidationSpec.from_contract(contract).checks}

        assert by_kind["min"].params == {"min": 0}
        assert by_kind["max"].params == {"max": 100}
        assert by_kind["allowed"].params == {"allowed": (1, 2)}
        assert by_kind["pattern"].params == {"pattern": "x"}

    def test_rules_and_cross_column_rules_come_last_in_order(self) -> None:
        rule = CrossColumnRule(name="lt", left="a", op="<=", right="b")
        contract = Contract(
            name="c",
            columns={"a": Column(int), "b": Column(int)},
            rules=["row_count > 0"],
            cross_column_rules=[rule],
        )
        spec = ValidationSpec.from_contract(contract)

        assert _names(spec)[-2:] == ["rule:row_count > 0", "cross_column:lt"]
        rule_check = next(c for c in spec.checks if c.kind == "rule")
        assert rule_check.params == {"expression": "row_count > 0"}
        assert spec.checks[-1].params["rule"] is rule

    def test_column_without_constraints_yields_only_existence_check(self) -> None:
        spec = ValidationSpec.from_contract(Contract(name="c", columns={"a": Column(int)}))
        assert _names(spec) == ["column_exists:a"]

    def test_empty_contract_compiles_to_no_checks(self) -> None:
        assert ValidationSpec.from_contract(Contract(name="empty")).checks == ()


class TestSpecShape:
    def test_spec_and_checks_are_frozen(self) -> None:
        spec = ValidationSpec.from_contract(Contract(name="c", columns={"a": Column(int)}))
        with pytest.raises(dataclasses.FrozenInstanceError):
            spec.checks = ()  # type: ignore[misc]
        with pytest.raises(dataclasses.FrozenInstanceError):
            spec.checks[0].kind = "other"  # type: ignore[misc]

    def test_from_contract_is_pure(self) -> None:
        contract = Contract(name="c", columns={"a": Column(int, min=0)})
        assert ValidationSpec.from_contract(contract) == ValidationSpec.from_contract(contract)

    def test_check_spec_is_constructible_directly(self) -> None:
        check = CheckSpec("not_null", "a", "not_null:a")
        assert check.params == {}


class TestEnginesConsumeSpec:
    @pytest.mark.parametrize("engine_cls", [PandasEngine, PolarsEngine])
    def test_validate_accepts_contract_or_prebuilt_spec(self, engine_cls: type) -> None:
        contract = Contract(
            name="orders",
            columns={"amount": Column(float, min=0)},
            rules=["row_count == 2"],
        )
        frame_cls = pd.DataFrame if engine_cls is PandasEngine else pl.DataFrame
        data = frame_cls({"amount": [1.0, 2.0]})

        from_contract = engine_cls().validate(data, contract)
        from_spec = engine_cls().validate(data, ValidationSpec.from_contract(contract))

        assert from_contract.to_dict() == from_spec.to_dict()

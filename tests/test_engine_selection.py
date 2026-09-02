"""Engine selection at runtime via ExecutionContext and the CLI (issue #15).

The ``engine=`` shortcut, the registry, and custom engines are covered by
``tests/test_contract_engine_injection.py``; this module focuses on the
``ExecutionContext`` path and the CLI wiring built on it.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
import polars as pl
import pytest
from click.testing import CliRunner

from dqflow import Column, Contract, ExecutionContext
from dqflow.cli import main

_CONTRACT_YAML = """
name: orders
columns:
  order_id:
    type: string
    not_null: true
  amount:
    type: float
    min: 0
rules:
  - row_count > 0
"""


@pytest.fixture
def contract() -> Contract:
    return Contract(
        name="orders",
        columns={"order_id": Column(str, not_null=True), "amount": Column(float, min=0)},
        rules=["row_count > 0"],
    )


class TestProgrammaticSelection:
    def test_default_context_runs_on_pandas(self, contract: Contract) -> None:
        result = contract.validate(
            pd.DataFrame({"order_id": ["A"], "amount": [1.0]}),
            context=ExecutionContext(),
        )
        assert result.ok

    def test_polars_selected_by_context(self, contract: Contract) -> None:
        result = contract.validate(
            pl.DataFrame({"order_id": ["A"], "amount": [1.0]}),
            context=ExecutionContext(engine="polars"),
        )
        assert result.ok

    def test_engines_agree_when_selected_by_context(self, contract: Contract) -> None:
        rows = {"order_id": ["A", "B", "C"], "amount": [1.0, -2.0, 3.0]}
        pandas_result = contract.validate(pd.DataFrame(rows), context=ExecutionContext())
        polars_result = contract.validate(
            pl.DataFrame(rows), context=ExecutionContext(engine="polars")
        )
        assert pandas_result.to_dict() == polars_result.to_dict()


class TestCliWiring:
    def test_engine_option_builds_execution_context(self, monkeypatch: pytest.MonkeyPatch) -> None:
        captured: dict[str, object] = {}
        original = Contract.validate

        def spy(self: Contract, df: object, *args: object, **kwargs: object):  # type: ignore[no-untyped-def]
            captured["context"] = kwargs.get("context")
            return original(self, df, *args, **kwargs)

        monkeypatch.setattr(Contract, "validate", spy)

        with TemporaryDirectory() as tmp:
            contract_path = Path(tmp) / "c.yml"
            contract_path.write_text(_CONTRACT_YAML)
            data_path = Path(tmp) / "d.csv"
            pd.DataFrame({"order_id": ["A"], "amount": [1.0]}).to_csv(data_path, index=False)

            result = CliRunner().invoke(
                main, ["validate", str(contract_path), str(data_path), "--engine", "polars"]
            )

        assert result.exit_code == 0
        ctx = captured["context"]
        assert isinstance(ctx, ExecutionContext)
        assert ctx.engine == "polars"

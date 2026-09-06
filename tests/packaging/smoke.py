"""Smoke-test an installed wheel and one optional-dependency profile."""

from __future__ import annotations

import importlib.metadata
import json
import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from click.testing import CliRunner

import dqflow
from dqflow.cli import main as cli_main


def _installed(name: str) -> bool:
    try:
        importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return False
    return True


def _contract_file(directory: Path) -> Path:
    path = directory / "contract with ữnicode.yaml"
    path.write_text(
        "schema_version: '1.0'\n"
        "name: smoke\n"
        "columns:\n"
        "  id:\n"
        "    dtype: integer\n"
        "    not_null: true\n",
        encoding="utf-8",
    )
    return path


def main() -> None:
    profile = os.environ["DQFLOW_SMOKE_PROFILE"]
    assert dqflow.__version__ == importlib.metadata.version("dqflow")
    subprocess.run(["dq", "--version"], check=True, capture_output=True, text=True)

    with TemporaryDirectory() as raw_directory:
        directory = Path(raw_directory) / "directory with spaces"
        directory.mkdir()
        contract = _contract_file(directory)
        lint = CliRunner().invoke(cli_main, ["lint", str(contract), "--output", "json"])
        assert lint.exit_code == 0, lint.output
        assert json.loads(lint.output)["ok"] is True

        if profile == "base":
            assert not _installed("pandas")
            assert not _installed("polars")
            data_path = directory / "data.csv"
            data_path.write_text("id\n1\n", encoding="utf-8")
            result = CliRunner().invoke(cli_main, ["validate", str(contract), str(data_path)])
            assert result.exit_code != 0
            assert "dqflow[pandas]" in result.output
            return

        if profile in {"pandas", "pandas-parquet", "all"}:
            import pandas as pd

            frame = pd.DataFrame({"id": [1, 2]})
            result = dqflow.Contract.from_yaml(contract).validate(frame)
            assert result.ok
            csv_path = directory / "data ữnicode.csv"
            frame.to_csv(csv_path, index=False)
            cli_result = CliRunner().invoke(
                cli_main, ["validate", str(contract), str(csv_path), "--output", "json"]
            )
            assert cli_result.exit_code == 0, cli_result.output

        if profile in {"polars", "all"}:
            import polars as pl

            frame = pl.DataFrame({"id": [1, 2]})
            result = dqflow.Contract.from_yaml(contract).validate(frame, engine="polars")
            assert result.ok

        if profile == "polars":
            assert not _installed("pandas")

        if profile in {"pandas-parquet", "all"}:
            import pandas as pd

            parquet_path = directory / "data ữnicode.parquet"
            pd.DataFrame({"id": [1, 2]}).to_parquet(parquet_path)
            cli_result = CliRunner().invoke(
                cli_main, ["validate", str(contract), str(parquet_path), "--output", "json"]
            )
            assert cli_result.exit_code == 0, cli_result.output


if __name__ == "__main__":
    main()

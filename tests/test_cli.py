"""Tests for CLI commands."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
from click.testing import CliRunner

from dqflow.cli import main


class TestCLI:
    """Tests for CLI commands."""

    def test_version(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "dqflow" in result.output

    def test_validate_passing(self) -> None:
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create contract
            contract_path = tmpdir / "contract.yaml"
            contract_path.write_text("""
name: test
columns:
  id:
    type: integer
  name:
    type: string
""")

            # Create data
            data_path = tmpdir / "data.csv"
            df = pd.DataFrame({"id": [1, 2, 3], "name": ["a", "b", "c"]})
            df.to_csv(data_path, index=False)

            result = runner.invoke(main, ["validate", str(contract_path), str(data_path)])
            assert result.exit_code == 0
            assert "passed" in result.output

    def test_validate_failing_with_fail_fast(self) -> None:
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            contract_path = tmpdir / "contract.yaml"
            contract_path.write_text("""
name: test
columns:
  id:
    type: integer
    not_null: true
""")

            data_path = tmpdir / "data.csv"
            df = pd.DataFrame({"id": [1, None, 3]})
            df.to_csv(data_path, index=False)

            result = runner.invoke(
                main, ["validate", str(contract_path), str(data_path), "--fail-fast"]
            )
            assert result.exit_code == 1

    def test_validate_json_output(self) -> None:
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            contract_path = tmpdir / "contract.yaml"
            contract_path.write_text("""
name: test
columns:
  id:
    type: integer
""")

            data_path = tmpdir / "data.csv"
            df = pd.DataFrame({"id": [1, 2, 3]})
            df.to_csv(data_path, index=False)

            result = runner.invoke(
                main, ["validate", str(contract_path), str(data_path), "-o", "json"]
            )
            assert result.exit_code == 0
            assert '"contract_name"' in result.output
            assert '"ok"' in result.output

    def test_show_command(self) -> None:
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            contract_path = tmpdir / "contract.yaml"
            contract_path.write_text("""
name: orders
description: Order data contract
columns:
  order_id:
    type: string
    not_null: true
  amount:
    type: float
    min: 0
    max: 10000
rules:
  - row_count > 0
""")

            result = runner.invoke(main, ["show", str(contract_path)])
            assert result.exit_code == 0
            assert "orders" in result.output
            assert "order_id" in result.output
            assert "NOT NULL" in result.output
            assert "min=0" in result.output

    def test_infer_command(self) -> None:
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            data_path = tmpdir / "data.csv"
            df = pd.DataFrame({
                "id": [1, 2, 3],
                "name": ["a", "b", "c"],
                "value": [1.5, 2.5, 3.5],
            })
            df.to_csv(data_path, index=False)

            output_path = tmpdir / "inferred.yaml"
            result = runner.invoke(main, ["infer", str(data_path), str(output_path)])
            assert result.exit_code == 0
            assert output_path.exists()

            content = output_path.read_text()
            assert "name:" in content or "id:" in content

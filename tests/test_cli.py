"""Tests for CLI commands."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
from click.testing import CliRunner

from dqflow.cli import main

_CONTRACT_V1 = """
name: orders
columns:
  order_id:
    type: string
    not_null: true
  amount:
    type: float
    min: 0
  currency:
    type: string
    allowed: ["USD", "EUR"]
"""

_CONTRACT_V2_BREAKING = """
name: orders
columns:
  order_id:
    type: string
    not_null: true
  amount:
    type: float
    min: 10
  currency:
    type: string
    allowed: ["USD", "EUR", "JPY"]
"""


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

    def test_validate_text_output_is_grouped_with_samples(self) -> None:
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            contract_path = tmpdir / "contract.yaml"
            contract_path.write_text(_CONTRACT_V1)

            data_path = tmpdir / "data.csv"
            pd.DataFrame(
                {
                    "order_id": ["A1", None, "A3"],
                    "amount": [10.0, -5.0, 20.0],
                    "currency": ["USD", "GBP", "EUR"],
                }
            ).to_csv(data_path, index=False)

            result = runner.invoke(main, ["validate", str(contract_path), str(data_path)])
            assert result.exit_code == 0
            assert "checks failed" in result.output
            assert "Columns" in result.output
            assert "on 3 rows" in result.output
            assert "'GBP'" in result.output  # offending value sampled

    def test_validate_quiet_hides_passing_checks(self) -> None:
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            contract_path = tmpdir / "contract.yaml"
            contract_path.write_text(_CONTRACT_V1)
            data_path = tmpdir / "data.csv"
            pd.DataFrame(
                {"order_id": ["A1", "A2"], "amount": [1.0, -9.0], "currency": ["USD", "EUR"]}
            ).to_csv(data_path, index=False)

            result = runner.invoke(
                main, ["validate", str(contract_path), str(data_path), "--quiet"]
            )
            assert result.exit_code == 0
            assert "below the minimum" in result.output
            assert "checks passed" not in result.output

    def test_validate_verbose_lists_passing_checks(self) -> None:
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            contract_path = tmpdir / "contract.yaml"
            contract_path.write_text(_CONTRACT_V1)
            data_path = tmpdir / "data.csv"
            pd.DataFrame(
                {"order_id": ["A1", "A2"], "amount": [1.0, 2.0], "currency": ["USD", "EUR"]}
            ).to_csv(data_path, index=False)

            result = runner.invoke(main, ["validate", str(contract_path), str(data_path), "-v"])
            assert result.exit_code == 0
            assert result.output.count("✔") >= 5

    def test_validate_quiet_and_verbose_conflict(self) -> None:
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            contract_path = tmpdir / "contract.yaml"
            contract_path.write_text(_CONTRACT_V1)
            data_path = tmpdir / "data.csv"
            pd.DataFrame({"order_id": ["A1"], "amount": [1.0], "currency": ["USD"]}).to_csv(
                data_path, index=False
            )

            result = runner.invoke(
                main, ["validate", str(contract_path), str(data_path), "-q", "-v"]
            )
            assert result.exit_code != 0
            assert "at most one" in result.output

    def test_validate_color_flag_forces_ansi(self) -> None:
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            contract_path = tmpdir / "contract.yaml"
            contract_path.write_text(_CONTRACT_V1)
            data_path = tmpdir / "data.csv"
            pd.DataFrame({"order_id": ["A1"], "amount": [-1.0], "currency": ["USD"]}).to_csv(
                data_path, index=False
            )

            plain = runner.invoke(main, ["validate", str(contract_path), str(data_path)])
            colored = runner.invoke(
                main, ["validate", str(contract_path), str(data_path), "--color"]
            )
            assert "\x1b[" not in plain.output
            assert "\x1b[" in colored.output

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

    def test_validate_engine_polars_matches_pandas(self) -> None:
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            contract_path = tmpdir / "contract.yaml"
            contract_path.write_text(_CONTRACT_V1)

            data_path = tmpdir / "data.csv"
            pd.DataFrame(
                {
                    "order_id": ["A1", "A2", "A3"],
                    "amount": [10.0, 5.0, 20.0],
                    "currency": ["USD", "EUR", "USD"],
                }
            ).to_csv(data_path, index=False)

            args = ["validate", str(contract_path), str(data_path), "-o", "json"]
            pandas_out = runner.invoke(main, [*args, "--engine", "pandas"])
            polars_out = runner.invoke(main, [*args, "--engine", "polars"])

            assert pandas_out.exit_code == 0
            assert polars_out.exit_code == 0
            assert json.loads(pandas_out.output) == json.loads(polars_out.output)

    def test_validate_engine_polars_fail_fast(self) -> None:
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            contract_path = tmpdir / "contract.yaml"
            contract_path.write_text(_CONTRACT_V1)

            data_path = tmpdir / "data.csv"
            pd.DataFrame(
                {"order_id": ["A1", None], "amount": [10.0, -5.0], "currency": ["USD", "GBP"]}
            ).to_csv(data_path, index=False)

            args = ["validate", str(contract_path), str(data_path), "--engine", "polars"]
            result = runner.invoke(main, [*args, "--fail-fast"])
            assert result.exit_code == 1

    def test_validate_rejects_unknown_engine(self) -> None:
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            contract_path = tmpdir / "contract.yaml"
            contract_path.write_text(_CONTRACT_V1)
            data_path = tmpdir / "data.csv"
            pd.DataFrame({"order_id": ["A1"], "amount": [1.0], "currency": ["USD"]}).to_csv(
                data_path, index=False
            )

            result = runner.invoke(
                main, ["validate", str(contract_path), str(data_path), "--engine", "spark"]
            )
            assert result.exit_code == 2

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
            df = pd.DataFrame(
                {
                    "id": [1, 2, 3],
                    "name": ["a", "b", "c"],
                    "value": [1.5, 2.5, 3.5],
                }
            )
            df.to_csv(data_path, index=False)

            output_path = tmpdir / "inferred.yaml"
            result = runner.invoke(main, ["infer", str(data_path), str(output_path)])
            assert result.exit_code == 0
            assert output_path.exists()

            content = output_path.read_text()
            assert content.startswith("# inferred by `dq infer` from")
            assert "# review before committing" in content
            assert (
                "  id:\n"
                "    dtype: integer\n"
                "    not_null: true\n"
                "    min: 1\n"
                "    max: 3\n"
                "    unique: true\n"
            ) in content
            assert result.output == (f"Wrote {output_path} (3 columns, inferred from 3 rows)\n")

    def test_infer_command_options(self) -> None:
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            data_path = tmpdir / "data.csv"
            pd.DataFrame(
                {
                    "category": ["a", "b", "c"],
                    "value": [1, 2, 100],
                }
            ).to_csv(data_path, index=False)
            output_path = tmpdir / "inferred.yaml"

            result = runner.invoke(
                main,
                [
                    "infer",
                    str(data_path),
                    str(output_path),
                    "--sample",
                    "2",
                    "--no-ranges",
                    "--max-allowed-cardinality",
                    "1",
                ],
            )

            assert result.exit_code == 0
            content = output_path.read_text()
            assert "min:" not in content
            assert "max:" not in content
            assert "allowed:" not in content
            assert "inferred from 2 rows" in result.output

    def test_diff_no_changes_exits_zero(self) -> None:
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "c.yaml"
            path.write_text(_CONTRACT_V1)

            result = runner.invoke(main, ["diff", str(path), str(path)])
            assert result.exit_code == 0
            assert "no changes" in result.output

    def test_diff_breaking_changes_exit_one(self) -> None:
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            old = tmpdir / "v1.yaml"
            new = tmpdir / "v2.yaml"
            old.write_text(_CONTRACT_V1)
            new.write_text(_CONTRACT_V2_BREAKING)

            result = runner.invoke(main, ["diff", str(old), str(new)])
            assert result.exit_code == 1
            assert "BREAKING" in result.output
            assert "stricter lower bound" in result.output

    def test_diff_canonical_example_output_and_classification(self) -> None:
        example = Path(__file__).parents[1] / "examples" / "contract-diff"

        result = CliRunner().invoke(
            main,
            ["diff", str(example / "orders-v1.yaml"), str(example / "orders-v2.yaml")],
        )

        assert result.exit_code == 1
        assert (
            result.output
            == """orders: 3 changes (1 breaking)

  BREAKING
    ~ column "amount" min: 0 -> 1  (stricter lower bound)

  non-breaking
    ~ column "currency" allowed: +[GBP]  (widened allowed set)
    + column "discount" (float)          (new nullable column)
"""
        )

    def test_diff_allow_breaking_forces_exit_zero(self) -> None:
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            old = tmpdir / "v1.yaml"
            new = tmpdir / "v2.yaml"
            old.write_text(_CONTRACT_V1)
            new.write_text(_CONTRACT_V2_BREAKING)

            result = runner.invoke(main, ["diff", str(old), str(new), "--allow-breaking"])
            assert result.exit_code == 0
            assert "BREAKING" in result.output

    def test_diff_json_output(self) -> None:
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            old = tmpdir / "v1.yaml"
            new = tmpdir / "v2.yaml"
            old.write_text(_CONTRACT_V1)
            new.write_text(_CONTRACT_V2_BREAKING)

            result = runner.invoke(main, ["diff", str(old), str(new), "-o", "json"])
            assert result.exit_code == 1
            payload = json.loads(result.output)
            assert payload["has_breaking"] is True
            assert payload["summary"]["breaking"] >= 1

    def test_diff_missing_file_exits_two(self) -> None:
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "c.yaml"
            path.write_text(_CONTRACT_V1)

            result = runner.invoke(main, ["diff", str(path), str(Path(tmpdir) / "missing.yaml")])
            assert result.exit_code == 2

    def test_infer_command_strict_rejects_malformed_csv(self) -> None:
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            data_path = tmpdir / "malformed.csv"
            data_path.write_text('id,name\n1,"unterminated\n')
            output_path = tmpdir / "inferred.yaml"

            result = runner.invoke(
                main,
                ["infer", str(data_path), str(output_path), "--strict"],
            )

            assert result.exit_code != 0
            assert "Could not read" in result.output
            assert not output_path.exists()


_BROKEN_CONTRACT = """
schema_version: "1.0"
name: orders
columns:
  amount:
    type: float
    min: 100
    max: 1
    bogus: true
rules:
  - "import os"
"""


class TestLint:
    """Tests for `dq lint`."""

    def _runner(self) -> CliRunner:
        return CliRunner()

    def test_clean_contract_exits_zero(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "c.yaml"
            path.write_text(_CONTRACT_V1)
            result = self._runner().invoke(main, ["lint", str(path)])
            assert result.exit_code == 0
            assert "OK" in result.output or "warning" in result.output

    def test_broken_contract_exits_one_with_paths(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "c.yaml"
            path.write_text(_BROKEN_CONTRACT)
            result = self._runner().invoke(main, ["lint", str(path)])
            assert result.exit_code == 1
            assert "min-greater-than-max" in result.output
            assert "unknown-field" in result.output
            assert "invalid-rule" in result.output
            assert "columns.amount.min" in result.output
            assert "Traceback" not in result.output

    def test_json_output(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "c.yaml"
            path.write_text(_BROKEN_CONTRACT)
            result = self._runner().invoke(main, ["lint", str(path), "--output", "json"])
            assert result.exit_code == 1
            payload = json.loads(result.output)
            assert payload["ok"] is False
            assert payload["error_count"] >= 3
            assert {d["code"] for d in payload["diagnostics"]} >= {"min-greater-than-max"}

    def test_strict_fails_on_warnings(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "c.yaml"
            path.write_text("name: orders\ncolumns:\n  a: {dtype: string}\n")  # no schema_version
            ok = self._runner().invoke(main, ["lint", str(path)])
            strict = self._runner().invoke(main, ["lint", str(path), "--strict"])
            assert ok.exit_code == 0
            assert strict.exit_code == 1

    def test_malformed_yaml_reports_cleanly(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "c.yaml"
            path.write_text("name: orders\ncolumns: {a: [1, 2\n")
            result = self._runner().invoke(main, ["lint", str(path)])
            assert result.exit_code == 1
            assert "invalid-yaml" in result.output
            assert "Traceback" not in result.output


class TestValidateContractErrors:
    """`dq validate` turns contract-load failures into clean messages."""

    def test_broken_contract_is_a_clean_error(self) -> None:
        with TemporaryDirectory() as tmp:
            contract = Path(tmp) / "c.yaml"
            contract.write_text(_BROKEN_CONTRACT)
            data = Path(tmp) / "d.csv"
            pd.DataFrame({"amount": [1.0]}).to_csv(data, index=False)
            result = CliRunner().invoke(main, ["validate", str(contract), str(data)])
            assert result.exit_code != 0
            assert "Traceback" not in result.output
            assert "dq lint" in result.output

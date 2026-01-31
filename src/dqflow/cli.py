"""Command-line interface for dqflow."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
import pandas as pd

from dqflow import __version__
from dqflow.contract import Contract


@click.group()
@click.version_option(version=__version__, prog_name="dqflow")
def main() -> None:
    """dqflow - Contract-first data quality for modern pipelines."""
    pass


@main.command()
@click.argument("contract", type=click.Path(exists=True, path_type=Path))
@click.argument("data", type=click.Path(exists=True, path_type=Path))
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.option("--fail-fast", is_flag=True, help="Exit with error code on validation failure")
def validate(contract: Path, data: Path, output: str, fail_fast: bool) -> None:
    """Validate DATA against CONTRACT.

    CONTRACT: Path to contract YAML file
    DATA: Path to data file (parquet, csv, json)
    """
    # Load contract
    c = Contract.from_yaml(contract)

    # Load data based on extension
    df = _load_dataframe(data)

    # Validate
    result = c.validate(df)

    # Output results
    if output == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        click.echo(result.summary())

    if fail_fast and not result.ok:
        sys.exit(1)


@main.command()
@click.argument("contract", type=click.Path(exists=True, path_type=Path))
def show(contract: Path) -> None:
    """Show details of a CONTRACT."""
    c = Contract.from_yaml(contract)

    click.echo(f"Contract: {c.name}")
    if c.description:
        click.echo(f"Description: {c.description}")
    click.echo()

    click.echo("Columns:")
    for col_name, col_def in c.columns.items():
        constraints = []
        if col_def.not_null:
            constraints.append("NOT NULL")
        if col_def.min is not None:
            constraints.append(f"min={col_def.min}")
        if col_def.max is not None:
            constraints.append(f"max={col_def.max}")
        if col_def.allowed:
            constraints.append(f"allowed={col_def.allowed}")
        if col_def.freshness_minutes:
            constraints.append(f"freshness={col_def.freshness_minutes}m")

        constraint_str = f" ({', '.join(constraints)})" if constraints else ""
        click.echo(f"  {col_name}: {col_def.dtype}{constraint_str}")

    if c.rules:
        click.echo()
        click.echo("Rules:")
        for rule in c.rules:
            click.echo(f"  - {rule}")


@main.command()
@click.argument("data", type=click.Path(exists=True, path_type=Path))
@click.argument("output", type=click.Path(path_type=Path))
def infer(data: Path, output: Path) -> None:
    """Infer a contract from DATA and write to OUTPUT."""
    df = _load_dataframe(data)

    from dqflow.column import Column

    columns = {}
    for col in df.columns:
        dtype = df[col].dtype
        if pd.api.types.is_integer_dtype(dtype):
            columns[col] = Column(dtype=int)
        elif pd.api.types.is_float_dtype(dtype):
            columns[col] = Column(dtype=float)
        elif pd.api.types.is_bool_dtype(dtype):
            columns[col] = Column(dtype=bool)
        elif pd.api.types.is_datetime64_any_dtype(dtype):
            columns[col] = Column(dtype="timestamp")
        else:
            columns[col] = Column(dtype=str)

    contract = Contract(name=output.stem, columns=columns)
    contract.to_yaml(output)
    click.echo(f"Contract written to {output}")


def _load_dataframe(path: Path) -> pd.DataFrame:
    """Load DataFrame from file based on extension."""
    suffix = path.suffix.lower()
    if suffix == ".parquet":
        return pd.read_parquet(path)
    elif suffix == ".csv":
        return pd.read_csv(path)
    elif suffix == ".json":
        return pd.read_json(path)
    else:
        raise click.ClickException(f"Unsupported file format: {suffix}")


if __name__ == "__main__":
    main()

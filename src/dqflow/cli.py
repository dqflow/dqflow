"""Command-line interface for dqflow."""

# mypy: disable-error-code=untyped-decorator

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
import pandas as pd

from dqflow import __version__
from dqflow.contract import Contract
from dqflow.inference import infer_contract, inference_header


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
        if col_def.unique:
            constraints.append("UNIQUE")
        if col_def.pattern:
            constraints.append(f"pattern={col_def.pattern!r}")

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
@click.option(
    "--sample",
    type=click.IntRange(min=1),
    help="Infer from at most N rows.",
)
@click.option("--no-ranges", is_flag=True, help="Do not infer min/max constraints.")
@click.option(
    "--max-allowed-cardinality",
    type=click.IntRange(min=0),
    default=20,
    show_default=True,
    help="Maximum distinct values for an allowed constraint.",
)
@click.option("--strict", is_flag=True, help="Fail instead of skipping malformed input rows.")
def infer(
    data: Path,
    output: Path,
    sample: int | None,
    no_ranges: bool,
    max_allowed_cardinality: int,
    strict: bool,
) -> None:
    """Infer a contract from DATA and write to OUTPUT."""
    try:
        df = _load_dataframe(data, sample=sample, strict=strict)
    except (OSError, ValueError, pd.errors.ParserError) as exc:
        raise click.ClickException(f"Could not read {data}: {exc}") from exc

    contract = infer_contract(
        df,
        name=output.stem,
        infer_ranges=not no_ranges,
        max_allowed_cardinality=max_allowed_cardinality,
    )
    header = inference_header(str(data), len(df))
    contract.to_yaml(output, header=header)
    click.echo(f"Wrote {output} ({len(contract.columns)} columns, inferred from {len(df):,} rows)")


def _load_dataframe(
    path: Path,
    *,
    sample: int | None = None,
    strict: bool = True,
) -> pd.DataFrame:
    """Load DataFrame from file based on extension."""
    suffix = path.suffix.lower()
    if suffix == ".parquet":
        df = pd.read_parquet(path)
    elif suffix == ".csv":
        return pd.read_csv(
            path,
            nrows=sample,
            on_bad_lines="error" if strict else "skip",
        )
    elif suffix == ".json":
        df = pd.read_json(path)
    else:
        raise click.ClickException(f"Unsupported file format: {suffix}")
    return df.head(sample) if sample is not None else df


if __name__ == "__main__":
    main()

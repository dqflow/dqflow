"""Validate a Polars LazyFrame with the experimental engine."""

from pathlib import Path

import polars as pl

from dqflow import Contract
from dqflow.engines.polars import PolarsEngine

HERE = Path(__file__).parent


def main() -> None:
    events = pl.scan_csv(HERE / "data" / "events.csv")
    contract = Contract.from_yaml(HERE / "contract.yaml")
    result = contract.validate(events, engine=PolarsEngine())

    if not result.ok:
        raise RuntimeError(result.summary())

    print(result.summary())
    print("validated 3 Polars rows")


if __name__ == "__main__":
    main()

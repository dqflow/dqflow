"""Infer a draft, refine observed constraints, and validate the source."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from dqflow import Contract, infer_contract

HERE = Path(__file__).parent


def main() -> None:
    customers = pd.read_csv(HERE / "data" / "customers.csv")
    draft = infer_contract(customers, name="customers")

    # Replace observed numeric bounds with business-approved bounds.
    draft.columns["credit_limit"].min = 0
    draft.columns["credit_limit"].max = 10_000

    with TemporaryDirectory() as tmpdir:
        draft_path = Path(tmpdir) / "customers.yaml"
        draft.to_yaml(draft_path)
        refined = Contract.from_yaml(draft_path)

    result = refined.validate(customers)
    if not result.ok:
        raise RuntimeError(result.summary())

    curated = Contract.from_yaml(HERE / "contract.yaml")
    assert curated.validate(customers).ok
    print(result.summary())
    print("reviewed the inferred draft and validated the curated contract")


if __name__ == "__main__":
    main()

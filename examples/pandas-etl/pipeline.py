"""Validate transformed orders before a simulated publish step."""

from pathlib import Path

import pandas as pd

from dqflow import Contract

HERE = Path(__file__).parent


def main() -> None:
    orders = pd.read_csv(HERE / "data" / "orders.csv")
    contract = Contract.from_yaml(HERE / "contract.yaml")
    result = contract.validate(orders)

    if not result.ok:
        raise RuntimeError(result.summary())

    print(result.summary())
    print(f"published {len(orders)} valid orders")


if __name__ == "__main__":
    main()

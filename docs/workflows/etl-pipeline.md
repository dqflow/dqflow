# Validate in an ETL pipeline

Validate immediately after loading or transforming data and before writing to a
downstream destination.

```python
import pandas as pd
from dqflow import Contract


def load_orders() -> pd.DataFrame:
    return pd.read_csv("data/orders.csv")


def publish_orders(df: pd.DataFrame) -> None:
    df.to_parquet("output/orders.parquet")


def run() -> None:
    contract = Contract.from_yaml("contracts/orders.yaml")
    orders = load_orders()
    result = contract.validate(orders)

    if not result.ok:
        # Log the structured form before failing the task.
        print(result.to_dict())
        raise RuntimeError(result.summary())

    publish_orders(orders)
```

This pattern works in a plain script and in task functions for Airflow, Dagster,
or Prefect: raising an exception makes the orchestrator task fail. Do not catch
and discard that exception unless the pipeline has an explicit quarantine path.

A complete runnable version is in
[`examples/pandas-etl`](https://github.com/dqflow/dqflow/tree/main/examples/pandas-etl).

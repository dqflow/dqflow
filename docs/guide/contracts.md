# Defining contracts

A `Contract` defines required columns and quality checks for one dataset.

```python
from dqflow import Column, Contract

contract = Contract(
    name="orders",
    description="Orders emitted by checkout",
    columns={
        "order_id": Column(str, not_null=True, unique=True),
        "amount": Column(float, min=0),
    },
    rules=[
        "row_count > 0",
        "null_rate('amount') < 0.01",
    ],
    metadata={"owner": "data-platform"},
)
```

`dtype` is part of the declaration but is not checked yet. The current engines
enforce column existence and the constraints listed in
[Column validations](columns.md).

## Validate data

```python
import pandas as pd

df = pd.read_csv("orders.csv")
result = contract.validate(df)

if not result.ok:
    raise ValueError(result.summary())
```

The returned `ValidationResult` provides:

- `ok`: whether every check passed;
- `checks`: all `CheckResult` objects;
- `failed_checks`: only failed checks;
- `summary()`: human-readable text;
- `to_dict()`: JSON-serializable output.

## YAML contracts

```python
from dqflow import Contract

contract = Contract.from_yaml("contracts/orders.yaml")
contract.to_yaml("contracts/orders-copy.yaml")
```

Use YAML for reviewable declarative contracts and Python when you need callable
cross-column rules. See [YAML contracts](yaml.md).

When a YAML contract changes, compare the base and proposed versions with
[`dq diff`](diff.md). It classifies changes from a producer's perspective and
returns a non-zero exit code for breaking changes, making contracts safe to
review and gate in CI.

## Select an engine

Pandas is the default. Polars is explicit:

```python
from dqflow.engines.polars import PolarsEngine

result = contract.validate(polars_df, engine=PolarsEngine())
```

See [Choosing an engine](engines.md) for installation and current limitations.

# Defining Contracts

A **Contract** defines the expected shape and quality of your data.

## Basic Contract

```python
from dqflow import Contract, Column

contract = Contract(
    name="orders",
    columns={
        "order_id": Column(str, not_null=True),
        "amount": Column(float, min=0),
    },
)
```

## Contract with Rules

Add table-level rules:

```python
contract = Contract(
    name="orders",
    columns={
        "order_id": Column(str, not_null=True),
        "amount": Column(float, min=0),
    },
    rules=[
        "row_count > 0",
        "null_rate(amount) < 0.01",
    ],
)
```

## Contract with Metadata

```python
contract = Contract(
    name="orders",
    description="E-commerce order data",
    columns={...},
    rules=[...],
    metadata={
        "owner": "data-team",
        "source": "shopify",
    },
)
```

## Validating Data

```python
import pandas as pd

df = pd.read_parquet("orders.parquet")
result = contract.validate(df)

if not result.ok:
    print(result.summary())
    raise Exception("Data quality check failed")
```

## Accessing Results

```python
# Boolean check
result.ok  # True if all checks passed

# Summary string
result.summary()

# List of failed checks
result.failed_checks

# JSON-serializable dict
result.to_dict()
```

## Loading from YAML

```python
contract = Contract.from_yaml("contracts/orders.yaml")
```

See [YAML Contracts](yaml.md) for more details.

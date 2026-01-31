# Contract

The `Contract` class defines data quality expectations for a dataset.

## Class Definition

```python
from dqflow import Contract

contract = Contract(
    name: str,
    columns: dict[str, Column] = {},
    rules: list[str] = [],
    description: str = "",
    metadata: dict[str, Any] = {},
)
```

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Contract name (required) |
| `columns` | `dict[str, Column]` | Column definitions |
| `rules` | `list[str]` | Table-level validation rules |
| `description` | `str` | Human-readable description |
| `metadata` | `dict[str, Any]` | Custom metadata |

## Methods

### validate

Validate a DataFrame against this contract.

```python
result = contract.validate(df: pd.DataFrame) -> ValidationResult
```

**Returns:** [ValidationResult](result.md)

**Example:**

```python
import pandas as pd
from dqflow import Contract, Column

df = pd.DataFrame({"id": [1, 2, 3]})
contract = Contract(name="test", columns={"id": Column(int)})

result = contract.validate(df)
print(result.ok)  # True
```

### from_yaml

Load a contract from a YAML file.

```python
contract = Contract.from_yaml(path: str | Path) -> Contract
```

**Example:**

```python
contract = Contract.from_yaml("contracts/orders.yaml")
```

### to_yaml

Save a contract to a YAML file.

```python
contract.to_yaml(path: str | Path) -> None
```

**Example:**

```python
contract.to_yaml("contracts/orders.yaml")
```

## Example

```python
from dqflow import Contract, Column

contract = Contract(
    name="orders",
    description="E-commerce order data",
    columns={
        "order_id": Column(str, not_null=True),
        "amount": Column(float, min=0, max=100000),
        "currency": Column(str, allowed=["USD", "EUR"]),
    },
    rules=[
        "row_count > 0",
        "null_rate(amount) < 0.01",
    ],
    metadata={
        "owner": "data-team",
        "version": "1.0",
    },
)

# Validate
result = contract.validate(df)

# Save to YAML
contract.to_yaml("contracts/orders.yaml")
```

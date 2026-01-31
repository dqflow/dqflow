# YAML Contracts

Define contracts in YAML for version control and easy editing.

## Basic YAML Contract

```yaml
# contracts/orders.yaml
name: orders
description: E-commerce order data contract

columns:
  order_id:
    type: string
    not_null: true

  amount:
    type: float
    min: 0
    max: 100000

  currency:
    type: string
    allowed: ["USD", "EUR", "GBP"]

rules:
  - row_count > 0
  - "null_rate(amount) < 0.01"
```

## Loading YAML Contracts

```python
from dqflow import Contract

contract = Contract.from_yaml("contracts/orders.yaml")
result = contract.validate(df)
```

## Column Types in YAML

| YAML Type | Python Equivalent |
|-----------|-------------------|
| `string` | `str` |
| `integer` | `int` |
| `float` | `float` |
| `boolean` | `bool` |
| `timestamp` | `"timestamp"` |

## Full Example

```yaml
name: orders
description: E-commerce order data quality contract

columns:
  order_id:
    type: string
    not_null: true

  customer_id:
    type: string
    not_null: true

  amount:
    type: float
    min: 0
    max: 100000

  currency:
    type: string
    allowed: ["USD", "EUR", "GBP"]

  status:
    type: string
    allowed: ["pending", "processing", "shipped", "delivered", "cancelled"]

  created_at:
    type: timestamp
    freshness_minutes: 1440

rules:
  - row_count > 0
  - "null_rate(amount) < 0.01"
  - "null_rate(customer_id) < 0.001"
```

## Saving Contracts to YAML

```python
contract = Contract(
    name="orders",
    columns={...},
    rules=[...],
)

contract.to_yaml("contracts/orders.yaml")
```

## Organizing Contracts

Recommended folder structure:

```
project/
├── contracts/
│   ├── orders.yaml
│   ├── customers.yaml
│   └── products.yaml
├── data/
└── pipelines/
```

## Using with CLI

```bash
dq validate contracts/orders.yaml data/orders.parquet
dq show contracts/orders.yaml
```

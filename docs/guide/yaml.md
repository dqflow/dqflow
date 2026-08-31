# YAML contracts

YAML contracts are declarative files suited to code review and version control.

```yaml
name: orders
description: Orders emitted by checkout

columns:
  order_id:
    dtype: string
    not_null: true
    unique: true
    pattern: "^A[0-9]{3}$"
  amount:
    dtype: float
    min: 0
  currency:
    dtype: string
    allowed: [USD, EUR]

rules:
  - row_count > 0
  - "null_rate('amount') < 0.01"

cross_column_rules:
  - name: shipped_after_created
    left: shipped_at
    op: ">="
    right: created_at
    error_message: shipped_at must not precede created_at
```

Both `dtype` and the legacy key `type` are accepted when reading YAML. `to_yaml()`
writes `dtype`. Declared dtype and freshness are not currently enforced.

## Load and save

```python
from dqflow import Contract

contract = Contract.from_yaml("contracts/orders.yaml")
result = contract.validate(df)
contract.to_yaml("contracts/orders-copy.yaml")
```

Callable cross-column rules and `custom` callables cannot be represented in YAML.
Use a Python contract for those cases.

## Validate with the CLI

```bash
dq show contracts/orders.yaml
dq validate contracts/orders.yaml data/orders.csv --fail-fast
```

See [CLI usage](cli.md) for exit-code and file-format details.

# Quick Start

This guide will help you validate your first DataFrame in under 5 minutes.

!!! note
    `dtype`, `freshness_minutes`, and `custom` are declarative fields that are not
    enforced yet. Column existence, `not_null`, `min`, `max`, `allowed`, `unique`,
    and regex `pattern` constraints are enforced.

## Basic Example

```python
import pandas as pd
from dqflow import Contract, Column

# Sample data with quality issues
df = pd.DataFrame({
    "order_id": ["A001", None, "A003"],      # Has null value
    "amount": [100.0, -50.0, 75.0],          # Has negative value
    "currency": ["USD", "GBP", "EUR"],       # GBP not in allowed list
})

# Define your data contract
contract = Contract(
    name="orders",
    columns={
        "order_id": Column(str, not_null=True),
        "amount": Column(float, min=0),
        "currency": Column(str, allowed=["USD", "EUR"]),
    },
    rules=["row_count > 0"],
)

# Validate
result = contract.validate(df)

# Check results
print(result.summary())
```

**Output:**

```
Contract 'orders': 4/7 checks passed
Failed checks:
  - not_null:order_id: Column 'order_id' has 1 null value
  - min:amount: Column 'amount' has 1 value below the minimum 0
  - allowed:currency: Column 'currency' has 1 value outside the allowed set
```

## Use in Pipelines

```python
if not result.ok:
    raise Exception(result.summary())  # Fail fast!
```

## JSON Output

For logging and monitoring:

```python
import json
print(json.dumps(result.to_dict(), indent=2))
```

## Next Steps

- [Column Validations](../guide/columns.md) - Learn all column checks
- [Table Rules](../guide/rules.md) - Add table-level validations
- [YAML Contracts](../guide/yaml.md) - Define contracts in YAML
- [CLI Usage](../guide/cli.md) - Use the command-line interface

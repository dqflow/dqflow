# Table Rules

Table rules validate properties across the entire dataset.

## Basic Rules

```python
from dqflow import Contract

contract = Contract(
    name="orders",
    columns={...},
    rules=[
        "row_count > 0",
        "row_count > 1000",
    ],
)
```

## Available Functions

### row_count

Total number of rows:

```python
"row_count > 0"
"row_count >= 1000"
"row_count < 1000000"
```

### null_rate

Proportion of null values (0.0 to 1.0):

```python
"null_rate(amount) < 0.01"      # Less than 1% nulls
"null_rate(email) == 0"         # No nulls allowed
"null_rate(phone) < 0.5"        # Less than 50% nulls
```

### unique_count

Number of distinct values:

```python
"unique_count(customer_id) > 100"
"unique_count(status) <= 5"
```

### duplicate_rate

Proportion of duplicate values (0.0 to 1.0):

```python
"duplicate_rate(order_id) == 0"    # All unique
"duplicate_rate(email) < 0.1"      # Less than 10% duplicates
```

## Rule Syntax

Rules are Python expressions evaluated against the DataFrame:

```python
# Comparison operators
"row_count > 0"
"row_count >= 100"
"row_count < 1000"
"row_count <= 500"
"row_count == 100"

# Combining conditions
"row_count > 0 and row_count < 1000"
```

## Example Contract

```python
contract = Contract(
    name="orders",
    columns={
        "order_id": Column(str, not_null=True),
        "amount": Column(float, min=0),
    },
    rules=[
        "row_count > 0",
        "row_count < 10000000",
        "null_rate(amount) < 0.01",
        "duplicate_rate(order_id) == 0",
        "unique_count(order_id) == row_count",
    ],
)
```

## Custom Expressions

Rules support basic Python expressions:

```python
"row_count > 100 and null_rate(amount) < 0.05"
"unique_count(status) <= 10"
```

!!! note
    Rules are evaluated in a sandboxed environment with limited functions for security.

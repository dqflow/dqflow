# Column Validations

Column definitions specify expected data types and constraints.

## Basic Column

```python
from dqflow import Column

# Just type
Column(str)

# Type with constraints
Column(str, not_null=True)
```

## Available Constraints

### not_null

Ensure no null/NaN values:

```python
Column(str, not_null=True)
```

### min / max

Numeric bounds:

```python
Column(float, min=0)
Column(float, max=100)
Column(float, min=0, max=100)
```

### allowed

Restrict to specific values:

```python
Column(str, allowed=["USD", "EUR", "GBP"])
Column(int, allowed=[1, 2, 3])
```

### freshness_minutes

Ensure timestamp data is recent:

```python
Column("timestamp", freshness_minutes=60)      # Within last hour
Column("timestamp", freshness_minutes=1440)    # Within last 24 hours
```

## Supported Types

| Python Type | Description |
|-------------|-------------|
| `str` | String/text |
| `int` | Integer |
| `float` | Floating point |
| `bool` | Boolean |
| `"timestamp"` | Datetime |

## Full Example

```python
from dqflow import Contract, Column

contract = Contract(
    name="orders",
    columns={
        "order_id": Column(str, not_null=True),
        "customer_id": Column(str, not_null=True),
        "amount": Column(float, min=0, max=100000),
        "currency": Column(str, allowed=["USD", "EUR", "GBP"]),
        "status": Column(str, allowed=["pending", "shipped", "delivered"]),
        "created_at": Column("timestamp", freshness_minutes=1440),
    },
)
```

## Column Metadata

Add descriptions and custom metadata:

```python
Column(
    dtype=str,
    not_null=True,
    description="Unique order identifier",
    metadata={"pii": False},
)
```

# Column

The `Column` class defines expectations for a single column.

## Class Definition

```python
from dqflow import Column

column = Column(
    dtype: type | str,
    not_null: bool = False,
    min: float | None = None,
    max: float | None = None,
    allowed: Sequence[Any] | None = None,
    freshness_minutes: int | None = None,
    description: str = "",
    metadata: dict[str, Any] = {},
)
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dtype` | `type \| str` | required | Expected data type |
| `not_null` | `bool` | `False` | Reject null values |
| `min` | `float \| None` | `None` | Minimum value (numeric) |
| `max` | `float \| None` | `None` | Maximum value (numeric) |
| `allowed` | `Sequence[Any] \| None` | `None` | Allowed values |
| `freshness_minutes` | `int \| None` | `None` | Max age for timestamps |
| `description` | `str` | `""` | Human-readable description |
| `metadata` | `dict[str, Any]` | `{}` | Custom metadata |

## Supported Types

| Type | Description |
|------|-------------|
| `str` | String/text |
| `int` | Integer |
| `float` | Floating point |
| `bool` | Boolean |
| `"timestamp"` | Datetime |

## Examples

### Basic Column

```python
Column(str)
Column(int)
Column(float)
```

### Not Null

```python
Column(str, not_null=True)
```

### Numeric Bounds

```python
Column(float, min=0)
Column(float, max=100)
Column(float, min=0, max=100)
```

### Allowed Values

```python
Column(str, allowed=["USD", "EUR", "GBP"])
Column(int, allowed=[1, 2, 3, 4, 5])
```

### Freshness Check

```python
Column("timestamp", freshness_minutes=60)      # Within 1 hour
Column("timestamp", freshness_minutes=1440)    # Within 24 hours
```

### With Metadata

```python
Column(
    dtype=str,
    not_null=True,
    description="Unique customer identifier",
    metadata={"pii": True, "source": "crm"},
)
```

### Full Example

```python
from dqflow import Column

columns = {
    "order_id": Column(str, not_null=True),
    "customer_id": Column(str, not_null=True),
    "amount": Column(float, min=0, max=100000),
    "currency": Column(str, allowed=["USD", "EUR", "GBP"]),
    "status": Column(str, allowed=["pending", "shipped", "delivered"]),
    "created_at": Column("timestamp", freshness_minutes=1440),
}
```

## Validation Behavior

| Constraint | Check |
|------------|-------|
| `not_null=True` | Fails if any null/NaN values |
| `min=X` | Fails if any value < X |
| `max=X` | Fails if any value > X |
| `allowed=[...]` | Fails if any value not in list |
| `freshness_minutes=X` | Fails if max timestamp > X minutes old |

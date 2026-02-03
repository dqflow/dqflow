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

### custom

Apply custom validation logic:

```python
def is_email(value: str) -> bool:
    return "@" in str(value) and "." in str(value)

Column(str, custom=is_email)
```

Use lambda for simple checks:

```python
Column(int, custom=lambda x: x > 0)  # Positive only
Column(int, custom=lambda x: x % 2 == 0)  # Even numbers
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

## Custom Validation Examples

### Email Validation

```python
import re

def is_valid_email(value: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, str(value)))

Column(str, custom=is_valid_email)
```

### Phone Number Validation

```python
def is_valid_phone(value: str) -> bool:
    import re
    return bool(re.match(r'^\+?1?\d{9,15}$', str(value)))

Column(str, custom=is_valid_phone)
```

### Business Rules

```python
# Must be divisible by 5
Column(int, custom=lambda x: x % 5 == 0)

# Must be in valid age range
Column(int, custom=lambda x: 0 <= x <= 120)

# Must be a percentage (0-100)
Column(float, custom=lambda x: 0 <= x <= 100)
```

### Combining with Other Constraints

You can combine custom checks with built-in constraints:

```python
Column(
    dtype=float,
    not_null=True,
    min=0,
    max=100,
    custom=lambda x: x % 5 == 0,  # Scores in increments of 5
    description="Test score (0-100, increments of 5)"
)
```

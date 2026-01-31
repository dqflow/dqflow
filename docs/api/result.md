# ValidationResult

The `ValidationResult` class contains the outcome of contract validation.

## Class Definition

```python
from dqflow import ValidationResult

result = ValidationResult(
    contract_name: str,
    checks: list[CheckResult] = [],
)
```

## Properties

| Property | Type | Description |
|----------|------|-------------|
| `contract_name` | `str` | Name of the validated contract |
| `checks` | `list[CheckResult]` | All check results |
| `ok` | `bool` | `True` if all checks passed |
| `failed_checks` | `list[CheckResult]` | Only failed checks |

## Methods

### summary

Get a human-readable summary.

```python
result.summary() -> str
```

**Example:**

```python
print(result.summary())
```

**Output:**

```
Contract 'orders': 5/7 checks passed
Failed checks:
  - not_null:order_id: Found 1 null values
  - min:amount: Minimum value -50.0 is below 0
```

### to_dict

Get a JSON-serializable dictionary.

```python
result.to_dict() -> dict[str, Any]
```

**Example:**

```python
import json
print(json.dumps(result.to_dict(), indent=2))
```

**Output:**

```json
{
  "contract_name": "orders",
  "ok": false,
  "total_checks": 7,
  "passed": 5,
  "failed": 2,
  "checks": [
    {
      "name": "column_exists:order_id",
      "passed": true,
      "message": "",
      "details": {}
    },
    {
      "name": "not_null:order_id",
      "passed": false,
      "message": "Found 1 null values",
      "details": {"null_count": 1}
    }
  ]
}
```

## CheckResult

Individual check results.

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Check identifier |
| `passed` | `bool` | Whether check passed |
| `message` | `str` | Error message (if failed) |
| `details` | `dict` | Additional details |

## Usage Examples

### Basic Check

```python
result = contract.validate(df)

if result.ok:
    print("All checks passed!")
else:
    print(result.summary())
```

### Iterate Failed Checks

```python
for check in result.failed_checks:
    print(f"{check.name}: {check.message}")
```

### Pipeline Integration

```python
result = contract.validate(df)

if not result.ok:
    # Log details
    logger.error(result.summary())

    # Send to monitoring
    metrics.record(result.to_dict())

    # Fail the pipeline
    raise Exception(f"Data quality check failed: {result.summary()}")
```

### Access Check Details

```python
for check in result.checks:
    if not check.passed:
        print(f"Check: {check.name}")
        print(f"Message: {check.message}")
        print(f"Details: {check.details}")
```

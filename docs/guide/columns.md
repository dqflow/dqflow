# Column validations

Every entry in `Contract.columns` is required. The engine first emits a
`column_exists:<name>` check and then evaluates the configured constraints when
the column exists.

```python
from dqflow import Column

Column(str, not_null=True, unique=True, pattern=r"^[A-Z]\d{4}$")
Column(float, min=0, max=100_000)
Column(str, allowed=["USD", "EUR"])
```

## Enforced constraints

| Constraint | Behavior |
| --- | --- |
| `not_null=True` | Fails when any value is null/NaN |
| `min=value` | Requires the observed minimum to be at least `value` |
| `max=value` | Requires the observed maximum to be at most `value` |
| `allowed=[...]` | Rejects non-null values outside the sequence |
| `unique=True` | Rejects duplicated non-null values; nulls are ignored |
| `pattern=...` | Requires every non-null string to match the regex |

Combine `unique=True` with `not_null=True` when null values must also fail.

```python
from dqflow import Column, Contract

contract = Contract(
    name="orders",
    columns={
        "order_id": Column(str, not_null=True, unique=True, pattern=r"^A\d{3}$"),
        "amount": Column(float, min=0, max=100_000),
        "currency": Column(str, allowed=["USD", "EUR"]),
    },
)
```

## Declared but not enforced

`dtype`, `freshness_minutes`, and `custom` are currently descriptive fields.
They are retained on `Column`; dtype and freshness can be written to YAML and
displayed by the CLI, but neither validation engine checks them yet.

```python
Column("timestamp", freshness_minutes=60)  # declaration only today
Column(str, custom=lambda value: bool(value))  # declaration only today
```

For custom logic that runs today, use a callable
[`CrossColumnRule`](custom-checks.md). Track future enforcement in
[#51](https://github.com/dqflow/dqflow/issues/51).

## Metadata

Descriptions and metadata help document ownership or classification without
changing validation behavior:

```python
Column(
    dtype=str,
    not_null=True,
    description="Unique customer identifier",
    metadata={"pii": False, "owner": "checkout"},
)
```

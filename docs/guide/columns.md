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
| `dtype` | Requires a compatible logical integer, float, string, boolean, or timestamp dtype |
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

## Dtype compatibility

Both engines normalize native backend types to five logical names: `integer`,
`float`, `string`, `boolean`, and `timestamp`. Python declarations such as
`int`, `float`, `str`, and `bool` map to those names. Integer data also satisfies
a `float` declaration. Null values do not change the observed logical type, and
an all-null column is dtype-compatible; add `not_null=True` to reject it.

Dtype validation does not coerce values. A mismatch produces a `dtype:<name>`
check with `expected_dtype` and `actual_dtype` details.

## Declared but not enforced

`freshness_minutes` and `custom` remain descriptive fields. Freshness can be
written to YAML and displayed by the CLI, but neither validation engine checks
it yet; custom callables are retained only on Python `Column` objects.

```python
Column("timestamp", freshness_minutes=60)  # dtype runs; freshness does not
Column(str, custom=lambda value: bool(value))  # dtype runs; custom does not
```

For custom logic that runs today, use a callable
[`CrossColumnRule`](custom-checks.md).

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

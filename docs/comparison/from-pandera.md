# Migrating from Pandera

[Pandera](https://pandera.readthedocs.io/) validates a DataFrame against a schema
declared in Python. dqflow validates a DataFrame against a **contract** — one
declarative artifact, Python *or* YAML, that you also `dq diff` in review. If you
already run Pandera, most column-level checks port directly.

This guide covers the mapping, a side-by-side example, and the Pandera features
that have **no dqflow equivalent yet** — read that section before you commit to a
move.

## Concept map

| Pandera | dqflow | Notes |
| --- | --- | --- |
| `DataFrameSchema({...})` or `class S(pa.DataFrameModel)` | `Contract(name=..., columns={...})` | One object; serialise with `Contract.to_yaml()` / load with `Contract.from_yaml()` |
| `Column(dtype)` / `field: Series[dtype]` | `Column(dtype, ...)` | In dqflow the dtype is **descriptive today** — not coerced or enforced (see below) |
| `Column(nullable=False)` / `Field(nullable=False)` | `Column(not_null=True)` | Pandera columns are non-nullable by default; **dqflow columns are nullable by default** |
| `Field(unique=True)` | `Column(unique=True)` | |
| `Field(ge=0, le=100)` | `Column(min=0, max=100)` | dqflow bounds are inclusive |
| `Field(gt=0)` (strict) | `CrossColumnRule(name="amount_pos", left="amount", op=">", right=0)` | dqflow column `min`/`max` are inclusive only; a strict bound is a row-wise rule |
| `Field(isin=[...])` | `Column(allowed=[...])` | |
| `Field(str_matches=r"...")` | `Column(pattern=r"...")` | Applied to every non-null string value |
| `Field(coerce=True)` | *(none)* | dqflow never coerces types |
| `Check(lambda s: ...)` on a column | `CrossColumnRule(check=lambda df: ...)` | Callable rules receive the whole DataFrame and are Python-only (not serialisable) |
| `@pa.dataframe_check` comparing columns | `CrossColumnRule(left=, op=, right=)` | Structured form serialises to YAML |
| DataFrame-level count assertions | `rules=["row_count > 0", "null_rate('id') == 0", "unique_count('tier') <= 3"]` | The three names `row_count`, `null_rate('col')`, `unique_count('col')` |
| `schema.validate(df, lazy=True)` | `contract.validate(df)` | dqflow **always** evaluates every check |
| `except pa.errors.SchemaErrors as e: e.failure_cases` | `result.ok`, `result.failed_checks`, `result.summary()`, `result.to_dict()` | dqflow **never raises** on a validation failure — you decide what to do |
| `pandera.infer_schema(df)` | `dq infer data.csv contract.yaml` | Draft to review, not a guarantee |
| `schema.to_yaml()` / `schema.to_script()` | `Contract.to_yaml(path)` | |
| `@pa.check_types` on a function signature | *(none)* — call `contract.validate(df)` yourself at the boundary | |

## Side by side

Same dataset, same intent.

### Pandera

```python
import pandera.pandas as pa
from pandera.typing import Series


class Orders(pa.DataFrameModel):
    order_id: Series[str] = pa.Field(str_matches=r"^A\d{3}$", unique=True, nullable=False)
    amount: Series[float] = pa.Field(ge=0)
    currency: Series[str] = pa.Field(isin=["USD", "EUR", "GBP"])


Orders.validate(df, lazy=True)  # raises pa.errors.SchemaErrors on failure
```

### dqflow — Python

```python
from dqflow import Column, Contract

contract = Contract(
    name="orders",
    columns={
        "order_id": Column(str, not_null=True, unique=True, pattern=r"^A\d{3}$"),
        "amount": Column(float, min=0),
        "currency": Column(str, allowed=["USD", "EUR", "GBP"]),
    },
    rules=["row_count > 0"],
)

result = contract.validate(df)
if not result.ok:
    raise ValueError(result.summary())
```

### dqflow — YAML

```yaml
# contracts/orders.yaml
schema_version: "1.0"
name: orders

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
    allowed: [USD, EUR, GBP]

rules:
  - row_count > 0
```

```python
from dqflow import Contract

contract = Contract.from_yaml("contracts/orders.yaml")
result = contract.validate(df)
```

The YAML form is what unlocks `dq diff` — commit `contracts/orders.yaml`, and a
pull request that tightens it fails the check. See the
[first PR gate tutorial](../getting-started/first-pr-gate.md).

## What does not port yet

dqflow has **no equivalent** for these Pandera features:

- **Statistical / hypothesis checks** (`pa.Hypothesis`, `Check` with a
  distribution test).
- **Data synthesis** — Pandera can generate example data from a schema
  (`schema.example()`); dqflow cannot.
- **Type coercion and enforcement** — `Field(coerce=True)` and strict dtype
  checking. dqflow keeps `dtype` as documentation for now
  ([limitations](index.md#dqflows-current-limitations)).
- **Index / MultiIndex validation** — dqflow validates columns only.
- **Wide backend support** — Pandera runs on pandas, Polars, PySpark, Ibis, Dask,
  Modin, PyArrow and GeoPandas. dqflow runs on pandas, with an experimental
  Polars engine.
- **`@pa.check_types` decorators** — dqflow has no function-signature
  integration; validate explicitly at pipeline boundaries.

If those are load-bearing for you, staying on Pandera (or running both) is the
right call.

## Run both during migration

You do not have to switch in one step. Validate with Pandera as you do today, and
add a dqflow contract alongside it:

```python
pandera_ok = True
try:
    Orders.validate(df, lazy=True)
except pa.errors.SchemaErrors:
    pandera_ok = False

dq_result = contract.validate(df)

# Compare the two while you build confidence in the contract
assert pandera_ok == dq_result.ok, dq_result.summary()
```

Once the dqflow contract matches your Pandera schema on real data, drop the
Pandera schema and wire `dq diff` into CI.

## Next steps

- [First PR gate tutorial](../getting-started/first-pr-gate.md) — contract to a
  failing check in ~10 minutes
- [Defining contracts](../guide/contracts.md) and [Column validations](../guide/columns.md)
- [How dqflow compares](index.md) — the honest limitations list

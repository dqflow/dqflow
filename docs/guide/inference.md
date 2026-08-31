# Inferring Contracts

`dq infer` profiles a CSV, JSON, or Parquet file and writes a draft YAML
contract. The first two comment lines record the source, number of rows, and
inference time, and remind you to review the result before committing it.

```bash
dq infer data/orders.csv contracts/orders.yaml --sample 100000
```

The output preserves source column order and writes each constraint in a stable
order, so rerunning inference produces reviewable diffs.

## Heuristics

Inference uses only the rows it reads:

| Constraint | Inferred when |
|---|---|
| `dtype` | The pandas dtype maps to `boolean`, `integer`, `float`, `timestamp`, or `string` |
| `not_null` | No sampled value is null |
| `allowed` | A string or categorical column has at most 20 distinct non-null values by default |
| `min` / `max` | A non-empty numeric or datetime column has observed bounds |
| `unique` | All non-null sampled values are distinct |
| `pattern` | Every non-null string matches a supported email, UUID, or ISO `YYYY-MM-DD` format |

Nulls do not count as values for `allowed`, `unique`, or `pattern`. Bounds are
the exact observed bounds; inference does not add a margin. A contract inferred
from a sample describes that sample, not every value that future data may
contain.

## Tuning inference

```bash
dq infer DATA OUTPUT \
  --sample 100000 \
  --max-allowed-cardinality 10 \
  --no-ranges \
  --strict
```

- `--sample N` reads at most the first `N` rows. Omit it to read the full file.
- `--max-allowed-cardinality N` changes the `allowed` threshold. Use `0` to
  disable `allowed` inference.
- `--no-ranges` disables numeric and datetime `min` / `max` inference.
- `--strict` makes malformed CSV rows fail the command. Without it, malformed
  CSV rows are skipped; other read errors still fail.

Sampling can make identifier-like columns appear unique and can miss rare enum
values, nulls, outliers, or malformed formats. Review those constraints before
using the generated contract in CI.

## Python API

Inference is also available without the CLI:

```python
import pandas as pd
from dqflow import infer_contract

df = pd.read_csv("data/orders.csv")
contract = infer_contract(
    df,
    name="orders",
    infer_ranges=True,
    max_allowed_cardinality=20,
)
assert contract.validate(df).ok
contract.to_yaml("contracts/orders.yaml")
```

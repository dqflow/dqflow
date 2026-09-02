# CLI usage

The `dq` command validates files, inspects contracts, and infers draft contracts.

## Install file-format support

CSV and JSON work with the base installation. Parquet requires a pandas Parquet
backend:

```bash
pip install dqflow
pip install "dqflow[parquet]"  # adds pyarrow
```

## `dq validate`

```bash
dq validate CONTRACT DATA [--output text|json] [--engine pandas|polars]
             [--fail-fast] [--quiet | --verbose] [--color | --no-color]
```

Supported extensions are `.csv`, `.json`, and—after installing the extra—
`.parquet`.

```bash
dq validate contracts/orders.yaml data/orders.csv
dq validate contracts/orders.yaml data/orders.csv --output json
dq validate contracts/orders.yaml data/orders.parquet --fail-fast
```

`--engine` selects the validation engine (default `pandas`). `--engine polars`
reads the data file with Polars' native readers and runs the Polars engine, which
needs `pip install "dqflow[polars]"`. Both engines produce the same result shape.

Without `--fail-fast`, a completed validation command exits `0` even when checks
fail; inspect the text or JSON result. With `--fail-fast`, the command still
evaluates and prints **all** checks, then exits `1` when the result is not OK. The
option does not short-circuit at the first failure.

### Text output

The default renderer groups checks into **schema**, **columns**, **table rules**,
and **cross-column rules**, shows per-group pass/fail counts, and appends a
failure rate and a bounded sample of offending values to each failing check.

```console
$ dq validate contracts/orders.yaml data/orders.csv
orders · 5 of 8 checks failed on 4 rows

  Schema  3/3 passed

  Columns  4/4 failed
    order_id  ✘ not_null  has 1 null value (25.0%)
              ✘ unique    has 2 non-unique values (50.0%)  ·  e.g. 'A001'
    amount    ✘ min       has 1 value below the minimum 0 (25.0%)
    currency  ✘ allowed   has 1 value outside the allowed set (25.0%)  ·  e.g. 'GBP'

  Table rules  1/1 failed
    ✘ null_rate('order_id') == 0

  3 passed · 5 failed
```

- `-q` / `--quiet` prints only failing checks (plus the summary line).
- `-v` / `--verbose` prints every check, passing ones included.
- Colour is used on a TTY and suppressed when the output is piped or when the
  `NO_COLOR` environment variable is set. `--color` / `--no-color` overrides the
  detection.

`--output json` is unaffected by these flags. Its schema is unchanged; failing
checks now carry extra `details` keys (`null_rate`, `violating_rows`,
`violating_rate`, `sample_invalid_values`, `sample_duplicate_values`,
`failing_rate`).

## `dq diff`

```bash
dq diff OLD NEW [--output text|json] [--allow-breaking]
```

Compares two contract YAML files and classifies each difference as breaking or
non-breaking for data producers. Exits `1` when a breaking change is present;
`--allow-breaking` forces exit `0`.

```bash
dq diff contracts/orders@v1.yaml contracts/orders@v2.yaml
dq diff old.yaml new.yaml --output json
```

See [Diffing contracts](diff.md) for the full classification table and the JSON
schema.

## `dq show`

```bash
dq show contracts/orders.yaml
```

This prints the contract description, declared columns and constraints, and table
rules. Declared dtype and freshness values may appear even though the engines do
not enforce them yet.

## `dq infer`

```bash
dq infer DATA OUTPUT \
  --sample 100000 \
  --max-allowed-cardinality 20
```

Useful options:

- `--sample N` reads at most `N` rows.
- `--no-ranges` omits observed min/max bounds.
- `--max-allowed-cardinality N` controls enum inference; zero disables it.
- `--strict` rejects malformed CSV rows instead of skipping them.

Inference creates a draft, not a production specification. See
[Infer and refine a contract](../workflows/infer-refine.md).

## CI

Use `--fail-fast` to turn a failed contract into a failed job:

```yaml
- name: Validate orders
  run: dq validate contracts/orders.yaml data/orders.csv --fail-fast
```

For a complete workflow, see [Gate a pull request](../workflows/ci-pull-request.md).

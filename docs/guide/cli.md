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
dq validate CONTRACT DATA [--output text|json] [--fail-fast]
```

Supported extensions are `.csv`, `.json`, and—after installing the extra—
`.parquet`.

```bash
dq validate contracts/orders.yaml data/orders.csv
dq validate contracts/orders.yaml data/orders.csv --output json
dq validate contracts/orders.yaml data/orders.parquet --fail-fast
```

Without `--fail-fast`, a completed validation command exits `0` even when checks
fail; inspect the text or JSON result. With `--fail-fast`, the command still
evaluates and prints **all** checks, then exits `1` when the result is not OK. The
option does not short-circuit at the first failure.

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

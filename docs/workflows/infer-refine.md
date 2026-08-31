# Infer and refine a contract

Inference is useful for a first draft, but observed data is not automatically a
safe specification.

## 1. Infer from representative data

```bash
dq infer data/customers.csv contracts/customers.yaml --sample 100000
```

## 2. Review every observed constraint

Pay particular attention to:

- `unique` inferred from a small sample;
- exact numeric min/max values with no business margin;
- `allowed` values that may omit rare future categories;
- `not_null` when the sample happened to contain no nulls;
- regex patterns inferred from only email, UUID, or ISO-date shapes.

Remove accidental constraints and replace observed ranges with business limits.

## 3. Validate and commit

```bash
dq show contracts/customers.yaml
dq validate contracts/customers.yaml data/customers.csv --fail-fast
git add contracts/customers.yaml
```

Review the YAML diff before committing it. Re-run inference deliberately when the
source schema changes; do not overwrite a curated contract automatically.

See [`examples/infer-refine`](https://github.com/dqflow/dqflow/tree/main/examples/infer-refine)
for Python API and CLI variants.

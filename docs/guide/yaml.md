# YAML contracts

YAML contracts are declarative files suited to code review and version control.

```yaml
schema_version: "1.0"
name: orders
description: Orders emitted by checkout

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
    allowed: [USD, EUR]

rules:
  - row_count > 0
  - "null_rate('amount') < 0.01"

cross_column_rules:
  - name: shipped_after_created
    left: shipped_at
    op: ">="
    right: created_at
    error_message: shipped_at must not precede created_at
```

Both `dtype` and the legacy key `type` are accepted when reading YAML. `to_yaml()`
writes `dtype`. Declared dtype and freshness are not currently enforced.

`schema_version` declares the contract *format* version. It is optional when
reading (the current version is assumed, with a warning) and always written by
`to_yaml()` and `dq infer`. See [Schema versioning](schema-versioning.md).

Unknown keys — at the top level or on a column — are an error. Use `metadata:`
for arbitrary data.

A `# yaml-language-server: $schema=…` modeline or a `$schema` key wires the file
to the published [JSON Schema](editor-integration.md) for editor autocompletion:

```yaml
# yaml-language-server: $schema=https://dqflow.readthedocs.io/en/latest/schema/contract-1.0.json
schema_version: "1.0"
name: orders
```

## Check before you run

```bash
dq lint contracts/orders.yaml
```

`dq lint` validates the file's structure without reading any data and reports the
exact path of any problem. `Contract.from_yaml()` runs the same checks and raises
a typed [`ContractError`](../api/schema.md) instead of a traceback. See
[Linting contracts](lint.md).

## Load and save

```python
from dqflow import Contract

contract = Contract.from_yaml("contracts/orders.yaml")
result = contract.validate(df)
contract.to_yaml("contracts/orders-copy.yaml")
```

Callable cross-column rules and `custom` callables cannot be represented in YAML.
Use a Python contract for those cases.

## Validate with the CLI

```bash
dq show contracts/orders.yaml
dq validate contracts/orders.yaml data/orders.csv --fail-fast
```

See [CLI usage](cli.md) for exit-code and file-format details.

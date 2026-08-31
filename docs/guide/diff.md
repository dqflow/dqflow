# Diffing contracts

`dq diff` compares two contract versions and classifies every difference as
**breaking** or **non-breaking** for data producers. Use it in code review and CI
to catch a tightened constraint before it rejects data that used to pass.

```bash
dq diff OLD NEW [--output text|json] [--allow-breaking]
```

```console
$ dq diff contracts/orders@v1.yaml contracts/orders@v2.yaml
orders: 3 changes (1 breaking)

  BREAKING
    ~ column "amount" min: 0 -> 10        (stricter lower bound)

  non-breaking
    ~ column "currency" allowed: +[JPY]  (widened allowed set)
    + column "discount" (float)          (new nullable column)

$ echo $?
1
```

`OLD` and `NEW` are contract YAML files. The command exits `1` when any breaking
change is present so a CI job fails the pull request; pass `--allow-breaking` to
force exit `0`.

## What counts as breaking

A change is **breaking** when data that conformed to the old contract may violate
the new one. Classification follows the contract's *declared intent* — `dtype`
and `freshness_minutes` are compared even though the engines do not enforce them
yet ([roadmap](https://github.com/dqflow/dqflow/blob/main/ROADMAP.md)).

| Change | Breaking | Non-breaking |
| --- | --- | --- |
| **column added** | new column is `not_null` or `unique` | new column is nullable |
| **column removed** | — | always (a dropped requirement only lets more data pass) |
| **`dtype`** | any change except widening (`float -> integer`, `string -> integer`, …) | `integer -> float` |
| **`not_null`** | added (`false -> true`) | removed (`true -> false`) |
| **`unique`** | added | removed |
| **`min`** | added; raised | removed; lowered |
| **`max`** | added; lowered | removed; raised |
| **`allowed`** | added; any value removed from the set | removed; only additions to the set |
| **`pattern`** | added; any change to an existing pattern | removed |
| **`freshness_minutes`** | added; decreased | removed; increased |
| **table rule** | added | removed |
| **cross-column rule** | added; redefined (same `name`, different `left`/`op`/`right`) | removed |

Notes:

- dqflow requires every declared column to be present in the data. A *nullable*
  new column is treated as non-breaking on the assumption that the producer can
  emit it (even as all-null); a `not_null` new column demands real values and is
  breaking. If your producers may omit columns entirely, treat any column
  addition as breaking and run with `--allow-breaking` off.
- Table rules are opaque expressions, so `dq diff` matches them by exact string.
  A reworded rule (e.g. `null_rate('a') < 0.5` → `< 0.2`) shows as one removal
  **and** one addition rather than a single "changed" entry.
- A bound whose value is no longer comparable to the old one (for example the
  `dtype` flipped from numeric to `timestamp` in the same change) is reported as
  breaking.
- `description` and `metadata` are not compared — they do not affect validation.

## JSON output

```bash
dq diff old.yaml new.yaml --output json
```

The schema is stable:

```json
{
  "old_contract": "orders",
  "new_contract": "orders",
  "summary": { "total": 3, "breaking": 1, "non_breaking": 2 },
  "has_breaking": true,
  "changes": [
    {
      "kind": "field_changed",
      "classification": "breaking",
      "reason": "stricter lower bound",
      "column": "amount",
      "attribute": "min",
      "old": 0,
      "new": 10
    }
  ]
}
```

`kind` is one of `column_added`, `column_removed`, `field_added`,
`field_removed`, `field_changed`, `table_rule_added`, `table_rule_removed`,
`cross_column_rule_added`, `cross_column_rule_removed`,
`cross_column_rule_changed`. `column` and `attribute` are `null` for
table-level and cross-column changes. `old` / `new` are `null` when the field or
object was absent on that side.

## Python API

`dq diff` wraps [`dqflow.diff.diff_contracts()`](../api/diff.md):

```python
from dqflow import Contract, diff_contracts

result = diff_contracts(
    Contract.from_yaml("contracts/orders@v1.yaml"),
    Contract.from_yaml("contracts/orders@v2.yaml"),
)

if result.has_breaking:
    for change in result.breaking_changes:
        print(change.column, change.attribute, change.reason)

report = result.to_dict()  # stable JSON structure
print(result.render_text())  # the grouped text summary
```

`diff_contracts()` also accepts paths directly:
`diff_contracts("v1.yaml", "v2.yaml")`.

## In CI

```yaml
- name: Contract compatibility
  run: |
    git show origin/main:contracts/orders.yaml > /tmp/orders-main.yaml
    dq diff /tmp/orders-main.yaml contracts/orders.yaml
```

The step fails when the pull request tightens the contract. Reviewers who have
decided a breaking change is acceptable re-run with `--allow-breaking` or merge
past the failed check.

See [CLI usage](cli.md) for the other `dq` commands.

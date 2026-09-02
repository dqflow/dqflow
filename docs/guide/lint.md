# Linting contracts

`dq lint` checks a contract file for schema and structural problems **without
reading any data**. Use it in an editor loop, a pre-commit hook, or a CI step so
a broken contract fails fast with a clear location instead of a traceback part-way
through validation.

```bash
dq lint contracts/orders.yaml
```

```console
contracts/orders.yaml: 2 errors, 1 warning

  ERROR  columns.amount.min:6   min (100) is greater than max (1)         [min-greater-than-max]
  ERROR  columns.amount.bogus:8  unknown field 'bogus'; expected one of …  [unknown-field]
  WARN   (root)                  no schema_version; assuming "1.0"         [missing-schema-version]
```

Every diagnostic carries a **document path** (`columns.amount.min`, `rules[2]`)
and, when the file could be tracked, a **line number**.

## Options and exit codes

```bash
dq lint CONTRACT [--output text|json] [--strict]
```

| Exit | Meaning |
| --- | --- |
| `0` | No errors (warnings are allowed unless `--strict`). |
| `1` | One or more errors — or, with `--strict`, one or more warnings. |
| `2` | Usage error (missing file, bad option). |

`--output json` prints `{"contract", "ok", "error_count", "warning_count",
"diagnostics": [...]}`, where each diagnostic is
`{"severity", "code", "message", "path", "line"}`. The `code` is a stable token
you can branch on; the `message` is not.

`Contract.from_yaml()` runs the same checks and raises
[`ContractParseError` / `ContractSchemaError` / `ContractVersionError`](../api/schema.md)
(all subclasses of `ContractError`); `dq validate`, `dq show` and `dq diff`
surface those as a one-line error and point you at `dq lint`.

For the editing loop, dqflow also publishes a [JSON Schema](editor-integration.md)
— `dq schema` prints it — that a YAML language server can check as you type. It
is a subset of the linter (no cross-field checks), so keep `dq lint` in CI.

## Diagnostic codes

### Errors — the contract will not load

| Code | Trigger |
| --- | --- |
| `invalid-yaml` | The file is not valid YAML. |
| `not-a-mapping` | The document, `columns`, or a column entry is not a mapping. |
| `unknown-field` | A key that is not part of the schema (`metadata:` is the escape hatch for arbitrary data). |
| `wrong-type` | A value has the wrong type — `not_null` not a boolean, `rules` not a list, and so on. |
| `min-greater-than-max` | A column's `min` exceeds its `max`. |
| `invalid-regex` | A `pattern` is not a valid regular expression. |
| `invalid-rule` | A table rule fails to parse or uses a construct outside the [rule whitelist](rules.md). |
| `invalid-operator` | A cross-column rule `op` is not one of `>= <= > < == !=`. |
| `incomplete-cross-column-rule` | A cross-column rule is missing `name`, or any of `left` / `op` / `right` (callable rules cannot be written in YAML). |
| `duplicate-cross-column-rule-name` | Two cross-column rules share a `name`. |
| `unsupported-schema-version` | `schema_version` is a different major version, or not `MAJOR.MINOR`. |

### Warnings — loadable, but probably not intended

| Code | Trigger |
| --- | --- |
| `missing-schema-version` | No `schema_version`; the current version is assumed. |
| `newer-schema-minor` | `schema_version` is a newer minor of the current major. |
| `missing-name` | No `name`; the file stem is used. |
| `missing-column-dtype` | A column mapping has no `dtype` / `type`; it defaults to string. |
| `empty-contract` | No columns, rules, or cross-column rules. |
| `empty-allowed` | `allowed: []` — every non-null value would fail. |
| `duplicate-rule` | The same table-rule string appears twice. |

# Schema versioning

A dqflow contract declares the version of the contract *format* it is written in:

```yaml
schema_version: "1.0"
name: orders
columns:
  order_id:
    dtype: string
    not_null: true
```

`Contract.to_yaml()` and `dq infer` always write the current version
(`1.0`). The value is `MAJOR.MINOR`.

Each version has a published JSON Schema —
`https://dqflow.github.io/dqflow/schema/contract-1.0.json` (also `dq schema`) —
for [editor tooling](editor-integration.md).

## Compatibility policy

When dqflow reads a contract it compares the file's `schema_version` with the
version it emits:

| File version vs. current | Behaviour |
| --- | --- |
| Same major, minor **≤** current | Loaded normally. |
| Same major, minor **>** current | Loaded, with a `newer-schema-minor` warning — the file may use fields this dqflow does not know about. |
| **Different major**, or not `MAJOR.MINOR` | Rejected with `ContractVersionError` / an `unsupported-schema-version` error. |
| **Absent** | Loaded as the current version, with a `missing-schema-version` warning. Add the key to silence it. |

In short: **a minor bump only adds optional things** (older dqflow keeps
working, newer files stay readable), and **a major bump may remove or redefine
fields** (and is a hard stop for an older dqflow).

## Deprecation

Before a field is removed or repurposed in a new major version it is deprecated
for **at least one minor release**, called out in the
[changelog](../changelog.md), and — where the change is mechanical — an upgrade
note is provided. Contracts you have already committed keep loading until the
next major version; `dq lint` tells you when one needs attention.

## Checking a contract

```bash
dq lint contracts/orders.yaml
```

See [Linting contracts](lint.md) for the full diagnostic list.

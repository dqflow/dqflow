# Editor integration

dqflow publishes a JSON Schema for the contract format at a stable URL:

```
https://dqflow.readthedocs.io/en/latest/schema/contract-1.0.json
```

Point your editor's YAML tooling at it and you get autocompletion, hover docs,
and inline flags for obvious mistakes (unknown fields, wrong types) as you type.
`dq schema` prints the same document for offline use.

!!! note
    The JSON Schema is a **subset** of what [`dq lint`](lint.md) checks — it
    cannot express `min` ≤ `max`, regex validity, or table-rule syntax. Keep
    `dq lint` in your pre-commit hook and CI; the schema is for the editing loop.

## Per-file (any editor with a YAML language server)

Add a modeline to the top of the contract:

```yaml
# yaml-language-server: $schema=https://dqflow.readthedocs.io/en/latest/schema/contract-1.0.json
schema_version: "1.0"
name: orders
columns:
  order_id:
    dtype: string
    not_null: true
```

Or use the schema's own convention — a `$schema` key, which dqflow accepts and
ignores:

```yaml
$schema: https://dqflow.readthedocs.io/en/latest/schema/contract-1.0.json
schema_version: "1.0"
name: orders
```

## VS Code

Install the [YAML extension](https://marketplace.visualstudio.com/items?itemName=redhat.vscode-yaml)
and map your contract files in `settings.json`:

```json
{
  "yaml.schemas": {
    "https://dqflow.readthedocs.io/en/latest/schema/contract-1.0.json": [
      "contracts/**/*.yaml",
      "**/*.contract.yaml"
    ]
  }
}
```

## JetBrains IDEs (PyCharm, IntelliJ)

**Settings → Languages & Frameworks → Schemas and DTDs → JSON Schema Mappings**,
add a mapping from the URL above to a file glob such as `contracts/*.yaml`.

## Offline / vendored schema

```bash
dq schema > contracts/contract.schema.json
```

Then point `$schema` / `yaml.schemas` at the local path instead of the URL.

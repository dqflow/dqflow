# Contract schema

`dqflow.schema` validates a contract *document* — the YAML / serialisable form —
and reports precise, path-aware diagnostics instead of raw tracebacks.
`Contract.from_yaml()` runs this validation before it constructs anything;
[`dq lint`](../guide/lint.md) exposes it directly.

See [Linting contracts](../guide/lint.md) for the diagnostic-code table and
[Schema versioning](../guide/schema-versioning.md) for the compatibility policy.

## Validation

::: dqflow.schema.lint_contract_file

::: dqflow.schema.lint_contract_data

::: dqflow.schema.Diagnostic

## Exceptions

Raised by `Contract.from_yaml()`; all derive from `ContractError`.

::: dqflow.schema.ContractError

::: dqflow.schema.ContractParseError

::: dqflow.schema.ContractSchemaError

::: dqflow.schema.ContractVersionError

## Version

::: dqflow.schema.SCHEMA_VERSION

::: dqflow.schema.SUPPORTED_SCHEMA_VERSIONS

## Published JSON Schema

A JSON Schema for the serialisable contract format is published for
[editor tooling](../guide/editor-integration.md) and shipped inside the package.
It is a subset of the linter — it cannot express cross-field checks.

::: dqflow.schema.contract_json_schema

::: dqflow.schema.CONTRACT_SCHEMA_URI

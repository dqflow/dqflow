# Contract

`Contract` is the top-level data contract. It groups column constraints, table
rules, cross-column rules, descriptions, and metadata, then delegates validation
to an engine.

::: dqflow.contract.Contract
    options:
      members:
        - validate
        - from_yaml
        - to_yaml

## Notes

- Every declared column is required; a missing column produces a failed
  `column_exists:<name>` check.
- The default engine is pandas. Pass `engine=PolarsEngine()` explicitly for a
  Polars DataFrame.
- Callable cross-column rules cannot be serialized to YAML and are omitted by
  `to_yaml()`.

See [Defining Contracts](../guide/contracts.md) for an end-to-end example.

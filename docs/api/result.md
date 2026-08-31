# Validation results

## ValidationResult

`ValidationResult` contains every check produced by an engine.

::: dqflow.result.ValidationResult

## CheckResult

`CheckResult` represents one schema, column, table, or cross-column check.

::: dqflow.result.CheckResult

`ValidationResult.to_dict()` recursively converts NumPy scalars and sets into
JSON-serializable Python values, making it suitable for logs and CI artifacts.

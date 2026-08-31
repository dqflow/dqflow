# Validation results

## ValidationResult

`ValidationResult` contains every check produced by an engine.

::: dqflow.result.ValidationResult

## CheckResult

`CheckResult` represents one schema, column, table, or cross-column check.

::: dqflow.result.CheckResult

`ValidationResult.to_dict()` recursively converts NumPy scalars and sets into
JSON-serializable Python values, making it suitable for logs and CI artifacts.

## Reporting details

Failing checks attach extra keys to `CheckResult.details` for reporting. The set
depends on the check kind:

| Check | Keys |
| --- | --- |
| `not_null` | `null_count`, `null_rate` |
| `min` / `max` | `actual_min` / `actual_max`, `violating_rows`, `violating_rate` |
| `allowed` | `invalid_values`, `sample_invalid_values`, `invalid_value_count`, `violating_rows`, `violating_rate` |
| `unique` | `duplicate_count`, `sample_duplicate_values`, `violating_rate` |
| `pattern` | `invalid_count`, `sample_invalid_values`, `violating_rate` |
| cross-column | `failing_rows`, `failing_rate` |

Value samples are bounded (at most five, sorted). `dqflow.report.render_result()`
turns a `ValidationResult` into the grouped text that `dq validate` prints; see
[CLI usage](../guide/cli.md).

# Column and CrossColumnRule

## Column

`Column` describes a required column and its constraints.

::: dqflow.column.Column

!!! note "Enforcement boundary"
    `dtype` is enforced as one of five logical types: integer, float, string,
    boolean, or timestamp. `Column` has no callable hook — use a callable
    `CrossColumnRule` for custom logic.

## CrossColumnRule

`CrossColumnRule` performs a row-wise comparison between columns, between a
column and a literal, or through a Python callable.

::: dqflow.column.CrossColumnRule

Structured rules support `>=`, `<=`, `>`, `<`, `==`, and `!=`. Callable rules
are available only in Python contracts; they cannot be represented in YAML.

See [Cross-column and custom checks](../guide/custom-checks.md) for examples.

# Column and CrossColumnRule

## Column

`Column` describes a required column and its constraints.

::: dqflow.column.Column

!!! warning "Declared but not enforced"
    `dtype`, `freshness_minutes`, and `custom` are stored and serialized, but the
    current engines do not validate them. Use the enforced `pattern` constraint
    or a callable `CrossColumnRule` where appropriate.

## CrossColumnRule

`CrossColumnRule` performs a row-wise comparison between columns, between a
column and a literal, or through a Python callable.

::: dqflow.column.CrossColumnRule

Structured rules support `>=`, `<=`, `>`, `<`, `==`, and `!=`. Callable rules
are available only in Python contracts; they cannot be represented in YAML.

See [Cross-column and custom checks](../guide/custom-checks.md) for examples.

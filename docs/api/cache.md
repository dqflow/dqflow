# Statistics cache

`StatsCache` is the engine-agnostic cache behind table-rule statistics —
`row_count`, `null_rate(col)`, and `unique_count(col)`. It is lazy (nothing is
computed until a rule asks) and memoized (a column used by several rules is
scanned once), and it is scoped to a single `validate()` call.

Each engine provides a subclass with three primitives that read its DataFrame;
`PandasEngine` uses `dqflow.engines.pandas.PandasStatsCache` and `PolarsEngine`
uses `dqflow.engines.polars.PolarsStatsCache`.

::: dqflow.cache.StatsCache

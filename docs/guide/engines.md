# Choosing an engine

dqflow has a stable default pandas engine and an experimental Polars engine. Both
produce the same `ValidationResult` shape and are covered by output-parity tests.

| Engine | Install | Input | Current behavior |
| --- | --- | --- | --- |
| pandas | `pip install dqflow` | `pandas.DataFrame` | Default and stable |
| Polars | `pip install "dqflow[polars]"` | `DataFrame` or `LazyFrame` | Experimental; lazy input is collected |

## Pandas

No engine argument is needed:

```python
result = contract.validate(pandas_df)
```

Choose pandas for the most established path, CLI file loading, and existing
pandas pipelines.

## Polars

```python
from dqflow.engines.polars import PolarsEngine

result = contract.validate(polars_df, engine=PolarsEngine())
```

Choose Polars when the pipeline already uses Polars and you are comfortable with
an experimental API. Passing a `LazyFrame` does not keep execution lazy today;
the engine calls `collect()` first. Track lazy execution in
[#25](https://github.com/dqflow/dqflow/issues/25).

## Constraints shared by both engines

Both engines enforce column existence, `not_null`, `min`, `max`, `allowed`,
`unique`, `pattern`, table rules, and cross-column rules. Neither currently
enforces declared dtype, freshness, or `Column.custom`.

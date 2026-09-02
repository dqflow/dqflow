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
result = contract.validate(polars_df, engine="polars")

# or pass an instance
from dqflow.engines.polars import PolarsEngine

result = contract.validate(polars_df, engine=PolarsEngine())
```

`engine=` accepts a registered name (`"pandas"`, `"polars"`), an `Engine`
instance, or `None` for the pandas default. The CLI exposes the same choice as
`dq validate --engine polars`.

Choose Polars when the pipeline already uses Polars and you are comfortable with
an experimental API. Passing a `LazyFrame` does not keep execution lazy today;
the engine calls `collect()` first. Track lazy execution in
[#25](https://github.com/dqflow/dqflow/issues/25).

## Runtime configuration with `ExecutionContext`

`engine=` is a shortcut. The full runtime configuration for a run lives in an
[`ExecutionContext`](../api/context.md) — a frozen dataclass you pass as
`context=`:

```python
from dqflow import ExecutionContext

context = ExecutionContext(engine="polars", cache=False)
result = contract.validate(polars_df, context=context)
```

`engine=` and `context=` are mutually exclusive.

| Field | Effect today |
| --- | --- |
| `engine` | Registered engine name; resolved through the registry. |
| `cache` | `True` (default) memoises table-rule statistics so a column used by several rules is scanned once. `False` recomputes every statistic on access. |
| `parallel`, `max_workers` | Carried, no effect yet — reserved for [#22](https://github.com/dqflow/dqflow/issues/22). |
| `strict`, `fail_fast` | Carried, no effect yet — reserved for [#44](https://github.com/dqflow/dqflow/issues/44). `fail_fast` here is unrelated to the `dq validate --fail-fast` exit-code flag. |

The CLI builds the context for you: `dq validate --engine polars` runs with
`ExecutionContext(engine="polars")`.

## Registering a custom engine

```python
from dqflow.engines import register_engine

register_engine("myengine", lambda: MyEngine())
result = contract.validate(df, engine="myengine")
```

## Constraints shared by both engines

Both engines enforce column existence, `not_null`, `min`, `max`, `allowed`,
`unique`, `pattern`, table rules, and cross-column rules. Neither currently
enforces declared dtype, freshness, or `Column.custom`.

Engines do not read `Column` objects directly. `Contract.validate()` first
compiles the contract into an engine-agnostic
[`ValidationSpec`](../api/spec.md) — an ordered list of checks — and every engine
executes that same spec. Table-rule expressions run through the shared
[`dqflow.rules`](../api/rules.md) evaluator, and their statistics come from a
shared lazy [`StatsCache`](../api/cache.md). A new engine only implements spec
execution plus three cache primitives.

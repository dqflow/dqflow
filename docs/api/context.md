# ExecutionContext

`ExecutionContext` bundles the runtime configuration for a single validation run:
which engine to use, whether table-rule statistics are cached, and execution-mode
flags. It is the third axis alongside the `Contract` (*what* the data must look
like) and its compiled [`ValidationSpec`](spec.md) (*how* it is checked) — the
context is *how the run executes*.

`Contract.validate()` builds one from its `engine=` shortcut, or you can pass a
context directly:

```python
from dqflow import Contract, ExecutionContext

context = ExecutionContext(engine="polars", cache=True)
result = contract.validate(polars_df, context=context)
```

Only `engine` and `cache` change behaviour today. `parallel`, `max_workers`,
`strict`, and `fail_fast` are carried but not yet acted on — they are the stable
home for settings that
[#22](https://github.com/dqflow/dqflow/issues/22) (parallel execution) and
[#44](https://github.com/dqflow/dqflow/issues/44) (severity / thresholds) will
consume.

::: dqflow.execution.context.ExecutionContext

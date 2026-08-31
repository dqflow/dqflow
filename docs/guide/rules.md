# Table rules

Table rules evaluate aggregate properties of the complete DataFrame.

```python
from dqflow import Contract

contract = Contract(
    name="orders",
    rules=[
        "row_count > 0",
        "null_rate('amount') < 0.01",
        "unique_count('currency') <= 3",
    ],
)
```

## Available names

| Name | Result |
| --- | --- |
| `row_count` | Total rows as an integer |
| `null_rate('column')` | Null proportion from `0.0` to `1.0` |
| `unique_count('column')` | Distinct count, including null as a distinct value |

Column names must be string literals. `duplicate_rate` and other helpers are not
implemented yet.

Rules can use ordinary comparisons and boolean operators:

```python
"row_count >= 100"
"row_count > 0 and null_rate('email') < 0.05"
"unique_count('status') <= 10"
```

When a rule evaluates to false, its check fails. Evaluation errors also become
failed checks rather than escaping as exceptions.

## Safety model

Rule expressions are parsed with `ast` and evaluated by
`dqflow.rules.evaluate_rule` — one shared evaluator for every engine — which
walks a strict whitelist of nodes: the three names above, numeric and string
literals, `and` / `or` / `not`, arithmetic, and comparisons. There is **no
`eval`**, no attribute access, no indexing, no builtins, and no calls other than
`null_rate()` / `unique_count()` with a string-literal column name. Anything else
raises and the check fails with `Failed to evaluate rule: ...`.

This is a much smaller surface than `eval`, but it is still not a security
boundary: only run rule expressions from contracts you trust. Do not accept
arbitrary YAML contracts from users or third parties.

For row-wise relationships and Python callables, use
[Cross-column and custom checks](custom-checks.md).

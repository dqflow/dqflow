# Cross-column and custom checks

`CrossColumnRule` is the supported way to run row-wise relationships. Use the
structured form when possible because it works in both Python and YAML.

## Compare two columns

```python
from dqflow import Contract, CrossColumnRule

contract = Contract(
    name="orders",
    cross_column_rules=[
        CrossColumnRule(
            name="shipped_after_created",
            left="shipped_at",
            op=">=",
            right="created_at",
            error_message="shipped_at must not precede created_at",
        )
    ],
)
```

The right side may also be a numeric or string literal. When a string matches an
existing column name, it is treated as a column reference.

## Add a callable check

For logic that cannot be expressed as one comparison, pass a function that
returns one boolean value per row:

```python
import pandas as pd
from dqflow import Contract, CrossColumnRule


def valid_discount(df: pd.DataFrame) -> pd.Series:
    return (df["discount"] >= 0) & (df["discount"] <= df["subtotal"])


contract = Contract(
    name="orders",
    cross_column_rules=[
        CrossColumnRule(
            name="valid_discount",
            check=valid_discount,
            error_message="discount must be between zero and subtotal",
        )
    ],
)
```

Callable rules are trusted Python code and are not serialized by `to_yaml()`.
Keep them in version-controlled Python modules. The `Column.custom` field is only
declarative today and is not invoked by either engine.

## Failure details

A cross-column result is named `cross_column:<rule-name>` and includes
`details["failing_rows"]`. Exceptions raised by the callable become a failed
check with an evaluation-error message.

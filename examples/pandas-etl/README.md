# pandas ETL example

This example loads orders, validates them before the publish step, and fails the
pipeline with a structured summary when the contract does not pass.

```bash
pip install dqflow
python examples/pandas-etl/pipeline.py
```

Expected output ends with `published 3 valid orders`. Change an amount to a
negative value in `data/orders.csv` to see the task fail before publishing.

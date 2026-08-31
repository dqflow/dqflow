# Polars pipeline example

This example runs the same YAML contract against a Polars `LazyFrame`. dqflow
currently collects lazy input before validating it.

```bash
pip install "dqflow[polars]"
python examples/polars-pipeline/pipeline.py
```

Expected output ends with `validated 3 Polars rows`.

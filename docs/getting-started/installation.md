# Installation

## Requirements

- Python 3.9 or higher
- pandas 1.5.0 or higher

## Install from PyPI

```bash
pip install dqflow
```

Optional features are installed explicitly:

```bash
# Experimental Polars engine
pip install "dqflow[polars]"

# Parquet input for dq validate / dq infer
pip install "dqflow[parquet]"
```

CSV and JSON input do not require a file-format extra. Parquet uses `pyarrow`
from the `parquet` extra.

## Install from source

```bash
git clone https://github.com/dqflow/dqflow.git
cd dqflow
pip install -e .
```

## Development installation

For contributing to dqflow:

```bash
git clone https://github.com/dqflow/dqflow.git
cd dqflow
pip install -e ".[dev,docs,polars]"
pre-commit install
```

## Verify installation

```bash
dq --version
```

```python
import dqflow
print(dqflow.__version__)
```

# Install dqflow

For the shortest path to a working validation, follow the
[5-minute quickstart](quickstart.md). Use this page when you need a specific
engine, file format, or development setup.

## Requirements

- Python 3.9 or higher
- pandas 1.5.0 or higher

## Install from PyPI

Create a virtual environment so dqflow and its dependencies stay isolated from
your other projects:

=== "macOS / Linux"

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install dqflow
    dq --version
    ```

=== "Windows PowerShell"

    ```powershell
    py -m venv .venv
    .venv\Scripts\Activate.ps1
    python -m pip install dqflow
    dq --version
    ```

For an existing managed environment, the install itself is one command:

```bash
python -m pip install dqflow
```

Optional features are installed explicitly:

```bash
# Experimental Polars engine
python -m pip install "dqflow[polars]"

# Parquet input for dq validate / dq infer
python -m pip install "dqflow[parquet]"
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

## Verify the Python import

```python
import dqflow
print(dqflow.__version__)
```

Next, [infer and validate your first contract](quickstart.md).

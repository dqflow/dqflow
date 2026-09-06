# Install dqflow

For the shortest path to a working validation, follow the
[5-minute quickstart](quickstart.md). Use this page when you need a specific
engine, file format, or development setup.

## Requirements

- Python 3.11 through 3.14
- A backend extra for validation: pandas or Polars

## Install from PyPI

Create a virtual environment so dqflow and its dependencies stay isolated from
your other projects:

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install "dqflow[pandas]"
dq --version
```

### Windows PowerShell

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install "dqflow[pandas]"
dq --version
```

For an existing managed environment, the install itself is one command:

```bash
python -m pip install "dqflow[pandas]"
```

Optional features are installed explicitly:

```bash
# Default pandas engine
python -m pip install "dqflow[pandas]"

# Experimental Polars engine
python -m pip install "dqflow[polars]"

# pandas engine plus Parquet input
python -m pip install "dqflow[pandas-parquet]"

# Every backend and file-format dependency
python -m pip install "dqflow[all]"
```

The base `dqflow` install intentionally includes no dataframe library. It can
run `dq lint`, `dq schema`, `dq show`, and `dq diff`. Validation requires the
corresponding backend extra; `dq infer` currently requires pandas. CSV and JSON
need no additional file-format dependency. The pandas CLI uses PyArrow for
Parquet; Polars uses its native reader.

See the [supported-environments policy](../reference/compatibility.md) for the
complete version matrix and lifecycle rules.

## Install from source

```bash
git clone https://github.com/dqflow/dqflow.git
cd dqflow
pip install -e ".[pandas]"
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

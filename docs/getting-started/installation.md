# Installation

## Requirements

- Python 3.9 or higher
- pandas 1.5.0 or higher

## Install from PyPI

```bash
pip install dqflow
```

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
pip install -e ".[dev]"
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

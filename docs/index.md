# dqflow

**Lightweight, contract-first data quality engine for modern data pipelines.**

[![PyPI version](https://badge.fury.io/py/dqflow.svg)](https://pypi.org/project/dqflow/)
[![CI](https://github.com/dqflow/dqflow/actions/workflows/ci.yml/badge.svg)](https://github.com/dqflow/dqflow/actions/workflows/ci.yml)
[![Python](https://img.shields.io/pypi/pyversions/dqflow.svg)](https://pypi.org/project/dqflow/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## What is dqflow?

dqflow lets you define **explicit expectations** for your data (schema, validity, freshness) and **fail fast** when data breaks — before bad data reaches downstream systems.

```python
from dqflow import Contract, Column

contract = Contract(
    name="orders",
    columns={
        "order_id": Column(str, not_null=True),
        "amount": Column(float, min=0),
        "currency": Column(str, allowed=["USD", "EUR"]),
    },
)

result = contract.validate(df)
if not result.ok:
    raise Exception(result.summary())
```

## Why dqflow?

Data quality issues are inevitable — **silent failures are not**.

Most teams rely on ad-hoc checks, fragile assertions, or heavyweight frameworks that are hard to maintain. dqflow takes a different approach:

- **Contracts over checks** — expectations are explicit and versionable
- **Pipeline-first** — designed for ETL, ELT, and streaming workflows
- **Lightweight & Pythonic** — minimal API, easy to embed
- **Fail fast** — break pipelines intentionally, not silently

## Features

- Contract-as-code (Python & YAML)
- Column-level validations (not null, min/max, allowed values, freshness)
- Table-level rules (row count, null rate, custom expressions)
- Structured validation results (JSON-friendly)
- CLI support
- Pandas engine (PySpark coming soon)

## Quick Links

- [Installation](getting-started/installation.md)
- [Quick Start](getting-started/quickstart.md)
- [API Reference](api/contract.md)
- [GitHub Repository](https://github.com/dqflow/dqflow)

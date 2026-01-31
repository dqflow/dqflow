# dqflow

**dqflow** is a lightweight, contract-first data quality engine for modern data pipelines.

Define explicit expectations for your data (schema, validity, freshness) and **fail fast** when data breaks — before bad data reaches downstream systems.

---

## Why dqflow?

Data quality issues are inevitable — silent failures are not.

Most teams rely on ad-hoc checks, fragile assertions, or heavyweight frameworks that are hard to maintain. dqflow takes a different approach:

* **Contracts over checks** — expectations are explicit and versionable
* **Pipeline-first** — designed for ETL, ELT, and streaming workflows
* **Lightweight & Pythonic** — minimal API, easy to embed
* **Fail fast** — break pipelines intentionally, not silently

---

## Installation

```bash
pip install dqflow
```

---

## Quick Example

```python
import pandas as pd
from dqflow import Contract, Column

# Sample data with quality issues
df = pd.DataFrame({
    "order_id": ["A001", None, "A003"],      # Has null value
    "amount": [100.0, -50.0, 75.0],          # Has negative value
    "currency": ["USD", "GBP", "EUR"],       # GBP not in allowed list
})

# Define your data contract
contract = Contract(
    name="orders",
    columns={
        "order_id": Column(str, not_null=True),
        "amount": Column(float, min=0),
        "currency": Column(str, allowed=["USD", "EUR"]),
    },
    rules=["row_count > 0"],
)

# Validate
result = contract.validate(df)

# Check results
print(result.summary())
```

**Output:**
```
Contract 'orders': 4/7 checks passed
Failed checks:
  - not_null:order_id: Found 1 null values
  - min:amount: Minimum value -50.0 is below 0
  - allowed:currency: Found invalid values: {'GBP'}
```

**Use in pipelines:**
```python
if not result.ok:
    raise Exception(result.summary())  # Fail fast!
```

---

## Full Example with All Features

```python
import pandas as pd
from dqflow import Contract, Column

# Define contract with all constraint types
orders = Contract(
    name="orders",
    columns={
        "order_id": Column(str, not_null=True),
        "amount": Column(float, min=0, max=100000),
        "currency": Column(str, allowed=["USD", "EUR"]),
        "created_at": Column("timestamp", freshness_minutes=60),
    },
    rules=[
        "row_count > 1000",
        "null_rate(amount) < 0.01",
    ],
)

result = orders.validate(df)

# Programmatic access to results
print("Passed:", result.ok)
print("Failed checks:", [c.name for c in result.failed_checks])

# JSON output for logging/monitoring
import json
print(json.dumps(result.to_dict(), indent=2))
```

**Output:**
```shell
Passed: False
Failed checks: ['column_exists:created_at', 'not_null:order_id', 'min:amount', 'allowed:currency', 'rule:row_count > 1000', 'rule:null_rate(amount) < 0.01']
{
  "checks": [
    {
      "details": {},
      "message": "",
      "name": "column_exists:order_id",
      "passed": true
    },
    {
      "details": {},
      "message": "",
      "name": "column_exists:amount",
      "passed": true
    },
    {
      "details": {},
      "message": "",
      "name": "column_exists:currency",
      "passed": true
    },
    {
      "details": {},
      "message": "Column 'created_at' not found in DataFrame",
      "name": "column_exists:created_at",
      "passed": false
    },
    {
      "details": {
        "null_count": 1
      },
      "message": "Found 1 null values",
      "name": "not_null:order_id",
      "passed": false
    },
    {
      "details": {
        "actual_min": -50.0
      },
      "message": "Minimum value -50.0 is below 0",
      "name": "min:amount",
      "passed": false
    },
    {
      "details": {
        "actual_max": 100.0
      },
      "message": "",
      "name": "max:amount",
      "passed": true
    },
    {
      "details": {
        "invalid_values": [
          "GBP"
        ]
      },
      "message": "Found invalid values: {'GBP'}",
      "name": "allowed:currency",
      "passed": false
    },
    {
      "details": {},
      "message": "Rule 'row_count > 1000' failed",
      "name": "rule:row_count > 1000",
      "passed": false
    },
    {
      "details": {},
      "message": "Failed to evaluate rule: name 'amount' is not defined",
      "name": "rule:null_rate(amount) < 0.01",
      "passed": false
    }
  ],
  "contract_name": "orders",
  "failed": 6,
  "ok": false,
  "passed": 4,
  "total_checks": 10
}
```

---

## Features (v0.1 scope)

* Contract-as-code (Python & YAML)
* Column-level checks

  * type validation
  * not null
  * min / max
  * allowed values
* Table-level checks

  * row count
  * freshness
* Structured validation results (JSON-friendly)
* Pandas engine
* CLI support

---

## YAML Contract

Define contracts in YAML for version control:

```yaml
# contracts/orders.yaml
name: orders
description: E-commerce order data contract

columns:
  order_id:
    type: string
    not_null: true
  amount:
    type: float
    min: 0
    max: 100000
  currency:
    type: string
    allowed: ["USD", "EUR", "GBP"]
  created_at:
    type: timestamp
    freshness_minutes: 1440

rules:
  - row_count > 0
  - "null_rate(amount) < 0.01"
```

Load in Python:
```python
from dqflow import Contract

contract = Contract.from_yaml("contracts/orders.yaml")
result = contract.validate(df)
```

---

## CLI Usage

```bash
# Validate data against a contract
dq validate contracts/orders.yaml data/orders.parquet

# Show contract details
dq show contracts/orders.yaml

# Infer contract from existing data
dq infer data/orders.csv contracts/orders.yaml

# JSON output for CI/CD
dq validate contracts/orders.yaml data/orders.parquet --output json --fail-fast
```

---

## Supported engines

* ✅ Pandas
* 🚧 PySpark (planned)
* 🚧 SQL tables (planned)

---

## Philosophy

* **Explicit is better than implicit**
* **Bad data should break pipelines early**
* **Quality rules are part of your system design**

> dqflow is not a full data observability platform.
> It is a small, opinionated library meant to be embedded directly into pipelines.

---

## Roadmap

* PySpark engine
* dbt / dlt integrations
* Incremental & backfill-aware validation
* Metrics export (Prometheus-compatible)

---

## License

MIT

---

## Status

🚧 Early development (v0.1.1)

APIs may change. Feedback and contributions are welcome.

---

## Contributing

```bash
# Clone and install dev dependencies
git clone https://github.com/dqflow/dqflow.git
cd dqflow
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check .
```

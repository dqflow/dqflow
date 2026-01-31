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

## Quick example

```python
from dqflow import Contract, Column

orders = Contract(
    name="orders",
    columns={
        "order_id": Column(str, not_null=True),
        "amount": Column(float, min=0),
        "currency": Column(str, allowed=["USD", "EUR"]),
        "created_at": Column("timestamp", freshness_minutes=60),
    },
    rules=[
        "row_count > 1000",
        "null_rate(amount) < 0.01",
    ],
)

result = orders.validate(df)

if not result.ok:
    raise Exception(result.summary())
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

## CLI usage

```bash
dq validate contracts/orders.yaml data/orders.parquet
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

🚧 Early development (v0.1.0)

APIs may change. Feedback and contributions are welcome.

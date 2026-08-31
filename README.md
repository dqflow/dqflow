# dqflow

<p align="center">
  <picture>
    <source
      media="(prefers-color-scheme: dark)"
      srcset="https://raw.githubusercontent.com/dqflow/dqflow/main/docs/assets/dqflow-dark-logo.png"
    />
    <img
      src="https://raw.githubusercontent.com/dqflow/dqflow/main/docs/assets/dqflow-light-logo.png"
      width="360"
      alt="dqflow"
    />
  </picture>
</p>

<h2 align="center">Data contracts for Python data pipelines.</h2>
<p align="center"><strong>Define → Validate → Fail Fast</strong></p>

<p align="center">
  <a href="https://pypi.org/project/dqflow/"><img src="https://img.shields.io/pypi/v/dqflow.svg" alt="PyPI version"></a>
  <a href="https://github.com/dqflow/dqflow/actions/workflows/ci.yml"><img src="https://github.com/dqflow/dqflow/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://dqflow.github.io/dqflow/"><img src="https://img.shields.io/badge/docs-mkdocs-blue.svg" alt="Docs"></a>
  <a href="https://pypi.org/project/dqflow/"><img src="https://img.shields.io/pypi/pyversions/dqflow.svg" alt="Python versions"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
</p>

<p align="center">
  <a href="https://dqflow.github.io/dqflow/">Documentation</a> ·
  <a href="https://pypi.org/project/dqflow/">PyPI</a> ·
  <a href="https://github.com/dqflow/dqflow/blob/main/ROADMAP.md">Roadmap</a>
</p>

---

**dqflow** lets you declare what a DataFrame must look like — required columns, valid
values, table-level rules — as a small, versionable contract, validate your data
against it inside the pipeline, and stop bad data *before* it reaches anything
downstream.

## Workflow

```text
  1. DEFINE                2. VALIDATE                 3. FAIL FAST
  ─────────                ───────────                 ────────────
  write a contract   ─▶    contract.validate(df)  ─▶   result.ok is False
  in Python or YAML        → ValidationResult          → raise / exit code ≠ 0

                                                       result.ok is True
                                                       → pipeline continues
```

## Why dqflow

- **Contracts, not scattered asserts.** One declarative artifact — reviewed, diffed,
  and versioned like the rest of your code.
- **Lightweight.** Three runtime dependencies (`pandas`, `pyyaml`, `click`). No
  server, no database, no daemon. `pip install` and embed it.
- **Pythonic.** Plain `Contract` / `Column` objects, or YAML. Validation returns a
  structured result object, not a stack trace.
- **Fail fast, on purpose.** `result.ok` is a boolean; `dq validate --fail-fast`
  returns a non-zero exit code. Wire it into a pipeline task or a CI step.
- **Deliberately scoped.** dqflow emits structured results — it does not try to be a
  monitoring platform.

## Installation

```bash
pip install dqflow

# optional, experimental Polars engine
pip install "dqflow[polars]"

# optional, required for Parquet files in the CLI
pip install "dqflow[parquet]"
```

Requires Python 3.9+.

> `dtype`, `freshness_minutes`, and `custom` can be declared on a `Column`, but
> are not enforced by the validation engines yet. `pattern` **is** enforced.

## 30-second Quick Start

```python
import pandas as pd
from dqflow import Contract, Column

df = pd.DataFrame({
    "order_id": ["A001", "A002", None, "A004"],
    "amount":   [19.99, -5.00, 42.50, 99.00],
    "currency": ["USD", "EUR", "USD", "GBP"],
})

contract = Contract(
    name="orders",
    columns={
        "order_id": Column(str, not_null=True, unique=True),
        "amount":   Column(float, min=0),
        "currency": Column(str, allowed=["USD", "EUR"]),
    },
    rules=["row_count > 0"],
)

result = contract.validate(df)
print(result.summary())

if not result.ok:
    raise ValueError(result.summary())
```

```text
Contract 'orders': 5/8 checks passed
Failed checks:
  - not_null:order_id: Found 1 null values
  - min:amount: Minimum value -5.0 is below 0
  - allowed:currency: Found invalid values: {'GBP'}
```

## Python contract

Contracts also carry table rules and cross-column rules, and hand back a structured
result.

```python
import pandas as pd
from dqflow import Contract, Column, CrossColumnRule

df = pd.DataFrame({
    "order_id":   ["A001", "A002", "A003"],
    "amount":     [19.99, 5.00, 42.50],
    "currency":   ["USD", "EUR", "USD"],
    "created_at": pd.to_datetime(["2026-08-01", "2026-08-02", "2026-08-03"]),
    "shipped_at": pd.to_datetime(["2026-08-02", "2026-08-01", "2026-08-05"]),
})

contract = Contract(
    name="orders",
    description="Orders emitted by the checkout service",
    columns={
        "order_id":   Column(str, not_null=True, unique=True),
        "amount":     Column(float, min=0, max=100_000),
        "currency":   Column(str, allowed=["USD", "EUR"]),
        "created_at": Column("timestamp", not_null=True),
    },
    rules=[
        "row_count > 0",
        "null_rate('amount') < 0.01",
        "unique_count('currency') <= 3",
    ],
    cross_column_rules=[
        CrossColumnRule(
            name="shipped_after_created",
            left="shipped_at", op=">=", right="created_at",
            error_message="shipped_at must not precede created_at",
        ),
    ],
)

result = contract.validate(df)
print(result.summary())

result.ok              # bool  — did every check pass?
result.failed_checks   # list[CheckResult]
result.to_dict()       # JSON-serializable dict for logs / CI
```

```text
Contract 'orders': 13/14 checks passed
Failed checks:
  - cross_column:shipped_after_created: shipped_at must not precede created_at
```

Rule expressions expose the names
`row_count`, `null_rate('column')`, and `unique_count('column')` — column names are
passed as strings. The current engines evaluate these expressions with Python
`eval` after removing builtins; do not load contracts from untrusted sources. A
dedicated evaluator is tracked in [#18](https://github.com/dqflow/dqflow/issues/18).

## YAML contract

The same contract lives just as well in version control as YAML.

```yaml
# contracts/orders.yaml
name: orders
description: Orders emitted by the checkout service

columns:
  order_id:
    type: string
    not_null: true
    unique: true
  amount:
    type: float
    min: 0
  currency:
    type: string
    allowed: ["USD", "EUR"]

rules:
  - row_count > 0
  - "null_rate('order_id') == 0"
```

```python
from dqflow import Contract

# load from YAML (or write a contract back out with contract.to_yaml(path))
contract = Contract.from_yaml("contracts/orders.yaml")
result = contract.validate(df)
```

## CLI usage

The `dq` command validates data files (`.csv`, `.parquet`, `.json`) against a YAML
contract.

```bash
# Validate data against a contract
dq validate contracts/orders.yaml data/orders.csv

# Non-zero exit code on failure — drop this into CI
dq validate contracts/orders.yaml data/orders.csv --fail-fast

# Machine-readable output
dq validate contracts/orders.yaml data/orders.csv --output json

# Inspect a contract
dq show contracts/orders.yaml

# Infer a draft contract (dtypes and observed constraints) from existing data
dq infer data/orders.csv contracts/orders.yaml --sample 100000

# Diff two contract versions; exits 1 when a change is breaking for producers
dq diff contracts/orders@v1.yaml contracts/orders@v2.yaml
```

`--fail-fast` evaluates the complete contract, prints all failed checks, and then
returns exit code `1` when validation fails. It does not stop after the first
failed check. Parquet input requires `dqflow[parquet]`.

Given `data/orders.csv` where `order_id` has a duplicate and a null, `amount` has a
negative value, and `currency` contains `GBP`:

```console
$ dq validate contracts/orders.yaml data/orders.csv --fail-fast
Contract 'orders': 4/9 checks passed
Failed checks:
  - not_null:order_id: Found 1 null values
  - unique:order_id: Found 2 duplicate values
  - min:amount: Minimum value -5.0 is below 0
  - allowed:currency: Found invalid values: {'GBP'}
  - rule:null_rate('order_id') == 0: Rule 'null_rate('order_id') == 0' failed
$ echo $?          # --fail-fast turns a failed contract into a non-zero exit
1
```

## Features

| Capability | Status |
| --- | --- |
| Python contracts — `Contract`, `Column`, `CrossColumnRule` | ✅ Implemented |
| YAML contracts — `Contract.from_yaml()` / `.to_yaml()` | ✅ Implemented |
| Schema check — required columns must be present in the data | ✅ Implemented |
| Validity checks — `not_null`, `min`, `max`, `allowed`, `unique`, `pattern` | ✅ Implemented |
| Table rules — `row_count`, `null_rate('col')`, `unique_count('col')` | ✅ Implemented |
| Cross-column rules — `left`/`op`/`right` or a callable | ✅ Implemented |
| Structured results — `.ok`, `.failed_checks`, `.summary()`, `.to_dict()` | ✅ Implemented |
| CLI — `dq validate` / `dq show` / `dq infer` / `dq diff` | ✅ Implemented |
| Contract inference from data (dtypes and observed constraints) | ✅ Implemented |
| Contract diff — breaking / non-breaking classification, JSON, CI exit code | ✅ Implemented |
| pandas engine | ✅ Implemented |
| Polars engine (`dqflow[polars]`) | 🧪 Experimental |
| Declared type / `freshness_minutes` / `custom` enforcement | 🔜 Declared in the contract, not yet enforced |
| GitHub Action, HTML reports, severity levels | 🔜 Planned — see [ROADMAP.md](https://github.com/dqflow/dqflow/blob/main/ROADMAP.md) |
| PySpark & SQL engines | 🔜 Planned — see [ROADMAP.md](https://github.com/dqflow/dqflow/blob/main/ROADMAP.md) |

> A `Column` accepts `dtype`, `freshness_minutes`, and `custom` today, and
> `dq show` / `dq infer` use the declared dtype — but the engines do **not** yet check
> data against them. Regex `pattern` constraints are enforced. Treat the other
> fields as documentation until the roadmap catches up.

## Architecture

```text
  Contract                            Python object or YAML file
  columns · rules · cross-column rules
      │
      ▼
  ValidationSpec    ┐                  shared layers being extracted
  RuleEngine        ├── (in progress)  (P0 refactor, issues #15–#21).
  ExecutionContext  ┘                  today Contract.validate() calls
      │                                an engine directly.
      ▼
  Engine  ───────────────────────▶     pandas   default, stable
      │                                Polars   experimental
      ▼
  ValidationResult  ─────────────▶     your pipeline / CI
  .ok · .summary() · .to_dict()        raise · non-zero exit · JSON logs
```

Today the flow is `Contract → engine (pandas / Polars) → ValidationResult`, and each
engine carries its own `eval`-based rule evaluator and stats cache. `ValidationSpec`,
`RuleEngine`, and `ExecutionContext` are the shared layers being extracted — see
[ROADMAP.md](https://github.com/dqflow/dqflow/blob/main/ROADMAP.md) (issues #15–#21).

## Supported engines

| Engine | Input | Status |
| --- | --- | --- |
| **pandas** | `pandas.DataFrame` | Default, stable |
| **Polars** | `polars.DataFrame` / `LazyFrame` | Experimental — `pip install "dqflow[polars]"` |
| PySpark | `pyspark.sql.DataFrame` | Planned |
| SQL | warehouse table / query | Planned |

```python
from dqflow.engines.polars import PolarsEngine

result = contract.validate(polars_df, engine=PolarsEngine())
```

## Runnable examples

The [`examples/`](https://github.com/dqflow/dqflow/tree/main/examples) directory
contains five self-contained projects. Each one includes sample data or contracts,
a runnable script, and its own README.

| Example | What it demonstrates | Install |
| --- | --- | --- |
| [pandas ETL](https://github.com/dqflow/dqflow/tree/main/examples/pandas-etl) | Validate transformed orders before publishing downstream | `pip install dqflow` |
| [Polars pipeline](https://github.com/dqflow/dqflow/tree/main/examples/polars-pipeline) | Validate a Polars `LazyFrame` with the experimental engine | `pip install "dqflow[polars]"` |
| [CI validation](https://github.com/dqflow/dqflow/tree/main/examples/ci-validation) | Turn a failed YAML contract into a non-zero CI exit code | `pip install dqflow` |
| [Infer and refine](https://github.com/dqflow/dqflow/tree/main/examples/infer-refine) | Infer a draft, replace observed bounds with business rules, and validate it | `pip install dqflow` |
| [Contract diff](https://github.com/dqflow/dqflow/tree/main/examples/contract-diff) | Compare two contract versions and block breaking changes | `pip install dqflow` |

Run them from the repository root:

```bash
python examples/pandas-etl/pipeline.py
python examples/polars-pipeline/pipeline.py
python examples/ci-validation/validate.py
python examples/infer-refine/infer_and_validate.py
python examples/contract-diff/diff.py
```

Expected output:

```text
Contract 'orders': 9/9 checks passed
published 3 valid orders

Contract 'events': 9/9 checks passed
validated 3 Polars rows

Contract 'users': 11/11 checks passed

Contract 'customers': 12/12 checks passed
reviewed the inferred draft and validated the curated contract

orders: 3 changes (1 breaking)
blocked: 1 breaking change(s) for data producers
```

All five scripts are also exercised by
[`tests/test_examples.py`](https://github.com/dqflow/dqflow/blob/main/tests/test_examples.py).

## When to use dqflow

- You have Python data pipelines — Airflow, Dagster, Prefect, dbt-adjacent scripts,
  notebooks headed for production.
- You want data expectations in git, reviewed in pull requests.
- You want a pipeline step or CI job to **hard-fail** on bad data instead of passing
  it downstream.
- Your data fits in memory as a pandas (or Polars) DataFrame.
- You want structured pass/fail output to feed your own logs or dashboards.

## When *not* to use dqflow

- You need dashboards, alerting, anomaly detection, or lineage — dqflow produces
  files and exit codes, not a web app.
- You need to push checks down to a warehouse table without loading it (SQL engine is
  planned, not available).
- You need Spark-scale distributed validation (PySpark engine is planned).
- You need dtype conformance, freshness, or `custom` column functions enforced
  *today* — those fields are declared but not yet checked. Regex `pattern` checks
  are enforced.
- You need to execute contracts from untrusted sources — the current rule evaluator
  removes builtins but still relies on Python `eval`.

> **dqflow is not a full data observability platform.** It is a small, opinionated
> library meant to be embedded directly into pipelines. Where richer tooling is
> useful, dqflow's job is to emit clean, structured results those systems can consume.

## Roadmap

A GitHub Action, HTML reports, severity levels, Polars parity, and PySpark / SQL
engines are all planned. See **[ROADMAP.md](https://github.com/dqflow/dqflow/blob/main/ROADMAP.md)** for the full
plan, priorities, and non-goals.

## Contributing

Issues and pull requests are welcome. See [CONTRIBUTING.md](https://github.com/dqflow/dqflow/blob/main/CONTRIBUTING.md).

```bash
git clone https://github.com/dqflow/dqflow.git
cd dqflow
pip install -e ".[dev]"

pytest              # run tests
ruff check .        # lint
mypy src/dqflow     # type-check
```

## License

[MIT](https://github.com/dqflow/dqflow/blob/main/LICENSE)

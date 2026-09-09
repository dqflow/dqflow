# How dqflow compares

dqflow's job is narrow on purpose: it is the shortest **contract pull-request
gate for in-memory Python DataFrames**. You keep one declarative contract in
version control, validate a pandas or Polars DataFrame against it at runtime, and
run `dq diff` in review to block a contract edit that would reject data your
producers already send.

It is deliberately **not** the largest catalogue of checks, a warehouse-native
engine, or a data-observability platform. The tools below overlap with parts of
that space and are often the better choice — this page says when.

!!! note "Honest by policy"
    Every row states what dqflow does *today*. Declared-but-not-yet-enforced
    fields and experimental engines are called out in
    [dqflow's current limitations](#dqflows-current-limitations) and the
    [ROADMAP](https://github.com/dqflow/dqflow/blob/main/ROADMAP.md). No
    benchmark claims appear here — that is a project non-goal.

## At a glance

| | **dqflow** | **Pandera** | **Great Expectations** | **Soda Core / SodaCL** | **Data Contract CLI** |
| --- | --- | --- | --- | --- | --- |
| Primary model | One contract file (Python or YAML) | Schema in Python (`DataFrameSchema` / `DataFrameModel`) | Expectation Suites held by a stateful Data Context | SodaCL checks in `checks.yml` | ODCS data-contract document |
| Where it runs | In-memory DataFrames | In-memory DataFrames | In-memory **and** SQL warehouses | Mostly SQL warehouses; in-memory via extras | Connects to live sources (warehouses, files, streams) |
| Backends | pandas, Polars *(experimental)* | pandas, Polars, PySpark, Ibis, Dask, Modin, PyArrow, GeoPandas | pandas, Spark, SQL databases | many warehouses, Spark, pandas/Dask extra | many tested data sources (warehouses, files, streams) |
| Contract as a reviewable file | Yes — Python or YAML | Yes — Python, or serialized to YAML/JSON | Suites as JSON/YAML, usually generated | Yes — `checks.yml` | Yes — ODCS YAML |
| Breaking-change diff / gate | **Yes** — `dq diff` classifies each change and exits `1` | No | No | No (verifies a contract, does not diff versions) | **Yes** — `datacontract breaking` / `changelog` |
| Built-in check breadth | Small, fixed set | Large, plus custom + statistical checks | Very large expectation library | Large SodaCL vocabulary | Schema + quality rules from the spec |
| Reporting | Text + JSON (HTML planned) | Raised errors / error report | HTML **Data Docs** | CLI output; rich UI in Soda Cloud | CLI output; HTML export |
| Infrastructure required | None | None | Data Context directory; often a store | Data-source config; Soda Cloud optional | None to run; connects out to sources |
| Standard / spec | dqflow contract schema (`schema_version`) | — | — | Soda data contracts | **Open Data Contract Standard (ODCS)** |

## When another tool fits better

**Prefer [Pandera](https://pandera.readthedocs.io/)** when you want typed schema
models declared inline with your pandas / Polars / PySpark / Dask code and
enforced with `@pa.check_types` decorators, statistical or hypothesis checks, or
synthetic-data generation for property-based tests. Pandera's backend reach is
much wider than dqflow's — though several features (`SeriesSchema`, groupby
checks, hypothesis testing, schema inference) are pandas-only.

**Prefer [Great Expectations](https://greatexpectations.io/)** when you want a
large library of ready-made expectations, browsable HTML Data Docs, validation
against SQL warehouses, or an established stateful project structure that
non-engineers also touch. Its conceptual model (Data Context, Batch Definitions,
Checkpoints) is heavier than a single contract file.

**Prefer [Soda](https://www.soda.io/)** when your data already lives in a
warehouse and you want checks executed there as SQL rather than pulling data into
Python, or when you want the Soda Cloud layer for scheduling, anomaly detection,
and a collaboration UI. Soda Core alone is pipeline-native and has no
observability features.

**Prefer [Data Contract CLI](https://cli.datacontract.com/)** when you are
standardizing on ODCS, need import/export across many formats and tools (dbt,
JSON Schema, Avro, SQL, Terraform…), or must test one contract against many live
data sources. It is a specification and interoperability tool first.

## Where dqflow is the simpler answer

- The check you care about most is **"did this pull request quietly tighten the
  contract?"** — dqflow classifies every change as breaking or non-breaking and
  fails the check with a plain exit code, no service required.
- Your data fits in memory as a pandas or Polars DataFrame and you want
  expectations reviewed in git, not stored in a separate system.
- You want to go from `pip install` to a failing CI check in
  [about ten minutes](../getting-started/first-pr-gate.md) without a Data
  Context, a warehouse connection, or an account.
- You want the base install to stay tiny (`pyyaml` + `click`) with the DataFrame
  backend opt-in.

## dqflow's current limitations

Stated plainly, and tracked on the
[ROADMAP](https://github.com/dqflow/dqflow/blob/main/ROADMAP.md):

- **No column-level custom callable and no timestamp-freshness check.** Logical
  `dtype`, column existence, `not_null`, `min`, `max`, `allowed`, `unique`, and
  regex `pattern` are enforced; row-wise custom logic goes in a callable
  `CrossColumnRule`.
- **The Polars engine is experimental.** The dependency and Python matrix is
  tested ([compatibility matrix](../reference/compatibility.md)), but the API and
  lazy-execution behaviour may still change ([#25](https://github.com/dqflow/dqflow/issues/25)).
- **In-memory only.** No warehouse push-down; a SQL engine and a PySpark engine
  are planned, not available.
- **No HTML reports, severity levels, or official GitHub Action yet**
  ([#42](https://github.com/dqflow/dqflow/issues/42),
  [#43](https://github.com/dqflow/dqflow/issues/43),
  [#44](https://github.com/dqflow/dqflow/issues/44)). Output today is grouped
  text and `--output json`.
- **The rule evaluator is not a security boundary.** Table-rule expressions run
  through a whitelisted AST walker, not `eval`, but you should still never load
  contracts from untrusted sources.
- **The check set is intentionally small.** dqflow is not trying to match the
  expectation catalogue of Great Expectations or the check vocabulary of SodaCL.

## Migrating

- [From Pandera](from-pandera.md) — concept map, a side-by-side example, and what
  does not port yet.

Moving from Great Expectations, Soda, or Data Contract CLI: open a
[Q&A discussion](https://github.com/dqflow/dqflow/discussions) describing your
current setup — migration notes for those tools are being written from real
cases.

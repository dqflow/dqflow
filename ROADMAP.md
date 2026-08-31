# dqflow Roadmap

> **Data contracts for Python data pipelines.**
>
> **Define → Validate → Fail Fast**

dqflow is a small, contract-first library you embed directly into ETL/ELT jobs,
services, and CI. You declare what your data must look like (schema, validity,
freshness, relationships), validate a DataFrame against that contract, and break
the pipeline *before* bad data reaches anything downstream.

This roadmap is the map between the project's direction and its
[GitHub issues](https://github.com/dqflow/dqflow/issues?q=is%3Aissue+label%3Aroadmap).
Every roadmap item is a tracked issue labelled [`roadmap`](https://github.com/dqflow/dqflow/labels/roadmap);
this file groups those issues, sets priorities, and records the dependencies
between them. It is not a separate plan — if an item isn't an issue, it isn't on
the roadmap yet.

---

## Guiding principles

- **Contract-first.** The contract is the source of truth. Validation,
  reporting, inference and diffing all serve the contract.
- **Lightweight.** Few dependencies, small API surface, no daemon, no server, no
  database.
- **Python-native.** Works with what Python data teams already use — pandas,
  Polars, pytest, GitHub Actions, Airflow/Dagster/Prefect, dbt.
- **Fail fast.** Validation failures are actionable and, by default, loud.
- **CI/CD friendly.** Structured output, stable exit codes, machine-readable
  reports, and a real GitHub Action.

---

## Where dqflow is today

Already shipped:

- `Contract` as code (Python) and YAML (`Contract.from_yaml` / `to_yaml`)
- Column checks: `not_null`, `min`, `max`, `allowed`, `unique`
- Column fields defined but **not yet enforced** by engines: `pattern`,
  `freshness_minutes`, `custom` (→ [#51](https://github.com/dqflow/dqflow/issues/51))
- Table rules (`row_count`, `null_rate`, `unique_count`) via a restricted
  expression evaluator (still uses `eval` internally → [#18](https://github.com/dqflow/dqflow/issues/18))
- Cross-column rules (`left`/`op`/`right` or a callable), no `eval` (#28, #29)
- Structured results: `ValidationResult.ok`, `.summary()`, `.to_dict()`
- Engine base class + **pandas** engine (default) and an **experimental Polars**
  engine (`dqflow[polars]`); output-parity tests
- CLI: `dq validate`, `dq show`, `dq infer`, and `dq diff`
  ([#37](https://github.com/dqflow/dqflow/issues/37), shipped in 0.3.0) —
  contract comparison with breaking / non-breaking change classification, text
  and JSON output, and a CI exit code
- `dq validate` output ([#38](https://github.com/dqflow/dqflow/issues/38)) —
  grouped by schema / columns / rules, per-check failure rates and value
  samples, `--quiet` / `--verbose` / `--color`, a standalone text renderer, and
  an unchanged `--output json` schema
- Benchmark scripts in `benchmarks/` (#24, closed) — not yet wired into CI
- Docs site (MkDocs), CI (test matrix, ruff, mypy), PyPI release workflow

---

## Categories

Work is organised into six categories, roughly in priority order. Each maps to a
GitHub milestone.

| Category | Priority | Milestone |
|----------|----------|-----------|
| [Architecture Foundation](#architecture-foundation) | **P0** | [Architecture Foundation](https://github.com/dqflow/dqflow/milestone/2) |
| [Developer Experience](#developer-experience) | **P0** | [Developer Experience](https://github.com/dqflow/dqflow/milestone/3) |
| [Performance & Execution](#performance--execution) | **P1** | [Performance & Execution](https://github.com/dqflow/dqflow/milestone/4) |
| [CI/CD & Reporting](#cicd--reporting) | **P1** | [CI/CD & Reporting](https://github.com/dqflow/dqflow/milestone/5) |
| [Ecosystem & Integrations](#ecosystem--integrations) | **P1 / P2** | [Ecosystem & Integrations](https://github.com/dqflow/dqflow/milestone/6) |
| [Advanced Validation](#advanced-validation) | **P2** | [Advanced Validation](https://github.com/dqflow/dqflow/milestone/7) |

---

## Architecture Foundation

**Priority: P0.** Do this first. The engines currently interpret `Column`
objects directly and each carries its own copy of rule evaluation (including
`eval`). That duplication makes every later feature — new engines, severity,
advanced rules, a shared cache — more expensive. These five issues pay that debt
down, in order.

**Execution order:** [#17](https://github.com/dqflow/dqflow/issues/17) →
[#16](https://github.com/dqflow/dqflow/issues/16) →
[#18](https://github.com/dqflow/dqflow/issues/18) →
[#15](https://github.com/dqflow/dqflow/issues/15) →
[#21](https://github.com/dqflow/dqflow/issues/21)

```
#17 Decouple Contract from Engine
      │
      ├──> #16 ValidationSpec (engine-agnostic IR)
      │        │
      │        ├──> #18 Central RuleEngine (one safe evaluator)
      │        └──> #21 Shared Computation Cache ─┐
      │                                           │
      └──> #15 ExecutionContext ──────────────────┘
                 │
                 └──> Performance & Execution, Ecosystem engines
```

| Issue | Title | Depends on | Blocks |
|-------|-------|------------|--------|
| [#17](https://github.com/dqflow/dqflow/issues/17) | Decouple Contract from Engine Execution | — | #16, #15 |
| [#16](https://github.com/dqflow/dqflow/issues/16) | Introduce ValidationSpec (IR layer) | #17 | #18, #21, #25, #49, #50 |
| [#18](https://github.com/dqflow/dqflow/issues/18) | Extract Central RuleEngine | #16 | #44, #51 |
| [#15](https://github.com/dqflow/dqflow/issues/15) | Introduce ExecutionContext | #17 | #21, #22, #23, #47 |
| [#21](https://github.com/dqflow/dqflow/issues/21) | Shared Computation Cache abstraction | #16, #15 | #23 |

---

## Developer Experience

**Priority: P0.** The everyday loop — write a contract, run it, read the
failure, fix it — is the product. Make it fast and pleasant.

| Issue | Title | Priority | Depends on | Status |
|-------|-------|----------|------------|--------|
| [#37](https://github.com/dqflow/dqflow/issues/37) | Implement `dq diff` for contract comparison | P0 | — | ✅ Shipped in 0.3.0 |
| [#38](https://github.com/dqflow/dqflow/issues/38) | Improve CLI validation output and error messages | P0 | — (benefits from #16) | ✅ Done |
| [#39](https://github.com/dqflow/dqflow/issues/39) | Improve `dq infer` contract generation | P0 | — | ✅ Shipped in 0.2.1 |
| [#40](https://github.com/dqflow/dqflow/issues/40) | Redesign README and project positioning | P0 | — | ✅ Shipped |
| [#41](https://github.com/dqflow/dqflow/issues/41) | Add contract versioning and breaking-change detection | P1 | #37 | Planned |

Covers: `dq diff` + breaking/non-breaking classification, better CLI output and
error messages, smarter `dq infer` (constraints, not just dtypes), README
redesign around "data contracts for Python pipelines", architecture diagram,
quick-start examples.

---

## Performance & Execution

**Priority: P1.** Keep validation cheap enough to run on every pipeline run.
These build on the Architecture Foundation (especially #15 and #21).

| Issue | Title | Priority | Depends on |
|-------|-------|----------|------------|
| [#22](https://github.com/dqflow/dqflow/issues/22) | Expose parallel execution in the CLI | P1 | #15 |
| [#23](https://github.com/dqflow/dqflow/issues/23) | Streaming / chunked validation for large DataFrames | P1 | #15, #21 |
| [#25](https://github.com/dqflow/dqflow/issues/25) | Polars engine: lazy evaluation + promote to supported | P1 | #16 |
| [#45](https://github.com/dqflow/dqflow/issues/45) | Benchmark and track validation performance regressions | P1 | — (extends #24) |

Covers: parallel column validation, memory-efficient chunked/streaming
validation, Polars lazy execution and pandas parity, and a benchmark suite with
committed baselines and CI regression gates.

---

## CI/CD & Reporting

**Priority: P1.** Make dqflow a natural part of a pull-request and pipeline
workflow.

| Issue | Title | Priority | Depends on |
|-------|-------|----------|------------|
| [#42](https://github.com/dqflow/dqflow/issues/42) | Add official GitHub Action | P1 | #38, #37 |
| [#43](https://github.com/dqflow/dqflow/issues/43) | Add HTML validation reports | P1 | #38 |
| [#44](https://github.com/dqflow/dqflow/issues/44) | Add validation severity levels and failure thresholds | P1 | #16, #18 |

Covers: a first-class GitHub Action (PR annotations, pass/fail check, report
artifact), CI-friendly JSON, configurable failure thresholds, contract
validation + `dq diff` in pull requests, self-contained HTML reports, quality
summaries and per-check detail.

---

## Ecosystem & Integrations

**Priority: P1 / P2.** Meet data where it lives, with thin adapters rather than
frameworks. New engines only implement `ValidationSpec` execution (#16) and use
the shared RuleEngine (#18).

| Issue | Title | Priority | Depends on |
|-------|-------|----------|------------|
| [#46](https://github.com/dqflow/dqflow/issues/46) | Improve documentation and examples | P1 | — (✅ shipped; ongoing) |
| [#47](https://github.com/dqflow/dqflow/issues/47) | Add Airflow, Dagster and Prefect integrations | P1 | #17, #15, #44 |
| [#48](https://github.com/dqflow/dqflow/issues/48) | Add dbt integration | P2 | — |
| [#49](https://github.com/dqflow/dqflow/issues/49) | Add PySpark engine | P2 | #16, #18, #15 |
| [#50](https://github.com/dqflow/dqflow/issues/50) | Add SQL validation support | P2 | #16, #18, #15 |

Covers: full API docs and runnable example projects, orchestrator adapters
(fail-the-task on violation), a contract ⇄ dbt bridge, native PySpark and SQL
(push-down) engines, a FastAPI example, contribution guide, issue templates,
release/changelog/PyPI automation, GitHub Discussions.

---

## Advanced Validation

**Priority: P2.** More expressive checks — still declarative, still no arbitrary
`eval`.

| Issue | Title | Priority | Depends on |
|-------|-------|----------|------------|
| [#51](https://github.com/dqflow/dqflow/issues/51) | Add advanced validation rules | P2 | #16, #18, #44 |

Covers: enforce the already-defined `pattern` / `freshness_minutes` / `custom`
fields, referential integrity, distribution checks, absolute and relative
row-count checks, `duplicate_rate` and other documented helpers, and a
contract-level custom-validator hook. Severity levels (#44) apply throughout.

---

## Priority summary

| Priority | Focus | Issues |
|----------|-------|--------|
| **P0** | Architecture foundation, then contract diffing, developer-friendly CLI, contract inference, README/positioning | #17, #16, #18, #15, #21, #37, #38, #39, #40 |
| **P1** | Contract versioning, GitHub Action, HTML reports, severity levels, Polars, performance, docs, orchestrator integrations | #41, #42, #43, #44, #22, #23, #25, #45, #46, #47 |
| **P2** | dbt, PySpark, SQL, advanced validation rules | #48, #49, #50, #51 |

The most important near-term work is the Architecture Foundation and the P0
Developer Experience issues. Everything else is explicitly lower priority.

---

## Non-Goals

dqflow is intentionally **not** trying to become:

- **A full data observability platform.** No metric-collection service, no
  anomaly-detection layer, no lineage graph.
- **A hosted monitoring dashboard.** dqflow produces files and exit codes, not a
  web app you log into.
- **An incident-management platform.** No alerting-rules engine, on-call
  routing, or ticketing.
- **A replacement for enterprise data platforms.** dqflow does not manage
  storage, cataloguing, access control, or orchestration.
- **A massive database-connector ecosystem.** A few well-supported engines
  (pandas, Polars, Spark, SQL) beat dozens of shallow ones.

Where features in these areas are useful, dqflow's job is to emit clean,
structured results (`to_dict()`, JSON, HTML) that those systems consume — not to
reimplement them.

### How dqflow differentiates

- **Lightweight design** — embeddable, few dependencies, no infrastructure
- **Contract-first architecture** — one declarative artifact drives everything
- **Developer experience** — the write/run/read/fix loop is the product
- **Python-native workflows** — pandas/Polars/pytest/GitHub Actions, not a DSL
- **CI/CD friendliness** — structured output, stable exit codes, a real Action

---

## Notes

- Categories are ordered by priority, not locked to release numbers. Items may
  be reprioritised based on adoption and community input.
- Existing issues that predate this roadmap are kept and mapped in, not closed.
- Experimental features are marked as such in the docs and `__init__`.
- The canonical, always-current view is the
  [`roadmap` label](https://github.com/dqflow/dqflow/issues?q=is%3Aissue+label%3Aroadmap)
  and the [milestones](https://github.com/dqflow/dqflow/milestones).

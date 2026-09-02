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
- **Adoption is a product concern.** Discovery, time-to-first-value, retention,
  and contribution are measured with the same discipline as code.

## Adoption thesis

dqflow's wedge is the shortest, clearest **contract pull-request gate for Python
DataFrames**, not the largest catalogue of checks or connectors:

```text
infer → review → diff → validate → block a breaking change in the PR
```

The activation promise is a versioned contract and an actionable failed CI check
in under ten minutes, without deploying a server. Architecture and activation
work therefore run in parallel.

### Baseline (2026-08-31)

- 4 GitHub stars, 1 fork, and 2 code contributors
- 222 PyPI downloads in the previous 30 days; downloads are a reach proxy, not
  unique users, and include release/automation traffic
- no active-user definition, adoption dashboard, or conversion funnel yet

Issue [#60](https://github.com/dqflow/dqflow/issues/60) defines the north-star
metric. Until it lands, “one million users” is a direction rather than a valid
execution metric. One million monthly downloads can be a provisional reach
milestone only when paired with active-project, retention, and contributor data.

| Stage | Product proof | Reach proxy | Community proof |
|-------|---------------|-------------|-----------------|
| Activation | First failed PR gate in <10 minutes | 1k monthly downloads | 10 external adopter interviews |
| Repeatability | Contracts retained across releases | 10k monthly downloads | 25 public examples, 10 contributors |
| Ecosystem | Integrations generate inbound adoption | 100k monthly downloads | 250 public dependents, 50 contributors |
| Scale | Self-serve acquisition compounds | 1M monthly downloads | active-project target defined by #60 |

---

## Where dqflow is today

Already shipped:

- `Contract` as code (Python) and YAML (`Contract.from_yaml` / `to_yaml`)
- Column checks: `not_null`, `min`, `max`, `allowed`, `unique`
- Column fields defined but **not yet enforced** by engines: `dtype`,
  `freshness_minutes`, `custom`; `pattern` is enforced
  (→ [#51](https://github.com/dqflow/dqflow/issues/51))
- Table rules (`row_count`, `null_rate`, `unique_count`) via a shared
  whitelisted-AST evaluator, `dqflow.rules.evaluate_rule` — no `eval`
  ([#18](https://github.com/dqflow/dqflow/issues/18), 0.4.0)
- Cross-column rules (`left`/`op`/`right` or a callable), no `eval` (#28, #29)
- Structured results: `ValidationResult.ok`, `.summary()`, `.to_dict()`
- Architecture Foundation: `Contract` decoupled from engines
  with an engine registry ([#17](https://github.com/dqflow/dqflow/issues/17)), a
  contract compiles once to an engine-agnostic `ValidationSpec`
  ([#16](https://github.com/dqflow/dqflow/issues/16)), table-rule statistics
  come from a shared lazy `StatsCache`
  ([#21](https://github.com/dqflow/dqflow/issues/21)) (all 0.4.0), and a run's
  engine / cache / execution flags are carried in one `ExecutionContext`
  ([#15](https://github.com/dqflow/dqflow/issues/15))
- Engine base class + **pandas** engine (default) and an **experimental Polars**
  engine (`dqflow[polars]`), selectable via `dq validate --engine` or
  `Contract.validate(df, engine=...)`; output-parity tests
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

Work is organised into eight categories. Architecture and activation run in
parallel; later categories begin when their dependencies are ready.

| Category | Priority | Milestone |
|----------|----------|-----------|
| [Adoption & Community](#adoption--community) | **P0** | Adoption & Community |
| [Architecture Foundation](#architecture-foundation) | **P0** | [Architecture Foundation](https://github.com/dqflow/dqflow/milestone/2) |
| [Developer Experience](#developer-experience) | **P0** | [Developer Experience](https://github.com/dqflow/dqflow/milestone/3) |
| [Reliability & Trust](#reliability--trust) | **P0 / P1** | Reliability & Trust |
| [Performance & Execution](#performance--execution) | **P1** | [Performance & Execution](https://github.com/dqflow/dqflow/milestone/4) |
| [CI/CD & Reporting](#cicd--reporting) | **P1** | [CI/CD & Reporting](https://github.com/dqflow/dqflow/milestone/5) |
| [Ecosystem & Integrations](#ecosystem--integrations) | **P1 / P2** | [Ecosystem & Integrations](https://github.com/dqflow/dqflow/milestone/6) |
| [Advanced Validation](#advanced-validation) | **P2** | [Advanced Validation](https://github.com/dqflow/dqflow/milestone/7) |

---

## Adoption & Community

**Priority: P0.** Measure public project health, lead with the shipped contract
diff story, then improve discovery and run small measurable launches. No runtime
telemetry is added.

| Issue | Title | Priority | Depends on |
|-------|-------|----------|------------|
| [#60](https://github.com/dqflow/dqflow/issues/60) | Define adoption metrics and publish a privacy-safe project health dashboard | P0 | — |
| [#62](https://github.com/dqflow/dqflow/issues/62) | Build repository discoverability and a repeatable community growth loop | P0 | #60 |
| [#69](https://github.com/dqflow/dqflow/issues/69) | Make contract diff a headline README and docs story | P0 | #37 (shipped); measure with #60 |

Covers: the active-user definition and funnel, repository metadata and community
workflows, honest comparison/migration pages, and a canonical `dq diff` demo that
blocks a breaking contract change in CI.

---

## Architecture Foundation

**Priority: P0.** Started early, in parallel with activation. The engines used to
interpret `Column` objects directly and each carried its own copy of rule
evaluation (including `eval`). That duplication made every later feature — new
engines, severity, advanced rules, a shared cache — more expensive. Four of the
five issues shipped in **0.4.0**; `ExecutionContext` (#15) followed and the
category is now complete.

**Execution order:** [#17](https://github.com/dqflow/dqflow/issues/17) →
[#16](https://github.com/dqflow/dqflow/issues/16) →
[#18](https://github.com/dqflow/dqflow/issues/18) →
[#15](https://github.com/dqflow/dqflow/issues/15) →
[#21](https://github.com/dqflow/dqflow/issues/21)

```
#17 Decouple Contract from Engine        ✅ 0.4.0
      │
      ├──> #16 ValidationSpec (IR)        ✅ 0.4.0
      │        │
      │        ├──> #18 Central rule evaluator, no eval   ✅ 0.4.0
      │        └──> #21 Shared computation cache ─┐        ✅ 0.4.0
      │                                           │
      └──> #15 ExecutionContext ──────────────────┘        ✅ Unreleased
                 │
                 └──> Performance & Execution, Ecosystem engines
```

| Issue | Title | Depends on | Blocks | Status |
|-------|-------|------------|--------|--------|
| [#17](https://github.com/dqflow/dqflow/issues/17) | Decouple Contract from Engine Execution | — | #16, #15 | ✅ 0.4.0 |
| [#16](https://github.com/dqflow/dqflow/issues/16) | Introduce ValidationSpec (IR layer) | #17 | #18, #21, #25, #49, #50 | ✅ 0.4.0 |
| [#18](https://github.com/dqflow/dqflow/issues/18) | Extract central rule evaluator | #16 | #44, #51 | ✅ 0.4.0 |
| [#15](https://github.com/dqflow/dqflow/issues/15) | Introduce ExecutionContext | #17 | #21, #22, #23, #47 | ✅ Unreleased |
| [#21](https://github.com/dqflow/dqflow/issues/21) | Shared Computation Cache abstraction | #16, #15 | #23 | ✅ 0.4.0 |

> #21 shipped before #15 with the cache always on. #15 adds the on/off switch
> (`ExecutionContext(cache=...)`); cache size limits remain future work.

---

## Developer Experience

**Priority: P0.** The everyday loop — write a contract, run it, read the
failure, fix it — is the product. Make it fast and pleasant.

**Activation slice:** [#61](https://github.com/dqflow/dqflow/issues/61) →
[#38](https://github.com/dqflow/dqflow/issues/38) →
[#42](https://github.com/dqflow/dqflow/issues/42), followed by pytest integration
[#64](https://github.com/dqflow/dqflow/issues/64).

| Issue | Title | Priority | Depends on | Status |
|-------|-------|----------|------------|--------|
| [#37](https://github.com/dqflow/dqflow/issues/37) | Implement `dq diff` for contract comparison | P0 | — | ✅ Shipped in 0.3.0 |
| [#38](https://github.com/dqflow/dqflow/issues/38) | Improve CLI validation output and error messages | P0 | — (benefits from #16) | ✅ Done |
| [#39](https://github.com/dqflow/dqflow/issues/39) | Improve `dq infer` contract generation | P0 | — | ✅ Shipped in 0.2.1 |
| [#40](https://github.com/dqflow/dqflow/issues/40) | Redesign README and project positioning | P0 | — | ✅ Shipped |
| [#61](https://github.com/dqflow/dqflow/issues/61) | Add a versioned contract schema and `dq lint` | P0 | — (align with #16, #41) | Planned |
| [#41](https://github.com/dqflow/dqflow/issues/41) | Add contract versioning and breaking-change detection | P1 | #37 | Planned |
| [#64](https://github.com/dqflow/dqflow/issues/64) | Add a first-class pytest integration | P1 | #38 | Planned |

Covers: `dq diff` + breaking/non-breaking classification, better CLI output and
error messages, smarter `dq infer` (constraints, not just dtypes), a versioned
contract schema and lint command, pytest-native assertions, and quick-start
examples.

---

## Reliability & Trust

**Priority: P0 / P1.** A production pipeline gate needs explicit compatibility,
security, and stability boundaries. These issues form the path from alpha to a
credible 1.0.

| Issue | Title | Priority | Depends on |
|-------|-------|----------|------------|
| [#65](https://github.com/dqflow/dqflow/issues/65) | Harden packaging and the supported compatibility matrix | P0 | — (benefits from #17) |
| [#67](https://github.com/dqflow/dqflow/issues/67) | Define the stable public API and dqflow 1.0 readiness bar | P0 | #61 |
| [#66](https://github.com/dqflow/dqflow/issues/66) | Add supply-chain security and verifiable release provenance | P1 | coordinates with #18, #61 |

Covers: supported Python/pandas/Polars versions, cross-platform and built-wheel
CI, backend-specific lightweight installs, API/CLI/JSON compatibility,
deprecation policy, `SECURITY.md`, pinned Actions, attestations, and SBOMs.

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
frameworks. New engines only implement `ValidationSpec` execution (#16), reuse
the shared rule evaluator (#18) and `StatsCache` (#21), and register through
`dqflow.engines.register_engine` (#17).

| Issue | Title | Priority | Depends on |
|-------|-------|----------|------------|
| [#46](https://github.com/dqflow/dqflow/issues/46) | Improve documentation and examples | P1 | — (✅ shipped; ongoing) |
| [#47](https://github.com/dqflow/dqflow/issues/47) | Add Airflow, Dagster and Prefect integrations | P1 | #17, #15, #44 |
| [#63](https://github.com/dqflow/dqflow/issues/63) | Add ODCS import/export interoperability | P1 | #61 |
| [#48](https://github.com/dqflow/dqflow/issues/48) | Add dbt integration | P2 | — |
| [#49](https://github.com/dqflow/dqflow/issues/49) | Add PySpark engine | P2 | #16, #18, #15 |
| [#50](https://github.com/dqflow/dqflow/issues/50) | Add SQL validation support | P2 | #16, #18, #15 |

Covers: full API docs and runnable examples, orchestrator adapters, loss-aware
ODCS interoperability, a contract ⇄ dbt bridge, native PySpark and SQL
(push-down) engines, and a FastAPI example.

---

## Advanced Validation

**Priority: P2.** More expressive checks — still declarative, still no arbitrary
`eval`.

| Issue | Title | Priority | Depends on |
|-------|-------|----------|------------|
| [#51](https://github.com/dqflow/dqflow/issues/51) | Add advanced validation rules | P2 | #16, #18, #44 |

Covers: enforce the already-defined `dtype` / `freshness_minutes` / `custom`
fields (`pattern` already runs), referential integrity, distribution checks, absolute and relative
row-count checks, `duplicate_rate` and other documented helpers, and a
contract-level custom-validator hook. Severity levels (#44) apply throughout.

---

## Priority summary

| Priority | Focus | Issues |
|----------|-------|--------|
| **P0** | Measure adoption; lead with contract diff; ship activation/trust alongside architecture | #60, #62, #69, #61, #65, #67, #17, #16, #18, #15, #21, #38 |
| **P1** | PR/test workflows, reporting, security, performance, ODCS and orchestrators | #64, #66, #41, #42, #43, #44, #22, #23, #25, #45, #46, #47, #63 |
| **P2** | dbt, PySpark, SQL, advanced validation rules | #48, #49, #50, #51 |

The most important near-term work is a measured activation slice and the minimum
architecture/reliability foundation needed to support it. Breadth should not
outrun evidence that new users activate and retained teams keep using contracts.

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

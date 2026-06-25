# dqflow Roadmap

This document defines the planned evolution of dqflow across versioned milestones.

dqflow aims to evolve into a lightweight, high-performance, and extensible data contract engine while maintaining simplicity and embeddability.

---

# Version 0.2 — Performance , Scalability & Visual Identity

Focus: Improve execution speed and scalability for large datasets.

## Core Engine Performance

- [ ] Add parallel column validation (ThreadPoolExecutor)
- [ ] Optimize PandasEngine (reduce redundant computations)
- [ ] Introduce shared computation cache across column checks
- [ ] Improve memory efficiency for large DataFrames

## New Execution Engine

- [ ] Add PolarsEngine for high-performance validation
- [ ] Support `pl.DataFrame` and `pl.LazyFrame`
- [ ] Enable lazy evaluation for optimized execution
- [ ] Add optional dependency: `dqflow[polars]`

## Benchmarking Framework

- [ ] Benchmark suite comparing pandas vs polars engines
- [ ] Performance metrics across:
  - row count scaling
  - column count scaling
  - rule complexity scaling

  ## Visual Identity

- [ ] Logo and visual identity


---

# Version 0.3 — Rule System & Expressiveness

Focus: Improve flexibility and safety of rule definitions.

## Rule Engine

- [ ] Replace unsafe `eval()` with a safe expression parser
- [ ] Validate rule syntax before execution
- [ ] Introduce typed rule context objects
- [ ] Add rule validation and linting support

## Built-in Rule Library

- [ ] row_count
- [ ] null_rate
- [ ] duplicate_rate
- [ ] uniqueness constraints

## Advanced Validation

- [ ] Cross-column validation support
- [ ] Multi-field dependency rules

---

# Version 0.4 — Integrations & Pipeline Support

Focus: Extend dqflow into modern data stack ecosystems.

## Data Platform Integrations

- [ ] PySparkEngine
- [ ] SQL engines (PostgreSQL, BigQuery)
- [ ] dbt integration (run contracts as tests)
- [ ] dlt integration (validation during ingestion)

## Pipeline Features

- [ ] Incremental validation mode
- [ ] Backfill-aware validation
- [ ] Streaming-friendly validation hooks

---

# Version 0.5 — Observability & Reporting

Focus: Turn validation results into actionable insights.

## Metrics & Observability

- [ ] Prometheus exporter
- [ ] Data quality metrics (fail rate, null rate, drift tracking)
- [ ] Time-series tracking of validation results

## Output Formats

- [ ] Standardized JSON output (`to_dict`, `to_json`)
- [ ] CSV export for CI/CD pipelines
- [ ] HTML report generation
- [ ] Optional PDF reporting
- [ ] CLI formatting modes (table, json, summary)

## Extensibility

- [ ] Pluggable report writer interface

---

# Version 0.6 — Developer Experience

Focus: Improve usability, onboarding, and debugging.

## CLI & UX

- [ ] Improve CLI experience (interactive mode)
- [ ] Better validation summaries
- [ ] Contract auto-generation from DataFrames
- [ ] Schema inference improvements

## Debugging Tools

- [ ] Explain failed rules with trace output
- [ ] Sample failing rows per check
- [ ] Column-level profiling reports

## Contract Tools

- [ ] Contract diff tool (compare versions)

---

# Version 0.7 — Ecosystem & Branding

Focus: Establish dqflow as a recognizable open-source project.

## Documentation

- [ ] MkDocs redesign
- [ ] Interactive examples and notebooks
- [ ] Architecture diagrams

## Ecosystem

- [ ] Plugin system for custom engines
- [ ] Community check registry
- [ ] Example repository with real-world pipelines

# Branding Upgrade
- [ ] Landing page improvements
- [ ] Use-case driven tutorials

---

# Long-Term Vision

dqflow is NOT a full observability platform.

Instead, it focuses on:

- Lightweight validation
- Fast execution
- Embeddable contracts
- Developer-first design

Inspired by tools like Great Expectations, but intentionally simpler.

---

# Contribution Focus Areas

High-impact contribution areas:

- Engine performance (pandas, polars)
- Rule engine safety and extensibility
- Integration ecosystem (dbt, spark, sql)
- CLI and developer experience
- Benchmarking and testing
- Documentation and tutorials

---

# Notes

- Roadmap is flexible and may evolve based on community input
- Features may be reprioritized based on adoption
- Experimental features will be clearly marked
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `dq lint CONTRACT` — validate a contract file's structure without reading any
  data. Reports unknown fields, wrong types, invalid regexes, contradictory
  bounds, unparseable table rules, bad cross-column operators, and an unsupported
  schema version, each with a document path (`columns.amount.min`) and a line
  number. `--output json` for machine-readable diagnostics; `--strict` to fail on
  warnings; exit `1` on errors ([#61](https://github.com/dqflow/dqflow/issues/61))
- Contracts declare a `schema_version` (`"1.0"`). `Contract.to_yaml()` and
  `dq infer` always write it; reading a file without one assumes the current
  version with a warning. A `MAJOR.MINOR` compatibility policy governs what older
  and newer files this release will load — see the *Schema versioning* guide
  ([#61](https://github.com/dqflow/dqflow/issues/61))
- `dqflow.schema` — `lint_contract_file()` / `lint_contract_data()`, the
  `Diagnostic` record, and typed exceptions `ContractError`,
  `ContractParseError`, `ContractSchemaError` (carries `.diagnostics`),
  `ContractVersionError`
- A JSON Schema for the contract format is published at
  `https://dqflow.github.io/dqflow/schema/contract-1.0.json` (and printed by
  `dq schema`; `dqflow.schema.contract_json_schema()`) for editor autocompletion
  via a `$schema` key or a `# yaml-language-server:` modeline. It is a subset of
  `dq lint` — no cross-field checks — see the *Editor integration* guide
  ([#61](https://github.com/dqflow/dqflow/issues/61))
- `dqflow.execution.ExecutionContext` — a frozen dataclass that carries the
  runtime configuration for one `Contract.validate()` call: `engine`, `cache`,
  and the reserved `parallel` / `max_workers` / `strict` / `fail_fast` flags.
  `Contract.validate(df, context=ExecutionContext(...))` is the full form;
  `engine=` stays as a shortcut (the two are mutually exclusive). `dq validate`
  builds the context from `--engine`
  ([#15](https://github.com/dqflow/dqflow/issues/15))
- `ExecutionContext(cache=False)` / `StatsCache(..., memoize=False)` disables
  memoisation of table-rule statistics — the cache on/off switch the shared
  `StatsCache` deferred to #15. Cache size limits remain future work
- Public API: `ExecutionContext`, `Engine`, `ValidationSpec`, `StatsCache`,
  `evaluate_rule`, `get_engine`, `register_engine`, and `available_engines` are
  now importable directly from `dqflow`
- A published compatibility policy — the *Stability & compatibility* reference
  page defines the covered surfaces (the `dqflow` / `dqflow.schema` API, the `dq`
  CLI and its exit codes, the `--output json` payloads), a SemVer / deprecation
  policy, and a tracked 1.0 readiness checklist. `tests/test_public_api.py`
  snapshots those surfaces and fails CI on any accidental drift; regenerate the
  snapshot with `python -m tests.api_surface.collect`
  ([#67](https://github.com/dqflow/dqflow/issues/67))

### Changed
- `Contract.from_yaml()` validates the document against the contract schema
  before construction. A malformed or structurally invalid contract now raises a
  typed `ContractError` with an actionable message instead of a raw
  `TypeError` / `AttributeError` / `yaml` traceback; `dq validate`, `dq show` and
  `dq diff` print that message and point at `dq lint`. Unknown fields — at the
  top level or on a column — are now rejected (`metadata:` remains the escape
  hatch) ([#61](https://github.com/dqflow/dqflow/issues/61))
- `Engine.validate()` takes a keyword-only `context: ExecutionContext | None`
  instead of `**kwargs`. The previously accepted no-op `parallel` /
  `max_workers` keyword arguments are removed — pass them through an
  `ExecutionContext`. Only affects code calling an engine's `validate()`
  directly

## [0.4.0] - 2026-09-02

The Architecture Foundation refactor: a contract now compiles once to an
engine-agnostic `ValidationSpec`, table rules run through one shared evaluator
(no `eval`), and their statistics come from one shared cache. Engines are
selected through a registry. Behaviour and the `--output json` schema are
unchanged apart from the one fix noted below.

### Added
- Engine registry — `dqflow.engines.get_engine()`, `register_engine()`, and
  `available_engines()`. `Contract.validate(df, engine=...)` accepts an engine
  name (`"pandas"` / `"polars"`), an `Engine` instance, or `None`;
  `dq validate --engine pandas|polars` selects the engine from the CLI; and
  `Contract` no longer imports any engine
  ([#17](https://github.com/dqflow/dqflow/issues/17))
- `dqflow.spec.ValidationSpec` — the engine-agnostic intermediate representation
  a contract compiles to. `Contract.validate()` compiles once via
  `ValidationSpec.from_contract()`; the pandas and Polars engines execute the
  spec's flat, ordered `CheckSpec` list instead of interpreting `Column` objects.
  `Engine.validate()` accepts a `Contract` or a prebuilt `ValidationSpec`
  ([#16](https://github.com/dqflow/dqflow/issues/16))
- `dqflow.rules.evaluate_rule` — one shared table-rule evaluator for every
  engine. Expressions are parsed with `ast` and run through a strict node
  whitelist (`row_count`, `null_rate()`, `unique_count()`, literals, boolean and
  arithmetic operators, comparisons); **`eval` is gone** from the pandas and
  Polars engines ([#18](https://github.com/dqflow/dqflow/issues/18))
- `dqflow.cache.StatsCache` — one shared, lazy, memoized cache for the
  `row_count` / `null_rate` / `unique_count` statistics table rules use. Each
  engine supplies three primitives; a column referenced by several rules is
  scanned once, and columns no rule mentions are never scanned
  ([#21](https://github.com/dqflow/dqflow/issues/21))
- `dq validate` text output is now grouped (schema / columns / table rules /
  cross-column rules) with per-group pass/fail counts, a failure rate per check,
  and a bounded sample of the offending values. Colour is used on a TTY and
  disabled when piped or when `NO_COLOR` is set; `--color` / `--no-color`
  overrides the detection ([#38](https://github.com/dqflow/dqflow/issues/38))
- `dq validate --quiet` (only failures) and `--verbose` (every check)
- `dqflow.report.render_result()` — the text renderer, a standalone presentation
  layer with no engine dependencies
- Failing `CheckResult.details` now carry `null_rate`, `violating_rows`,
  `violating_rate`, `failing_rate`, `sample_invalid_values`,
  `sample_duplicate_values`, and `invalid_value_count` where applicable

### Changed
- Engine `message` strings now always name the column and the expectation
  (e.g. `Column 'amount' has 2 values below the minimum 0`). The top-level
  `--output json` schema is unchanged; only `details` gained fields
- `null_rate()` in a table rule is now `0.0` (not `NaN`) on an empty DataFrame
  in the pandas engine, matching the Polars engine
  ([#21](https://github.com/dqflow/dqflow/issues/21))

## [0.3.0] - 2026-08-31

### Added
- `dq diff OLD NEW` and `dqflow.diff.diff_contracts()` — compare two contract
  versions and classify every change as breaking or non-breaking for data
  producers. Text and `--output json` output, a stable JSON schema, a non-zero
  exit on breaking changes with `--allow-breaking` to override, a documented
  breaking-change classification table, and an `examples/contract-diff` project
- `dqflow.contract.column_to_dict()` helper, shared by `Contract.to_yaml()` and
  the diff

### Fixed
- `dqflow.__version__` and `dq --version` still reported `0.2.1` after `0.2.2`
  shipped; the package version is now bumped consistently across
  `pyproject.toml` and `src/dqflow/__init__.py`
- Removed the stale duplicate `__version__` and re-exports in `dqflow.engines`

## [0.2.2] - 2026-08-31

### Added
- Generated API reference for contracts, columns, results, engines, and inference
- Task-oriented guides and four self-contained runnable example projects
- Strict MkDocs build in CI and a contributor setup script
- Optional `parquet` extra for CLI Parquet input

### Fixed
- README and docs now distinguish enforced `pattern` checks from the currently
  descriptive `dtype`, `freshness_minutes`, and `custom` fields
- Documented the current table-rule evaluator safety boundary and exact
  `--fail-fast` behavior
- Removed stale rule examples and corrected table-rule column syntax

## [0.2.1] - 2026-08-28

### Fixed
- README/docs rendering on PyPI: logo pointed at the dark-mode (white) artwork and
  was invisible on PyPI's white background; now uses the light-mode artwork
- Replaced Mermaid diagrams with plain-text diagrams so they render on PyPI and in
  any Markdown viewer
- Absolute links to `ROADMAP.md` / `CONTRIBUTING.md` / `LICENSE` in the README so
  they work from the PyPI project page
- Switched the PyPI version badge to shields.io

## [0.2.0] - 2026-08-28

### Added
- Experimental **Polars** validation engine — `pip install "dqflow[polars]"`,
  `PolarsEngine`, accepts `polars.DataFrame` / `LazyFrame`
- **Cross-column rules** via `CrossColumnRule` (now exported from `dqflow`):
  structured `left` / `op` / `right` comparisons or a callable, in Python and YAML,
  evaluated with no `eval`
- `unique` column constraint
- `Engine` base class and a standardized engine interface;
  `Contract.validate(df, engine=...)` to pick an engine explicitly
- `unique_count('column')` helper in table-rule expressions
- Benchmarking framework under `benchmarks/` for comparing engine performance
- Project [`ROADMAP.md`](ROADMAP.md) and a redesigned README and docs landing page
- Visual identity / logo

### Changed
- pandas engine performance: shared statistics cache, fewer passes over the data
- Rule expressions require column names as string literals
  (`null_rate('amount')`, not `null_rate(amount)`)
- Pinned CI `ruff` to match `.pre-commit-config.yaml`

### Notes
- `Column` accepts `dtype`, `freshness_minutes`, and `custom`, but the engines do
  not yet validate data against them; `pattern` is enforced

## [0.1.3] - 2025-01-31

### Added
- GitHub Actions CI/CD pipeline
- Automated PyPI publishing on release
- README badges (PyPI, CI, Python versions, License)
- RELEASING.md guide

### Fixed
- JSON serialization for numpy boolean types in `to_dict()`

## [0.1.1] - 2025-01-31

### Changed
- Updated GitHub repository URLs

## [0.1.0] - 2025-01-31

### Added
- Initial release
- Contract-as-code with Python API
- YAML contract support
- Column-level validations: not_null, min, max, allowed values, freshness
- Table-level rules: row_count, null_rate, unique_count, duplicate_rate
- Pandas validation engine
- CLI commands: `dq validate`, `dq show`, `dq infer`
- Structured validation results with JSON output

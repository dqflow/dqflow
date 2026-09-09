# Changelog

The complete release history lives in
[`CHANGELOG.md`](https://github.com/dqflow/dqflow/blob/main/CHANGELOG.md).

## Unreleased

- **Fixed** the Polars engine now applies a `pattern` constraint as a full match
  (like the pandas engine and `re.fullmatch`), not a substring search. An
  unanchored pattern such as `\d{3}` no longer wrongly passes `"abc123"`.
- **Removed** `Column.freshness_minutes` and `Column.custom` — declared-only
  fields that no engine enforced. `freshness_minutes` is now rejected as an
  unknown key by `dq lint` and `Contract.from_yaml`; drop it from contract
  files. Use a callable [`CrossColumnRule`](guide/custom-checks.md) for row-wise
  custom logic. `dq diff` no longer classifies `freshness_minutes` changes.

## 0.5.0 — 2026-09-07

- Declared dtypes are enforced consistently in pandas and Polars using five
  backend-independent logical type families. Dtype checks include expected and
  actual types in structured output; unknown names remain backward-compatible
  on load and produce a lint warning ([#51](https://github.com/dqflow/dqflow/issues/51)).
- Discoverability and community infrastructure: GitHub issue forms and a PR
  template, a Code of Conduct, RFC/Roadmap discussion forms, an honest
  [comparison guide](comparison/index.md) (Pandera, Great Expectations, Soda,
  Data Contract CLI) with a [Pandera migration path](comparison/from-pandera.md),
  the copyable `examples/first-pr-gate/` starter and its
  [10-minute tutorial](getting-started/first-pr-gate.md), and a
  [community section](community/index.md) covering the adoption funnel, a launch
  playbook, and maintainer response expectations
  ([#62](https://github.com/dqflow/dqflow/issues/62)).
- Python 3.11–3.14 and bounded pandas, Polars, and PyArrow versions now have a
  published compatibility matrix and release-blocking CI. pandas is now an
  optional backend: migrate `pip install dqflow` to `pip install
  "dqflow[pandas]"`; use `dqflow[pandas-parquet]` for pandas Parquet files.
  Polars-only installations no longer install pandas ([#65](https://github.com/dqflow/dqflow/issues/65)).
- Contract diff is now a headline end-to-end story with exact CLI output, a
  producer-oriented explanation, a copyable pull-request gate, and a reusable
  visual ([#69](https://github.com/dqflow/dqflow/issues/69)).
- Documentation is now built and versioned by Read the Docs. Public documentation
  links and the published contract schema URL now use
  `https://dqflow.readthedocs.io/en/latest/` ([#76](https://github.com/dqflow/dqflow/issues/76)).
- `dq lint CONTRACT` — validate a contract file without reading data. Path- and
  line-aware diagnostics for unknown fields, wrong types, bad regexes,
  contradictory bounds, unparseable rules, and an unsupported schema version;
  `--output json`, `--strict`, exit `1` on errors
  ([#61](https://github.com/dqflow/dqflow/issues/61)).
- Contracts carry a `schema_version` (`"1.0"`), always written by `to_yaml()` /
  `dq infer`; a `MAJOR.MINOR` compatibility policy governs cross-version loading.
  See [Schema versioning](guide/schema-versioning.md).
- `Contract.from_yaml()` validates before construction and raises a typed
  `dqflow.schema.ContractError` (`ContractParseError` / `ContractSchemaError` /
  `ContractVersionError`) instead of a traceback; unknown fields are rejected.
- `dqflow.schema` — `lint_contract_file` / `lint_contract_data`, `Diagnostic`,
  and the error classes.
- A published JSON Schema for the contract format
  (`https://dqflow.readthedocs.io/en/latest/schema/contract-1.0.json`, `dq schema`,
  `dqflow.schema.contract_json_schema()`) for editor autocompletion — see
  [Editor integration](guide/editor-integration.md). A subset of `dq lint`.
- `dqflow.execution.ExecutionContext` — a frozen dataclass carrying a run's
  engine, cache toggle, and reserved execution flags
  (`parallel` / `max_workers` / `strict` / `fail_fast`).
  `Contract.validate(df, context=ExecutionContext(...))` is the full form;
  `engine=` remains a shortcut, and `dq validate --engine` builds the context
  ([#15](https://github.com/dqflow/dqflow/issues/15)).
- `ExecutionContext(cache=False)` disables memoisation of table-rule statistics
  (the `StatsCache` on/off switch deferred to #15).
- `ExecutionContext`, `Engine`, `ValidationSpec`, `StatsCache`, `evaluate_rule`,
  `get_engine`, `register_engine` and `available_engines` are now importable
  straight from `dqflow`.
- `Engine.validate()` now takes a keyword-only `context` argument instead of
  `**kwargs`; the old no-op `parallel` / `max_workers` keywords are gone (pass an
  `ExecutionContext` instead).

## 0.4.0 — 2026-09-02

The Architecture Foundation refactor. Behaviour and the `--output json` schema
are unchanged (apart from the empty-frame `null_rate` fix below).

- Engine registry (`dqflow.engines.get_engine` / `register_engine`).
  `Contract.validate(df, engine=...)` accepts an engine name or instance,
  `dq validate --engine pandas|polars` selects it from the CLI, and `Contract`
  no longer imports an engine ([#17](https://github.com/dqflow/dqflow/issues/17)).
- `dqflow.spec.ValidationSpec` — contracts compile to an engine-agnostic
  intermediate representation, and the pandas and Polars engines execute that
  spec rather than reading `Column` objects
  ([#16](https://github.com/dqflow/dqflow/issues/16)).
- `dqflow.rules.evaluate_rule` — a single whitelisted-AST evaluator for table
  rules shared by every engine; the pandas and Polars engines no longer call
  `eval` ([#18](https://github.com/dqflow/dqflow/issues/18)).
- `dqflow.cache.StatsCache` — a shared, lazy, memoized cache for the statistics
  table rules use; each engine supplies three primitives and a column is scanned
  at most once ([#21](https://github.com/dqflow/dqflow/issues/21)).
- Grouped, colourised `dq validate` text output with per-check failure rates and
  a bounded sample of the offending values, plus `--quiet` / `--verbose` /
  `--color` flags and a standalone `dqflow.report.render_result()` renderer
  ([#38](https://github.com/dqflow/dqflow/issues/38)).
- Engine `message` strings now always name the column and the expectation;
  failing `CheckResult.details` gained rate and sample fields. `null_rate()` on
  an empty DataFrame is now `0.0` (not `NaN`) in the pandas engine.

## 0.3.0 — 2026-08-31

- Added `dq diff` and `dqflow.diff.diff_contracts()` — compare two contract
  versions and flag every change as breaking or non-breaking for data producers
  (text / JSON output, CI exit code, a documented classification table, and a
  runnable `examples/contract-diff` project).
- Bumped the package version consistently (`dq --version` was stuck at `0.2.1`)
  and removed stale re-exports from `dqflow.engines`.

## 0.2.2 — 2026-08-31

### Added

- Generated API reference for contracts, columns, results, engines, and inference
- Task-oriented workflow guides and four runnable example projects
- Strict documentation builds in CI and a contributor setup script
- Optional `parquet` extra for CLI Parquet input

### Fixed

- Documentation now distinguishes the enforced `pattern` check from descriptive
  `dtype`, `freshness_minutes`, and `custom` fields
- Rule syntax, evaluator safety, and `--fail-fast` behavior are documented
  according to the current implementation

## 0.2.1 — 2026-08-28

- Fixed README and docs rendering on PyPI.
- Replaced diagrams that did not render consistently.
- Corrected project links and the PyPI badge.

## 0.2.0 — 2026-08-28

- Added the experimental Polars engine and cross-column rules.
- Added `unique`, `pattern`, `unique_count()`, contract inference improvements,
  benchmarks, the roadmap, and the redesigned project documentation.
- Standardized the engine interface and structured output parity.

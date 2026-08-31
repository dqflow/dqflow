# Changelog

The complete release history lives in
[`CHANGELOG.md`](https://github.com/dqflow/dqflow/blob/main/CHANGELOG.md).

## Unreleased

- Grouped, colourised `dq validate` text output with per-check failure rates and
  a bounded sample of the offending values, plus `--quiet` / `--verbose` /
  `--color` flags and a standalone `dqflow.report.render_result()` renderer.
- Engine `message` strings now always name the column and the expectation;
  failing `CheckResult.details` gained rate and sample fields. The top-level
  `--output json` schema is unchanged.

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

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
- `Column` accepts `dtype`, `freshness_minutes`, `pattern`, and `custom`, but the
  engines do not yet validate data against them

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

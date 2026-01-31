# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

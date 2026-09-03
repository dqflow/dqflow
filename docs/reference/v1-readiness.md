# 1.0 readiness checklist

dqflow 1.0 is the point at which the [compatibility contract](stability.md)
becomes a promise: covered surfaces then change only in a major release. This
page is the living gate for that milestone. 1.0 ships when every box is checked.

Tracking issue: [#67](https://github.com/dqflow/dqflow/issues/67).

## Compatibility policy

- [x] Covered and experimental surfaces are documented — [Stability & compatibility](stability.md)
- [x] Semantic-versioning and deprecation policies are published, with a minimum notice period
- [x] CI detects accidental changes to the Python API, CLI, exit codes, and JSON payloads (`tests/test_public_api.py`)
- [x] The contract format is versioned with a compatibility policy — [Schema versioning](../guide/schema-versioning.md) ([#61](https://github.com/dqflow/dqflow/issues/61))
- [ ] Every pre-1.0 breaking change carries an actionable migration note in the changelog *(ongoing)*
- [ ] Contract versioning and breaking-change detection for consumers ([#41](https://github.com/dqflow/dqflow/issues/41))

## Correctness & safety

- [ ] Declared `dtype` is enforced by the engines, or removed from the covered contract format
- [ ] `freshness_minutes` and `custom` are enforced, or explicitly marked non-covered
- [ ] Polars engine reaches pandas parity and graduates from experimental ([#25](https://github.com/dqflow/dqflow/issues/25))
- [ ] Validation-severity levels and failure thresholds are settled ([#44](https://github.com/dqflow/dqflow/issues/44))

## Supported environments

- [ ] A public compatibility matrix and support policy exist (Python, pandas, Polars, PyArrow) ([#65](https://github.com/dqflow/dqflow/issues/65))
- [ ] CI covers every supported Python version and the min/latest dependency sets ([#65](https://github.com/dqflow/dqflow/issues/65))
- [ ] Windows and macOS smoke tests cover CLI paths and serialization ([#65](https://github.com/dqflow/dqflow/issues/65))
- [ ] Each backend installs with only its documented dependencies ([#65](https://github.com/dqflow/dqflow/issues/65))
- [ ] Built-wheel install/import smoke tests run before every release ([#65](https://github.com/dqflow/dqflow/issues/65))

## Supply chain & release

- [ ] `SECURITY.md`, pinned GitHub Actions, build provenance / attestations, and an SBOM ([#66](https://github.com/dqflow/dqflow/issues/66))
- [ ] Release checks fail on metadata, wheel-content, or optional-extra drift ([#65](https://github.com/dqflow/dqflow/issues/65))

## Performance

- [ ] A benchmark suite with committed baselines and a CI regression gate ([#45](https://github.com/dqflow/dqflow/issues/45))
- [ ] A published performance baseline for a representative validation workload

## Documentation

- [ ] Documentation site published with Getting Started, Concepts, Guides, and Reference ([#76](https://github.com/dqflow/dqflow/issues/76))
- [ ] Contract diff is a headline, end-to-end story with a copyable CI gate ([#69](https://github.com/dqflow/dqflow/issues/69))
- [ ] A first-class pytest integration is documented ([#64](https://github.com/dqflow/dqflow/issues/64))
- [ ] An upgrade guide covering every pre-1.0 breaking change

## Adoption signal

- [ ] Adoption metrics and a project-health baseline are in place ([#60](https://github.com/dqflow/dqflow/issues/60))
- [ ] No known unresolved design question about a covered surface

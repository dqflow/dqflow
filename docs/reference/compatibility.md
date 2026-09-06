# Supported environments

dqflow supports only combinations listed on this page. The package metadata and
continuous-integration jobs enforce the same bounds so an untested future major
version is rejected during installation instead of failing later at runtime.

## Compatibility matrix

| Component | Supported versions | CI coverage |
| --- | --- | --- |
| Python | 3.11, 3.12, 3.13, 3.14 | Full suite on every version |
| pandas | 2.3.3 through 3.x | Minimum 2.x and latest 3.x |
| Polars | 1.x | Minimum supported and latest 1.x |
| PyArrow | 22.x through 25.x | Minimum and latest through dependency resolution |
| Operating system | Linux, macOS, Windows | Full Linux suite; wheel, CLI, path, and serialization smoke tests on all three |

The Polars engine remains experimental until its behavior and lazy-execution
work tracked in [#25](https://github.com/dqflow/dqflow/issues/25) is complete.
Experimental describes API stability; the dependency and Python combinations
above are still continuously tested.

## Install profiles

The base package contains contract, schema, lint, diff, and reporting support,
but no dataframe library:

```bash
python -m pip install dqflow
```

Choose the backend required by the application:

```bash
python -m pip install "dqflow[pandas]"
python -m pip install "dqflow[polars]"
python -m pip install "dqflow[pandas-parquet]"
python -m pip install "dqflow[all]"
```

The old `parquet` extra is an alias for `pandas-parquet` for one minor release.
Polars reads Parquet through its native reader and does not require PyArrow for
the dqflow CLI.

Selecting an engine that is not installed raises an error containing the exact
extra to install. `dq infer` is currently pandas-specific and therefore requires
`dqflow[pandas]` or `dqflow[pandas-parquet]`.

## Support policy

- Python versions are supported while they are receiving upstream security
  fixes and dqflow's required dependencies publish compatible releases.
- Dropping a Python version or raising a minimum dependency is announced in the
  changelog. Before 1.0 it may happen in a minor release; from 1.0 it follows the
  project's [stability policy](stability.md).
- The oldest declared dependency set and the newest resolvable set are tested.
  pandas major lines are tested separately.
- New Python and dependency major versions are unsupported until a required CI
  job covers them. Upper bounds make that status explicit to installers.
- Free-threaded Python builds, alternative interpreters, and platforms not
  listed above are not currently supported.

## What release CI verifies

Every release builds the wheel once, installs that exact artifact into clean
environments for the base package and each extra, runs `pip check`, exercises the
CLI and engines, and only then publishes it. CI also checks wheel metadata,
version consistency, the console entry point, bundled contract schema, and the
absence of caches or repository-only files.

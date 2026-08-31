# Contributing

The canonical contributor guide is
[`CONTRIBUTING.md`](https://github.com/dqflow/dqflow/blob/main/CONTRIBUTING.md).

## From-scratch setup

Fork and clone the repository, then on macOS or Linux run:

```bash
./scripts/setup-dev.sh
source .venv/bin/activate
```

The script creates an isolated environment, installs development, docs, and
Polars dependencies, and installs pre-commit hooks. A manual Windows setup is
documented in the canonical guide.

## Verify a change

```bash
pytest
ruff format --check .
ruff check .
mypy src/dqflow
mkdocs build --strict
```

Update tests and user documentation with behavior changes. New or changed docs
must build without warnings because the same strict build runs in CI.

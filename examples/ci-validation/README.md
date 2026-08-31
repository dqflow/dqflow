# CI validation example

The script wraps `dq validate --fail-fast`, the same command used in a CI job.

```bash
pip install dqflow
python examples/ci-validation/validate.py
```

A pull-request workflow can call the CLI directly:

```yaml
- run: dq validate examples/ci-validation/contract.yaml examples/ci-validation/data/users.csv --fail-fast
```

The process returns exit code `1` after reporting all failed checks.

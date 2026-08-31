# Contract diff example

`orders-v1.yaml` and `orders-v2.yaml` are two versions of the same contract. The
script compares them with `diff_contracts()` and blocks when any change is
breaking for data producers.

```bash
pip install dqflow
python examples/contract-diff/diff.py
```

`v2` makes one breaking change (`amount.min` `0 -> 1`) and two non-breaking ones
(widened `currency.allowed`, a new nullable `discount` column), so the script
reports one breaking change.

A pull-request workflow can call the CLI directly:

```yaml
- run: dq diff examples/contract-diff/orders-v1.yaml examples/contract-diff/orders-v2.yaml
```

`dq diff` exits `1` when breaking changes are present; add `--allow-breaking` to
override, or `--output json` for a machine-readable report.

# Contract diff: gate a pull request

`orders-v1.yaml` and `orders-v2.yaml` are two versions of the same contract. The
example covers the complete producer-safety story: compare the proposed contract,
classify every change, and block when a new requirement may reject data accepted
by the old contract.

```bash
pip install dqflow
python examples/contract-diff/diff.py
```

`v2` makes one breaking change (`amount.min` `0 -> 1`) and two non-breaking ones
(widened `currency.allowed`, a new nullable `discount` column), so the script
prints:

```text
orders: 3 changes (1 breaking)

  BREAKING
    ~ column "amount" min: 0 -> 1  (stricter lower bound)

  non-breaking
    ~ column "currency" allowed: +[GBP]  (widened allowed set)
    + column "discount" (float)          (new nullable column)

blocked: 1 breaking change(s) for data producers
```

The Python demo exits `1`, just like `dq diff`, because this comparison is not
safe to merge:

```bash
python examples/contract-diff/diff.py
echo $?  # 1
```

For CI, copy `contract-compatibility.yml` to
`.github/workflows/contract-compatibility.yml`, update `contracts/orders.yaml`
to your contract path, and commit it. The workflow retrieves the contract from
the pull request's base branch and calls the CLI directly:

```yaml
- name: Block breaking contract changes
  run: dq diff "${RUNNER_TEMP}/orders-base.yaml" contracts/orders.yaml
```

`dq diff` exits `1` when breaking changes are present; add `--allow-breaking` to
make an explicitly approved exception, or `--output json` for a machine-readable
report. See the full
[contract diff guide](https://dqflow.readthedocs.io/en/latest/guide/diff/) for
the classification rules and Python API.

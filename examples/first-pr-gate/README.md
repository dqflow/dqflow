# First PR gate: a copyable starter

A complete, working starting point for the dqflow workflow:

```text
infer → validate → diff → gate the pull request
```

Copy this folder into a repository, push the workflow, and the next pull request
that tightens the contract gets a **red check** — no dqflow account, token,
server, or database.

## What is in here

| File | Role |
| --- | --- |
| `contracts/orders.yaml` | The current, agreed contract |
| `data/orders.csv` | A small fixture that satisfies the contract |
| `proposed-orders.yaml` | A revision that tightens `amount` and drops `GBP` — **breaking** |
| `data-contract.yml` | The pull-request workflow to copy to `.github/workflows/` |
| `gate.py` | Runs the same three CLI checks locally and exits `1` on the breaking edit |

## 10 minutes to a failing check

### 1 · Copy the starter (1 min)

From the root of your repository:

```bash
mkdir -p contracts data .github/workflows
cp path/to/first-pr-gate/contracts/orders.yaml contracts/orders.yaml
cp path/to/first-pr-gate/data/orders.csv       data/orders.csv
cp path/to/first-pr-gate/data-contract.yml     .github/workflows/data-contract.yml
```

### 2 · Confirm it is green locally (2 min)

```bash
pip install "dqflow[pandas]"
dq lint contracts/orders.yaml --strict
dq validate contracts/orders.yaml data/orders.csv --fail-fast
```

Both commands exit `0`. Replace `orders.yaml` and `orders.csv` with your own
contract and a representative fixture whenever you are ready — keep the file
paths or update them in `data-contract.yml`.

### 3 · Commit the baseline (2 min)

```bash
git add contracts/orders.yaml data/orders.csv .github/workflows/data-contract.yml
git commit -m "Add data contract and pull-request gate"
git push
```

The contract must exist on the base branch before step 5 can diff against it.

### 4 · Open a pull request that tightens the contract (3 min)

On a new branch, make the same change `proposed-orders.yaml` demonstrates — for
example raise `amount.min` to `1` and remove `GBP` from `currency.allowed` — then
push and open a pull request.

### 5 · Watch the check fail (2 min)

The **Data contract** check turns red. The log shows:

```text
orders: 3 changes (2 breaking)

  BREAKING
    ~ column "amount" min: 0 -> 1        (stricter lower bound)
    ~ column "currency" allowed: -[GBP]  (narrowed allowed set)
```

`dq diff` exits `1` on a breaking change, and GitHub turns that non-zero exit
into a failed check. Loosen the change, or add `--allow-breaking` to the diff
step for a coordinated, reviewed migration.

## Run the whole gate locally

```bash
python examples/first-pr-gate/gate.py
echo $?  # 1 — the proposed revision is breaking
```

`gate.py` is exercised by
[`tests/test_examples.py`](../../tests/test_examples.py).

## Next steps

- [10-minute first PR gate tutorial](https://dqflow.readthedocs.io/en/latest/getting-started/first-pr-gate/)
- [Add contract checks to CI](https://dqflow.readthedocs.io/en/latest/workflows/ci-pull-request/) — build the same workflow from scratch
- [Contract diff guide](https://dqflow.readthedocs.io/en/latest/guide/diff/) — every breaking / non-breaking rule
- Make **Data contract / contract** a required status check in branch protection

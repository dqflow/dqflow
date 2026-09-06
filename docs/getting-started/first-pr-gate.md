# Your first PR gate in 10 minutes

Start from a working skeleton instead of building the workflow by hand. By the
end you have a contract in git and a pull request that fails because it tightened
that contract.

**You need:** a GitHub repository you can push to, and Python 3.11–3.14.

If you would rather build the workflow step by step and understand each line,
use [Add contract checks to CI](../workflows/ci-pull-request.md) instead — this
page is the fast path.

## 1. Copy the starter (1 min)

The [`examples/first-pr-gate/`](https://github.com/dqflow/dqflow/tree/main/examples/first-pr-gate)
folder is the source. From your repository root:

```bash
mkdir -p contracts data .github/workflows

BASE=https://raw.githubusercontent.com/dqflow/dqflow/main/examples/first-pr-gate
curl -fsSL $BASE/contracts/orders.yaml -o contracts/orders.yaml
curl -fsSL $BASE/data/orders.csv       -o data/orders.csv
curl -fsSL $BASE/data-contract.yml     -o .github/workflows/data-contract.yml
```

## 2. Confirm it is green locally (2 min)

```bash
python -m pip install "dqflow[pandas]"
dq lint contracts/orders.yaml --strict
dq validate contracts/orders.yaml data/orders.csv --fail-fast
```

Both exit `0`. `orders.yaml` requires a non-null unique `order_id`, a
non-negative `amount`, and `currency` in `{USD, EUR, GBP}`; `orders.csv`
satisfies all of it.

## 3. Commit the baseline (2 min)

```bash
git checkout -b add-data-contract
git add contracts/orders.yaml data/orders.csv .github/workflows/data-contract.yml
git commit -m "Add data contract and pull-request gate"
git push -u origin add-data-contract
```

Merge this branch. The contract must exist on the base branch before a later PR
can be diffed against it.

## 4. Open a PR that tightens the contract (3 min)

On a new branch, edit `contracts/orders.yaml` to make it stricter — the same
change [`proposed-orders.yaml`](https://github.com/dqflow/dqflow/blob/main/examples/first-pr-gate/proposed-orders.yaml)
shows:

```yaml
  amount:
    dtype: float
    min: 1              # was 0
  currency:
    dtype: string
    allowed: [USD, EUR] # was [USD, EUR, GBP]
```

Commit, push, open a pull request.

## 5. Watch the check fail (2 min)

The **Data contract** check turns red on the `dq diff` step:

```text
orders: 3 changes (2 breaking)

  BREAKING
    ~ column "amount" min: 0 -> 1        (stricter lower bound)
    ~ column "currency" allowed: -[GBP]  (narrowed allowed set)
```

`dq diff` exits `1` when a change could reject data a producer already sends, and
GitHub turns that into a failed check. To land a coordinated, reviewed break, add
`--allow-breaking` to the diff step in the workflow and note the decision in the
PR.

## What you have now

```text
contract in git ──▶ every PR: lint + validate + diff vs. base ──▶ red on a silent tightening
```

Run the whole gate locally any time:

```bash
git clone https://github.com/dqflow/dqflow
python dqflow/examples/first-pr-gate/gate.py   # exits 1 on the breaking edit
```

## Next steps

- Make **Data contract / contract** a [required status check](../workflows/ci-pull-request.md#require-the-check-before-merge)
- [Contract diff guide](../guide/diff.md) — every breaking / non-breaking rule
- [Validate inside your ETL job](../workflows/etl-pipeline.md), not just in CI
- Replace `orders.yaml` with your real contract — `dq infer` gives you a draft:
  [infer and refine](../workflows/infer-refine.md)

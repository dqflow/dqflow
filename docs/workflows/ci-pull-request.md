# Add contract checks to CI in 5 minutes

This tutorial adds two pull-request checks:

1. **Fixture validation** proves that the current contract and validation command
   work together.
2. **Contract diff** compares the proposed contract with the base branch and
   blocks changes that may reject previously valid producer data.

Together with the [5-minute quickstart](../getting-started/quickstart.md), this
completes the `infer → validate → diff → gate the PR` path in about 10 minutes.

## Before you start

Commit one contract and one small, representative fixture to your repository:

```text
contracts/orders.yaml
data/orders.csv
```

The contract must already exist on the default branch for compatibility diffing.
For a brand-new contract, merge the initial version first or skip the diff step
until there is a base revision to compare.

## Create the workflow

Save the following as `.github/workflows/data-contract.yml`:

```yaml title=".github/workflows/data-contract.yml"
name: Data contract

on:
  pull_request:
    paths:
      - "contracts/**"
      - "data/**"
      - ".github/workflows/data-contract.yml"

permissions:
  contents: read

jobs:
  contract:
    runs-on: ubuntu-latest
    steps:
      - name: Check out the pull request
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dqflow
        run: python -m pip install dqflow

      - name: Lint the contract
        run: dq lint contracts/orders.yaml --strict

      - name: Validate a representative fixture
        run: dq validate contracts/orders.yaml data/orders.csv --fail-fast

      - name: Read the contract from the PR base branch
        env:
          BASE_REF: ${{ github.base_ref }}
        run: |
          git show "origin/${BASE_REF}:contracts/orders.yaml" \
            > "${RUNNER_TEMP}/orders-base.yaml"

      - name: Block breaking contract changes
        run: dq diff "${RUNNER_TEMP}/orders-base.yaml" contracts/orders.yaml
```

Change the two `orders` paths to match your repository, then commit and push.
The workflow needs no dqflow account, token, server, or database.

## What happens on a pull request

```text
contract + fixture ── dq validate ──▶ bad current data? ──▶ fail
        │
base contract + PR contract ── dq diff ──▶ breaking edit? ──▶ fail
```

| Outcome | Validation | Diff | Pull-request check |
| --- | ---: | ---: | --- |
| Fixture and contract agree; change is compatible | Pass | Pass | Green |
| Fixture violates the proposed contract | **Fail** | Any | Red |
| Contract becomes stricter for producers | Any | **Fail** | Red |

The validation step evaluates every check and prints all failures before exiting
`1`. The diff step exits `1` when it finds at least one breaking change. GitHub
Actions turns either non-zero exit into a failed check.

## Test the same checks locally

Run these before pushing:

```bash
dq lint contracts/orders.yaml --strict
dq validate contracts/orders.yaml data/orders.csv --fail-fast
dq diff path/to/base-orders.yaml contracts/orders.yaml
```

For a machine-readable artifact or a later reporting step, add `--output json`:

```bash
dq validate contracts/orders.yaml data/orders.csv --output json --fail-fast
dq diff path/to/base-orders.yaml contracts/orders.yaml --output json
```

## Require the check before merge

After the workflow has run once, make `Data contract / contract` a required
status check in the repository's branch protection or ruleset. Without that
repository setting, the workflow reports failures but GitHub may still allow a
merge.

## Approve an intentional breaking change

If producers and consumers have coordinated a breaking change, record that
decision in the pull request and temporarily add `--allow-breaking`:

```yaml
- name: Report an approved breaking contract change
  run: dq diff "${RUNNER_TEMP}/orders-base.yaml" contracts/orders.yaml --allow-breaking
```

This keeps the change visible in logs while allowing the job to pass. Remove the
flag after the migration; dqflow never silently approves a breaking change.

## Scale beyond one contract

Start with one important contract and fixture. Once the check is trusted, use a
small repository script or matrix to map each `contracts/*.yaml` file to its
fixture. Keep that mapping explicit: guessing fixture names in shell makes CI
harder to understand and debug.

## Next steps

- Review every classification in the [Contract Diff guide](../guide/diff.md).
- Copy the [canonical workflow example](https://github.com/dqflow/dqflow/blob/main/examples/contract-diff/contract-compatibility.yml).
- Run validation inside the real [ETL pipeline](etl-pipeline.md); a CI fixture
  verifies the wiring, not live production data.
- Browse all [runnable examples](https://github.com/dqflow/dqflow/tree/main/examples).

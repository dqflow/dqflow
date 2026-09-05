# Gate a pull request

Use two complementary gates: validate a representative fixture against the
current contract, and diff a contract edit against the pull request's base branch.
Validation catches bad fixture data; diffing catches a requirement that could
break producers before it merges.

```yaml
name: Data contract

on:
  pull_request:

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install dqflow
      - name: Validate fixture
        run: dq validate contracts/orders.yaml data/orders.csv --fail-fast
      - name: Block breaking contract changes
        env:
          BASE_REF: ${{ github.base_ref }}
        run: |
          git show "origin/${BASE_REF}:contracts/orders.yaml" > "${RUNNER_TEMP}/orders-base.yaml"
          dq diff "${RUNNER_TEMP}/orders-base.yaml" contracts/orders.yaml
```

The command evaluates all checks and exits `1` after printing failures. Use JSON
when another step needs to consume the result:

```bash
dq validate contracts/orders.yaml data/orders.csv --output json --fail-fast
```

Fixtures protect the contract and validation wiring; they do not validate live
production data. Run the same contract inside the production pipeline as well.

See the runnable
[`examples/ci-validation`](https://github.com/dqflow/dqflow/tree/main/examples/ci-validation)
and the canonical
[`examples/contract-diff`](https://github.com/dqflow/dqflow/tree/main/examples/contract-diff),
which includes a complete copyable workflow. The
[contract diff guide](../guide/diff.md) documents every classification.

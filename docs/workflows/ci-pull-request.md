# Gate a pull request

Store a representative fixture and its YAML contract in the repository, then run
the CLI with `--fail-fast` in CI.

```yaml
name: Data contract

on:
  pull_request:

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install dqflow
      - name: Validate fixture
        run: dq validate contracts/orders.yaml data/orders.csv --fail-fast
```

The command evaluates all checks and exits `1` after printing failures. Use JSON
when another step needs to consume the result:

```bash
dq validate contracts/orders.yaml data/orders.csv --output json --fail-fast
```

Fixtures protect the contract and validation wiring; they do not validate live
production data. Run the same contract inside the production pipeline as well.

See the runnable
[`examples/ci-validation`](https://github.com/dqflow/dqflow/tree/main/examples/ci-validation).

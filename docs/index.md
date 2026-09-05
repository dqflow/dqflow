# Welcome to dqflow

**dqflow** is a lightweight data-contract library for Python pipelines. It helps
you define data expectations once, validate incoming data at runtime, and catch
breaking contract changes before they merge.

```text
infer → validate → diff → gate the pull request
```

## Installation

Install dqflow from PyPI:

```bash
python -m pip install dqflow
```

Requires Python 3.9 or newer. See [Installation](getting-started/installation.md)
for virtual environments, Polars, Parquet, and development setup.

## Get started in 5 minutes

The [5-minute quickstart](getting-started/quickstart.md) walks through the full
local workflow with copyable commands:

1. Install dqflow.
2. Infer a YAML contract from a CSV file.
3. Validate the data against that contract.
4. Diff two contract revisions.
5. See a breaking change return exit code `1`.

After that, follow the [CI/CD tutorial](workflows/ci-pull-request.md) to add the
same checks to a GitHub pull request. Both guides take about 10 minutes total.

## Why dqflow

- **Contracts instead of scattered assertions.** Keep expectations in one YAML
  or Python artifact that can be reviewed and versioned.
- **Runtime validation.** Catch missing columns, nulls, duplicates, invalid
  ranges, unexpected values, and failed table rules.
- **Contract compatibility checks.** Detect stricter requirements that could
  reject data previously accepted from producers.
- **CI-friendly behavior.** Use standard commands, structured JSON output, and
  non-zero exit codes without operating another service.
- **Lightweight integration.** Use pandas by default or the experimental Polars
  engine directly inside an existing Python pipeline.

## Validation and contract diff

These checks protect different parts of the workflow:

| Command | Purpose | Typical location |
| --- | --- | --- |
| `dq lint` | Find malformed or contradictory contracts | Editor or CI |
| `dq validate` | Find data that violates the current contract | Pipeline or CI |
| `dq diff` | Find proposed requirements that may break producers | Pull request |

```bash
dq validate contracts/orders.yaml data/orders.csv --fail-fast
dq diff orders-v1.yaml orders-v2.yaml
```

Read [Contract Diff](guide/diff.md) for the breaking-change rules and
[Add contract checks to CI](workflows/ci-pull-request.md) for a complete GitHub
Actions workflow.

## Documentation

- [5-minute quickstart](getting-started/quickstart.md)
- [Defining contracts](guide/contracts.md)
- [Column validations](guide/columns.md)
- [Table rules](guide/rules.md)
- [YAML contracts](guide/yaml.md)
- [Contract Diff](guide/diff.md)
- [CLI usage](guide/cli.md)
- [API reference](api/contract.md)
- [Runnable examples](https://github.com/dqflow/dqflow/tree/main/examples)

!!! note "Current enforcement boundary"
    Column existence, `not_null`, `min`, `max`, `allowed`, `unique`, and regex
    `pattern` are enforced. `dtype`, `freshness_minutes`, and `custom` can be
    declared and diffed but are not yet validated by the engines.

## Project links

- [Source code](https://github.com/dqflow/dqflow)
- [Python package](https://pypi.org/project/dqflow/)
- [Issue tracker](https://github.com/dqflow/dqflow/issues)
- [Roadmap](https://github.com/dqflow/dqflow/blob/main/ROADMAP.md)

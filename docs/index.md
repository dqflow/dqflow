---
hide:
  - navigation
  - toc
---

<section class="dq-hero">
  <div>
    <div class="dq-hero__eyebrow">Data contracts for Python pipelines</div>
    <h1>Stop bad data before it ships.</h1>
    <p class="dq-hero__lede">
      dqflow turns data expectations into versioned contracts. Infer a useful
      starting point, validate every pipeline run, and block breaking contract
      changes in pull requests—with one lightweight Python package.
    </p>
    <div class="dq-hero__actions">
      <a class="md-button md-button--primary" href="getting-started/quickstart/">Validate data in 5 minutes</a>
      <a class="md-button" href="guide/diff/">See contract diff</a>
    </div>
    <div class="dq-hero__proof">
      <span>✓ No service to operate</span>
      <span>✓ pandas + experimental Polars</span>
      <span>✓ CI-friendly exit codes</span>
    </div>
  </div>
  <div class="dq-terminal" aria-label="dqflow command line example">
    <div class="dq-terminal__bar"><span></span><span></span><span></span></div>
    <div><span class="prompt">$</span> dq validate contracts/orders.yaml data/orders.csv --fail-fast</div>
    <div class="ok">✓ Schema &nbsp;3/3 passed</div>
    <div class="fail">✘ Columns 2/4 failed</div>
    <div class="dim">&nbsp; amount &nbsp;&nbsp;&nbsp;below minimum 0</div>
    <div class="dim">&nbsp; currency &nbsp;outside [USD, EUR]</div>
    <br/>
    <div><span class="prompt">$</span> dq diff orders-v1.yaml orders-v2.yaml</div>
    <div class="fail">BREAKING &nbsp;amount.min: 0 → 1</div>
    <div class="dim">exit 1 · pull request blocked</div>
  </div>
</section>

## One contract, from discovery to deployment

<p class="dq-section-intro">
Validation catches bad data now. Contract diff catches a proposed requirement
that could break producers later. dqflow gives both checks the same reviewable,
version-controlled source of truth.
</p>

<div class="dq-workflow">
  <div><strong>1. Infer</strong><span>Generate a draft from real data</span></div>
  <div><strong>2. Validate</strong><span>Check each batch or DataFrame</span></div>
  <div><strong>3. Diff</strong><span>Classify contract changes</span></div>
  <div><strong>4. Gate</strong><span>Block unsafe pull requests</span></div>
</div>

<div class="grid cards" markdown>

-   ⏱ **Get a result in 5 minutes**

    ---

    Install dqflow, infer a YAML contract, and validate a CSV with commands you
    can copy directly.

    [→ Start the quickstart](getting-started/quickstart.md)

-   ⎇ **Review contracts like APIs**

    ---

    See exactly which edits are breaking, why they are unsafe, and how the CLI
    communicates them to reviewers.

    [→ Learn contract diff](guide/diff.md)

-   ◉ **Gate every pull request**

    ---

    Copy a complete GitHub Actions workflow that validates fixtures and rejects
    incompatible contract changes.

    [→ Add the CI gate](workflows/ci-pull-request.md)

</div>

## What dqflow protects

| Risk | dqflow check | Where it runs |
| --- | --- | --- |
| Required columns disappear | Schema validation | Pipeline or CI |
| Nulls, duplicates, invalid ranges, or unexpected values arrive | `dq validate` | Pipeline or CI |
| A contract becomes stricter without producer coordination | `dq diff` | Pull request |
| A malformed contract reaches production | `dq lint` | Editor or CI |

```bash title="Install the stable pandas workflow"
python -m pip install dqflow
dq --version
```

!!! info "Deliberately lightweight"
    dqflow produces structured results and reliable exit codes. It does not run
    a server, store your data, or replace observability and lineage platforms.
    Your contracts and data stay in your pipeline.

## Choose your next step

<div class="grid cards" markdown>

-   **I am evaluating dqflow**

    Run the [5-minute quickstart](getting-started/quickstart.md), then try the
    [pandas ETL example](https://github.com/dqflow/dqflow/tree/main/examples/pandas-etl).

-   **I have a dataset**

    Follow [infer and refine](workflows/infer-refine.md) to turn it into a
    reviewed contract.

-   **I already have contracts**

    Add the [CI/CD workflow](workflows/ci-pull-request.md) and protect contract
    changes before merge.

-   **I need the full syntax**

    Browse [column checks](guide/columns.md), [table rules](guide/rules.md), or
    the [Python API](api/contract.md).

</div>

!!! note "Current enforcement boundary"
    Column existence, `not_null`, `min`, `max`, `allowed`, `unique`, and
    `pattern` are enforced. `dtype`, `freshness_minutes`, and `custom` can be
    declared and diffed but are not yet validated by the engines. See
    [stability and compatibility](reference/stability.md).

Questions or ideas? [Open an issue](https://github.com/dqflow/dqflow/issues/new)
or explore the [runnable examples](https://github.com/dqflow/dqflow/tree/main/examples).

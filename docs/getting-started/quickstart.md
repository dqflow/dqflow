# Validate your first dataset in 5 minutes

By the end of this guide you will have a contract inferred from real data, a
successful validation, and a breaking contract change caught before merge.

**You need:** Python 3.9+ and a terminal. The commands below create an isolated
folder and use dqflow's small example datasets.

## 1. Install dqflow

=== "macOS / Linux"

    ```bash
    mkdir dqflow-quickstart && cd dqflow-quickstart
    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install dqflow
    dq --version
    ```

=== "Windows PowerShell"

    ```powershell
    New-Item -ItemType Directory dqflow-quickstart
    Set-Location dqflow-quickstart
    py -m venv .venv
    .venv\Scripts\Activate.ps1
    python -m pip install dqflow
    dq --version
    ```

You should see `dqflow, version 0.4.0` or newer. If installation fails, see the
[installation guide](installation.md).

## 2. Download a three-row dataset

=== "curl (macOS / Linux)"

    ```bash
    curl -fsSL https://raw.githubusercontent.com/dqflow/dqflow/main/examples/infer-refine/data/customers.csv -o customers.csv
    ```

=== "PowerShell"

    ```powershell
    Invoke-WebRequest https://raw.githubusercontent.com/dqflow/dqflow/main/examples/infer-refine/data/customers.csv -OutFile customers.csv
    ```

The data looks like this:

```csv
customer_id,tier,credit_limit
C001,standard,1000
C002,premium,5000
C003,standard,2500
```

## 3. Infer a starting contract

```bash
dq infer customers.csv customers.yaml
```

```text
Wrote customers.yaml (3 columns, inferred from 3 rows)
```

Inference gives you a draft—not a business guarantee. Open `customers.yaml` and
review the observed types, ranges, nullability, and allowed values before
committing it. The [infer and refine workflow](../workflows/infer-refine.md)
explains which inferred constraints usually need widening.

## 4. Validate the data

```bash
dq validate customers.yaml customers.csv --fail-fast
```

The report groups schema, column, and table checks. This dataset matches the
inferred contract, so the command exits `0`:

```text
customers · 12/12 checks passed on 3 rows

  Schema  3/3 passed
  Columns  9/9 passed

  12 passed · 0 failed
```

`--fail-fast` means “return a failing process exit code if the contract fails.”
All checks still run, so you get the complete failure report in one pass.

## 5. Catch a breaking contract edit

Download two revisions of an orders contract:

=== "curl (macOS / Linux)"

    ```bash
    curl -fsSL https://raw.githubusercontent.com/dqflow/dqflow/main/examples/contract-diff/orders-v1.yaml -o orders-v1.yaml
    curl -fsSL https://raw.githubusercontent.com/dqflow/dqflow/main/examples/contract-diff/orders-v2.yaml -o orders-v2.yaml
    dq diff orders-v1.yaml orders-v2.yaml
    ```

=== "PowerShell"

    ```powershell
    Invoke-WebRequest https://raw.githubusercontent.com/dqflow/dqflow/main/examples/contract-diff/orders-v1.yaml -OutFile orders-v1.yaml
    Invoke-WebRequest https://raw.githubusercontent.com/dqflow/dqflow/main/examples/contract-diff/orders-v2.yaml -OutFile orders-v2.yaml
    dq diff orders-v1.yaml orders-v2.yaml
    ```

```text
orders: 3 changes (1 breaking)

  BREAKING
    ~ column "amount" min: 0 -> 1  (stricter lower bound)

  non-breaking
    ~ column "currency" allowed: +[GBP]  (widened allowed set)
    + column "discount" (float)          (new nullable column)
```

The exit code is `1` because raising `amount.min` could reject producer data that
the old contract accepted. That same exit code becomes your pull-request gate.

## You completed the core workflow

```text
data → infer a draft → validate the data → diff a change → exit 1 blocks the PR
```

Continue with the [5-minute CI/CD tutorial](../workflows/ci-pull-request.md) to
copy the gate into GitHub Actions, or read the [contract diff guide](../guide/diff.md)
for every breaking-change rule.

!!! note "What dqflow enforces today"
    Column existence, `not_null`, `min`, `max`, `allowed`, `unique`, and regex
    `pattern` are enforced. `dtype`, `freshness_minutes`, and `custom` are
    declarative fields that can be versioned and diffed but are not yet validated.

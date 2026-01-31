# CLI Usage

dqflow provides a command-line interface for validating data.

## Commands

### dq validate

Validate data against a contract:

```bash
dq validate CONTRACT DATA
```

**Arguments:**

- `CONTRACT` - Path to YAML contract file
- `DATA` - Path to data file (parquet, csv, json)

**Options:**

- `--output`, `-o` - Output format: `text` (default) or `json`
- `--fail-fast` - Exit with error code 1 on validation failure

**Examples:**

```bash
# Basic validation
dq validate contracts/orders.yaml data/orders.parquet

# JSON output
dq validate contracts/orders.yaml data/orders.csv --output json

# Fail fast (for CI/CD)
dq validate contracts/orders.yaml data/orders.parquet --fail-fast
```

### dq show

Display contract details:

```bash
dq show CONTRACT
```

**Example:**

```bash
dq show contracts/orders.yaml
```

**Output:**

```
Contract: orders
Description: E-commerce order data contract

Columns:
  order_id: string (NOT NULL)
  amount: float (min=0, max=100000)
  currency: string (allowed=['USD', 'EUR', 'GBP'])
  created_at: timestamp (freshness=1440m)

Rules:
  - row_count > 0
  - null_rate(amount) < 0.01
```

### dq infer

Infer a contract from existing data:

```bash
dq infer DATA OUTPUT
```

**Arguments:**

- `DATA` - Path to data file
- `OUTPUT` - Path to write contract YAML

**Example:**

```bash
dq infer data/orders.csv contracts/orders.yaml
```

## Supported File Formats

| Format | Extension |
|--------|-----------|
| Parquet | `.parquet` |
| CSV | `.csv` |
| JSON | `.json` |

## CI/CD Integration

Use `--fail-fast` in CI pipelines:

```yaml
# GitHub Actions example
- name: Validate data quality
  run: dq validate contracts/orders.yaml data/orders.parquet --fail-fast
```

```bash
# Shell script
dq validate contracts/orders.yaml data/orders.parquet --fail-fast || exit 1
```

## JSON Output

Use `-o json` for machine-readable output:

```bash
dq validate contracts/orders.yaml data/orders.parquet -o json
```

```json
{
  "contract_name": "orders",
  "ok": true,
  "total_checks": 7,
  "passed": 7,
  "failed": 0,
  "checks": [...]
}
```

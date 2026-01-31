# Contributing to dqflow

Thank you for your interest in contributing to dqflow! This guide will help you get started.

## Ways to Contribute

- **Report bugs** - Found a bug? Open an issue
- **Suggest features** - Have an idea? We'd love to hear it
- **Improve docs** - Fix typos, add examples, clarify explanations
- **Write code** - Fix bugs or implement new features
- **Review PRs** - Help review pull requests

## Reporting Bugs

Found a bug? Please help us fix it!

### Before Reporting

1. **Check existing issues** - Search [GitHub Issues](https://github.com/dqflow/dqflow/issues) to see if it's already reported
2. **Use the latest version** - Make sure you're using the latest release
   ```bash
   pip install --upgrade dqflow
   ```
3. **Reproduce the bug** - Try to create a minimal example that reproduces the issue

### How to Report

Open a [new issue](https://github.com/dqflow/dqflow/issues/new) with:

```markdown
## Bug Description
A clear, concise description of the bug.

## Steps to Reproduce
1. Install dqflow `pip install dqflow`
2. Run this code:

```python
import pandas as pd
from dqflow import Contract, Column

# Minimal code to reproduce the bug
df = pd.DataFrame({...})
contract = Contract(...)
result = contract.validate(df)
```

## Expected Behavior
What you expected to happen.

## Actual Behavior
What actually happened. Include the full error message/traceback.

## Environment
- dqflow version: (run `dq --version`)
- Python version: (run `python --version`)
- pandas version: (run `pip show pandas`)
- OS: macOS / Linux / Windows
```

### Good Bug Reports

A good bug report includes:
- **Minimal reproducible example** - The smallest code that shows the bug
- **Full error traceback** - Copy the complete error message
- **Environment details** - Version numbers matter!
- **What you tried** - Any workarounds you attempted

## Getting Started

### 1. Fork and Clone

```bash
# Fork the repo on GitHub, then:
git clone https://github.com/YOUR_USERNAME/dqflow.git
cd dqflow
```

### 2. Set Up Development Environment

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### 3. Verify Setup

```bash
# Run tests
pytest

# Run linting
ruff check .

# Run type checking
mypy src/dqflow
```

## Development Workflow

### Creating a Feature

1. **Open an issue first** (for non-trivial changes)
   - Describe the feature
   - Discuss the approach
   - Get feedback before coding

2. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Write your code**
   - Follow existing code style
   - Add tests for new functionality
   - Update documentation if needed

4. **Run checks**
   ```bash
   # Format code
   ruff format .

   # Lint
   ruff check .

   # Type check
   mypy src/dqflow

   # Run tests
   pytest
   ```

5. **Commit your changes**
   ```bash
   git add -A
   git commit -m "Add your feature description"
   ```

6. **Push and create PR**
   ```bash
   git push -u origin feature/your-feature-name
   ```
   Then open a Pull Request on GitHub.

### Fixing a Bug

1. **Create an issue** describing the bug (if one doesn't exist)
2. **Create a branch**
   ```bash
   git checkout -b fix/bug-description
   ```
3. **Write a failing test** that reproduces the bug
4. **Fix the bug**
5. **Verify the test passes**
6. **Submit a PR**

## Code Guidelines

### Style

- We use **ruff** for linting and formatting
- We use **mypy** for type checking
- Follow [PEP 8](https://pep8.org/) conventions
- Use type hints for all functions

### Testing

- Write tests for all new features
- Place tests in the `tests/` directory
- Use pytest fixtures for common setup
- Aim for good coverage of edge cases

```python
# Example test
def test_column_not_null_validation():
    df = pd.DataFrame({"id": [1, None, 3]})
    contract = Contract(
        name="test",
        columns={"id": Column(int, not_null=True)},
    )
    result = contract.validate(df)
    assert not result.ok
```

### Documentation

- Update docstrings for new/changed functions
- Update user docs in `docs/` for user-facing changes
- Add examples where helpful

### Commit Messages

Write clear, concise commit messages:

```
Good:
- Add severity levels to Column class
- Fix null handling in freshness check
- Update CLI to support JSON output

Bad:
- Fixed stuff
- WIP
- Updates
```

## Pull Request Guidelines

### Before Submitting

- [ ] All tests pass (`pytest`)
- [ ] Code is formatted (`ruff format .`)
- [ ] Linting passes (`ruff check .`)
- [ ] Type checking passes (`mypy src/dqflow`)
- [ ] Documentation is updated (if needed)
- [ ] Commit messages are clear

### PR Description

Include:
- **What** the PR does
- **Why** the change is needed
- **How** to test it
- Link to related issue (if any)

### Review Process

1. Maintainers will review your PR
2. Address any feedback
3. Once approved, your PR will be merged

## Project Structure

```
dqflow/
├── src/dqflow/          # Main source code
│   ├── __init__.py      # Public API
│   ├── contract.py      # Contract class
│   ├── column.py        # Column class
│   ├── result.py        # ValidationResult
│   ├── cli.py           # CLI commands
│   └── engines/         # Validation engines
│       ├── base.py      # Abstract base
│       └── pandas.py    # Pandas engine
├── tests/               # Test files
├── docs/                # Documentation
└── examples/            # Example contracts
```

## Feature Ideas

Looking for something to work on? Here are some ideas:

### Good First Issues
- Improve error messages with more context
- Add more examples to documentation
- Add validation for column name patterns

### Medium Complexity
- Add severity levels (warning vs error)
- Add custom validator support
- Improve schema inference in `dq infer`

### Larger Features
- PySpark engine
- SQL/database engine
- dbt integration
- Prometheus metrics export

## Questions?

- Open a [GitHub Issue](https://github.com/dqflow/dqflow/issues)
- Check existing issues and discussions

## Code of Conduct

Be respectful and inclusive. We welcome contributors of all backgrounds and experience levels.

---

Thank you for contributing to dqflow!

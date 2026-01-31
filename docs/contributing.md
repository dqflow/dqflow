# Contributing

Thank you for your interest in contributing to dqflow!

## Ways to Contribute

- **Report bugs** - Found a bug? [Open an issue](https://github.com/dqflow/dqflow/issues)
- **Suggest features** - Have an idea? We'd love to hear it
- **Improve docs** - Fix typos, add examples, clarify explanations
- **Write code** - Fix bugs or implement new features

## Quick Start

```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/dqflow.git
cd dqflow

# Setup environment
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest
```

## Development Workflow

1. Create a branch: `git checkout -b feature/your-feature`
2. Make changes and add tests
3. Run checks:
   ```bash
   ruff format .
   ruff check .
   mypy src/dqflow
   pytest
   ```
4. Commit and push
5. Open a Pull Request

## Code Guidelines

- Use **ruff** for formatting and linting
- Use **mypy** for type checking
- Write tests for new features
- Update docs for user-facing changes

## Feature Ideas

Looking to contribute? Here are some ideas:

| Difficulty | Feature |
|------------|---------|
| Easy | Improve error messages, add examples |
| Medium | Severity levels, custom validators |
| Hard | PySpark engine, dbt integration |

## Questions?

Open a [GitHub Issue](https://github.com/dqflow/dqflow/issues) or check existing discussions.

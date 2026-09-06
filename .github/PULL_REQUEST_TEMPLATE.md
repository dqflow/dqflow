<!--
Thanks for contributing to dqflow! Keep PRs small and focused.
For non-trivial changes, please open an issue or an RFC discussion first.
-->

## What

<!-- What does this PR change? -->

## Why

<!-- The problem it solves. Link the issue: Closes #NN -->

## How to test

<!-- Commands a reviewer can run, or the scenario you exercised. -->

## Checklist

- [ ] `pytest` passes
- [ ] `ruff check .` and `ruff format --check .` pass
- [ ] `mypy src/dqflow` passes
- [ ] `mkdocs build --strict` passes (if docs changed)
- [ ] `CHANGELOG.md` updated under `[Unreleased]` (for user-facing changes)
- [ ] Docs / examples updated (for user-facing changes)
- [ ] Public API snapshot regenerated with `python -m tests.api_surface.collect`
      (only if `dqflow` / `dqflow.schema` exports, the `dq` CLI, or `--output json`
      changed **on purpose** — include a changelog migration note)

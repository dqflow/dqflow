# Releasing dqflow

Step-by-step guide to release a new version.

## Pre-release Checklist

- [ ] All tests passing locally
- [ ] CI passing on main branch
- [ ] CHANGELOG.md updated

## Step 1: Update Version Numbers

Update version in **both** files:

| File | Location |
|------|----------|
| `pyproject.toml` | `version = "X.Y.Z"` |
| `src/dqflow/__init__.py` | `__version__ = "X.Y.Z"` |

## Step 2: Update CHANGELOG.md

Add entry at the top:

```markdown
## [X.Y.Z] - YYYY-MM-DD
### Added
- New feature description

### Changed
- Changed behavior description

### Fixed
- Bug fix description
```

## Step 3: Run Checks Locally

```bash
# Lint
ruff check .
ruff format .

# Type check
mypy src/dqflow

# Tests
pytest
```

## Step 4: Commit and Push

```bash
git add -A
git commit -m "Bump version to X.Y.Z"
git push
```

## Step 5: Wait for CI

Verify all checks pass: https://github.com/dqflow/dqflow/actions

## Step 6: Create Release

```bash
# Create and push tag
git tag vX.Y.Z
git push origin vX.Y.Z

# Create GitHub release (triggers PyPI publish)
gh release create vX.Y.Z --title "vX.Y.Z" --notes "Release notes here"
```

Or use `--generate-notes` for auto-generated notes:
```bash
gh release create vX.Y.Z --generate-notes
```

## Step 7: Verify Release

1. Check GitHub Actions: https://github.com/dqflow/dqflow/actions
2. Check PyPI: https://pypi.org/project/dqflow/
3. Test install:
   ```bash
   pip install dqflow==X.Y.Z
   dq --version
   ```

## Quick Release Script

For convenience, run this (replace version):

```bash
VERSION=0.1.3

# Update versions (manual step - edit the files first)
# Then:
git add -A && \
git commit -m "Bump version to $VERSION" && \
git push && \
git tag v$VERSION && \
git push origin v$VERSION && \
gh release create v$VERSION --generate-notes
```

## Versioning Guidelines

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (1.0.0): Breaking API changes
- **MINOR** (0.2.0): New features, backward compatible
- **PATCH** (0.1.1): Bug fixes, backward compatible

While in 0.x.x (early development), minor versions may include breaking changes.

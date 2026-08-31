#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
venv_dir="${repo_dir}/.venv"

python3 -m venv "${venv_dir}"
"${venv_dir}/bin/python" -m pip install --upgrade pip
"${venv_dir}/bin/python" -m pip install -e "${repo_dir}[dev,docs,polars]"
"${venv_dir}/bin/pre-commit" install

echo "Development environment ready."
echo "Activate it with: source .venv/bin/activate"
echo "Verify it with: pytest && ruff check . && mypy src/dqflow && mkdocs build --strict"

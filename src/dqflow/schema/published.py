"""Access to the published JSON Schema for the contract format.

``dq lint`` (see :mod:`dqflow.schema.validate`) is the authoritative validator.
The JSON Schema shipped here is a close approximation for editor tooling — a
YAML language server can autocomplete and flag obvious mistakes against it. It
cannot express cross-field checks (``min`` ≤ ``max``, regex validity, table-rule
syntax), so it is intentionally a subset of what the linter enforces.
"""

from __future__ import annotations

import json
from importlib import resources
from typing import Any

from dqflow.schema.version import SCHEMA_VERSION

#: File name of the packaged schema, and the leaf of the site path it is published at.
CONTRACT_SCHEMA_FILENAME = f"contract-{SCHEMA_VERSION}.json"

#: Canonical URL of the published schema (matches its ``$id``).
CONTRACT_SCHEMA_URI = f"https://dqflow.github.io/dqflow/schema/{CONTRACT_SCHEMA_FILENAME}"


def contract_schema_text() -> str:
    """Return the packaged JSON Schema file as text."""
    return (
        resources.files("dqflow.schema")
        .joinpath(CONTRACT_SCHEMA_FILENAME)
        .read_text(encoding="utf-8")
    )


def contract_json_schema() -> dict[str, Any]:
    """Return the published JSON Schema for the current contract format as a dict."""
    schema: dict[str, Any] = json.loads(contract_schema_text())
    return schema

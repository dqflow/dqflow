"""MkDocs hooks for the dqflow docs site.

Publishes the packaged contract JSON Schema at ``/schema/contract-<version>.json``
so the file has one source of truth (``src/dqflow/schema/``) and editors can
point at a stable URL. See ``docs/guide/editor-integration.md``.
"""

from __future__ import annotations

from typing import Any

from mkdocs.structure.files import File, Files

from dqflow.schema.published import CONTRACT_SCHEMA_FILENAME, contract_schema_text


def on_files(files: Files, config: Any) -> Files:
    files.append(
        File.generated(
            config,
            f"schema/{CONTRACT_SCHEMA_FILENAME}",
            content=contract_schema_text(),
        )
    )
    return files

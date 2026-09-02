"""The dqflow contract schema: version policy, validation, and typed errors.

``dqflow`` contracts have a versioned, machine-readable shape. This package
validates a contract *document* (the YAML / serialisable form) and reports
precise, path-aware :class:`Diagnostic` records instead of raw tracebacks.

* :func:`lint_contract_file` / :func:`lint_contract_data` — collect diagnostics.
* :class:`ContractError` and its subclasses — raised by
  :meth:`dqflow.contract.Contract.from_yaml`.
* :data:`SCHEMA_VERSION` — the format version this release emits.
"""

from dqflow.schema.errors import (
    ContractError,
    ContractParseError,
    ContractSchemaError,
    ContractVersionError,
    Diagnostic,
)
from dqflow.schema.published import (
    CONTRACT_SCHEMA_FILENAME,
    CONTRACT_SCHEMA_URI,
    contract_json_schema,
)
from dqflow.schema.report import format_diagnostics
from dqflow.schema.validate import (
    KNOWN_COLUMN_FIELDS,
    KNOWN_CROSS_COLUMN_FIELDS,
    KNOWN_TOP_LEVEL,
    lint_contract_data,
    lint_contract_file,
    parse_contract_yaml,
)
from dqflow.schema.version import (
    DEFAULT_SCHEMA_VERSION,
    SCHEMA_VERSION,
    SUPPORTED_SCHEMA_VERSIONS,
    check_version,
)

__all__ = [
    "CONTRACT_SCHEMA_FILENAME",
    "CONTRACT_SCHEMA_URI",
    "DEFAULT_SCHEMA_VERSION",
    "KNOWN_COLUMN_FIELDS",
    "KNOWN_CROSS_COLUMN_FIELDS",
    "KNOWN_TOP_LEVEL",
    "SCHEMA_VERSION",
    "SUPPORTED_SCHEMA_VERSIONS",
    "ContractError",
    "ContractParseError",
    "ContractSchemaError",
    "ContractVersionError",
    "Diagnostic",
    "check_version",
    "contract_json_schema",
    "format_diagnostics",
    "lint_contract_data",
    "lint_contract_file",
    "parse_contract_yaml",
]

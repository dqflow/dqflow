"""The contract schema version and its compatibility policy.

A contract file may declare ``schema_version: "MAJOR.MINOR"``. The policy:

* **Same major, minor ≤ current** — fully supported.
* **Same major, minor > current** — loadable, with a warning: the file may use
  fields this release does not know about.
* **Different major, or unparseable** — rejected.

A file that omits ``schema_version`` is read as :data:`DEFAULT_SCHEMA_VERSION`
with a warning. ``Contract.to_yaml`` always writes :data:`SCHEMA_VERSION`.
"""

from __future__ import annotations

from dqflow.schema.errors import ERROR, WARNING, Diagnostic

#: The schema version this release emits.
SCHEMA_VERSION = "1.0"

#: Versions this release can load without a compatibility warning.
SUPPORTED_SCHEMA_VERSIONS: tuple[str, ...] = ("1.0",)

#: Assumed when a contract file omits ``schema_version``.
DEFAULT_SCHEMA_VERSION = "1.0"

_CURRENT_MAJOR, _CURRENT_MINOR = (int(part) for part in SCHEMA_VERSION.split("."))


def _parse(version: str) -> tuple[int, int] | None:
    parts = version.split(".")
    if len(parts) != 2:
        return None
    try:
        return int(parts[0]), int(parts[1])
    except ValueError:
        return None


def check_version(value: object, *, path: str = "schema_version") -> list[Diagnostic]:
    """Return diagnostics for a contract's declared ``schema_version``.

    Args:
        value: The raw ``schema_version`` value (``None`` when the key is absent).
        path: Document path to attribute any diagnostic to.
    """
    if value is None:
        return [
            Diagnostic(
                WARNING,
                "missing-schema-version",
                f'no schema_version; assuming "{DEFAULT_SCHEMA_VERSION}"',
                path="",
            )
        ]

    if not isinstance(value, str):
        return [
            Diagnostic(
                ERROR,
                "unsupported-schema-version",
                f'schema_version must be a string like "{SCHEMA_VERSION}", got {value!r}',
                path=path,
            )
        ]

    parsed = _parse(value)
    if parsed is None:
        return [
            Diagnostic(
                ERROR,
                "unsupported-schema-version",
                f"schema_version {value!r} is not a MAJOR.MINOR version",
                path=path,
            )
        ]

    major, minor = parsed
    if major != _CURRENT_MAJOR:
        return [
            Diagnostic(
                ERROR,
                "unsupported-schema-version",
                f"contract schema_version {value!r} is not supported by this dqflow "
                f"release (understands {SCHEMA_VERSION}); upgrade dqflow or lower the version",
                path=path,
            )
        ]

    if minor > _CURRENT_MINOR:
        return [
            Diagnostic(
                WARNING,
                "newer-schema-minor",
                f"contract schema_version {value!r} is newer than this release "
                f"({SCHEMA_VERSION}); unknown fields may be ignored",
                path=path,
            )
        ]

    return []

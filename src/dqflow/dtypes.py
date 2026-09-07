"""Logical dtype names and backend-independent compatibility rules."""

from __future__ import annotations

SUPPORTED_LOGICAL_DTYPES: frozenset[str] = frozenset(
    {"integer", "float", "string", "boolean", "timestamp"}
)

_ALIASES: dict[str, str] = {
    "bool": "boolean",
    "boolean": "boolean",
    "bool_": "boolean",
    "date": "timestamp",
    "datetime": "timestamp",
    "datetime64": "timestamp",
    "double": "float",
    "float": "float",
    "float16": "float",
    "float32": "float",
    "float64": "float",
    "int": "integer",
    "integer": "integer",
    "int8": "integer",
    "int16": "integer",
    "int32": "integer",
    "int64": "integer",
    "str": "string",
    "string": "string",
    "timestamp": "timestamp",
    "uint8": "integer",
    "uint16": "integer",
    "uint32": "integer",
    "uint64": "integer",
    "utf8": "string",
}


def normalize_declared_dtype(dtype: type | str) -> str:
    """Return the canonical logical name for a declared dtype when known.

    Unknown declarations are retained as stable strings. This lets contracts
    written before dtype enforcement continue to load and receive a useful
    validation or lint diagnostic instead of failing during construction.
    """
    if isinstance(dtype, str):
        value = dtype.strip().lower()
    else:
        value = getattr(dtype, "__name__", str(dtype)).strip().lower()
    return _ALIASES.get(value, value)


def is_supported_dtype(dtype: type | str) -> bool:
    """Return whether ``dtype`` maps to a supported logical dtype."""
    return normalize_declared_dtype(dtype) in SUPPORTED_LOGICAL_DTYPES


def dtypes_compatible(expected: str, actual: str) -> bool:
    """Return whether an observed logical dtype satisfies a declaration.

    An all-null column has no observable value type, so it is compatible with
    every supported declaration. Nullability is enforced separately by the
    ``not_null`` constraint. Integer data also satisfies a float declaration,
    matching dqflow's existing integer-to-float widening semantics.
    """
    if expected not in SUPPORTED_LOGICAL_DTYPES:
        return False
    if actual == "null":
        return True
    return actual == expected or (expected == "float" and actual == "integer")


def dtype_details(expected: str, actual: str) -> dict[str, str]:
    """Build the stable structured details attached to a dtype check."""
    return {"expected_dtype": expected, "actual_dtype": actual}

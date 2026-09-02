"""Build a machine-readable description of dqflow's guaranteed public surface.

The three surfaces covered by the compatibility policy
(:doc:`docs/reference/stability`) are:

* the Python API re-exported from :mod:`dqflow` and :mod:`dqflow.schema`,
* the ``dq`` command-line interface (commands, options, arguments), and
* the ``--output json`` payload shapes for ``dq validate`` / ``dq diff`` /
  ``dq lint``.

``public_surface.json`` next to this file is the checked-in baseline.
``tests/test_public_api.py`` rebuilds this structure and fails on any drift, so
an accidental rename or signature change cannot ship silently. Regenerate the
baseline **deliberately**, as part of a reviewed change:

    python -m tests.api_surface.collect
"""

from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Any

import pandas as pd

import dqflow
import dqflow.schema as dqflow_schema
from dqflow import Column, Contract, diff_contracts
from dqflow.cli import main as cli_main
from dqflow.schema import lint_contract_data

SNAPSHOT_PATH = Path(__file__).with_name("public_surface.json")

#: Modules whose ``__all__`` is part of the stability guarantee.
_PUBLIC_MODULES = {"dqflow": dqflow, "dqflow.schema": dqflow_schema}


# --------------------------------------------------------------------------- #
# Python API
# --------------------------------------------------------------------------- #
def _signature(obj: Any) -> str | None:
    try:
        return str(inspect.signature(obj))
    except (TypeError, ValueError):
        return None


def _describe_constant(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (set, frozenset)):
        return {"type": type(value).__name__, "items": sorted(repr(v) for v in value)}
    if isinstance(value, (list, tuple)):
        return {"type": type(value).__name__, "items": [repr(v) for v in value]}
    return {"type": type(value).__name__, "repr": repr(value)}


def _defines_constructor(obj: type) -> bool:
    """Whether ``obj`` (not ``object``) defines its own ``__init__`` / ``__new__``."""
    return any(
        "__init__" in vars(klass) or "__new__" in vars(klass)
        for klass in obj.__mro__
        if klass is not object
    )


def _describe_class(obj: type) -> dict[str, Any]:
    # Skip the constructor signature for a class that only inherits object's
    # (e.g. the Engine ABC): it is not part of the API, and inspect renders it
    # differently across Python versions. The abstract methods are still captured.
    signature = _signature(obj) if _defines_constructor(obj) else None
    entry: dict[str, Any] = {"kind": "class", "signature": signature}
    if issubclass(obj, BaseException):
        entry["exception_bases"] = [b.__name__ for b in obj.__mro__[1:] if b is not object]
    members: dict[str, str] = {}
    for name, raw in sorted(vars(obj).items()):
        if name.startswith("_"):
            continue
        bound = getattr(obj, name)
        if isinstance(raw, property):
            members[name] = "property"
        elif isinstance(raw, staticmethod):
            members[name] = f"staticmethod {_signature(bound)}"
        elif isinstance(raw, classmethod):
            members[name] = f"classmethod {_signature(bound)}"
        elif inspect.isfunction(raw):
            members[name] = f"method {_signature(bound)}"
    entry["members"] = members
    return entry


def _describe_member(obj: Any) -> dict[str, Any]:
    if inspect.isclass(obj):
        return _describe_class(obj)
    if callable(obj):
        return {"kind": "function", "signature": _signature(obj)}
    return {"kind": "constant", "value": _describe_constant(obj)}


def _describe_module(module: Any) -> dict[str, Any]:
    names = sorted(module.__all__)
    return {
        "__all__": names,
        "members": {name: _describe_member(getattr(module, name)) for name in names},
    }


# --------------------------------------------------------------------------- #
# Command-line interface
# --------------------------------------------------------------------------- #
def _describe_click_type(click_type: Any) -> str:
    choices = getattr(click_type, "choices", None)
    if choices:
        return f"choice[{','.join(choices)}]"
    name = str(getattr(click_type, "name", type(click_type).__name__))
    if hasattr(click_type, "min") or hasattr(click_type, "max"):
        low, high = getattr(click_type, "min", None), getattr(click_type, "max", None)
        return f"{name}(min={low},max={high})"
    return name


def _describe_param(param: Any) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "name": param.name,
        "kind": param.param_type_name,  # "option" | "argument"
        "type": _describe_click_type(param.type),
        "required": bool(param.required),
    }
    if param.param_type_name == "option":
        opts = list(getattr(param, "opts", [])) + list(getattr(param, "secondary_opts", []))
        entry["opts"] = sorted(opts)
        entry["is_flag"] = bool(getattr(param, "is_flag", False))
    default = param.default
    if default is not None and not callable(default):
        entry["default"] = default
    return entry


def _describe_cli(group: Any) -> dict[str, Any]:
    return {
        "params": [_describe_param(p) for p in group.params],
        "commands": {
            name: {
                "help": bool(command.help),
                "params": [_describe_param(p) for p in command.params],
            }
            for name, command in sorted(group.commands.items())
        },
    }


# --------------------------------------------------------------------------- #
# JSON payload shapes
# --------------------------------------------------------------------------- #
def _shape(obj: Any) -> Any:
    """Reduce a JSON value to its structure: keys kept, scalars -> type names."""
    if isinstance(obj, dict):
        return {key: _shape(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [_shape(obj[0])] if obj else []
    return type(obj).__name__


def _payload_shapes() -> dict[str, Any]:
    old = Contract(name="orders", columns={"id": Column(str, not_null=True)})
    new = Contract(
        name="orders",
        columns={"id": Column(str, not_null=True), "amount": Column(float, min=0)},
    )
    validation = old.validate(pd.DataFrame({"id": ["a", None]}))
    contract_diff = diff_contracts(old, new)
    diagnostics = lint_contract_data({"name": "x", "columns": {"a": {"type": "not-a-type"}}})
    lint_payload = {
        "contract": "x.yaml",
        "ok": False,
        "error_count": len(diagnostics),
        "warning_count": 0,
        "diagnostics": [d.to_dict() for d in diagnostics],
    }
    return {
        "validate": _shape(validation.to_dict()),
        "diff": _shape(contract_diff.to_dict()),
        "lint": _shape(lint_payload),
    }


# --------------------------------------------------------------------------- #
# Assembly
# --------------------------------------------------------------------------- #
def build_surface() -> dict[str, Any]:
    """Return the full description of dqflow's guaranteed public surface."""
    return {
        "version": dqflow.__version__,
        "python_api": {name: _describe_module(module) for name, module in _PUBLIC_MODULES.items()},
        "cli": _describe_cli(cli_main),
        "json_payloads": _payload_shapes(),
    }


def dumps(surface: dict[str, Any]) -> str:
    """Serialise a surface to the canonical on-disk form (sorted, trailing newline)."""
    return json.dumps(surface, indent=2, sort_keys=True) + "\n"


def write_snapshot() -> None:
    SNAPSHOT_PATH.write_text(dumps(build_surface()), encoding="utf-8")


if __name__ == "__main__":
    write_snapshot()
    print(f"Wrote {SNAPSHOT_PATH.relative_to(Path.cwd())}")

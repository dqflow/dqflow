# Stability & compatibility

dqflow is pre-1.0 and still changing quickly. This page defines the **small set
of surfaces we treat as a compatibility contract**, how they may change, and how
that promise is enforced.

!!! note "Current status"
    dqflow is `0.x`. The policy below is already enforced in CI, but the
    guarantees only become *release blocking* at 1.0 — see the
    [1.0 readiness checklist](v1-readiness.md).

## What is covered

| Surface | Specifically |
| --- | --- |
| **Python API** | Every name exported from `dqflow` and `dqflow.schema` (their `__all__`), and the documented signatures of those functions, classes, and methods. |
| **CLI** | The `dq` sub-commands, their arguments and options, option names and value types, and defaults. |
| **Process exit codes** | `0` success, `1` a contract/data problem the caller asked to fail on, `2` incorrect invocation. See [CLI usage](../guide/cli.md). |
| **`--output json` payloads** | The key names and structure of `dq validate`, `dq diff`, and `dq lint` JSON output, and of `ValidationResult.to_dict()` / `ContractDiff.to_dict()` / `Diagnostic.to_dict()`. |
| **Contract format** | The YAML fields and the `schema_version` policy — governed separately in [Schema versioning](../guide/schema-versioning.md). |

A machine-readable description of the first four lives in
[`tests/api_surface/public_surface.json`](https://github.com/dqflow/dqflow/blob/main/tests/api_surface/public_surface.json).

## What is **not** covered

- Any module, class, function, or attribute not re-exported from `dqflow` /
  `dqflow.schema`, including everything under `dqflow.engines`, `dqflow.report`,
  `dqflow.rules`, `dqflow.cache`, `dqflow.execution` internals, and any name
  starting with `_`.
- The **Polars engine** (`dqflow[polars]`), which is explicitly experimental
  until [#25](https://github.com/dqflow/dqflow/issues/25).
- Human-readable (`--output text`) CLI output: wording, layout, colour, and the
  exact `details` keys attached to a failing check.
- Log messages, tracebacks, and the string form of exceptions (their **types**
  are covered).
- Performance characteristics and memory use.

If you depend on something in this list and need it stabilised, open an issue —
that is how a surface graduates into the table above.

## How versions change

dqflow follows [Semantic Versioning](https://semver.org/).

**Before 1.0 (`0.y.z`)**

- A `0.y.0` **minor** release may make a breaking change to a covered surface.
- Every such change is listed in [the changelog](../changelog.md) under a
  **Changed** or **Removed** heading with a one-line migration note.
- Bug-fix (`0.y.z`) releases never break a covered surface on purpose.

**From 1.0 onwards**

- Breaking changes to a covered surface happen only in a **major** release.
- Minor releases add things (new commands, new optional arguments, new keys in a
  JSON payload) without breaking existing use.

## Deprecation policy

Before a covered name, option, or field is removed or repurposed:

1. It is **deprecated for at least one minor release** while the old behaviour
   keeps working.
2. Using it emits a `DeprecationWarning` where that is possible (Python API,
   CLI).
3. The deprecation and its replacement are called out in
   [the changelog](../changelog.md), with a migration note when the change is
   mechanical.

New JSON payload keys can be added at any time, so consumers should ignore keys
they do not recognise rather than failing on them.

## How this is enforced

`tests/test_public_api.py` rebuilds the public surface by introspection on every
CI run and compares it to the committed snapshot. Any drift — a renamed export,
a changed signature, a new or removed CLI option, a reshaped JSON payload — fails
the build.

A deliberate change is made in three steps:

1. Make the code change.
2. Add a changelog entry, and update this page if the *set* of covered surfaces
   moved.
3. Regenerate the snapshot so the diff is reviewable:

    ```bash
    python -m tests.api_surface.collect
    ```

The snapshot diff in a pull request is the reviewer's signal that a
compatibility-relevant change is in play.

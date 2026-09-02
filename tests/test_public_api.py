"""dqflow's guaranteed public surface is pinned by a compatibility snapshot.

The snapshot (``tests/api_surface/public_surface.json``) covers the Python API
re-exported from :mod:`dqflow` / :mod:`dqflow.schema`, the ``dq`` CLI, and the
``--output json`` payload shapes. Any drift fails this test, so an accidental
rename, signature change, or dropped export cannot ship unnoticed.

When a change here is *deliberate*, weigh it against the compatibility policy in
``docs/reference/stability.md``, record it in ``CHANGELOG.md``, and regenerate
the snapshot:

    python -m tests.api_surface.collect

See ``tests/test_cli.py`` for the documented process exit codes, which are the
fourth part of the stability guarantee.
"""

from __future__ import annotations

import difflib

import pytest

from tests.api_surface.collect import SNAPSHOT_PATH, build_surface, dumps

_REGENERATE_HINT = (
    "If this change is intentional: review it against the compatibility policy in "
    "docs/reference/stability.md, record it in CHANGELOG.md, then regenerate the "
    "snapshot with\n    python -m tests.api_surface.collect"
)


def test_public_surface_matches_snapshot() -> None:
    expected = SNAPSHOT_PATH.read_text(encoding="utf-8")
    current = dumps(build_surface())

    if current != expected:
        diff = "\n".join(
            difflib.unified_diff(
                expected.splitlines(),
                current.splitlines(),
                fromfile="public_surface.json (committed)",
                tofile="public surface (current)",
                lineterm="",
            )
        )
        pytest.fail(
            f"dqflow's public surface changed.\n\n{diff}\n\n{_REGENERATE_HINT}",
            pytrace=False,
        )

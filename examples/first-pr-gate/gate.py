"""Run the pull-request contract gate exactly as CI does.

The three steps mirror ``.github/workflows/data-contract.yml``:

1. ``dq lint``     - the contract document is well-formed.
2. ``dq validate`` - the committed fixture still satisfies the current contract.
3. ``dq diff``     - the proposed revision does not tighten the contract in a way
   that would reject data producers already send.

Here ``proposed-orders.yaml`` tightens ``amount`` and drops ``GBP``, so step 3
fails and the script exits ``1`` - the same non-zero exit GitHub turns into a red
pull-request check.
"""

import subprocess
from pathlib import Path

HERE = Path(__file__).parent
CONTRACT = HERE / "contracts" / "orders.yaml"
PROPOSED = HERE / "proposed-orders.yaml"
DATA = HERE / "data" / "orders.csv"


def _run(*args: str) -> int:
    print(f"$ dq {' '.join(args)}", flush=True)
    code = subprocess.run(["dq", *args], check=False).returncode
    print(flush=True)
    return code


def main() -> int:
    if _run("lint", str(CONTRACT), "--strict"):
        return 1
    if _run("validate", str(CONTRACT), str(DATA), "--fail-fast"):
        return 1

    if _run("diff", str(CONTRACT), str(PROPOSED)):
        print("first-pr-gate: blocked a breaking contract change before merge", flush=True)
        return 1

    print("first-pr-gate: contract change is safe to merge", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Run the dq CLI exactly as a CI job would."""

import subprocess
from pathlib import Path

HERE = Path(__file__).parent


def main() -> None:
    subprocess.run(
        [
            "dq",
            "validate",
            str(HERE / "contract.yaml"),
            str(HERE / "data" / "users.csv"),
            "--fail-fast",
        ],
        check=True,
    )


if __name__ == "__main__":
    main()

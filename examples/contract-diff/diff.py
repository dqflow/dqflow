"""Compare two contract versions and gate a rollout on breaking changes."""

from pathlib import Path

from dqflow import diff_contracts

HERE = Path(__file__).parent


def main() -> int:
    result = diff_contracts(HERE / "orders-v1.yaml", HERE / "orders-v2.yaml")

    print(result.render_text())

    breaking = result.breaking_changes
    if breaking:
        print(f"\nblocked: {len(breaking)} breaking change(s) for data producers")
        return 1

    print("\nsafe to roll out")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

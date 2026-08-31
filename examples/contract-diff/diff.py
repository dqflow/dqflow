"""Compare two contract versions and gate a rollout on breaking changes."""

from pathlib import Path

from dqflow import diff_contracts

HERE = Path(__file__).parent


def main() -> None:
    result = diff_contracts(HERE / "orders-v1.yaml", HERE / "orders-v2.yaml")

    print(result.render_text())

    breaking = result.breaking_changes
    if breaking:
        print(f"\nblocked: {len(breaking)} breaking change(s) for data producers")
    else:
        print("\nsafe to roll out")


if __name__ == "__main__":
    main()

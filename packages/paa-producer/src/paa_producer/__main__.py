"""Minimal producer CLI placeholder."""

from __future__ import annotations

from paa_producer.commands import PRODUCER_COMMANDS


def main() -> int:
    print("paa-producer placeholder")
    print("commands:", ", ".join(PRODUCER_COMMANDS))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

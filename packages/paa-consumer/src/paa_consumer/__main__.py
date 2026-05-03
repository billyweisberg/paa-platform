"""Minimal consumer CLI placeholder."""

from __future__ import annotations

from paa_consumer.commands import CONSUMER_COMMANDS


def main() -> int:
    print("paa-consumer placeholder")
    print("commands:", ", ".join(CONSUMER_COMMANDS))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

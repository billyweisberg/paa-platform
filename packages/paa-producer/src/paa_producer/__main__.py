"""Minimal producer CLI placeholder."""

from __future__ import annotations

import argparse

from paa_producer.commands import PRODUCER_COMMANDS


def main() -> int:
    parser = argparse.ArgumentParser(prog="paa-producer")
    parser.add_argument("command", nargs="?", default="help")
    args = parser.parse_args()
    if args.command == "help":
        print("paa-producer placeholder")
        print("commands:", ", ".join(PRODUCER_COMMANDS))
        return 0
    print(f"command placeholder: {args.command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

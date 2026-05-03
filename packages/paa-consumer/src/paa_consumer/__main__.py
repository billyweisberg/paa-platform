"""Consumer CLI entrypoints."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from paa_core.install import install_authority_package, install_consumer_runtime
from paa_consumer.commands import CONSUMER_COMMANDS


def main() -> int:
    parser = argparse.ArgumentParser(prog="paa-consumer")
    parser.add_argument("command", nargs="?", default="help")
    parser.add_argument("--repo-root")
    parser.add_argument("--package-root")
    parser.add_argument("--authority-install-root")
    args = parser.parse_args()

    if args.command == "help":
        print("paa-consumer")
        print("commands:", ", ".join(CONSUMER_COMMANDS))
        return 0

    if args.command in {"install-consumer-runtime", "update-consumer-runtime"}:
        if not args.repo_root:
            parser.error(f"{args.command} requires --repo-root")
        result = install_consumer_runtime(Path(args.repo_root).resolve())
        print(
            json.dumps(
                {
                    "ok": True,
                    "install_mode": result.install_mode,
                    "repo_root": str(result.repo_root),
                    "codex_install_root": str(result.codex_install_root),
                    "runtime_data_root": str(result.runtime_data_root),
                    "platform_revision": result.platform_revision,
                },
                indent=2,
            )
        )
        return 0

    if args.command == "install-authority-package":
        if not args.repo_root or not args.package_root:
            parser.error("install-authority-package requires --repo-root and --package-root")
        destination = Path(args.authority_install_root).resolve() if args.authority_install_root else None
        result = install_authority_package(
            repo_root=Path(args.repo_root).resolve(),
            package_root=Path(args.package_root).resolve(),
            authority_install_root=destination,
        )
        print(
            json.dumps(
                {
                    "ok": True,
                    "repo_root": str(result.repo_root),
                    "package_root": str(result.package_root),
                    "authority_install_root": str(result.authority_install_root),
                },
                indent=2,
            )
        )
        return 0

    print(f"command placeholder: {args.command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

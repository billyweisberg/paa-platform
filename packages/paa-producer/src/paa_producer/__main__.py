"""Minimal producer CLI placeholder."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from paa_core.config import load_producer_project_config
from paa_producer.commands import PRODUCER_COMMANDS
from paa_producer.publish import publish_from_project_config


def main() -> int:
    parser = argparse.ArgumentParser(prog="paa-producer")
    parser.add_argument("command", nargs="?", default="help")
    parser.add_argument("--repo-root")
    parser.add_argument("--project-config")
    args = parser.parse_args()
    if args.command == "help":
        print("paa-producer placeholder")
        print("commands:", ", ".join(PRODUCER_COMMANDS))
        return 0
    if args.command == "publish-authority-package":
        if not args.repo_root or not args.project_config:
            parser.error("publish-authority-package requires --repo-root and --project-config")
        repo_root = Path(args.repo_root).resolve()
        config = load_producer_project_config(Path(args.project_config).resolve())
        result = publish_from_project_config(repo_root=repo_root, config=config)
        print(
            json.dumps(
                {
                    "ok": True,
                    "package_root": str(result.package_root),
                    "metadata_path": str(result.metadata_path),
                    "manifest_path": str(result.manifest_path),
                    "authority_version": result.authority_version,
                },
                indent=2,
            )
        )
        return 0
    print(f"command placeholder: {args.command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

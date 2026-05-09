#!/usr/bin/env python3
"""Append one JSONL automation event to the current run log."""

from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", required=True)
    parser.add_argument("--phase", required=True)
    parser.add_argument("--status", required=True)
    parser.add_argument("--message")
    parser.add_argument("--queue")
    parser.add_argument("--message-id")
    parser.add_argument("--model-invoked", action="store_true")
    parser.add_argument("--duration-ms", type=int)
    parser.add_argument("--cwd")
    parser.add_argument("--worktree-path")
    parser.add_argument("--extra-json")
    args = parser.parse_args()

    events_file = os.environ.get("PAA_AUTOMATION_EVENTS_FILE")
    run_id = os.environ.get("PAA_AUTOMATION_RUN_ID")
    automation_id = os.environ.get("PAA_AUTOMATION_RUN_DIR", "").split("/")[-2] if os.environ.get("PAA_AUTOMATION_RUN_DIR") else None
    role_key = os.environ.get("PAA_AUTOMATION_ROLE_KEY")
    role_display_name = os.environ.get("PAA_AUTOMATION_ROLE_DISPLAY_NAME")
    repo_root = os.environ.get("PAA_AUTOMATION_REPO_ROOT")
    if not events_file or not run_id:
        raise SystemExit("PAA_AUTOMATION_EVENTS_FILE and PAA_AUTOMATION_RUN_ID are required")

    payload = {
        "ts": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "run_id": run_id,
        "automation_id": automation_id,
        "role_key": role_key,
        "role_display_name": role_display_name,
        "phase": args.phase,
        "event": args.event,
        "status": args.status,
        "message": args.message,
        "queue": args.queue,
        "message_id": args.message_id,
        "model_invoked": args.model_invoked,
        "duration_ms": args.duration_ms,
        "cwd": args.cwd,
        "worktree_path": args.worktree_path,
        "repo_root": repo_root,
    }
    if args.extra_json:
        payload["extra"] = json.loads(args.extra_json)

    path = Path(events_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

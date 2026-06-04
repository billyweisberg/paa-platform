from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from paa_core.producer.authority_queries import build_issue_payload, task_or_die
from paa_core.producer.authority_support import load_manifest


def run_gh_issue_edit(repo: str, issue_number: int, title: str, body: str) -> None:
    with tempfile.NamedTemporaryFile('w', delete=False, suffix='.md') as tmp:
        tmp.write(body)
        tmp_path = tmp.name
    try:
        cmd = ['gh', 'issue', 'edit', str(issue_number), '-R', repo, '--title', title, '--body-file', tmp_path]
        subprocess.run(cmd, check=True)
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def run_gh_issue_create(repo: str, title: str, body: str) -> str:
    with tempfile.NamedTemporaryFile('w', delete=False, suffix='.md') as tmp:
        tmp.write(body)
        tmp_path = tmp.name
    try:
        cmd = ['gh', 'issue', 'create', '-R', repo, '--title', title, '--body-file', tmp_path]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def cmd_sync_issue(args: Any) -> None:
    manifest, data = load_manifest(args.manifest)
    task = task_or_die(data, issue_number=args.issue_number, task_id=args.task_id)
    payload = build_issue_payload(manifest, data, task)
    if not payload.get('ok'):
        print(json.dumps(payload, indent=2))
        sys.exit(1)
    if not payload.get('issue_number'):
        print(json.dumps({'ok': False, 'error': 'task has no issue_number; use create-issue instead', 'task_id': task['task_id']}, indent=2))
        sys.exit(1)
    run_gh_issue_edit(payload['repo'], payload['issue_number'], payload['title'], payload['body'])
    print(json.dumps({
        'ok': True,
        'action': 'synced',
        'repo': payload['repo'],
        'issue_number': payload['issue_number'],
        'task_id': task['task_id']
    }, indent=2))


def cmd_create_issue(args: Any) -> None:
    manifest, data = load_manifest(args.manifest)
    task = task_or_die(data, issue_number=args.issue_number, task_id=args.task_id)
    payload = build_issue_payload(manifest, data, task)
    if not payload.get('ok'):
        print(json.dumps(payload, indent=2))
        sys.exit(1)
    if payload.get('issue_number') and not args.force:
        print(json.dumps({'ok': False, 'error': 'task already has issue_number; use sync-issue or pass --force', 'issue_number': payload['issue_number'], 'task_id': task['task_id']}, indent=2))
        sys.exit(1)
    url = run_gh_issue_create(payload['repo'], payload['title'], payload['body'])
    print(json.dumps({
        'ok': True,
        'action': 'created',
        'repo': payload['repo'],
        'task_id': task['task_id'],
        'url': url
    }, indent=2))

from __future__ import annotations

from datetime import datetime, timezone
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from paa_core.producer.authority_support import load_manifest
from paa_core.producer.authority_resolution import find_task


def task_or_die(data: dict[str, Any], issue_number: int | None = None, task_id: str | None = None) -> dict[str, Any]:
    task = find_task(data, issue_number=issue_number, task_id=task_id)
    if not task:
        print(json.dumps({'ok': False, 'error': 'task not found'}, indent=2))
        sys.exit(1)
    return task


def bump_authority_version(current: str) -> str:
    today = datetime.now(timezone.utc).date().isoformat()
    if '.' in current:
        prefix, suffix = current.rsplit('.', 1)
        if prefix == today and suffix.isdigit():
            return f'{today}.{int(suffix) + 1}'
    return f'{today}.1'


def publish_authority(manifest: Path) -> None:
    script = manifest.parents[4] / 'tools' / 'codex-skills' / 'fractal-core-authority' / 'scripts' / 'publish_current.py'
    subprocess.run(['python3', str(script)], check=True, cwd=str(manifest.parents[4]))


def format_markdown_list(items: list[str]) -> str:
    return '\n'.join(f'- {item}' for item in items)


def build_issue_payload(manifest: Path, data: dict[str, Any], task: dict[str, Any]) -> dict[str, Any]:
    ops = data['operations']
    authoring = task.get('authoring') or {}
    missing = [
        key for key in [
            'objective', 'background', 'current_gap', 'acceptance_criteria',
            'validation_commands', 'out_of_scope', 'references'
        ] if key not in authoring
    ]
    if missing:
        return {
            'ok': False,
            'error': 'task authoring is incomplete',
            'missing_fields': missing,
            'task_id': task['task_id'],
            'issue_number': task.get('issue_number'),
        }

    title_prefix = ops.get('issue_title_prefix', '').strip()
    title = f"{title_prefix} {task['title']}".strip()
    body = '\n\n'.join([
        '## Objective\n' + authoring['objective'],
        '## Background\n' + format_markdown_list(authoring['background']),
        '## Current gap\n' + format_markdown_list(authoring['current_gap']),
        '## Acceptance criteria\n' + format_markdown_list(authoring['acceptance_criteria']),
        '## Validation\n```bash\n' + '\n'.join(authoring['validation_commands']) + '\n```',
        '## Out of scope\n' + format_markdown_list(authoring['out_of_scope']),
        '## References\n' + format_markdown_list(authoring['references']),
        '## Authority context\n' + format_markdown_list([
            f"authority version: {data['project']['authority_version']}",
            f"manifest path: {manifest}",
            f"milestone id: {task['milestone_id']}",
            f"phase id: {task['phase_id']}",
            f"task id: {task['task_id']}",
            f"requires QA: {task.get('requires_qa', False)}",
            f"merge policy: {task.get('merge_policy')}",
            'allowed successors: ' + (', '.join(task.get('allowed_successors', [])) or '(none)'),
        ])
    ])
    project = dict(data['project'])
    return {
        'ok': True,
        'manifest_path': str(manifest),
        'authority_version': project['authority_version'],
        'repo': project.get('repo'),
        'task_id': task['task_id'],
        'issue_number': task.get('issue_number'),
        'title': title,
        'body': body,
    }


def print_payload(payload: dict[str, Any], fmt: str) -> None:
    if fmt == 'markdown':
        print(f"# {payload['title']}\n")
        print(payload['body'])
    else:
        print(json.dumps(payload, indent=2))


def cmd_summary(args: Any) -> None:
    manifest, data = load_manifest(args.manifest)
    project = dict(data['project'])
    out = {
        'manifest_path': str(manifest),
        'project_id': project['project_id'],
        'authority_version': project['authority_version'],
        'published_at': project.get('published_at'),
        'repo': project.get('repo'),
        'active_phases': [p['phase_id'] for p in data.get('phases', []) if p.get('status') == 'active'],
        'active_tasks': [t['task_id'] for t in data.get('tasks', []) if t.get('status') in {'planned', 'in_dev', 'in_qa', 'in_review'}],
    }
    print(json.dumps(out, indent=2))


def cmd_current(args: Any) -> None:
    manifest, data = load_manifest(args.manifest)
    tasks = [t for t in data.get('tasks', []) if t.get('status') in {'in_dev', 'in_qa', 'in_review'}]
    print(json.dumps({'manifest_path': str(manifest), 'tasks': tasks}, indent=2))


def cmd_task(args: Any) -> None:
    manifest, data = load_manifest(args.manifest)
    task = task_or_die(data, issue_number=args.issue_number, task_id=args.task_id)
    print(json.dumps({'ok': True, 'manifest_path': str(manifest), 'task': task}, indent=2))


def cmd_next(args: Any) -> None:
    manifest, data = load_manifest(args.manifest)
    task = task_or_die(data, issue_number=args.issue_number, task_id=args.task_id)
    nxt = [find_task(data, task_id=t) for t in task.get('allowed_successors', [])]
    print(json.dumps({'ok': True, 'manifest_path': str(manifest), 'task_id': task['task_id'], 'allowed_successors': [t for t in nxt if t]}, indent=2))


def cmd_verify_issue(args: Any) -> None:
    manifest, data = load_manifest(args.manifest)
    task = find_task(data, issue_number=args.issue_number)
    if not task:
        print(json.dumps({'ok': False, 'issue_number': args.issue_number, 'authorized': False}, indent=2))
        sys.exit(1)
    print(json.dumps({'ok': True, 'manifest_path': str(manifest), 'issue_number': args.issue_number, 'authorized': True, 'task_id': task['task_id'], 'authority_version': data['project']['authority_version']}, indent=2))


def cmd_authoring_check(args: Any) -> None:
    manifest, data = load_manifest(args.manifest)
    task = task_or_die(data, issue_number=args.issue_number, task_id=args.task_id)
    payload = build_issue_payload(manifest, data, task)
    if not payload.get('ok'):
        print(json.dumps(payload, indent=2))
        sys.exit(1)
    print(json.dumps({
        'ok': True,
        'manifest_path': str(manifest),
        'task_id': task['task_id'],
        'issue_number': task.get('issue_number'),
        'authoring_complete': True
    }, indent=2))


def cmd_materialize_task(args: Any) -> None:
    manifest, data = load_manifest(args.manifest)
    task = task_or_die(data, issue_number=args.issue_number, task_id=args.task_id)
    payload = build_issue_payload(manifest, data, task)
    if not payload.get('ok'):
        print(json.dumps(payload, indent=2))
        sys.exit(1)
    print_payload(payload, args.format)


def cmd_materialize_next(args: Any) -> None:
    manifest, data = load_manifest(args.manifest)
    current = task_or_die(data, issue_number=args.issue_number, task_id=args.task_id)
    successors = [find_task(data, task_id=t) for t in current.get('allowed_successors', [])]
    successors = [t for t in successors if t]
    if len(successors) != 1:
        print(json.dumps({
            'ok': False,
            'error': 'expected exactly one allowed successor to materialize',
            'task_id': current['task_id'],
            'successor_count': len(successors)
        }, indent=2))
        sys.exit(1)
    payload = build_issue_payload(manifest, data, successors[0])
    if not payload.get('ok'):
        print(json.dumps(payload, indent=2))
        sys.exit(1)
    print_payload(payload, args.format)

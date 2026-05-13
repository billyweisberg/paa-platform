#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

PLATFORM_ROOT = Path(__file__).resolve().parents[2]


def resolve_consumer_repo() -> Path:
    configured = os.environ.get('PAA_CONSUMER_REPO')
    if configured:
        return Path(configured).expanduser().resolve()
    sibling_repo = PLATFORM_ROOT.parent / 'fractal-core-python'
    if sibling_repo.exists():
        return sibling_repo.resolve()
    raise RuntimeError('Set PAA_CONSUMER_REPO to the Fractal Core consumer repo root.')


CONSUMER_REPO = resolve_consumer_repo()
PACKAGE_ID = 'fcore-stage1-2026-05-02-issue106-retirement-boundary-diagnostics'
BRIEF_ID = 'fcore-coder-2026-05-02-issue106-retirement-boundary-diagnostics'
ISSUE_NUMBER = 106
PR_NUMBER = 107
ROLE_BRANCH = 'issue-106-dev-h6-fixture'
CANONICAL_BRANCH = 'issue-106'
WORKTREE_ROOT = Path(os.environ.get('PAA_ROLE_WORKTREE_ROOT', CONSUMER_REPO / '.codex-work' / 'worktrees' / 'paa'))
WORKTREE_PATH = WORKTREE_ROOT / ROLE_BRANCH
CREATED_ROLE_BRANCH = False

sys.path.insert(0, str(PLATFORM_ROOT / 'packages' / 'paa-core' / 'src'))
sys.path.insert(0, str(PLATFORM_ROOT / 'packages' / 'paa-consumer' / 'src'))

techlead = importlib.import_module('paa_consumer.techlead')
handoff_runtime = importlib.import_module('paa_core.handoff_runtime')


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd) if cwd else None, text=True, capture_output=True, check=False)


def ensure_disposable_worktree() -> None:
    global CREATED_ROLE_BRANCH
    WORKTREE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not techlead.git_local_branch_exists(CONSUMER_REPO, ROLE_BRANCH):
        result = run(['git', 'branch', ROLE_BRANCH, CANONICAL_BRANCH], cwd=CONSUMER_REPO)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or 'git branch failed')
        CREATED_ROLE_BRANCH = True
    existing = techlead.git_worktree_for_path(CONSUMER_REPO, WORKTREE_PATH)
    if existing is None:
        result = run(['git', 'worktree', 'add', str(WORKTREE_PATH), ROLE_BRANCH], cwd=CONSUMER_REPO)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or 'git worktree add failed')


def remove_leftovers() -> None:
    global CREATED_ROLE_BRANCH
    existing = techlead.git_worktree_for_path(CONSUMER_REPO, WORKTREE_PATH)
    if existing is not None:
        result = run(['git', 'worktree', 'remove', str(WORKTREE_PATH)], cwd=CONSUMER_REPO)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or 'git worktree remove failed')
    if WORKTREE_PATH.exists():
        raise RuntimeError(f'expected cleanup to remove {WORKTREE_PATH}')
    if CREATED_ROLE_BRANCH:
        result = run(['git', 'branch', '-D', ROLE_BRANCH], cwd=CONSUMER_REPO)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or 'git branch delete failed')
        CREATED_ROLE_BRANCH = False


def build_synthetic_qa_packet() -> Path:
    example_path = PLATFORM_ROOT / 'templates' / 'packet-examples' / 'qa_verification_packet.example.json'
    packet = handoff_runtime.load_json(example_path)
    packet['message_id'] = 'fcore-qa-2026-05-07-issue106-closed-cleanup-fixture'
    packet['correlation_id'] = 'issue-106'
    packet['github_context']['issue_number'] = ISSUE_NUMBER
    packet['github_context']['pr_number'] = PR_NUMBER
    packet['github_context']['branch'] = ROLE_BRANCH
    packet['github_context']['links'] = [
        f'https://github.com/billyweisberg/fractal-core-python/issues/{ISSUE_NUMBER}',
        f'https://github.com/billyweisberg/fractal-core-python/pull/{PR_NUMBER}',
    ]
    payload = packet['payload']
    payload['issue']['number'] = ISSUE_NUMBER
    payload['issue']['url'] = f'https://github.com/billyweisberg/fractal-core-python/issues/{ISSUE_NUMBER}'
    payload['pr']['number'] = PR_NUMBER
    payload['pr']['url'] = f'https://github.com/billyweisberg/fractal-core-python/pull/{PR_NUMBER}'
    payload['verification_status'] = 'pass'
    payload['recommended_action'] = {
        'merge_recommendation': 'merge',
        'next_step': 'TechLead may record the lineage as closed and retire the stale role execution surface.'
    }
    packet['authority_context']['task_id'] = 'py-p6-retirement-boundary-diagnostics-exposure'
    out_path = CONSUMER_REPO / '.project' / 'data' / 'paa' / 'reports' / 'phase-h6-closed-cleanup.synthetic-qa.json'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(packet, indent=2) + '\n')
    return out_path


def main() -> int:
    synthetic_qa_path = build_synthetic_qa_packet()
    ensure_disposable_worktree()
    original_build_lineage_view = techlead.build_lineage_view
    original_derive_decision_context = techlead.derive_decision_context
    fake_lineage_view = {
        'ok': True,
        'project_slug': 'fractal-core-python',
        'package_id_external': PACKAGE_ID,
        'brief_id_external': BRIEF_ID,
        'issue_number': ISSUE_NUMBER,
        'issue_url': f'https://github.com/billyweisberg/fractal-core-python/issues/{ISSUE_NUMBER}',
        'pr_number': PR_NUMBER,
        'pr_url': f'https://github.com/billyweisberg/fractal-core-python/pull/{PR_NUMBER}',
        'workflow_stage': 'slice_closed',
        'current_owner_role': 'TechLead',
        'lineage': {
            'canonical_branch': CANONICAL_BRANCH,
            'active_role_branch': ROLE_BRANCH,
            'branch_owner_role': 'TechLead',
            'lineage_state': 'closed',
            'latest_lineage_action': 'closed',
            'source_branch': CANONICAL_BRANCH,
            'superseded_branch': None,
            'worktree_hint': ROLE_BRANCH,
            'reset_reason': None,
            'current_packet_type': 'techlead_decision_packet',
            'current_packet_message_id': 'synthetic-closed-lineage',
            'current_packet_queue': 'fractal-core-architecture',
            'worktree_ownership': None,
            'worktree_staleness': None,
        },
        'source_packet_path': str(synthetic_qa_path),
        'recommended_actions': [],
        'unattended_safe': False,
        'ambiguity_reasons': [],
    }

    def fake_build_lineage_view(repo_root, project_slug, package_id_external, brief_id_external):
        return copy.deepcopy(fake_lineage_view)

    def fake_derive_decision_context(args):
        if args.decision_type != 'closed':
            return original_derive_decision_context(args)
        return {
            'ok': True,
            'workflow_stage': 'slice_closed',
            'issue_number': ISSUE_NUMBER,
            'issue_url': f'https://github.com/billyweisberg/fractal-core-python/issues/{ISSUE_NUMBER}',
            'pr_number': PR_NUMBER,
            'pr_url': f'https://github.com/billyweisberg/fractal-core-python/pull/{PR_NUMBER}',
            'branch': ROLE_BRANCH,
            'to_role': 'techlead',
            'target_role_cli': None,
            'decision_type': 'close_slice',
            'decision_rationale': 'Synthetic validation fixture for Phase H6 positive-path testing.',
            'next_assignment_type': None,
            'work_item_status_update_intent': 'accepted',
            'canonical_branch': CANONICAL_BRANCH,
            'role_branch': ROLE_BRANCH,
            'branch_owner_role': 'TechLead',
            'lineage_state': 'closed',
            'lineage_action': 'closed',
            'source_branch': CANONICAL_BRANCH,
            'superseded_branch': None,
            'worktree_hint': ROLE_BRANCH,
            'reset_reason': None,
            'source_packet_path': str(synthetic_qa_path),
            'recommended_actions': [],
            'unattended_safe': False,
        }

    techlead.build_lineage_view = fake_build_lineage_view
    techlead.derive_decision_context = fake_derive_decision_context
    try:
        args = SimpleNamespace(
            repo_root=CONSUMER_REPO,
            package_id_external=PACKAGE_ID,
            brief_id_external=BRIEF_ID,
            project_slug='fractal-core-python',
            target_role='python-team',
            role_branch=ROLE_BRANCH,
            worktree_path=WORKTREE_PATH,
            send_decision=False,
            source_packet_path=synthetic_qa_path,
            canonical_branch=CANONICAL_BRANCH,
            superseded_branch=None,
            worktree_hint=ROLE_BRANCH,
            reset_reason=None,
            output=CONSUMER_REPO / '.project' / 'data' / 'paa' / 'reports' / 'phase-h6-closed-cleanup.json',
            review_output=CONSUMER_REPO / '.project' / 'data' / 'paa' / 'reports' / 'phase-h6-closed-cleanup.md',
        )
        result = techlead.closed_cleanup(args)
    finally:
        techlead.build_lineage_view = original_build_lineage_view
        techlead.derive_decision_context = original_derive_decision_context

    print(json.dumps(result, indent=2))
    if not result.get('ok'):
        return 1
    if not result.get('cleanup_performed'):
        return 2
    cleanup_result = result.get('cleanup_result') or {}
    if not cleanup_result.get('role_branch_preserved'):
        return 3
    if not cleanup_result.get('canonical_branch_preserved'):
        return 4
    if techlead.git_worktree_for_path(CONSUMER_REPO, WORKTREE_PATH) is not None:
        return 5
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    finally:
        try:
            remove_leftovers()
        except Exception:
            pass

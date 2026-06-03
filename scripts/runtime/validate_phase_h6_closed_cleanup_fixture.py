#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

PLATFORM_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PLATFORM_ROOT / 'packages' / 'paa-core' / 'src'))

from paa_core.runtime.bridges.worktree import (  # noqa: E402
    DefaultRuntimeWorktreeService,
    RuntimeWorktreeCleanupRequest,
)

PACKAGE_ID = 'fcore-stage1-2026-05-02-issue106-retirement-boundary-diagnostics'
BRIEF_ID = 'fcore-coder-2026-05-02-issue106-retirement-boundary-diagnostics'
ISSUE_NUMBER = 106
ROLE_BRANCH = 'issue-106-dev-h6-fixture'
CANONICAL_BRANCH = 'issue-106'
WORKTREE_ROOT = Path(os.environ.get('PAA_ROLE_WORKTREE_ROOT', Path.cwd() / '.codex-work' / 'worktrees' / 'paa'))


def resolve_consumer_repo() -> Path:
    configured = os.environ.get('PAA_CONSUMER_REPO')
    if configured:
        return Path(configured).expanduser().resolve()
    sibling_repo = PLATFORM_ROOT.parent / 'fractal-core-python'
    if sibling_repo.exists():
        return sibling_repo.resolve()
    raise RuntimeError('Set PAA_CONSUMER_REPO to the Fractal Core consumer repo root.')


CONSUMER_REPO = resolve_consumer_repo()
WORKTREE_SERVICE = DefaultRuntimeWorktreeService()
WORKTREE_PATH = WORKTREE_ROOT / ROLE_BRANCH
CREATED_ROLE_BRANCH = False


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd) if cwd else None, text=True, capture_output=True, check=False)


def ensure_disposable_worktree() -> None:
    global CREATED_ROLE_BRANCH
    WORKTREE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not WORKTREE_SERVICE.git_local_branch_exists(CONSUMER_REPO, ROLE_BRANCH):
        result = run(['git', 'branch', ROLE_BRANCH, CANONICAL_BRANCH], cwd=CONSUMER_REPO)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or 'git branch failed')
        CREATED_ROLE_BRANCH = True
    existing = WORKTREE_SERVICE.git_worktree_for_path(CONSUMER_REPO, WORKTREE_PATH)
    if existing is None:
        result = run(['git', 'worktree', 'add', str(WORKTREE_PATH), ROLE_BRANCH], cwd=CONSUMER_REPO)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or 'git worktree add failed')


def remove_leftovers() -> None:
    global CREATED_ROLE_BRANCH
    existing = WORKTREE_SERVICE.git_worktree_for_path(CONSUMER_REPO, WORKTREE_PATH)
    if existing is not None:
        result = run(['git', 'worktree', 'remove', str(WORKTREE_PATH)], cwd=CONSUMER_REPO)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or 'git worktree remove failed')
    if CREATED_ROLE_BRANCH:
        result = run(['git', 'branch', '-D', ROLE_BRANCH], cwd=CONSUMER_REPO)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or 'git branch delete failed')
        CREATED_ROLE_BRANCH = False


def main() -> int:
    ensure_disposable_worktree()
    lineage_view = {
        'ok': True,
        'project_slug': 'fractal-core-python',
        'package_id_external': PACKAGE_ID,
        'brief_id_external': BRIEF_ID,
        'issue_number': ISSUE_NUMBER,
        'workflow_stage': 'slice_closed',
        'lineage': {
            'canonical_branch': CANONICAL_BRANCH,
            'active_role_branch': ROLE_BRANCH,
            'lineage_state': 'closed',
        },
    }
    ownership_view = WORKTREE_SERVICE.worktree_ownership_view(
        repo_root=CONSUMER_REPO,
        target_role='python-team',
        lineage_view=lineage_view,
        role_branch=ROLE_BRANCH,
        worktree_path=WORKTREE_PATH,
    )
    stale_view = WORKTREE_SERVICE.worktree_stale_view(
        repo_root=CONSUMER_REPO,
        target_role='python-team',
        lineage_view=lineage_view,
        role_branch=ROLE_BRANCH,
        worktree_path=WORKTREE_PATH,
    )
    decision_result = {'ok': True, 'workflow_stage': 'slice_closed', 'decision_type': 'close_slice'}
    result = WORKTREE_SERVICE.closed_cleanup(
        RuntimeWorktreeCleanupRequest(
            repo_root=CONSUMER_REPO,
            target_role='python-team',
            lineage_view=lineage_view,
            ownership_view=ownership_view,
            stale_view=stale_view,
            decision_result=decision_result,
        )
    )
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
    if WORKTREE_SERVICE.git_worktree_for_path(CONSUMER_REPO, WORKTREE_PATH) is not None:
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

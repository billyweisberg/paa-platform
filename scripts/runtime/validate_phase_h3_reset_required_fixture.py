#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

PLATFORM_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PLATFORM_ROOT / 'packages' / 'paa-core' / 'src'))

from paa_core.services.runtime_worktree import (  # noqa: E402
    DefaultRuntimeWorktreeService,
    RuntimeWorktreeCleanupRequest,
)

PACKAGE_ID = 'fcore-stage1-2026-05-02-issue106-retirement-boundary-diagnostics'
BRIEF_ID = 'fcore-coder-2026-05-02-issue106-retirement-boundary-diagnostics'
ISSUE_NUMBER = 106
ROLE_BRANCH = 'issue-106-dev'


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


def main() -> int:
    lineage_view = {
        'ok': True,
        'project_slug': 'fractal-core-python',
        'package_id_external': PACKAGE_ID,
        'brief_id_external': BRIEF_ID,
        'issue_number': ISSUE_NUMBER,
        'workflow_stage': 'dev_reset_required',
        'lineage': {
            'canonical_branch': 'issue-106',
            'active_role_branch': ROLE_BRANCH,
            'lineage_state': 'reset_required',
        },
    }
    ownership_view = WORKTREE_SERVICE.worktree_ownership_view(
        repo_root=CONSUMER_REPO,
        target_role='python-team',
        lineage_view=lineage_view,
        role_branch=ROLE_BRANCH,
    )
    stale_view = WORKTREE_SERVICE.worktree_stale_view(
        repo_root=CONSUMER_REPO,
        target_role='python-team',
        lineage_view=lineage_view,
        role_branch=ROLE_BRANCH,
    )
    decision_result = {
        'ok': True,
        'workflow_stage': 'dev_reset_required',
        'decision_type': 'reset_branch',
    }
    result = WORKTREE_SERVICE.reset_required_lifecycle(
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
    if result.get('workflow_stage') != 'dev_reset_required':
        return 2
    if not result.get('cleanup_candidate'):
        return 3
    if not (result.get('decision_result') or {}).get('ok'):
        return 4
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib
import json
import os
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

sys.path.insert(0, str(PLATFORM_ROOT / 'packages' / 'paa-core' / 'src'))
sys.path.insert(0, str(PLATFORM_ROOT / 'packages' / 'paa-consumer' / 'src'))

techlead = importlib.import_module('paa_consumer.techlead')
handoff_runtime = importlib.import_module('paa_core.handoff_runtime')


def build_synthetic_qa_packet() -> Path:
    example_path = PLATFORM_ROOT / 'templates' / 'packet-examples' / 'qa_verification_packet.example.json'
    packet = handoff_runtime.load_json(example_path)
    packet['message_id'] = 'fcore-qa-2026-05-07-issue106-reset-fixture'
    packet['correlation_id'] = 'issue-106'
    packet['github_context']['issue_number'] = ISSUE_NUMBER
    packet['github_context']['pr_number'] = PR_NUMBER
    packet['github_context']['branch'] = 'issue-106-dev'
    packet['github_context']['links'] = [
        f'https://github.com/billyweisberg/fractal-core-python/issues/{ISSUE_NUMBER}',
        f'https://github.com/billyweisberg/fractal-core-python/pull/{PR_NUMBER}',
    ]
    payload = packet['payload']
    payload['issue']['number'] = ISSUE_NUMBER
    payload['issue']['url'] = f'https://github.com/billyweisberg/fractal-core-python/issues/{ISSUE_NUMBER}'
    payload['pr']['number'] = PR_NUMBER
    payload['pr']['url'] = f'https://github.com/billyweisberg/fractal-core-python/pull/{PR_NUMBER}'
    payload['verification_status'] = 'needs_human_review'
    payload['recommended_action'] = {
        'merge_recommendation': 'do_not_merge',
        'next_step': 'TechLead should record a reset-required recovery decision.'
    }
    packet['authority_context']['task_id'] = 'py-p6-retirement-boundary-diagnostics-exposure'
    out_path = CONSUMER_REPO / '.project' / 'data' / 'paa' / 'reports' / 'phase-h3-reset-required.synthetic-qa.json'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(packet, indent=2) + '\n')
    return out_path


def main() -> int:
    synthetic_qa_path = build_synthetic_qa_packet()
    original_build_lineage_view = techlead.build_lineage_view
    fake_lineage_view = {
        'ok': True,
        'project_slug': 'fractal-core-python',
        'package_id_external': PACKAGE_ID,
        'brief_id_external': BRIEF_ID,
        'issue_number': ISSUE_NUMBER,
        'issue_url': f'https://github.com/billyweisberg/fractal-core-python/issues/{ISSUE_NUMBER}',
        'pr_number': PR_NUMBER,
        'pr_url': f'https://github.com/billyweisberg/fractal-core-python/pull/{PR_NUMBER}',
        'workflow_stage': 'dev_reset_required',
        'current_owner_role': 'Python Dev',
        'lineage': {
            'canonical_branch': 'issue-106',
            'active_role_branch': 'issue-106-dev',
            'branch_owner_role': 'TechLead',
            'lineage_state': 'reset_required',
            'latest_lineage_action': 'reset',
            'source_branch': 'issue-106',
            'superseded_branch': 'issue-106-dev',
            'worktree_hint': 'issue-106-dev',
            'reset_reason': 'Synthetic validation fixture for Phase H3 positive-path testing.',
            'current_packet_type': 'techlead_decision_packet',
            'current_packet_message_id': 'synthetic-reset-required-lineage',
            'current_packet_queue': 'fractal-core-architecture',
            'worktree_ownership': None,
            'worktree_staleness': None,
        },
        'source_packet_path': str(synthetic_qa_path),
        'recommended_actions': [
            {
                'priority': 1,
                'action_type': 'route_to_python',
                'reason': 'Synthetic Phase H3 fixture requires a reset-required recovery path.',
                'target_role': 'Python Dev',
                'blocking': True,
            }
        ],
        'unattended_safe': False,
        'ambiguity_reasons': [],
    }

    def fake_build_lineage_view(repo_root, project_slug, package_id_external, brief_id_external):
        return copy.deepcopy(fake_lineage_view)

    techlead.build_lineage_view = fake_build_lineage_view
    try:
        args = SimpleNamespace(
            repo_root=CONSUMER_REPO,
            package_id_external=PACKAGE_ID,
            brief_id_external=BRIEF_ID,
            project_slug='fractal-core-python',
            target_role='python-team',
            role_branch='issue-106-dev',
            worktree_path=None,
            send_decision=False,
            source_packet_path=synthetic_qa_path,
            canonical_branch='issue-106',
            superseded_branch='issue-106-dev',
            worktree_hint='issue-106-dev',
            reset_reason='Synthetic validation fixture for Phase H3 positive-path testing.',
            output=CONSUMER_REPO / '.project' / 'data' / 'paa' / 'reports' / 'phase-h3-reset-required.json',
            review_output=CONSUMER_REPO / '.project' / 'data' / 'paa' / 'reports' / 'phase-h3-reset-required.md',
        )
        result = techlead.reset_required_lifecycle(args)
    finally:
        techlead.build_lineage_view = original_build_lineage_view

    print(json.dumps(result, indent=2))
    if not result.get('ok'):
        return 1
    if result.get('workflow_stage') != 'dev_reset_required':
        return 2
    if not result.get('cleanup_candidate'):
        return 3
    decision_result = result.get('decision_result') or {}
    if not decision_result.get('ok'):
        return 4
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

from __future__ import annotations

import json
import stat
import subprocess
import tempfile
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))

from paa_core.runtime.bridges.decision import (
    DefaultRuntimeDecisionBridgeService,
    RuntimeDecisionBridgeRequest,
)


def _git(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ['git', *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


class _StubQueueAdminService:
    def __init__(self) -> None:
        self.sent: list[Path] = []

    def validate_packet(self, *, repo_root: Path, message_file: Path):
        packet = json.loads(message_file.read_text())
        return ({
            'ok': True,
            'message_file': str(message_file),
            'message_id': packet['message_id'],
            'schema_type': packet['schema_type'],
            'resolved_queue': 'paa-techlead',
            'from_role': packet['from_role'],
            'to_role': packet['to_role'],
        }, 0)

    def send_packet(self, *, repo_root: Path, message_file: Path):
        self.sent.append(message_file)
        packet = json.loads(message_file.read_text())
        return ({
            'ok': True,
            'message_file': str(message_file),
            'message_id': packet['message_id'],
            'schema_type': packet['schema_type'],
            'resolved_queue': 'paa-techlead',
            'from_role': packet['from_role'],
            'to_role': packet['to_role'],
        }, 0)


class RuntimeDecisionBridgeServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self._tempdir.name) / 'repo'
        self.repo_root.mkdir(parents=True, exist_ok=True)
        _git(self.repo_root, 'init', '-b', 'issue-6')
        _git(self.repo_root, 'config', 'user.name', 'Test User')
        _git(self.repo_root, 'config', 'user.email', 'test@example.com')
        (self.repo_root / 'README.md').write_text('decision bridge\n')
        _git(self.repo_root, 'add', 'README.md')
        _git(self.repo_root, 'commit', '-m', 'initial')
        _git(self.repo_root, 'remote', 'add', 'origin', 'git@github.com:billyweisberg/paa-platform.git')

        manifest_dir = self.repo_root / '.project' / 'data' / 'paa' / 'authority' / 'current' / 'authority'
        manifest_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_path = manifest_dir / 'fractal-core-python-authority.json'
        self.manifest_path.write_text('{}\n')

        bin_dir = self.repo_root / '.codex' / 'paa' / 'bin'
        bin_dir.mkdir(parents=True, exist_ok=True)
        producer = bin_dir / 'paa-producer'
        producer.write_text(
            """#!/usr/bin/env python3
import json
import sys
from pathlib import Path

args = sys.argv[1:]
out = Path(args[args.index('--output') + 1])
review = Path(args[args.index('--review-output') + 1])
out.parent.mkdir(parents=True, exist_ok=True)
review.parent.mkdir(parents=True, exist_ok=True)
packet = {
  'message_id': 'decision-1',
  'schema_type': 'techlead_decision_packet',
  'schema_version': '1.0',
  'project': 'paa-platform',
  'from_role': 'TechLead',
  'to_role': 'TechLead',
  'created_at': '2026-06-02T00:00:00Z',
  'correlation_id': 'corr-1',
  'authority_context': {
    'manifest_path': 'authority.json',
    'authority_version': '1',
    'milestone_id': 'm1',
    'phase_id': 'p1',
    'task_id': 'issue-6'
  },
  'github_context': {
    'repo': 'billyweisberg/paa-platform',
    'issue_number': 6,
    'pr_number': 11,
    'branch': 'issue-6',
    'links': {'issue': 'https://example.test/issues/6', 'pr': 'https://example.test/pulls/11'}
  },
  'payload': {
    'issue': {'number': 6},
    'pr': {'number': 11},
    'source_packet_ref': {'path': 'source.json'},
    'decision_type': 'closed',
    'decision_rationale': 'close it',
    'target_role': 'TechLead',
    'next_assignment_type': 'none',
    'canonical_branch': 'issue-6',
    'role_branch': 'issue-6-dev',
    'branch_owner_role': 'TechLead',
    'lineage_state': 'closed',
    'lineage_action': 'retain',
    'source_branch': 'issue-6',
    'superseded_branch': None,
    'worktree_hint': 'issue-6-dev',
    'reset_reason': None,
    'work_item_status_update_intent': 'close'
  }
}
out.write_text(json.dumps(packet, indent=2) + '\\n')
review.write_text('decision review\\n')
print(json.dumps({'message_id': 'decision-1', 'automation_run_id': 'run-1'}))
"""
        )
        producer.chmod(producer.stat().st_mode | stat.S_IEXEC)
        self.queue_admin = _StubQueueAdminService()
        self.service = DefaultRuntimeDecisionBridgeService(queue_admin_service=self.queue_admin)

    def tearDown(self) -> None:
        self._tempdir.cleanup()

    def test_emit_decision_compiles_and_validates(self) -> None:
        result = self.service.emit_decision(
            RuntimeDecisionBridgeRequest(
                repo_root=self.repo_root,
                project_slug='paa-platform',
                package_id_external='pkg-1',
                brief_id_external='brief-1',
                issue_number=6,
                issue_url='https://example.test/issues/6',
                pr_number=11,
                pr_url='https://example.test/pulls/11',
                branch='issue-6',
                canonical_branch='issue-6',
                to_role='TechLead',
                decision_type='closed',
                decision_rationale='close it',
                work_item_status_update_intent='close',
                source_packet_path='source.json',
                branch_owner_role='TechLead',
                lineage_state='closed',
                lineage_action='retain',
                workflow_stage='awaiting_acceptance',
                target_role_cli='techlead',
                next_assignment_type='none',
                role_branch='issue-6-dev',
                worktree_hint='issue-6-dev',
                output_path=self.repo_root / '.project' / 'data' / 'paa' / 'reports' / 'decision.json',
                review_output_path=self.repo_root / '.project' / 'data' / 'paa' / 'reports' / 'decision.md',
                send=False,
            )
        )

        self.assertTrue(result['ok'])
        self.assertFalse(result['sent'])
        self.assertEqual(result['message_id'], 'decision-1')
        self.assertEqual(result['resolved_queue'], 'paa-techlead')
        self.assertTrue(Path(result['output_path']).exists())

    def test_emit_decision_send_uses_queue_admin(self) -> None:
        result = self.service.emit_decision(
            RuntimeDecisionBridgeRequest(
                repo_root=self.repo_root,
                project_slug='paa-platform',
                package_id_external='pkg-1',
                brief_id_external='brief-1',
                issue_number=6,
                issue_url='https://example.test/issues/6',
                pr_number=11,
                pr_url='https://example.test/pulls/11',
                branch='issue-6',
                canonical_branch='issue-6',
                to_role='TechLead',
                decision_type='closed',
                decision_rationale='close it',
                work_item_status_update_intent='close',
                source_packet_path='source.json',
                branch_owner_role='TechLead',
                lineage_state='closed',
                lineage_action='retain',
                workflow_stage='awaiting_acceptance',
                target_role_cli='techlead',
                next_assignment_type='none',
                role_branch='issue-6-dev',
                worktree_hint='issue-6-dev',
                send=True,
            )
        )

        self.assertTrue(result['ok'])
        self.assertTrue(result['sent'])
        self.assertEqual(len(self.queue_admin.sent), 1)


if __name__ == '__main__':
    unittest.main()

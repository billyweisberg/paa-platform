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

from paa_core.services.runtime_assignment_bridge import (
    DefaultRuntimeAssignmentBridgeService,
    RuntimeAssignmentBridgeRequest,
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
        self.claimed: list[tuple[str, str]] = []
        self.acked: list[str] = []

    def validate_packet(self, *, repo_root: Path, message_file: Path):
        packet = json.loads(message_file.read_text())
        return ({
            'ok': True,
            'message_file': str(message_file),
            'message_id': packet['message_id'],
            'schema_type': packet['schema_type'],
            'resolved_queue': 'paa-qa',
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
            'resolved_queue': 'paa-qa',
            'from_role': packet['from_role'],
            'to_role': packet['to_role'],
        }, 0)

    def list_claims(self, *, repo_root: Path, queue: str, status: str):
        return {'claims': []}

    def claim_next(self, *, repo_root: Path, queue: str, claimed_by: str):
        self.claimed.append((queue, claimed_by))
        return ({'ok': True, 'claimed': True, 'claim_id': 'claim-1', 'message_id': 'worker-1'}, 0)

    def ack(self, *, repo_root: Path, claim_id: str):
        self.acked.append(claim_id)
        return {'ok': True, 'claim_id': claim_id, 'status': 'done'}

    def requeue(self, *, repo_root: Path, claim_id: str):
        return ({'ok': True, 'claim_id': claim_id, 'status': 'queued'}, 0)


class RuntimeAssignmentBridgeServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self._tempdir.name) / 'repo'
        self.repo_root.mkdir(parents=True, exist_ok=True)
        _git(self.repo_root, 'init', '-b', 'issue-6')
        _git(self.repo_root, 'config', 'user.name', 'Test User')
        _git(self.repo_root, 'config', 'user.email', 'test@example.com')
        (self.repo_root / 'README.md').write_text('assignment bridge\n')
        _git(self.repo_root, 'add', 'README.md')
        _git(self.repo_root, 'commit', '-m', 'initial')

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
to_role = args[args.index('--target-role') + 1]
assignment_type = args[args.index('--assignment-type') + 1]
allowed = []
for idx, value in enumerate(args):
    if value == '--allowed-result-type':
        allowed.append(args[idx + 1])
packet = {
  'message_id': 'assign-1',
  'schema_type': 'techlead_assignment_packet',
  'schema_version': '1.0',
  'project': 'paa-platform',
  'from_role': 'TechLead',
  'to_role': to_role,
  'created_at': '2026-06-02T00:00:00Z',
  'correlation_id': 'corr-1',
  'authority_context': {'manifest_path': 'authority.json', 'authority_version': '1', 'milestone_id': 'm1', 'phase_id': 'p1', 'task_id': 'issue-6'},
  'github_context': {'repo': 'billyweisberg/paa-platform', 'issue_number': 6, 'pr_number': 11, 'branch': 'issue-6', 'links': {'issue': 'https://example.test/issues/6', 'pr': 'https://example.test/pulls/11'}},
  'payload': {
    'issue': {'number': 6},
    'pr': {'number': 11},
    'target_role': to_role,
    'assignment_type': assignment_type,
    'allowed_result_types': allowed
  }
}
out.parent.mkdir(parents=True, exist_ok=True)
review.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(packet, indent=2) + '\\n')
review.write_text('assignment review\\n')
print(json.dumps({'message_id': 'assign-1', 'automation_run_id': 'run-1'}))
"""
        )
        producer.chmod(producer.stat().st_mode | stat.S_IEXEC)
        self.queue_admin = _StubQueueAdminService()
        self.service = DefaultRuntimeAssignmentBridgeService(queue_admin_service=self.queue_admin)
        self.source_packet_path = self.repo_root / 'source-worker.json'
        self.source_packet_path.write_text(json.dumps({
            'message_id': 'worker-1',
            'schema_type': 'worker_result_packet',
            'project': 'paa-platform',
            'to_role': 'techlead',
            'from_role': 'Dev',
        }) + '\n')

    def tearDown(self) -> None:
        self._tempdir.cleanup()

    def test_emit_next_assignment_compiles_and_validates(self) -> None:
        result = self.service.emit_next_assignment(
            RuntimeAssignmentBridgeRequest(
                repo_root=self.repo_root,
                project_slug='paa-platform',
                package_id_external='pkg-1',
                brief_id_external='brief-1',
                github_repo='billyweisberg/paa-platform',
                issue_number=6,
                issue_url='https://example.test/issues/6',
                pr_number=11,
                pr_url='https://example.test/pulls/11',
                branch='issue-6',
                workflow_stage='techlead_worker_review_pending',
                target_role='QA',
                target_role_cli='qa',
                assignment_type='verify_authorized_slice',
                assignment_summary='send to qa',
                allowed_result_types=('pass', 'fail_fixable'),
                source_packet_message_id='worker-1',
                source_packet_path=str(self.source_packet_path),
                send=False,
            )
        )

        self.assertTrue(result['ok'])
        self.assertFalse(result['sent'])
        self.assertEqual(result['message_id'], 'assign-1')
        self.assertEqual(result['resolved_queue'], 'paa-qa')
        self.assertTrue(Path(result['output_path']).exists())

    def test_emit_next_assignment_send_and_acknowledges_source(self) -> None:
        result = self.service.emit_next_assignment(
            RuntimeAssignmentBridgeRequest(
                repo_root=self.repo_root,
                project_slug='paa-platform',
                package_id_external='pkg-1',
                brief_id_external='brief-1',
                github_repo='billyweisberg/paa-platform',
                issue_number=6,
                issue_url='https://example.test/issues/6',
                pr_number=11,
                pr_url='https://example.test/pulls/11',
                branch='issue-6',
                workflow_stage='techlead_worker_review_pending',
                target_role='QA',
                target_role_cli='qa',
                assignment_type='verify_authorized_slice',
                assignment_summary='send to qa',
                allowed_result_types=('pass',),
                source_packet_message_id='worker-1',
                source_packet_path=str(self.source_packet_path),
                send=True,
            )
        )

        self.assertTrue(result['ok'])
        self.assertTrue(result['sent'])
        self.assertEqual(len(self.queue_admin.sent), 1)
        self.assertEqual(self.queue_admin.claimed, [('paa-techlead', 'techlead-emit-next-assignment')])
        self.assertEqual(self.queue_admin.acked, ['claim-1'])
        self.assertEqual(result['source_packet_ack']['ack_mode'], 'claim_then_ack')


if __name__ == '__main__':
    unittest.main()

from __future__ import annotations

import json
import os
import stat
import subprocess
import tempfile
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))

from paa_core.runtime.bridges.role_bridge import (
    DefaultRuntimeRoleBridgeService,
    RuntimeRoleEntryRequest,
    RuntimeRoleResultAssistRequest,
    RuntimeRoleReturnBridgeRequest,
)
from paa_core.runtime.bridges.worktree import (
    DefaultRuntimeWorktreeService,
    RuntimeWorktreePrepareRequest,
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


class RuntimeRoleBridgeServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self._original_branch_suffix = dict(DefaultRuntimeWorktreeService._STATIC_ROLE_BRANCH_SUFFIX)
        self._original_role_labels = dict(DefaultRuntimeWorktreeService._STATIC_ROLE_LABEL_BY_CLI)
        DefaultRuntimeWorktreeService._STATIC_ROLE_BRANCH_SUFFIX.setdefault('python-team', 'dev')
        DefaultRuntimeWorktreeService._STATIC_ROLE_LABEL_BY_CLI.setdefault('python-team', 'Dev')

        self._tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self._tempdir.name) / 'repo'
        self.repo_root.mkdir(parents=True, exist_ok=True)
        _git(self.repo_root, 'init', '-b', 'issue-6')
        _git(self.repo_root, 'config', 'user.name', 'Test User')
        _git(self.repo_root, 'config', 'user.email', 'test@example.com')
        (self.repo_root / 'README.md').write_text('runtime role bridge test\n')
        _git(self.repo_root, 'add', 'README.md')
        _git(self.repo_root, 'commit', '-m', 'initial')

        self.worktree_service = DefaultRuntimeWorktreeService()
        self.service = DefaultRuntimeRoleBridgeService(worktree_service=self.worktree_service)
        self.lineage_view = {
            'ok': True,
            'issue_number': 6,
            'issue_url': 'https://example.test/issues/6',
            'pr_number': 11,
            'pr_url': 'https://example.test/pulls/11',
            'workflow_stage': 'qa_execution_in_progress',
            'package_id_external': 'pkg-1',
            'brief_id_external': 'brief-1',
            'lineage': {
                'canonical_branch': 'issue-6',
                'lineage_state': 'active',
                'branch_owner_role': 'TechLead',
                'worktree_hint': 'issue-6-qa',
            },
        }
        self.prepare_result = self.worktree_service.prepare_role_worktree(
            RuntimeWorktreePrepareRequest(
                repo_root=self.repo_root,
                target_role='qa',
                lineage_view=self.lineage_view,
            )
        )
        self.assertTrue(self.prepare_result['ok'])
        self.assignment_path, self.assignment_review_path = self.worktree_service.default_assignment_paths(
            self.repo_root,
            6,
            'QA',
        )
        self.assignment_path.parent.mkdir(parents=True, exist_ok=True)
        self.assignment_path.write_text(json.dumps({
            'message_id': 'assign-1',
            'schema_type': 'techlead_assignment_packet',
            'payload': {
                'target_role': 'QA',
                'assignment_type': 'verify_authorized_slice',
                'assignment_summary': 'Verify authorized slice.',
                'allowed_result_types': ['pass'],
                'canonical_branch': 'issue-6',
                'role_branch': 'issue-6-qa',
                'worktree_hint': 'issue-6-qa',
            },
        }, indent=2) + '\n')
        self.assignment_review_path.write_text('review\n')
        self.result_input_path = self.service.default_result_input_path(self.repo_root, 6, 'QA')
        self.result_input_path.parent.mkdir(parents=True, exist_ok=True)
        self.result_input_path.write_text(json.dumps({'verification_status': 'pass'}) + '\n')
        self._install_fake_producer()

    def tearDown(self) -> None:
        DefaultRuntimeWorktreeService._STATIC_ROLE_BRANCH_SUFFIX = self._original_branch_suffix
        DefaultRuntimeWorktreeService._STATIC_ROLE_LABEL_BY_CLI = self._original_role_labels
        self._tempdir.cleanup()

    def _install_fake_producer(self) -> None:
        bin_dir = self.repo_root / '.codex' / 'paa' / 'bin'
        bin_dir.mkdir(parents=True, exist_ok=True)
        script = bin_dir / 'paa-producer'
        script.write_text(
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
  'message_id': 'qa-result-1',
  'schema_type': 'qa_verification_packet',
  'schema_version': '1.0',
  'project': 'paa-platform',
  'from_role': 'QA',
  'to_role': 'TechLead',
  'created_at': '2026-06-02T00:00:00Z',
  'correlation_id': 'corr-1',
  'authority_context': {
    'manifest_path': 'authority.json',
    'authority_version': '1',
    'milestone_id': 'm1',
    'phase_id': 'p1',
    'task_id': 'issue-6',
  },
  'github_context': {
    'repo': 'billyweisberg/paa-platform',
    'issue_number': 6,
    'pr_number': 11,
    'branch': 'issue-6-qa',
    'links': {'issue': 'https://example.test/issues/6', 'pr': 'https://example.test/pulls/11'}
  },
  'payload': {
    'issue': {'number': 6},
    'pr': {'number': 11},
    'verification_status': 'pass',
    'verification_scope': 'slice',
    'mechanical_checks': [],
    'technical_scope_checks': [],
    'protected_path_checks': [],
    'artifact_checks': [],
    'findings': [],
    'recommended_action': 'accept',
  }
}
out.write_text(json.dumps(packet, indent=2) + '\\n')
review.write_text('qa review\\n')
print(json.dumps({'ok': True, 'output_path': str(out), 'review_output_path': str(review)}))
"""
        )
        script.chmod(script.stat().st_mode | stat.S_IEXEC)

    def test_role_entry_helper_returns_manual_entry_surfaces(self) -> None:
        result = self.service.role_entry_helper(
            RuntimeRoleEntryRequest(
                repo_root=self.repo_root,
                package_id_external='pkg-1',
                brief_id_external='brief-1',
                project_slug='paa-platform',
                target_role='qa',
                lineage_view=self.lineage_view,
            )
        )

        self.assertTrue(result['ok'])
        self.assertEqual(result['target_role'], 'QA')
        self.assertIn('materialize-qa-verification-packet', result['manual_execution_surfaces']['result_compile_command'])

    def test_role_result_assist_builds_result_contract(self) -> None:
        result = self.service.role_result_assist(
            RuntimeRoleResultAssistRequest(
                repo_root=self.repo_root,
                package_id_external='pkg-1',
                brief_id_external='brief-1',
                project_slug='paa-platform',
                target_role='qa',
                lineage_view=self.lineage_view,
            )
        )

        self.assertTrue(result['ok'])
        self.assertEqual(result['result_family'], 'qa_verification_packet')
        self.assertEqual(result['required_context']['issue_number'], 6)
        self.assertEqual(Path(result['manual_result_surfaces']['result_input_template_path']).resolve(), self.result_input_path.resolve())

    def test_role_return_bridge_compiles_and_validates_packet(self) -> None:
        output_path = self.repo_root / '.project' / 'data' / 'paa' / 'reports' / 'compiled.json'
        review_output_path = self.repo_root / '.project' / 'data' / 'paa' / 'reports' / 'compiled.md'
        result = self.service.role_return_bridge(
            RuntimeRoleReturnBridgeRequest(
                repo_root=self.repo_root,
                package_id_external='pkg-1',
                brief_id_external='brief-1',
                project_slug='paa-platform',
                target_role='qa',
                lineage_view=self.lineage_view,
                result_input_path=self.result_input_path,
                output_path=output_path,
                review_output_path=review_output_path,
            )
        )

        self.assertTrue(result['ok'])
        self.assertFalse(result['sent'])
        self.assertEqual(result['resolved_queue'], 'paa-techlead')
        self.assertEqual(Path(result['output_path']).resolve(), output_path.resolve())
        self.assertTrue(output_path.exists())
        self.assertTrue(review_output_path.exists())
        self.assertTrue(result['validate']['ok'])


if __name__ == '__main__':
    unittest.main()

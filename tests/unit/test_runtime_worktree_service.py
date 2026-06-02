from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))

from paa_core.services.runtime_worktree import (
    DefaultRuntimeWorktreeService,
    RuntimeWorktreeBranchRequest,
    RuntimeWorktreeInspectRequest,
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


class RuntimeWorktreeServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self._tempdir.name) / 'repo'
        self.repo_root.mkdir(parents=True, exist_ok=True)
        _git(self.repo_root, 'init', '-b', 'issue-6')
        _git(self.repo_root, 'config', 'user.name', 'Test User')
        _git(self.repo_root, 'config', 'user.email', 'test@example.com')
        (self.repo_root / 'README.md').write_text('runtime worktree test\n')
        _git(self.repo_root, 'add', 'README.md')
        _git(self.repo_root, 'commit', '-m', 'initial')
        self.service = DefaultRuntimeWorktreeService()
        self.lineage_view = {
            'ok': True,
            'issue_number': 6,
            'workflow_stage': 'worker_execution_in_progress',
            'package_id_external': 'pkg-1',
            'brief_id_external': 'brief-1',
            'lineage': {
                'canonical_branch': 'issue-6',
                'lineage_state': 'active',
                'branch_owner_role': 'TechLead',
                'worktree_hint': 'issue-6-dev',
            },
        }

    def tearDown(self) -> None:
        self._tempdir.cleanup()

    def test_prepare_role_branch_creates_role_branch_from_canonical_branch(self) -> None:
        result = self.service.prepare_role_branch(
            RuntimeWorktreeBranchRequest(
                repo_root=self.repo_root,
                target_role='qa',
                lineage_view=self.lineage_view,
                action='ensure',
            )
        )

        self.assertTrue(result['ok'])
        self.assertEqual(result['role_branch'], 'issue-6-qa')
        branch_head = _git(self.repo_root, 'rev-parse', '--verify', 'issue-6-qa')
        source_head = _git(self.repo_root, 'rev-parse', '--verify', 'issue-6')
        self.assertEqual(branch_head, source_head)

    def test_prepare_role_worktree_creates_registered_worktree(self) -> None:
        result = self.service.prepare_role_worktree(
            RuntimeWorktreePrepareRequest(
                repo_root=self.repo_root,
                target_role='qa',
                lineage_view=self.lineage_view,
            )
        )

        self.assertTrue(result['ok'])
        self.assertTrue(result['created'])
        worktree_path = Path(result['worktree_path'])
        self.assertTrue(worktree_path.exists())
        self.assertTrue(result['worktree_ownership']['registered'])
        self.assertEqual(result['worktree_ownership']['checked_out_branch'], 'issue-6-qa')

    def test_worktree_ownership_and_staleness_report_active_registered_worktree(self) -> None:
        prepare_result = self.service.prepare_role_worktree(
            RuntimeWorktreePrepareRequest(
                repo_root=self.repo_root,
                target_role='qa',
                lineage_view=self.lineage_view,
            )
        )
        worktree_path = Path(prepare_result['worktree_path'])

        ownership = self.service.worktree_ownership_view(
            repo_root=self.repo_root,
            target_role='qa',
            lineage_view=self.lineage_view,
            worktree_path=worktree_path,
        )

        self.assertTrue(ownership['ok'])
        self.assertTrue(ownership['worktree_ownership']['registered'])
        self.assertEqual(ownership['worktree_staleness']['status'], 'active')
        self.assertFalse(ownership['worktree_staleness']['stale'])

    def test_inspect_role_worktree_reads_assignment_artifact(self) -> None:
        prepare_result = self.service.prepare_role_worktree(
            RuntimeWorktreePrepareRequest(
                repo_root=self.repo_root,
                target_role='qa',
                lineage_view=self.lineage_view,
            )
        )
        reports_dir = self.repo_root / '.project' / 'data' / 'paa' / 'reports'
        reports_dir.mkdir(parents=True, exist_ok=True)
        assignment_path, review_path = self.service.default_assignment_paths(self.repo_root, 6, 'QA')
        assignment_path.write_text(
            '{\n'
            '  "message_id": "assign-1",\n'
            '  "schema_type": "techlead_assignment_packet",\n'
            '  "payload": {\n'
            '    "target_role": "QA",\n'
            '    "assignment_type": "verify_authorized_slice",\n'
            '    "assignment_summary": "Verify authorized slice.",\n'
            '    "allowed_result_types": ["pass"],\n'
            '    "canonical_branch": "issue-6",\n'
            '    "role_branch": "issue-6-qa",\n'
            '    "worktree_hint": "issue-6-qa"\n'
            '  }\n'
            '}\n'
        )
        review_path.write_text('review\n')

        result = self.service.inspect_role_worktree(
            RuntimeWorktreeInspectRequest(
                repo_root=self.repo_root,
                target_role='qa',
                lineage_view=self.lineage_view,
            )
        )

        self.assertTrue(result['ok'])
        self.assertEqual(result['target_role'], 'QA')
        self.assertEqual(result['assignment_artifact']['assignment_type'], 'verify_authorized_slice')
        self.assertEqual(result['current_branch'], 'issue-6-qa')


if __name__ == '__main__':
    unittest.main()

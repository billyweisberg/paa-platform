from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))

from paa_core.runtime.bridges.lineage import (
    DefaultRuntimeLineageService,
    RuntimeLineageRequest,
)


class RuntimeLineageServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path('/tmp/repo')

    def test_build_lineage_view_returns_active_branch_lineage(self) -> None:
        local_decision_packet = {
            'message_id': 'decision-1',
            'schema_type': 'techlead_decision_packet',
            'queue_name': 'paa-techlead',
            'payload': {
                'canonical_branch': 'issue-42',
                'role_branch': 'issue-42-dev',
                'branch_owner_role': 'TechLead',
                'lineage_state': 'active',
                'lineage_action': 'created',
                'source_branch': 'issue-42',
                'worktree_hint': 'issue-42-dev',
            },
        }

        service = DefaultRuntimeLineageService(
            load_authority=lambda repo_root: ({}, {'tasks': []}),
            load_design_package=lambda project_slug, package_id_external: {'package_id_external': package_id_external},
            resolve_issue_number_from_package=lambda package, package_id_external, project_slug=None: 42,
            resolve_task_summary=lambda manifest, package, issue_number: {'issue_number': 42, 'task_id': 'task-42'},
            queue_state_loader=lambda repo_root: {},
            local_decision_loader=lambda issue_number, reports_dir=None: local_decision_packet,
            qa_packet_loader=lambda issue_number, reports_dir: {'pr_number': 77, 'path': '/tmp/qa.json'},
            reports_dir_resolver=lambda repo_root: repo_root / '.project' / 'data' / 'paa' / 'reports',
            packet_preview_loader=lambda queues, issue_number, schema_type=None, to_role=None: None,
            github_state_loader=lambda *args, **kwargs: (
                {'url': 'https://example.invalid/issues/42', 'state': 'OPEN'},
                {'number': 77, 'url': 'https://example.invalid/pulls/77', 'headRefName': 'issue-42', 'mergedAt': None},
            ),
            github_repo_resolver=lambda repo_root: 'billyweisberg/paa-platform',
            workflow_deriver=lambda *args, **kwargs: ('dev_in_progress', 'Dev', [], [{'action': 'monitor_dev'}], False),
            newest_packet=lambda *packets: next((packet for packet in packets if packet), None),
            target_role_for_branch=lambda branch: 'python-team' if branch else None,
            default_role_worktree_path=lambda repo_root, role_branch: repo_root / role_branch,
            git_worktree_for_path=lambda repo_root, worktree_path: {'path': str(worktree_path)},
            worktree_ownership_record=lambda repo_root, target_role, role_branch, worktree_path, worktree_entry=None: {
                'target_role': target_role,
                'role_branch': role_branch,
                'worktree_path': str(worktree_path),
            },
            worktree_staleness_assessment=lambda lineage_state, worktree_ownership: {'status': 'fresh'},
        )

        result = service.build_lineage_view(
            RuntimeLineageRequest(
                repo_root=self.repo_root,
                project_slug='paa-platform',
                package_id_external='pkg-1',
                brief_id_external='brief-1',
            )
        )

        self.assertTrue(result['ok'])
        self.assertEqual(result['issue_number'], 42)
        self.assertEqual(result['lineage']['canonical_branch'], 'issue-42')
        self.assertEqual(result['lineage']['active_role_branch'], 'issue-42-dev')
        self.assertEqual(result['lineage']['lineage_state'], 'active')
        self.assertEqual(result['lineage']['current_packet_type'], 'techlead_decision_packet')


if __name__ == '__main__':
    unittest.main()

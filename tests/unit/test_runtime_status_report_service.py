from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))

from paa_core.services.runtime_status_report import (
    DefaultRuntimeStatusReportService,
    RuntimeStatusReportRequest,
)


class RuntimeStatusReportServiceTests(unittest.TestCase):
    def test_build_report_returns_report_shape(self) -> None:
        repo_root = Path('/tmp/repo')

        service = DefaultRuntimeStatusReportService(
            load_authority=lambda repo_root: (
                {'tasks': [{'issue_number': 42, 'task_id': 'task-42', 'title': 'Issue 42', 'status': 'in_progress', 'brief_id_external': 'brief-1'}]},
                {'project': {'authority_version': 'v1', 'published_at': '2026-06-01T00:00:00Z', 'published_from_branch': 'main'}},
            ),
            queue_state_loader=lambda repo_root: {
                'paa-techlead': {'messages_ready': 0, 'messages_unacknowledged': 0, 'preview': []},
                'paa-dev': {'messages_ready': 0, 'messages_unacknowledged': 0, 'preview': []},
                'paa-qa': {'messages_ready': 0, 'messages_unacknowledged': 0, 'preview': []},
            },
            automation_state_loader=lambda repo_root: ([{'role': 'TechLead', 'status': 'active', 'runtime': 'codex', 'root': str(repo_root), 'last_run_at': None}], False),
            mirror_status_loader=lambda authority_version, repo_root: ('aligned', [{'location': str(repo_root / 'authority.json'), 'status': 'present'}]),
            qa_packet_loader=lambda issue_number, reports_dir: {'verification_status': 'pass', 'pr_number': 77, 'path': '/tmp/qa.json', 'protected_path_checks': {'protected_10000_step_parity_passed': True}, 'technical_scope_checks': {}},
            reports_dir_resolver=lambda repo_root: repo_root / '.project' / 'data' / 'paa' / 'reports',
            packet_preview_loader=lambda queues, issue_number, schema_type=None, to_role=None: None,
            newest_packet_preview_loader=lambda queues: None,
            issue_number_from_packet_preview=lambda payload: None,
            github_state_loader=lambda *args, **kwargs: (
                {'number': 42, 'title': 'Issue 42', 'state': 'OPEN', 'url': 'https://example.invalid/issues/42'},
                {'number': 77, 'headRefName': 'issue-42', 'state': 'OPEN', 'isDraft': False, 'url': 'https://example.invalid/pulls/77', 'statusCheckRollup': [], 'mergedAt': None},
            ),
            github_repo_resolver=lambda repo_root: 'billyweisberg/paa-platform',
            workflow_deriver=lambda *args, **kwargs: ('dev_in_progress', 'Dev', [], [{'action': 'monitor_dev'}], False),
            local_decision_loader=lambda issue_number, reports_dir=None: None,
            terminal_lineage_override=lambda **kwargs: (
                kwargs['workflow_stage'],
                kwargs['owner_role'],
                kwargs['recommended'],
                kwargs['unattended_safe'],
            ),
            lineage_view_builder=lambda repo_root, project_slug, package_id_external, brief_id_external: {
                'lineage': {
                    'canonical_branch': 'issue-42',
                    'active_role_branch': 'issue-42-dev',
                    'branch_owner_role': 'TechLead',
                    'lineage_state': 'active',
                    'latest_lineage_action': 'created',
                    'source_branch': 'issue-42',
                    'superseded_branch': None,
                    'worktree_hint': 'issue-42-dev',
                    'reset_reason': None,
                    'current_packet_type': None,
                    'current_packet_message_id': None,
                    'current_packet_queue': None,
                    'worktree_ownership': None,
                    'worktree_staleness': None,
                }
            },
            derive_execution_state=lambda issue, pr: 'open',
            derive_ci_status=lambda pr: 'unknown',
            runtime_queue_names=lambda repo_root: ['paa-techlead', 'paa-dev', 'paa-qa'],
            traceability_loader=lambda project_slug, active_issue_number: {'status': 'available', 'active_work_chain': None, 'latest_accepted_chain': None},
        )

        report = service.build_report(
            RuntimeStatusReportRequest(
                repo_root=repo_root,
                project_slug='paa-platform',
            )
        )

        self.assertEqual(report['project_id'], 'paa-platform')
        self.assertEqual(report['authority']['status'], 'aligned')
        self.assertEqual(report['workflow']['current_stage'], 'dev_in_progress')
        self.assertEqual(report['active_work']['work_item']['issue_number'], 42)
        self.assertIn('paa-techlead', report['queues'])
        self.assertEqual(report['lineage']['canonical_branch'], 'issue-42')


if __name__ == '__main__':
    unittest.main()

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))

from paa_core.runtime.bridges.assignment_context import (
    DefaultRuntimeAssignmentContextService,
    RuntimeAssignmentContextRequest,
)


class RuntimeAssignmentContextServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path('/tmp/repo')

    def test_explicit_team_worker_uses_assignment_service(self) -> None:
        captured = {}

        class _AssignmentService:
            def derive_assignment_decision(self, request):
                captured['request'] = request
                summary = SimpleNamespace(
                    target_role='Python Dev',
                    target_role_cli='python',
                    assignment_type='implement_authorized_slice',
                    allowed_result_types=('implemented_ready_for_qa',),
                    assignment_summary='Use service result',
                    decision_reason='explicit',
                )
                return SimpleNamespace(
                    ok=True,
                    workflow_stage=request.workflow_stage,
                    issue_number=request.issue_number,
                    issue_url=request.issue_url,
                    pr_number=request.pr_number,
                    pr_url=request.pr_url,
                    branch_name=request.branch_name,
                    source_packet_message_id=None,
                    source_packet_path=None,
                    source_packet_queue_name=None,
                    source_packet_schema_type=None,
                    summary=summary,
                    recommended_actions=request.recommended_actions,
                    unattended_safe=True,
                    reason=None,
                    details=None,
                )

        service = DefaultRuntimeAssignmentContextService(
            load_authority=lambda repo_root: ({}, {'tasks': []}),
            github_repo_resolver=lambda repo_root: 'billyweisberg/paa-platform',
            load_design_package=lambda project_slug, package_id_external: {'package_id_external': package_id_external},
            resolve_issue_number_from_package=lambda package, package_id_external, project_slug: 42,
            resolve_task_summary=lambda manifest, package, issue_number: {'issue_number': 42, 'task_id': 'task-42'},
            queue_state_loader=lambda repo_root: {},
            qa_packet_loader=lambda issue_number, reports_dir: None,
            reports_dir_resolver=lambda repo_root: repo_root / '.project' / 'data' / 'paa' / 'reports',
            packet_preview_loader=lambda queues, issue_number, schema_type=None, to_role=None: None,
            github_state_loader=lambda *args, **kwargs: (
                {'number': 42, 'url': 'https://example.invalid/issues/42'},
                {'number': 77, 'url': 'https://example.invalid/pulls/77', 'headRefName': 'issue-42-worker'},
            ),
            workflow_deriver=lambda *args, **kwargs: ('worker_execution_in_progress', 'TechLead', [], [{'action': 'assign_worker'}], True),
            team_worker_role_for_cli=lambda target_role, repo_root=None: SimpleNamespace(display_name='Python Dev', key='python'),
            team_worker_role_for_label=lambda role_label, repo_root=None: None,
            normalize_role_name=lambda raw_role: raw_role,
            assignment_decision_service=_AssignmentService(),
            delivery_review_decision_service=object(),
        )

        context = service.derive_next_assignment_context(
            RuntimeAssignmentContextRequest(
                repo_root=self.repo_root,
                project_slug='fractal-core-python',
                package_id_external='pkg-1',
                target_role='python-dev',
            )
        )

        self.assertTrue(context['ok'])
        self.assertEqual(captured['request'].explicit_target_role, 'python-dev')
        self.assertEqual(context['target_role_cli'], 'python')
        self.assertEqual(context['branch'], 'issue-42-worker')

    def test_delivery_review_uses_delivery_review_service(self) -> None:
        captured = {}
        source_packet = {
            'message_id': 'msg-456',
            'schema_type': 'delivery_review_packet',
            'queue_name': 'fractal-core-architecture',
            'payload': {
                'result_type': 'ready_for_dev',
                'techlead_action_recommended': {
                    'action': 'assign_worker',
                    'target_role': 'Python Dev',
                    'reason': 'cleared',
                },
                'source_assignment_ref': {
                    'path': '/tmp/delivery-review.json',
                },
            },
        }

        class _DeliveryReviewService:
            def derive_delivery_review_decision(self, request):
                captured['request'] = request
                summary = SimpleNamespace(
                    recommended_target_role='Python Dev',
                    recommended_next_decision='assign_worker',
                    delivery_review_summary='Route to Python Dev.',
                )
                return SimpleNamespace(
                    ok=True,
                    workflow_stage=request.workflow_stage,
                    issue_number=request.issue_number,
                    issue_url=request.issue_url,
                    pr_number=request.pr_number,
                    pr_url=request.pr_url,
                    branch_name=request.branch_name,
                    recommended_action_name=request.recommended_action_name,
                    recommended_target_role=request.recommended_target_role,
                    resolved_team_worker_key=request.resolved_team_worker_key,
                    resolved_team_worker_display_name=request.resolved_team_worker_display_name,
                    source_packet_message_id=request.source_packet_message_id,
                    source_packet_path=request.source_packet_path,
                    source_packet_schema_type=request.source_packet_schema_type,
                    summary=summary,
                    recommended_actions=('assign_worker',),
                    unattended_safe=True,
                    reason=request.recommended_reason,
                    details=None,
                    metadata={'source_queue_name': 'fractal-core-architecture'},
                )

        def _packet_preview_loader(_queues, _issue_number, schema_type=None, to_role=None):
            if schema_type == 'delivery_review_packet' and to_role == 'techlead':
                return source_packet
            return None

        service = DefaultRuntimeAssignmentContextService(
            load_authority=lambda repo_root: ({}, {'tasks': []}),
            github_repo_resolver=lambda repo_root: 'billyweisberg/paa-platform',
            load_design_package=lambda project_slug, package_id_external: {'package_id_external': package_id_external},
            resolve_issue_number_from_package=lambda package, package_id_external, project_slug: 42,
            resolve_task_summary=lambda manifest, package, issue_number: {'issue_number': 42, 'task_id': 'task-42'},
            queue_state_loader=lambda repo_root: {},
            qa_packet_loader=lambda issue_number, reports_dir: None,
            reports_dir_resolver=lambda repo_root: repo_root / '.project' / 'data' / 'paa' / 'reports',
            packet_preview_loader=_packet_preview_loader,
            github_state_loader=lambda *args, **kwargs: (
                {'number': 42, 'url': 'https://example.invalid/issues/42'},
                {'number': 77, 'url': 'https://example.invalid/pulls/77', 'headRefName': 'issue-42-delivery'},
            ),
            workflow_deriver=lambda *args, **kwargs: ('techlead_delivery_review_pending', 'TechLead', [], [{'action': 'route_to_techlead'}], False),
            team_worker_role_for_cli=lambda target_role, repo_root=None: None,
            team_worker_role_for_label=lambda role_label, repo_root=None: SimpleNamespace(display_name='Python Dev', key='python'),
            normalize_role_name=lambda raw_role: raw_role,
            assignment_decision_service=object(),
            delivery_review_decision_service=_DeliveryReviewService(),
        )

        context = service.derive_next_assignment_context(
            RuntimeAssignmentContextRequest(
                repo_root=self.repo_root,
                project_slug='fractal-core-python',
                package_id_external='pkg-1',
            )
        )

        self.assertTrue(context['ok'])
        self.assertEqual(captured['request'].delivery_review_result_type, 'ready_for_dev')
        self.assertEqual(captured['request'].resolved_team_worker_key, 'python')
        self.assertEqual(context['target_role_cli'], 'python')
        self.assertEqual(context['source_packet_queue'], 'fractal-core-architecture')


if __name__ == '__main__':
    unittest.main()

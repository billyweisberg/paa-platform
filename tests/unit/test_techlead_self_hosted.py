import json
import tempfile
import unittest
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch

from paa_consumer import techlead


class TechLeadSelfHostedTests(unittest.TestCase):
    def test_derive_next_assignment_context_uses_service_for_explicit_team_worker(self):
        captured = {}

        class _AssignmentService:
            def derive_assignment_decision(self, request):
                captured['request'] = request
                summary = SimpleNamespace(
                    target_role='Python Dev',
                    target_role_cli='python',
                    assignment_type='implement_authorized_slice',
                    allowed_result_types=('implemented_ready_for_qa', 'blocked', 'needs_clarification'),
                    assignment_summary='Use the extracted assignment decision service.',
                    decision_reason='supported_explicit_team_worker_emission',
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

        args = SimpleNamespace(
            repo_root=Path('/tmp/repo'),
            project_slug='fractal-core-python',
            package_id_external='pkg-1',
            target_role='python-dev',
        )

        with patch('paa_consumer.techlead.load_authority', return_value=({}, {'tasks': []})), \
             patch('paa_consumer.techlead.github_repo_for_root', return_value='billyweisberg/paa-platform'), \
             patch('paa_consumer.techlead.load_design_package', return_value={'package_id_external': 'pkg-1'}), \
             patch('paa_consumer.techlead.resolve_issue_number_from_package', return_value=42), \
             patch('paa_consumer.techlead.resolve_task_summary', return_value={'issue_number': 42, 'task_id': 'task-42'}), \
             patch('paa_consumer.techlead.queue_state', return_value={}), \
             patch('paa_consumer.techlead.latest_qa_packet', return_value=None), \
             patch('paa_consumer.techlead.latest_packet_preview', return_value=None), \
             patch('paa_consumer.techlead.github_state', return_value=(
                 {'number': 42, 'url': 'https://example.invalid/issues/42'},
                 {'number': 77, 'url': 'https://example.invalid/pulls/77', 'headRefName': 'issue-42-worker'},
             )), \
             patch('paa_consumer.techlead.derive_workflow', return_value=('worker_execution_in_progress', 'TechLead', [], [{'action': 'assign_worker'}], True)), \
             patch('paa_consumer.techlead.team_worker_role_for_cli', return_value=SimpleNamespace(display_name='Python Dev', key='python')), \
             patch('paa_consumer.techlead.DefaultTechLeadAssignmentDecisionService', return_value=_AssignmentService()):
            context = techlead.derive_next_assignment_context(args)

        self.assertTrue(context['ok'])
        self.assertEqual(captured['request'].explicit_target_role, 'python-dev')
        self.assertEqual(captured['request'].issue_number, 42)
        self.assertEqual(context['target_role_cli'], 'python')
        self.assertEqual(context['branch'], 'issue-42-worker')

    def test_derive_next_assignment_context_uses_service_for_qa_routing(self):
        captured = {}
        source_packet = {
            'message_id': 'msg-123',
            'schema_type': 'worker_result_packet',
            'queue_name': 'fractal-core-python',
            'path': '/tmp/worker-result.json',
        }

        class _AssignmentService:
            def derive_assignment_decision(self, request):
                captured['request'] = request
                summary = SimpleNamespace(
                    target_role='QA',
                    target_role_cli='qa',
                    assignment_type='verify_authorized_slice',
                    allowed_result_types=('pass', 'fail_fixable', 'needs_human_review'),
                    assignment_summary='Route the returned slice to QA.',
                    decision_reason='supported_worker_review_ready_to_qa_assignment',
                )
                return SimpleNamespace(
                    ok=True,
                    workflow_stage=request.workflow_stage,
                    issue_number=request.issue_number,
                    issue_url=request.issue_url,
                    pr_number=request.pr_number,
                    pr_url=request.pr_url,
                    branch_name=request.branch_name,
                    source_packet_message_id=request.source_packet_message_id,
                    source_packet_path=request.source_packet_path,
                    source_packet_queue_name=request.source_packet_queue_name,
                    source_packet_schema_type=request.source_packet_schema_type,
                    summary=summary,
                    recommended_actions=request.recommended_actions,
                    unattended_safe=False,
                    reason=None,
                    details=None,
                )

        args = SimpleNamespace(
            repo_root=Path('/tmp/repo'),
            project_slug='fractal-core-python',
            package_id_external='pkg-1',
            target_role=None,
        )

        def _latest_packet_preview(_queues, _issue_number, schema_type=None, to_role=None):
            if schema_type == 'worker_result_packet' and to_role == 'techlead':
                return source_packet
            return None

        with patch('paa_consumer.techlead.load_authority', return_value=({}, {'tasks': []})), \
             patch('paa_consumer.techlead.github_repo_for_root', return_value='billyweisberg/paa-platform'), \
             patch('paa_consumer.techlead.load_design_package', return_value={'package_id_external': 'pkg-1'}), \
             patch('paa_consumer.techlead.resolve_issue_number_from_package', return_value=42), \
             patch('paa_consumer.techlead.resolve_task_summary', return_value={'issue_number': 42, 'task_id': 'task-42'}), \
             patch('paa_consumer.techlead.queue_state', return_value={}), \
             patch('paa_consumer.techlead.latest_qa_packet', return_value=None), \
             patch('paa_consumer.techlead.latest_packet_preview', side_effect=_latest_packet_preview), \
             patch('paa_consumer.techlead.github_state', return_value=(
                 {'number': 42, 'url': 'https://example.invalid/issues/42'},
                 {'number': 77, 'url': 'https://example.invalid/pulls/77', 'headRefName': 'issue-42-worker'},
             )), \
             patch('paa_consumer.techlead.derive_workflow', return_value=('techlead_worker_review_pending', 'TechLead', [], [{'action': 'route_to_qa'}], False)), \
             patch('paa_consumer.techlead.DefaultTechLeadAssignmentDecisionService', return_value=_AssignmentService()):
            context = techlead.derive_next_assignment_context(args)

        self.assertTrue(context['ok'])
        self.assertEqual(captured['request'].source_packet_message_id, 'msg-123')
        self.assertEqual(captured['request'].source_packet_schema_type, 'worker_result_packet')
        self.assertEqual(context['target_role_cli'], 'qa')
        self.assertEqual(context['source_packet_queue'], 'fractal-core-python')

    def test_workflow_lifecycle_apply_for_packet_builds_worker_request(self):
        captured = {}

        class _WorkflowService:
            def apply_workflow_transition(self, request):
                captured['request'] = request
                return SimpleNamespace(applied=True)

        packet = {
            'message_id': 'msg-123',
            'schema_type': 'worker_result_packet',
            'queue_name': 'fractal-core-python',
        }

        with patch('paa_consumer.techlead.resolve_work_item_id', return_value='work-item-uuid'), \
             patch('paa_consumer.techlead.DefaultWorkflowLifecycleService', return_value=_WorkflowService()):
            result = techlead.workflow_lifecycle_apply_for_packet(
                current_task={'issue_number': 42, 'task_id': 'task-42'},
                packet=packet,
            )

        self.assertIsNotNone(result)
        self.assertEqual(captured['request'].work_item_id, 'work-item-uuid')
        self.assertEqual(captured['request'].requested_transition_type, 'worker_result_returned')
        self.assertEqual(captured['request'].requested_from_stage, 'worker_execution_in_progress')
        self.assertEqual(captured['request'].source_message_id_external, 'msg-123')
        self.assertEqual(captured['request'].source_packet_schema_type, 'worker_result_packet')

    def test_workflow_lifecycle_worker_result_evaluation_builds_request(self):
        captured = {}

        class _WorkflowService:
            def evaluate_workflow_transition(self, request):
                captured['request'] = request
                return SimpleNamespace(decision_summary=SimpleNamespace(metadata={'resolved_to_stage': 'techlead_worker_review_pending'}))

        packet = {
            'message_id': 'msg-123',
            'schema_type': 'worker_result_packet',
            'queue_name': 'fractal-core-python',
        }

        with patch('paa_consumer.techlead.resolve_work_item_id', return_value='work-item-uuid'), \
             patch('paa_consumer.techlead.DefaultWorkflowLifecycleService', return_value=_WorkflowService()):
            result = techlead.workflow_lifecycle_worker_result_evaluation(
                current_task={'issue_number': 42, 'task_id': 'task-42'},
                packet=packet,
            )

        self.assertIsNotNone(result)
        self.assertEqual(captured['request'].work_item_id, 'work-item-uuid')
        self.assertEqual(captured['request'].requested_transition_type, 'worker_result_returned')
        self.assertEqual(captured['request'].requested_from_stage, 'worker_execution_in_progress')
        self.assertEqual(captured['request'].source_message_id_external, 'msg-123')
        self.assertEqual(captured['request'].source_packet_schema_type, 'worker_result_packet')

    def test_emit_next_assignment_applies_workflow_transition_for_worker_packet(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            source_packet_path = repo_root / 'worker-result.json'
            source_packet_path.write_text(json.dumps({
                'schema_type': 'worker_result_packet',
                'message_id': 'msg-123',
                'queue_name': 'fractal-core-python',
            }))

            context = {
                'ok': True,
                'workflow_stage': 'techlead_worker_review_pending',
                'issue_number': 42,
                'issue_url': 'https://example.invalid/issues/42',
                'pr_number': 77,
                'pr_url': 'https://example.invalid/pull/77',
                'branch': 'issue-42-worker',
                'target_role': 'QA',
                'target_role_cli': 'qa',
                'assignment_type': 'verify_authorized_slice',
                'allowed_result_types': ['pass', 'fail_fixable'],
                'assignment_summary': 'Route worker result to QA.',
                'source_packet_message_id': 'msg-123',
                'source_packet_path': str(source_packet_path),
                'source_packet_queue': 'fractal-core-python',
                'source_packet_schema_type': 'worker_result_packet',
            }
            applied = []

            def _apply(**kwargs):
                applied.append(kwargs)
                return SimpleNamespace(
                    applied=True,
                    requested_transition_type='worker_result_returned',
                    state_view=SimpleNamespace(workflow_stage='techlead_worker_review_pending'),
                    recommended_next_action='TechLead should review the returned worker result.',
                )

            args = type('Args', (), {
                'repo_root': repo_root,
                'project_slug': 'fractal-core-python',
                'package_id_external': 'pkg-1',
                'brief_id_external': 'brief-1',
                'output': repo_root / 'assignment.json',
                'review_output': repo_root / 'assignment.md',
                'send': False,
                'db_profile': 'paa_dev',
                'db_container': 'db',
                'db_name': 'paa_dev',
                'db_user': 'paa',
            })()

            with patch('paa_consumer.techlead.derive_next_assignment_context', return_value=context), \
                 patch('paa_consumer.techlead.workflow_lifecycle_apply_for_packet', side_effect=_apply), \
                 patch('paa_consumer.techlead.run_json', return_value={'message_id': 'assign-1', 'automation_run_id': 'run-1'}), \
                 patch('paa_consumer.techlead.run_json_with_errors', return_value=(0, {'resolved_queue': 'fractal-core-qa'}, None)):
                result = techlead.emit_next_assignment(args)

        self.assertTrue(result['ok'])
        self.assertEqual(len(applied), 1)
        self.assertEqual(applied[0]['current_task']['issue_number'], 42)
        self.assertEqual(applied[0]['packet']['schema_type'], 'worker_result_packet')
        self.assertEqual(result['workflow_transition']['applied'], True)
        self.assertEqual(result['workflow_transition']['requested_transition_type'], 'worker_result_returned')

    def test_derive_workflow_worker_packet_uses_workflow_lifecycle_result(self):
        queues = {
            'fractal-core-python': {
                'preview': [{
                    'payload_preview': {
                        'correlation_id': 'issue-42',
                        'schema_type': 'worker_result_packet',
                        'to_role': 'techlead',
                        'message_id': 'msg-123',
                        'created_at': '2026-05-17T12:00:00Z',
                        'payload': {
                            'worker_role': 'Worker',
                            'result_type': 'implemented_ready_for_qa',
                        },
                    }
                }],
                'messages_ready': 1,
            },
            'fractal-core-qa': {'preview': [], 'messages_ready': 0},
            'fractal-core-architecture': {'preview': [], 'messages_ready': 0},
        }

        lifecycle_result = SimpleNamespace(
            decision_summary=SimpleNamespace(
                transition_allowed=True,
                blocking_reasons=(),
                notes=('validated',),
                metadata={'resolved_to_stage': 'techlead_worker_review_pending'},
            ),
            recommended_next_action='Apply the worker-result transition to move the slice into TechLead worker review.',
        )

        with patch(
            'paa_consumer.techlead.workflow_lifecycle_worker_result_evaluation',
            return_value=lifecycle_result,
        ):
            stage, owner, escalations, recommended, unattended_safe = techlead.derive_workflow(
                {'issue_number': 42, 'task_id': 'task-42', 'title': 'Issue #42', 'status': 'open'},
                {'state': 'OPEN', 'comments': []},
                None,
                None,
                queues,
            )

        self.assertEqual(stage, 'techlead_worker_review_pending')
        self.assertEqual(owner, 'TechLead')
        self.assertFalse(unattended_safe)
        self.assertEqual(escalations[0]['details']['workflow_transition_allowed'], True)
        self.assertEqual(escalations[0]['details']['workflow_target_stage'], 'techlead_worker_review_pending')
        self.assertEqual(recommended[0]['target_role'], 'TechLead')

    def test_repo_auth_current_prefers_execution_context_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            fallback_dir = repo_root / '.project' / 'data' / 'paa' / 'authority' / 'current' / 'authority'
            fallback_dir.mkdir(parents=True, exist_ok=True)
            fallback_manifest = fallback_dir / 'fallback-authority.json'
            fallback_manifest.write_text(json.dumps({'project': {'repo': 'fallback/repo'}}))

            resolved_manifest = repo_root / 'resolved' / 'paa-platform-authority.json'
            resolved_manifest.parent.mkdir(parents=True, exist_ok=True)
            resolved_manifest.write_text(json.dumps({'project': {'repo': 'billyweisberg/paa-platform'}}))

            with patch(
                'paa_consumer.techlead.DefaultExecutionPackageResolutionService.resolve_execution_context_for_repo_root',
                return_value=SimpleNamespace(
                    capability_summary=SimpleNamespace(allowed=True),
                    manifest_path=str(resolved_manifest),
                ),
            ):
                resolved = techlead.repo_auth_current(repo_root)

            self.assertEqual(resolved, resolved_manifest.resolve())

    def test_repo_auth_current_uses_dynamic_installed_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            manifest_dir = repo_root / '.project' / 'data' / 'paa' / 'authority' / 'current' / 'authority'
            manifest_dir.mkdir(parents=True, exist_ok=True)
            manifest_path = manifest_dir / 'paa-platform-authority.json'
            manifest_path.write_text(json.dumps({'project': {'repo': 'billyweisberg/paa-platform'}}))

            resolved = techlead.repo_auth_current(repo_root)

            self.assertEqual(resolved, manifest_path)

    def test_github_state_falls_back_to_packet_context(self):
        packet = {
            'github_context': {
                'repo': 'billyweisberg/paa-platform',
                'issue_number': 9002,
                'pr_number': 9001,
                'branch': 'system-design-1',
                'links': [
                    'https://example.invalid/paa/proof/pull/9001',
                    'https://example.invalid/paa/proof/issues/9002',
                ],
            },
            'payload': {
                'accepted_pr': {
                    'number': 9001,
                    'url': 'https://example.invalid/paa/proof/pull/9001',
                },
                'next_issue': {
                    'number': 9002,
                    'url': 'https://example.invalid/paa/proof/issues/9002',
                },
            },
        }

        with patch('paa_consumer.techlead.run_json', side_effect=RuntimeError('gh unavailable')):
            issue, pr = techlead.github_state(
                9002,
                'billyweisberg/paa-platform',
                fallback_pr_number=9001,
                fallback_task={'title': 'Proof Slice Task'},
                fallback_packet=packet,
            )

        self.assertEqual(issue['number'], 9002)
        self.assertEqual(issue['title'], 'Proof Slice Task')
        self.assertEqual(issue['url'], 'https://example.invalid/paa/proof/issues/9002')
        self.assertIsNotNone(pr)
        self.assertEqual(pr['number'], 9001)
        self.assertEqual(pr['headRefName'], 'system-design-1')
        self.assertEqual(pr['url'], 'https://example.invalid/paa/proof/pull/9001')

    def test_closeout_qa_pass_uses_proof_only_terminal_path(self):
        qa_packet = {
            'message_id': 'qa-proof-1',
            'verification_status': 'pass',
            'path': '/tmp/qa-proof-1.json',
            'pr_number': 9001,
            'created_at': '2026-05-17T00:00:00Z',
            'recommended_action': {'merge_recommendation': 'do_not_merge_proof_slice'},
        }
        persisted = {}

        def _capture_persist(*args, **kwargs):
            persisted['decision'] = kwargs.get('decision')
            persisted['decision_notes'] = kwargs.get('decision_notes')
            persisted['metadata_extra'] = kwargs.get('metadata_extra')

        with patch('paa_consumer.techlead.load_design_package', return_value={'authority_context': {'execution_mode': 'proof_only'}}), \
             patch('paa_consumer.techlead.latest_qa_packet', return_value=qa_packet), \
             patch('paa_consumer.techlead.queue_state', return_value={'fractal-core-architecture': {'preview': []}}), \
             patch('paa_consumer.techlead.latest_packet_preview', return_value={'github_context': {'repo': 'billyweisberg/paa-platform'}}), \
             patch('paa_consumer.techlead.github_state', return_value=({'state': 'OPEN', 'closedAt': None}, {'number': 9001, 'state': 'OPEN', 'mergedAt': None, 'url': 'https://example.invalid/pull/9001'})), \
             patch('paa_consumer.techlead.persist_techlead_acceptance_event', side_effect=_capture_persist), \
             patch('paa_consumer.techlead.emit_decision', return_value={'ok': True, 'message_id': 'decision-proof-1', 'sent': False}):
            args = type('Args', (), {
                'repo_root': Path('/tmp/proof-repo'),
                'project_slug': 'paa-platform',
                'package_id_external': 'paa-stage1-2026-05-16-component-design-planning-service',
                'brief_id_external': 'paa-coder-2026-05-16-component-design-planning-service-governed-draft',
                'issue_number': 9002,
                'send_decision': False,
                'ack_qa_packet': False,
                'claimed_by': 'test-proof-closeout',
                'canonical_branch': 'main',
                'role_branch': 'issue-9002-qa',
                'worktree_hint': '.codex-work/worktrees/paa/issue-9002-qa',
                'output': None,
                'review_output': None,
                'db_container': 'db',
                'db_name': 'paa_dev',
                'db_user': 'mmuser',
            })()
            result = techlead.closeout_qa_pass(args)

        self.assertTrue(result['ok'])
        self.assertEqual(result['execution_mode'], 'proof_only')
        self.assertEqual(result['closeout_mode'], 'proof_only')
        self.assertEqual(persisted['decision'], 'proof_only_closed')
        self.assertTrue(persisted['metadata_extra']['proof_only_closeout'])
        self.assertEqual(persisted['metadata_extra']['closeout_mode'], 'proof_only')


if __name__ == '__main__':
    unittest.main()

import unittest
from types import SimpleNamespace

from paa_core.runtime.bridges.workflow import DefaultRuntimeWorkflowService


class RuntimeWorkflowServiceTests(unittest.TestCase):
    def _build_service(self, **overrides):
        def packet_preview_loader(queues, issue_number, schema_type=None, to_role=None):
            if issue_number is None:
                return None
            for queue_data in queues.values():
                for item in queue_data.get('preview', []):
                    payload = item.get('payload_preview') or {}
                    if payload.get('correlation_id') != f'issue-{issue_number}':
                        continue
                    if schema_type and payload.get('schema_type') != schema_type:
                        continue
                    if to_role and (payload.get('to_role') or '').lower() != to_role.lower():
                        continue
                    return payload
            return None

        def newest_packet(*packets):
            filtered = [packet for packet in packets if packet]
            if not filtered:
                return None
            return sorted(filtered, key=lambda packet: packet.get('created_at') or '', reverse=True)[0]

        def latest_issue_comment(issue, prefix):
            latest = None
            for comment in issue.get('comments') or []:
                if (comment.get('body') or '').startswith(prefix):
                    latest = comment
            return latest

        def latest_comment_with_prefixes(comments, prefixes):
            latest = None
            for comment in comments or []:
                if any((comment.get('body') or '').startswith(prefix) for prefix in prefixes):
                    latest = comment
            return latest

        def comments_with_prefixes(comments, prefixes):
            return [
                comment for comment in comments or []
                if any((comment.get('body') or '').startswith(prefix) for prefix in prefixes)
            ]

        def latest_comment_before(comments, timestamp):
            return None

        def comment_is_newer(comment, timestamp):
            return False

        def qa_packet_superseded(qa_packet, dev_queue_packet):
            return False

        def action_type_for_role(role):
            mapping = {
                'QA': 'route_to_qa',
                'TechLead': 'route_to_techlead',
                'Dev': 'route_to_dev',
                'Architect': 'route_to_architect',
            }
            return mapping.get(role, 'route_to_techlead')

        def build_acceptance_decision_request(**kwargs):
            current_task = kwargs.get('current_task') or {}
            payload = (kwargs.get('source_packet') or {}).get('payload') or {}
            return SimpleNamespace(
                issue_number=current_task.get('issue_number'),
                workflow_stage=kwargs.get('workflow_stage'),
                qa_result_type=(kwargs.get('qa_packet') or {}).get('verification_status') or payload.get('verification_status'),
            )

        def build_worker_review_routing_request(**kwargs):
            current_task = kwargs.get('current_task') or {}
            workflow_stage = 'techlead_dev_review_pending' if kwargs.get('worker_role') in {'Dev', 'Python Dev'} else 'techlead_worker_review_pending'
            payload = (kwargs.get('worker_result_packet') or {}).get('payload') or {}
            return SimpleNamespace(
                issue_number=current_task.get('issue_number'),
                worker_role=kwargs.get('worker_role'),
                worker_result_type=payload.get('result_type'),
                workflow_stage=workflow_stage,
            )

        def resolve_worker_review_stage(**kwargs):
            return 'techlead_dev_review_pending' if kwargs.get('worker_role') in {'Dev', 'Python Dev'} else 'techlead_worker_review_pending'

        def workflow_lifecycle_worker_result_evaluation(**kwargs):
            return None

        params = {
            'packet_preview_loader': packet_preview_loader,
            'newest_packet': newest_packet,
            'latest_issue_comment': latest_issue_comment,
            'latest_comment_with_prefixes': latest_comment_with_prefixes,
            'comments_with_prefixes': comments_with_prefixes,
            'latest_comment_before': latest_comment_before,
            'comment_is_newer': comment_is_newer,
            'qa_packet_superseded': qa_packet_superseded,
            'action_type_for_role': action_type_for_role,
            'techlead_queue_name': lambda: 'paa-techlead',
            'dev_queue_name': lambda: 'paa-dev',
            'build_acceptance_decision_request': build_acceptance_decision_request,
            'build_worker_review_routing_request': build_worker_review_routing_request,
            'resolve_worker_review_stage': resolve_worker_review_stage,
            'workflow_lifecycle_worker_result_evaluation': workflow_lifecycle_worker_result_evaluation,
        }
        params.update(overrides)
        return DefaultRuntimeWorkflowService(**params)

    def test_worker_packet_uses_worker_review_routing_service(self):
        queues = {
            'paa-dev': {
                'preview': [{
                    'payload_preview': {
                        'correlation_id': 'issue-42',
                        'schema_type': 'worker_result_packet',
                        'to_role': 'techlead',
                        'message_id': 'msg-123',
                        'created_at': '2026-05-17T12:00:00Z',
                        'payload': {
                            'worker_role': 'Dev',
                            'result_type': 'implemented_ready_for_qa',
                        },
                    }
                }],
                'messages_ready': 1,
            },
            'paa-qa': {'preview': [], 'messages_ready': 0},
            'paa-techlead': {'preview': [], 'messages_ready': 0},
        }
        lifecycle_result = SimpleNamespace(
            decision_summary=SimpleNamespace(
                transition_allowed=True,
                blocking_reasons=(),
                notes=('validated',),
                metadata={'resolved_to_stage': 'techlead_worker_review_pending'},
            ),
            recommended_next_action='Apply the worker-result transition.',
        )
        captured = {}

        class WorkerReviewRoutingService:
            def derive_worker_review_routing(self, request):
                captured['request'] = request
                return SimpleNamespace(
                    summary=SimpleNamespace(
                        decision_supported=True,
                        recommended_next_decision='assign_qa',
                        recommended_target_role='QA',
                        qa_assignment_allowed=True,
                        review_summary='Worker result is ready for QA verification.',
                        blocking_reasons=(),
                    ),
                    reason=None,
                )

        service = self._build_service(
            workflow_lifecycle_worker_result_evaluation=lambda **kwargs: lifecycle_result,
            worker_review_routing_service_factory=lambda: WorkerReviewRoutingService(),
        )

        result = service.derive_workflow(
            {'issue_number': 42, 'task_id': 'task-42', 'title': 'Issue #42', 'status': 'open'},
            {'state': 'OPEN', 'comments': [], 'number': 42},
            {'number': 77, 'state': 'OPEN'},
            None,
            queues,
        )

        self.assertEqual(captured['request'].issue_number, 42)
        self.assertEqual(captured['request'].worker_role, 'Dev')
        self.assertEqual(result.workflow_stage, 'techlead_dev_review_pending')
        self.assertEqual(result.owner_role, 'TechLead')
        self.assertFalse(result.unattended_safe)
        self.assertEqual(result.escalations[0]['details']['review_routing_next_decision'], 'assign_qa')
        self.assertEqual(result.recommended_actions[0]['target_role'], 'QA')

    def test_qa_pass_uses_acceptance_decision_service(self):
        captured = {}
        qa_packet = {
            'message_id': 'qa-pass-1',
            'verification_status': 'pass',
            'path': '/tmp/qa-pass-1.json',
            'recommended_action': {'merge_recommendation': 'accept_and_merge'},
            'pr_number': 77,
        }
        queues = {
            'paa-dev': {'preview': [], 'messages_ready': 0},
            'paa-qa': {'preview': [], 'messages_ready': 0},
            'paa-techlead': {'preview': [], 'messages_ready': 0},
        }

        class AcceptanceService:
            def derive_acceptance_decision(self, request):
                captured['request'] = request
                return SimpleNamespace(
                    summary=SimpleNamespace(
                        decision_supported=True,
                        recommended_next_decision='prepare_merge',
                        acceptance_allowed=True,
                        closeout_allowed=False,
                        decision_summary='Use the extracted acceptance decision service.',
                        blocking_reasons=(),
                    ),
                    reason=None,
                )

        service = self._build_service(
            acceptance_decision_service_factory=lambda: AcceptanceService(),
        )

        result = service.derive_workflow(
            {'issue_number': 42, 'task_id': 'task-42', 'title': 'Issue #42', 'status': 'open'},
            {'state': 'OPEN', 'comments': [], 'number': 42},
            {'number': 77, 'state': 'OPEN'},
            qa_packet,
            queues,
        )

        self.assertEqual(captured['request'].issue_number, 42)
        self.assertEqual(result.workflow_stage, 'techlead_qa_review_pending')
        self.assertEqual(result.owner_role, 'TechLead')
        self.assertFalse(result.unattended_safe)
        self.assertEqual(result.escalations[0]['details']['acceptance_next_decision'], 'prepare_merge')
        self.assertEqual(result.recommended_actions[0]['reason'], 'Use the extracted acceptance decision service.')

    def test_techlead_decision_packet_short_circuits_rederivation(self):
        queues = {
            'paa-techlead': {
                'preview': [{
                    'payload_preview': {
                        'correlation_id': 'issue-42',
                        'schema_type': 'techlead_decision_packet',
                        'to_role': 'TechLead',
                        'message_id': 'decision-1',
                        'created_at': '2026-05-17T12:00:00Z',
                        'payload': {
                            'decision_type': 'closed',
                            'target_role': 'QA',
                            'next_assignment_type': 'verify',
                        },
                    }
                }],
                'messages_ready': 1,
            },
            'paa-dev': {'preview': [], 'messages_ready': 0},
            'paa-qa': {'preview': [], 'messages_ready': 0},
        }
        service = self._build_service()
        result = service.derive_workflow(
            {'issue_number': 42, 'task_id': 'task-42', 'title': 'Issue #42', 'status': 'open'},
            {'state': 'OPEN', 'comments': [], 'number': 42},
            None,
            None,
            queues,
        )
        self.assertEqual(result.workflow_stage, 'techlead_decision_recorded')
        self.assertEqual(result.owner_role, 'TechLead')
        self.assertEqual(result.recommended_actions[0]['target_role'], 'QA')


if __name__ == '__main__':
    unittest.main()

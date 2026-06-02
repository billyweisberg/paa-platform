from __future__ import annotations

import sys
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-consumer' / 'src'))
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))

from paa_consumer.inbox import dispatch_packet, resolve_packet_queue, resolve_techlead_packet_queue


class PaaConsumerInboxTests(unittest.TestCase):
    def test_worker_result_packets_route_to_paa_techlead_queue(self) -> None:
        queue_name = resolve_packet_queue(
            {
                'schema_type': 'worker_result_packet',
                'payload': {},
            },
            repo_root=ROOT,
        )

        self.assertEqual(queue_name, 'paa-techlead')

    def test_techlead_assignment_packets_route_dev_assignments_to_paa_dev_queue(self) -> None:
        queue_name = resolve_techlead_packet_queue(
            {
                'schema_type': 'techlead_assignment_packet',
                'to_role': 'Dev',
                'payload': {'target_role': 'Dev'},
            },
            repo_root=ROOT,
        )

        self.assertEqual(queue_name, 'paa-dev')

    def test_dispatch_packet_persists_packet_compilation_before_send_event(self) -> None:
        message_file = ROOT / '.codex-work' / 'test-dispatch-packet.json'
        call_order: list[str] = []

        class _FakeClient:
            def __init__(self, *args, **kwargs) -> None:
                pass

            def publish(self, exchange, routing_key, payload):
                call_order.append('publish')
                return 200, {'routed': True}

        message = {
            'message_id': 'msg-1',
            'schema_type': 'qa_verification_packet',
            'from_role': 'qa',
            'to_role': 'techlead',
            'github_context': {'repo': 'billyweisberg/paa-platform', 'issue_number': 6, 'pr_number': 999, 'branch': 'codex/test', 'links': []},
            'payload': {
                'issue': {'number': 6},
                'pr': {'number': 999, 'ready_for_review': True},
                'verification_status': 'pass',
                'verification_scope': {'scope': 'verify_authorized_slice'},
                'mechanical_checks': [],
                'technical_scope_checks': [],
                'protected_path_checks': [],
                'artifact_checks': [],
                'findings': [],
                'recommended_action': {'merge_recommendation': 'accept_and_merge'},
            },
            'authority_context': {
                'manifest_path': 'docs/2_Design/2026-05-17-paa-proof-slice-authority-manifest.json',
                'authority_version': '2026-06-01.1',
                'milestone_id': 'm0-paa-runtime-proof',
                'phase_id': 'p0-qa-runtime-host',
                'task_id': 'paa-qa-runtime-host',
            },
        }

        with patch('paa_consumer.inbox.handoff_runtime.load_json', return_value=message), \
            patch('paa_consumer.inbox.handoff_runtime.validate_envelope', return_value=[]), \
            patch('paa_consumer.inbox.handoff_runtime.persist_packet_compilation_for_send_message', side_effect=lambda *args, **kwargs: call_order.append('persist_packet_compilation')), \
            patch('paa_consumer.inbox.handoff_runtime.persist_send_event', side_effect=lambda *args, **kwargs: call_order.append('persist_send_event')), \
            patch('paa_consumer.inbox.handoff_runtime.persist_slice_result', side_effect=lambda *args, **kwargs: call_order.append('persist_slice_result')), \
            patch('paa_consumer.inbox.handoff_runtime.persist_qa_verification', side_effect=lambda *args, **kwargs: call_order.append('persist_qa_verification')), \
            patch('paa_consumer.inbox.handoff_runtime.RabbitMQManagementClient', _FakeClient):
            result = dispatch_packet(ROOT, message_file)

        self.assertTrue(result['ok'])
        self.assertEqual(call_order[0:3], ['persist_packet_compilation', 'publish', 'persist_send_event'])


if __name__ == '__main__':
    unittest.main()

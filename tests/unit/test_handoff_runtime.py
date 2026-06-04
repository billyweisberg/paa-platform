import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
import tempfile

from paa_core.runtime.transport.handoff_runtime import (
    DEFAULT_EXCHANGE,
    DEFAULT_QUEUES,
    _resolved_runtime_exchange,
    _resolved_runtime_queues,
    cmd_claim_next,
    cmd_purge,
    cmd_send,
    lookup_packet_compilation_run,
    packet_compiler_agent_name_for_message,
    persist_packet_compilation_for_send_message,
    role_name_for_db,
    resolve_work_item_id_from_message,
)


class HandoffRuntimeTests(unittest.TestCase):
    def test_resolve_work_item_id_from_message_falls_back_to_package_and_brief_authority(self):
        message = {
            'project': 'paa-platform',
            'github_context': {
                'issue_number': 9002,
            },
            'payload': {
                'coder_brief_resolution': {
                    'package_id_external': 'paa-stage1-2026-05-16-component-design-planning-service',
                    'brief_id_external': 'paa-coder-2026-05-16-component-design-planning-service-governed-draft',
                }
            },
        }
        with patch(
            'paa_core.runtime.transport.handoff_runtime.PostgresRuntimeEventRepository.resolve_work_item_id_for_message',
            return_value='9e4509a5-5738-476b-a417-28e0012278f1',
        ) as mock_resolve:
            work_item_id = resolve_work_item_id_from_message(message)
        self.assertEqual(work_item_id, '9e4509a5-5738-476b-a417-28e0012278f1')
        self.assertEqual(mock_resolve.call_args[0][0], message)

    def test_runtime_topology_resolution_uses_repo_project_config_when_defaults_are_requested(self):
        args = SimpleNamespace(
            repo_root=str(Path(__file__).resolve().parents[2]),
            exchange=DEFAULT_EXCHANGE,
            queues=list(DEFAULT_QUEUES),
        )

        self.assertEqual(_resolved_runtime_exchange(args), 'paa-handoff')
        self.assertEqual(_resolved_runtime_queues(args), ['paa-techlead', 'paa-dev', 'paa-qa'])

    def test_role_name_for_db_maps_legacy_worker_roles_to_paa_dev(self):
        self.assertEqual(role_name_for_db('python-team'), 'Dev')
        self.assertEqual(role_name_for_db('Python Dev'), 'Dev')
        self.assertEqual(role_name_for_db('Frontend Dev'), 'Dev')

    def test_packet_compiler_agent_name_for_message_uses_paa_agent_names(self):
        self.assertEqual(packet_compiler_agent_name_for_message({'from_role': 'python-team'}), 'Dev Agent')
        self.assertEqual(packet_compiler_agent_name_for_message({'from_role': 'qa'}), 'QA Agent')
        self.assertEqual(packet_compiler_agent_name_for_message({'from_role': 'techlead'}), 'TechLead Agent')

    def test_persist_packet_compilation_for_send_message_writes_packet_output_path(self):
        message = {
            'message_id': 'msg-1',
            'schema_type': 'worker_result_packet',
            'project': 'paa-platform',
            'from_role': 'python-team',
            'created_at': '2026-06-02T00:00:00Z',
            'github_context': {'issue_number': 6},
            'payload': {},
            'correlation_id': 'issue-6',
        }
        fake_record = SimpleNamespace(automation_run_id='run-1')
        with patch(
            'paa_core.runtime.transport.handoff_runtime.PostgresRuntimeEventRepository.create_packet_compilation_run_for_message',
            return_value=fake_record,
        ) as mock_create:
            automation_run_id = persist_packet_compilation_for_send_message(
                message,
                message_file='/Users/billyweisberg/Repos/billyweisberg/paa-platform/.codex-work/runtime-proof/worker.json',
            )
        self.assertEqual(automation_run_id, 'run-1')
        self.assertEqual(mock_create.call_args.kwargs['agent_name'], 'Dev Agent')
        self.assertEqual(
            mock_create.call_args.kwargs['message_file'],
            '/Users/billyweisberg/Repos/billyweisberg/paa-platform/.codex-work/runtime-proof/worker.json',
        )

    def test_cmd_send_persists_packet_compilation_before_send_event(self):
        message = {
            'message_id': 'msg-1',
            'schema_type': 'worker_result_packet',
            'project': 'paa-platform',
            'from_role': 'python-team',
            'to_role': 'techlead',
            'created_at': '2026-06-02T00:00:00Z',
            'correlation_id': 'issue-6',
            'github_context': {'issue_number': 6},
            'payload': {'issue': {'number': 6}},
            'authority_context': {'task_id': 'proof'},
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / 'packet.json'
            path.write_text(__import__('json').dumps(message))
            args = SimpleNamespace(
                message_file=str(path),
                user='guest',
                password='guest',
                host='127.0.0.1',
                port=15672,
                vhost='/',
                queue='paa-techlead',
                repo_root=str(Path(__file__).resolve().parents[2]),
                exchange=DEFAULT_EXCHANGE,
            )
            fake_client = SimpleNamespace(publish=lambda exchange, queue, payload: ({}, {'routed': True}))
            with patch('paa_core.runtime.transport.handoff_runtime.validate_envelope', return_value=[]), \
                 patch('paa_core.runtime.transport.handoff_runtime.RabbitMQManagementClient', return_value=fake_client), \
                 patch('paa_core.runtime.transport.handoff_runtime.persist_packet_compilation_for_send_message') as mock_compile, \
                 patch('paa_core.runtime.transport.handoff_runtime.persist_send_event') as mock_send_event, \
                 patch('paa_core.runtime.transport.handoff_runtime.persist_slice_result'), \
                 patch('paa_core.runtime.transport.handoff_runtime.persist_qa_verification'), \
                 patch('builtins.print'):
                cmd_send(args)
        mock_compile.assert_called_once_with(message, message_file=str(path))
        mock_send_event.assert_called_once()

    def test_lookup_packet_compilation_run_returns_repository_record_shape(self):
        message = {
            'message_id': 'msg-1',
            'schema_type': 'worker_result_packet',
        }
        fake_record = SimpleNamespace(
            automation_run_id='run-1',
            trigger_type='packet_compilation:worker_result_packet',
            summary='Compiled worker_result_packet for issue #6',
            artifacts={},
        )
        with patch(
            'paa_core.runtime.transport.handoff_runtime.PostgresRuntimeEventRepository.find_packet_compilation_run',
            return_value=fake_record,
        ):
            result = lookup_packet_compilation_run(message)
        self.assertEqual(result['automation_run_id'], 'run-1')
        self.assertEqual(result['trigger_type'], 'packet_compilation:worker_result_packet')
        self.assertIsNone(result['package_id_external'])
        self.assertIsNone(result['brief_id_external'])

    def test_cmd_claim_next_records_invalid_claim_when_broker_payload_is_not_an_object(self):
        args = SimpleNamespace(
            user='guest',
            password='guest',
            host='127.0.0.1',
            port=15672,
            vhost='/',
            queue='paa-techlead',
            claimed_by='TechLead Agent',
        )
        fake_client = SimpleNamespace(get_messages=lambda queue, count=1, ackmode='ack_requeue_false': ({}, [{'payload': 'null'}]))
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            with patch('paa_core.runtime.transport.handoff_runtime.ensure_state_dirs', return_value=(root, 'test', root)), \
                 patch('paa_core.runtime.transport.handoff_runtime.RabbitMQManagementClient', return_value=fake_client), \
                 patch('builtins.print') as mock_print:
                with self.assertRaises(SystemExit) as exc:
                    cmd_claim_next(args)
        self.assertEqual(exc.exception.code, 1)
        printed = mock_print.call_args[0][0]
        self.assertIn('"ok": false', printed.lower())
        self.assertIn('queue message payload must decode to an object envelope', printed)

    def test_cmd_purge_uses_resolved_runtime_queues_when_queue_not_provided(self):
        args = SimpleNamespace(
            user='guest',
            password='guest',
            host='127.0.0.1',
            port=15672,
            vhost='/',
            queue=None,
            repo_root=str(Path(__file__).resolve().parents[2]),
            queues=list(DEFAULT_QUEUES),
        )
        fake_client = SimpleNamespace(purge_queue=lambda queue: ({}, None))
        with patch('paa_core.runtime.transport.handoff_runtime.RabbitMQManagementClient', return_value=fake_client), \
             patch('builtins.print') as mock_print:
            cmd_purge(args)
        printed = mock_print.call_args[0][0]
        self.assertIn('"queue_count": 3', printed)
        self.assertIn('paa-techlead', printed)
        self.assertIn('paa-dev', printed)
        self.assertIn('paa-qa', printed)


if __name__ == '__main__':
    unittest.main()

import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
import tempfile

from paa_core.handoff_runtime import (
    DEFAULT_EXCHANGE,
    DEFAULT_QUEUES,
    _resolved_runtime_exchange,
    _resolved_runtime_queues,
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
        with patch('paa_core.handoff_runtime.run_psql', return_value='9e4509a5-5738-476b-a417-28e0012278f1\n') as mock_run:
            work_item_id = resolve_work_item_id_from_message(message)
        self.assertEqual(work_item_id, '9e4509a5-5738-476b-a417-28e0012278f1')
        called_sql = mock_run.call_args[0][0]
        self.assertIn('paa-stage1-2026-05-16-component-design-planning-service', called_sql)
        self.assertIn('paa-coder-2026-05-16-component-design-planning-service-governed-draft', called_sql)

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
        with patch('paa_core.handoff_runtime.lookup_packet_compilation_run', side_effect=[None, {'automation_run_id': 'run-1'}]), \
             patch('paa_core.handoff_runtime.resolve_work_item_id_from_message', return_value='work-1'), \
             patch('paa_core.handoff_runtime.run_psql') as mock_run:
            automation_run_id = persist_packet_compilation_for_send_message(
                message,
                message_file='/Users/billyweisberg/Repos/billyweisberg/paa-platform/.codex-work/runtime-proof/worker.json',
            )
        self.assertEqual(automation_run_id, 'run-1')
        called_sql = mock_run.call_args[0][0]
        self.assertIn('packet_compilation:worker_result_packet', called_sql)
        self.assertIn('Dev Agent', called_sql)
        self.assertIn('packet_output_path', called_sql)
        self.assertIn('/Users/billyweisberg/Repos/billyweisberg/paa-platform/.codex-work/runtime-proof/worker.json', called_sql)

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
            with patch('paa_core.handoff_runtime.validate_envelope', return_value=[]), \
                 patch('paa_core.handoff_runtime.RabbitMQManagementClient', return_value=fake_client), \
                 patch('paa_core.handoff_runtime.persist_packet_compilation_for_send_message') as mock_compile, \
                 patch('paa_core.handoff_runtime.persist_send_event') as mock_send_event, \
                 patch('paa_core.handoff_runtime.persist_slice_result'), \
                 patch('paa_core.handoff_runtime.persist_qa_verification'), \
                 patch('builtins.print'):
                cmd_send(args)
        mock_compile.assert_called_once_with(message, message_file=str(path))
        mock_send_event.assert_called_once()

    def test_lookup_packet_compilation_run_tolerates_missing_trailing_fields(self):
        message = {
            'message_id': 'msg-1',
            'schema_type': 'worker_result_packet',
        }
        with patch('paa_core.handoff_runtime.run_psql', return_value='run-1\tpacket_compilation:worker_result_packet\tCompiled worker_result_packet for issue #6'):
            result = lookup_packet_compilation_run(message)
        self.assertEqual(result['automation_run_id'], 'run-1')
        self.assertEqual(result['trigger_type'], 'packet_compilation:worker_result_packet')
        self.assertIsNone(result['package_id_external'])
        self.assertIsNone(result['brief_id_external'])


if __name__ == '__main__':
    unittest.main()

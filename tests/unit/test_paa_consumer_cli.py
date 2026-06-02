from __future__ import annotations

import io
import json
import sys
from pathlib import Path
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'packages' / 'paa-consumer' / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'packages' / 'paa-core' / 'src'))

from paa_consumer.__main__ import main


class PaaConsumerCliTests(unittest.TestCase):
    def test_help_lists_bootstrap_service_map_command(self) -> None:
        buffer = io.StringIO()
        with patch('sys.stdout', buffer), patch('sys.argv', ['paa-consumer', 'help']):
            exit_code = main()

        self.assertEqual(exit_code, 0)
        self.assertIn('techlead-service-map', buffer.getvalue())
        self.assertIn('techlead-runtime', buffer.getvalue())
        self.assertIn('qa-runtime', buffer.getvalue())

    def test_techlead_service_map_outputs_extracted_service_inventory(self) -> None:
        buffer = io.StringIO()
        with patch('sys.stdout', buffer), patch('sys.argv', ['paa-consumer', 'techlead-service-map']):
            exit_code = main()

        self.assertEqual(exit_code, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload['techlead_shell_status'], 'mostly_shell')
        self.assertEqual(payload['extracted_service_count'], 7)
        self.assertEqual(payload['extracted_services'][0]['component_name'], 'TechLeadAssignmentDecisionService')
        remaining_names = {item['name'] for item in payload['remaining_shell_pockets']}
        self.assertIn('terminal_lineage_override_policy', remaining_names)
        self.assertNotIn('live_closed_closeout_context', remaining_names)

    def test_runtime_supervisor_uses_builder_and_prints_summary(self) -> None:
        buffer = io.StringIO()
        fake_supervisor = type(
            'FakeSupervisor',
            (),
            {
                'run': lambda self, **kwargs: {
                    'ok': True,
                    'host_count': 3,
                    'intake_mode': kwargs['intake_mode'],
                    'max_iterations': kwargs['max_iterations'],
                    'results': {'techlead': {}, 'dev': {}, 'qa': {}},
                    'errors': {},
                }
            },
        )()

        with patch('paa_consumer.__main__.build_runtime_supervisor', return_value=fake_supervisor), \
             patch('sys.stdout', buffer), \
             patch('sys.argv', ['paa-consumer', 'runtime-supervisor', '--max-iterations', '2']):
            exit_code = main()

        self.assertEqual(exit_code, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload['host_count'], 3)
        self.assertEqual(payload['max_iterations'], 2)
        self.assertEqual(set(payload['results'].keys()), {'techlead', 'dev', 'qa'})


    def test_runtime_supervisor_start_routes_to_control_surface(self) -> None:
        buffer = io.StringIO()
        with patch('paa_consumer.__main__.start_runtime_supervisor', return_value={'ok': True, 'pid': 123}), \
             patch('sys.stdout', buffer), \
             patch('sys.argv', ['paa-consumer', 'runtime-supervisor-start']):
            exit_code = main()

        self.assertEqual(exit_code, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload['pid'], 123)

    def test_runtime_supervisor_status_routes_to_control_surface(self) -> None:
        buffer = io.StringIO()
        with patch('paa_consumer.__main__.runtime_supervisor_status', return_value={'ok': True, 'running': True, 'pid': 321}), \
             patch('sys.stdout', buffer), \
             patch('sys.argv', ['paa-consumer', 'runtime-supervisor-status']):
            exit_code = main()

        self.assertEqual(exit_code, 0)
        payload = json.loads(buffer.getvalue())
        self.assertTrue(payload['running'])
        self.assertEqual(payload['pid'], 321)

    def test_runtime_supervisor_logs_routes_to_control_surface(self) -> None:
        buffer = io.StringIO()
        with patch('paa_consumer.__main__.runtime_supervisor_logs', return_value='line-1\nline-2'), \
             patch('sys.stdout', buffer), \
             patch('sys.argv', ['paa-consumer', 'runtime-supervisor-logs']):
            exit_code = main()

        self.assertEqual(exit_code, 0)
        self.assertEqual(buffer.getvalue().strip(), 'line-1\nline-2')

    def test_runtime_supervisor_stop_routes_to_control_surface(self) -> None:
        buffer = io.StringIO()
        with patch('paa_consumer.__main__.stop_runtime_supervisor', return_value={'ok': True, 'stopped': True}), \
             patch('sys.stdout', buffer), \
             patch('sys.argv', ['paa-consumer', 'runtime-supervisor-stop']):
            exit_code = main()

        self.assertEqual(exit_code, 0)
        payload = json.loads(buffer.getvalue())
        self.assertTrue(payload['stopped'])

    def test_techlead_runtime_uses_host_builder_and_prints_loop_summary(self) -> None:
        buffer = io.StringIO()
        fake_host = type(
            'FakeHost',
            (),
            {
                'run_loop': lambda self, **kwargs: {
                    'host_name': 'techlead-runtime-host',
                    'queue_name': 'paa-techlead',
                    'intake_mode': kwargs['intake_mode'],
                    'emit_next_assignment': kwargs['emit_next_assignment'],
                    'iteration_count': kwargs['max_iterations'],
                    'iterations': [],
                }
            },
        )()

        with patch('paa_consumer.__main__.build_techlead_runtime_host', return_value=fake_host), \
             patch('sys.stdout', buffer), \
             patch('sys.argv', ['paa-consumer', 'techlead-runtime', '--max-iterations', '2', '--emit-next-assignment']):
            exit_code = main()

        self.assertEqual(exit_code, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload['queue_name'], 'paa-techlead')
        self.assertTrue(payload['emit_next_assignment'])
        self.assertEqual(payload['iteration_count'], 2)

    def test_qa_runtime_uses_host_builder_and_prints_loop_summary(self) -> None:
        buffer = io.StringIO()
        fake_host = type(
            'FakeHost',
            (),
            {
                'run_loop': lambda self, **kwargs: {
                    'host_name': 'qa-runtime-host',
                    'queue_name': 'paa-qa',
                    'intake_mode': kwargs['intake_mode'],
                    'emit_verification': kwargs['emit_verification'],
                    'iteration_count': kwargs['max_iterations'],
                    'iterations': [],
                }
            },
        )()

        with patch('paa_consumer.__main__.build_qa_runtime_host', return_value=fake_host), \
             patch('sys.stdout', buffer), \
             patch('sys.argv', ['paa-consumer', 'qa-runtime', '--max-iterations', '2', '--emit-verification']):
            exit_code = main()

        self.assertEqual(exit_code, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload['queue_name'], 'paa-qa')
        self.assertTrue(payload['emit_verification'])
        self.assertEqual(payload['iteration_count'], 2)

    def test_queue_purge_routes_to_shared_queue_runtime(self) -> None:
        with patch('paa_consumer.__main__.run_queue_command', return_value=0) as mock_run, \
             patch('sys.argv', ['paa-consumer', '--repo-root', '/tmp/repo', '--queue', 'paa-techlead', 'queue-purge']):
            exit_code = main()

        self.assertEqual(exit_code, 0)
        self.assertEqual(mock_run.call_args[0][1], ['purge', '--queue', 'paa-techlead'])

    def test_legacy_techlead_shell_command_is_blocked_by_default(self) -> None:
        buffer = io.StringIO()
        with patch('sys.stdout', buffer), patch('sys.argv', ['paa-consumer', 'techlead-status']):
            exit_code = main()

        self.assertEqual(exit_code, 2)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload['reason'], 'legacy_techlead_shell_disabled')

    def test_legacy_techlead_shell_command_can_be_explicitly_allowed(self) -> None:
        with patch('paa_consumer.__main__.techlead_main', return_value=0) as mock_legacy, \
             patch('sys.argv', ['paa-consumer', '--allow-legacy-techlead-shell', 'techlead-status']):
            exit_code = main()

        self.assertEqual(exit_code, 0)
        mock_legacy.assert_called_once_with(['status'])


if __name__ == '__main__':
    unittest.main()

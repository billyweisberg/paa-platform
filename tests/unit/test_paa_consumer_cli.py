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


if __name__ == '__main__':
    unittest.main()

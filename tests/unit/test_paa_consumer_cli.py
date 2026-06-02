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

    def test_runtime_supervisor_command_forwards_to_paa_cli(self) -> None:
        with patch('paa_consumer.__main__._run_paa_cli', return_value=0) as mock_run, \
             patch('sys.argv', ['paa-consumer', '--repo-root', '/tmp/repo', 'runtime-supervisor-start']):
            exit_code = main()

        self.assertEqual(exit_code, 0)
        self.assertEqual(mock_run.call_args.args[0], ['runtime', 'start', '--repo-root', '/tmp/repo'])

    def test_runtime_supervisor_command_forwards_to_paa_cli_runtime_group(self) -> None:
        with patch('paa_consumer.__main__._run_paa_cli', return_value=0) as mock_run, \
             patch('sys.argv', ['paa-consumer', '--repo-root', '/tmp/repo', 'runtime-supervisor', '--max-iterations', '2']):
            exit_code = main()

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            mock_run.call_args.args[0],
            ['runtime', 'supervisor', '--repo-root', '/tmp/repo', '--max-iterations', '2'],
        )

    def test_runtime_supervisor_status_forwards_to_paa_cli_runtime_group(self) -> None:
        with patch('paa_consumer.__main__._run_paa_cli', return_value=0) as mock_run, \
             patch('sys.argv', ['paa-consumer', '--repo-root', '/tmp/repo', 'runtime-supervisor-status']):
            exit_code = main()

        self.assertEqual(exit_code, 0)
        self.assertEqual(mock_run.call_args.args[0], ['runtime', 'status', '--repo-root', '/tmp/repo'])

    def test_techlead_runtime_forwards_to_paa_cli_runtime_group(self) -> None:
        with patch('paa_consumer.__main__._run_paa_cli', return_value=0) as mock_run, \
             patch('sys.argv', ['paa-consumer', '--repo-root', '/tmp/repo', 'techlead-runtime', '--max-iterations', '2']):
            exit_code = main()

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            mock_run.call_args.args[0],
            ['runtime', 'techlead', '--repo-root', '/tmp/repo', '--max-iterations', '2'],
        )

    def test_qa_runtime_forwards_to_paa_cli_runtime_group(self) -> None:
        with patch('paa_consumer.__main__._run_paa_cli', return_value=0) as mock_run, \
             patch('sys.argv', ['paa-consumer', '--repo-root', '/tmp/repo', 'qa-runtime', '--max-iterations', '2']):
            exit_code = main()

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            mock_run.call_args.args[0],
            ['runtime', 'qa', '--repo-root', '/tmp/repo', '--max-iterations', '2'],
        )

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

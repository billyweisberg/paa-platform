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


if __name__ == '__main__':
    unittest.main()

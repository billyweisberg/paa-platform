from __future__ import annotations

import json
import sys
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))
sys.path.insert(0, str(ROOT / 'packages' / 'paa-producer' / 'src'))
sys.path.insert(0, str(ROOT / 'packages' / 'paa-cli' / 'src'))

from typer.testing import CliRunner

from paa_cli.app import build_app


class PAAOperatorCLIAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()
        self.app = build_app()

    def test_root_help_exposes_component_and_plan_families(self) -> None:
        result = self.runner.invoke(self.app, ['--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('component', result.stdout)
        self.assertIn('plan', result.stdout)

    def test_component_progress_renders_json_output(self) -> None:
        with patch('paa_cli.command_adapters.implementation_plan_progress', return_value={'implementation_plan_id': 'plan-1', 'next_activity_key': 'dto'}):
            result = self.runner.invoke(self.app, ['component', 'progress', '--plan-id', 'plan-1', '--output', 'json'])
        self.assertEqual(result.exit_code, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload['command_family'], 'component')
        self.assertEqual(payload['sections'][0]['data']['implementation_plan_id'], 'plan-1')

    def test_component_next_propagates_fail_closed_exit_code(self) -> None:
        with patch('paa_cli.command_adapters.derive_next_activity_bundle', return_value={'ok': False, 'blocking_reasons': ('No required incomplete activities remain.',)}):
            result = self.runner.invoke(self.app, ['component', 'next', '--plan-id', 'plan-1', '--output', 'summary'])
        self.assertEqual(result.exit_code, 2)
        self.assertIn('failure=no_next_activity', result.stdout)

    def test_plan_inspect_renders_table_output(self) -> None:
        with patch('paa_cli.command_adapters.implementation_plan_progress', return_value={'implementation_plan_id': 'plan-1', 'authority_state_summary': 'active_plan'}):
            result = self.runner.invoke(self.app, ['plan', 'inspect', '--plan-id', 'plan-1'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Implementation Plan Progress', result.stdout)
        self.assertIn('authority_state_summary', result.stdout)


if __name__ == '__main__':
    unittest.main()

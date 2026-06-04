from __future__ import annotations

import io
import json
import sys
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

REPO_ROOT = Path('/Users/billyweisberg/Repos/billyweisberg/paa-platform')
sys.path.insert(0, str(REPO_ROOT / 'packages' / 'paa-core' / 'src'))
sys.path.insert(0, str(REPO_ROOT / 'packages' / 'paa-cli' / 'src'))

from paa_cli.app import _run_producer_command
from paa_core.application.dto.producer import ProducerOperationResult
from paa_core.producer.implementation_plan_activity_state import set_implementation_plan_activity_state


class ImplementationPlanActivityStateTests(unittest.TestCase):
    def test_helper_updates_repository_and_returns_structured_payload(self) -> None:
        with patch(
            'paa_core.producer.implementation_plan_activity_state.PostgresImplementationPlanRepository'
        ) as mock_repo_cls:
            payload = set_implementation_plan_activity_state(
                plan_id='plan-1',
                activity_key='activity-1',
                activity_state='completed',
                completed_at='2026-05-30T00:00:00Z',
                metadata_json='{"source": "unit-test"}',
            )

        self.assertTrue(payload['ok'])
        self.assertEqual(payload['requested_state'], 'completed')
        self.assertEqual(payload['metadata'], {'source': 'unit-test'})
        mock_repo_cls.return_value.set_implementation_plan_activity_state.assert_called_once()

    def test_helper_rejects_non_object_metadata_json(self) -> None:
        with self.assertRaises(ValueError):
            set_implementation_plan_activity_state(
                plan_id='plan-1',
                activity_key='activity-1',
                activity_state='completed',
                metadata_json='["not-an-object"]',
            )

    def test_cli_requires_plan_id(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        fake_client = Mock()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as ctx:
                _run_producer_command(
                    ['set-implementation-plan-activity-state', '--activity-key', 'a1', '--activity-state', 'completed'],
                    fake_client,
                )
        self.assertNotEqual(ctx.exception.code, 0)
        self.assertIn('--plan-id', stderr.getvalue())

    def test_cli_outputs_json(self) -> None:
        stdout = io.StringIO()
        fake_client = Mock()
        fake_client.set_implementation_plan_activity_state.return_value = ProducerOperationResult(
            payload={'ok': True, 'implementation_plan_id': 'plan-1', 'activity_key': 'a1'},
            exit_code=0,
        )
        with redirect_stdout(stdout):
            exit_code = _run_producer_command(
                [
                    'set-implementation-plan-activity-state',
                    '--plan-id',
                    'plan-1',
                    '--activity-key',
                    'a1',
                    '--activity-state',
                    'completed',
                ],
                fake_client,
            )
        self.assertEqual(exit_code, 0)
        self.assertEqual(json.loads(stdout.getvalue())['implementation_plan_id'], 'plan-1')
        fake_client.set_implementation_plan_activity_state.assert_called_once()

    def test_cli_rejects_non_object_metadata_json(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        fake_client = Mock()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as ctx:
                _run_producer_command(
                    [
                        'set-implementation-plan-activity-state',
                        '--plan-id',
                        'plan-1',
                        '--activity-key',
                        'a1',
                        '--activity-state',
                        'completed',
                        '--metadata-json',
                        '["not-an-object"]',
                    ],
                    fake_client,
                )
        self.assertNotEqual(ctx.exception.code, 0)
        self.assertIn('metadata_json must decode to a JSON object', stderr.getvalue())


if __name__ == '__main__':
    unittest.main()

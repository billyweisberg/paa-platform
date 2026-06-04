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
from paa_core.producer.implementation_plan_progress import (
    derive_next_activity_bundle,
    implementation_plan_progress,
    reconcile_implementation_plan_progress,
)


class ImplementationPlanProgressCliTests(unittest.TestCase):
    def test_progress_helper_returns_service_payload(self) -> None:
        with patch('paa_core.producer.implementation_plan_progress.DefaultImplementationPlanProgressService') as mock_service_cls:
            with patch('paa_core.producer.implementation_plan_progress.asdict', return_value={'implementation_plan_id': 'plan-1'}):
                payload = implementation_plan_progress(plan_id='plan-1')
        self.assertEqual(payload['implementation_plan_id'], 'plan-1')
        mock_service_cls.return_value.summarize_plan_progress.assert_called_once()

    def test_next_helper_returns_service_payload(self) -> None:
        with patch('paa_core.producer.implementation_plan_progress.DefaultImplementationPlanProgressService') as mock_service_cls:
            with patch('paa_core.producer.implementation_plan_progress.asdict', return_value={'ok': True}):
                payload = derive_next_activity_bundle(plan_id='plan-1')
        self.assertTrue(payload['ok'])
        mock_service_cls.return_value.derive_next_activity_bundle.assert_called_once()

    def test_reconcile_helper_persists_progress(self) -> None:
        with patch('paa_core.producer.implementation_plan_progress.PostgresImplementationPlanRepository') as mock_repo_cls:
            repo = mock_repo_cls.return_value
            with patch('paa_core.producer.implementation_plan_progress.DefaultImplementationPlanProgressService') as mock_service_cls:
                summary = type('Summary', (), {
                    'metadata': {'component_completion': {'realization_state': 'partially_realized'}},
                    'authority_state_summary': 'partially_realized_plan',
                })()
                mock_service_cls.return_value.summarize_plan_progress.return_value = summary
                with patch('paa_core.producer.implementation_plan_progress.asdict', return_value={'authority_state_summary': 'partially_realized_plan'}):
                    payload = reconcile_implementation_plan_progress(plan_id='plan-1')
        self.assertEqual(payload['authority_state_summary'], 'partially_realized_plan')
        repo.update_implementation_plan_progress.assert_called_once()

    def test_cli_missing_plan_id_fails_cleanly(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        fake_client = Mock()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as ctx:
                _run_producer_command(['implementation-plan-progress'], fake_client)
        self.assertNotEqual(ctx.exception.code, 0)
        self.assertIn('--plan-id', stderr.getvalue())

    def test_cli_json_output_for_progress(self) -> None:
        stdout = io.StringIO()
        fake_client = Mock()
        fake_client.implementation_plan_progress.return_value = ProducerOperationResult(
            payload={'implementation_plan_id': 'plan-1', 'next_activity_key': 'a1'},
            exit_code=0,
        )
        with redirect_stdout(stdout):
            exit_code = _run_producer_command(['implementation-plan-progress', '--plan-id', 'plan-1'], fake_client)
        self.assertEqual(exit_code, 0)
        self.assertEqual(json.loads(stdout.getvalue())['implementation_plan_id'], 'plan-1')
        fake_client.implementation_plan_progress.assert_called_once()

    def test_cli_json_output_for_next(self) -> None:
        stdout = io.StringIO()
        fake_client = Mock()
        fake_client.derive_next_activity_bundle.return_value = ProducerOperationResult(
            payload={'ok': True, 'next_bundle_activity_keys': ['a1']},
            exit_code=0,
        )
        with redirect_stdout(stdout):
            exit_code = _run_producer_command(['derive-next-activity-bundle', '--plan-id', 'plan-1'], fake_client)
        self.assertEqual(exit_code, 0)
        self.assertTrue(json.loads(stdout.getvalue())['ok'])
        fake_client.derive_next_activity_bundle.assert_called_once()


if __name__ == '__main__':
    unittest.main()

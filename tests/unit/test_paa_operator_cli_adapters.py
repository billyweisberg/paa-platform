from __future__ import annotations

import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))
sys.path.insert(0, str(ROOT / 'packages' / 'paa-producer' / 'src'))
sys.path.insert(0, str(ROOT / 'packages' / 'paa-cli' / 'src'))

from paa_cli.command_adapters import ComponentCommandAdapter, PlanCommandAdapter
from paa_cli.models import OperatorCommand, OperatorCommandRequest, OperatorInvocationContext


class PAAOperatorCLIAdapterTests(unittest.TestCase):
    def test_component_materialize_calls_materializer_and_returns_summary(self) -> None:
        request = OperatorCommandRequest(
            command=OperatorCommand(command_family='component', command_name='materialize'),
            invocation_context=OperatorInvocationContext(),
            arguments={'spec': __file__},
        )

        class _Result:
            source_path = __file__
            implementation_plan_id = 'plan-123'
            plan_id_external = 'plan-ext'
            component_id = 'component-123'
            component_element_keys = ('a', 'b')
            activity_keys = ('x',)

        with patch('paa_core.application.operator_command_adapters.materialize_component_spec', return_value=_Result()):
            result = ComponentCommandAdapter().run(request)

        self.assertTrue(result.success)
        self.assertEqual(result.metadata['implementation_plan_id'], 'plan-123')
        self.assertEqual(result.sections[0].data['component_element_count'], 2)

    def test_component_next_requires_plan_id(self) -> None:
        request = OperatorCommandRequest(
            command=OperatorCommand(command_family='component', command_name='next'),
            invocation_context=OperatorInvocationContext(),
        )
        result = ComponentCommandAdapter().run(request)
        self.assertFalse(result.success)
        self.assertEqual(result.failure.code, 'missing_argument')

    def test_plan_progress_calls_progress_surface(self) -> None:
        request = OperatorCommandRequest(
            command=OperatorCommand(command_family='plan', command_name='progress'),
            invocation_context=OperatorInvocationContext(),
            arguments={'plan_id': 'plan-123'},
        )
        with patch('paa_core.application.operator_command_adapters.implementation_plan_progress', return_value={'next_activity_key': 'dto'}):
            result = PlanCommandAdapter().run(request)
        self.assertTrue(result.success)
        self.assertEqual(result.sections[0].data['next_activity_key'], 'dto')

    def test_component_next_fails_closed_when_no_activity_bundle_is_available(self) -> None:
        request = OperatorCommandRequest(
            command=OperatorCommand(command_family='component', command_name='next'),
            invocation_context=OperatorInvocationContext(),
            arguments={'plan_id': 'plan-123'},
        )
        payload = {'ok': False, 'blocking_reasons': ('No required incomplete activities remain.',)}
        with patch('paa_core.application.operator_command_adapters.derive_next_activity_bundle', return_value=payload):
            result = ComponentCommandAdapter().run(request)
        self.assertFalse(result.success)
        self.assertEqual(result.failure.code, 'no_next_activity')
        self.assertIn('No required incomplete activities remain.', result.failure.details)

    def test_unsupported_component_command_fails_closed(self) -> None:
        request = OperatorCommandRequest(
            command=OperatorCommand(command_family='component', command_name='delete-everything'),
            invocation_context=OperatorInvocationContext(),
        )
        result = ComponentCommandAdapter().run(request)
        self.assertFalse(result.supported)
        self.assertEqual(result.failure.code, 'unsupported_command')

    def test_component_complete_runs_mutation_reconcile_and_next(self) -> None:
        request = OperatorCommandRequest(
            command=OperatorCommand(command_family='component', command_name='complete'),
            invocation_context=OperatorInvocationContext(),
            arguments={'plan_id': 'plan-123', 'activity_key': 'dto-models'},
        )
        with patch(
            'paa_core.application.operator_command_adapters.set_implementation_plan_activity_state',
            return_value={'ok': True, 'implementation_plan_id': 'plan-123', 'activity_key': 'dto-models', 'requested_state': 'completed'},
        ) as mock_mutate, patch(
            'paa_core.application.operator_command_adapters.reconcile_implementation_plan_progress',
            return_value={'authority_state_summary': 'partially_realized_plan', 'next_activity_key': 'postgres-adapter'},
        ) as mock_reconcile, patch(
            'paa_core.application.operator_command_adapters.derive_next_activity_bundle',
            return_value={'ok': True, 'next_bundle_activity_keys': ['postgres-adapter'], 'bundle_kind': 'single_activity'},
        ) as mock_next:
            result = ComponentCommandAdapter().run(request)

        self.assertTrue(result.success)
        self.assertTrue(result.metadata['reconcile_performed'])
        self.assertTrue(result.metadata['next_activity_derived'])
        mock_mutate.assert_called_once()
        mock_reconcile.assert_called_once_with(plan_id='plan-123')
        mock_next.assert_called_once_with(plan_id='plan-123')

    def test_component_complete_can_skip_followthrough(self) -> None:
        request = OperatorCommandRequest(
            command=OperatorCommand(command_family='component', command_name='complete'),
            invocation_context=OperatorInvocationContext(),
            arguments={'plan_id': 'plan-123', 'activity_key': 'dto-models', 'no_reconcile': True},
        )
        with patch(
            'paa_core.application.operator_command_adapters.set_implementation_plan_activity_state',
            return_value={'ok': True, 'implementation_plan_id': 'plan-123', 'activity_key': 'dto-models', 'requested_state': 'completed'},
        ) as mock_mutate, patch(
            'paa_core.application.operator_command_adapters.reconcile_implementation_plan_progress'
        ) as mock_reconcile:
            result = ComponentCommandAdapter().run(request)

        self.assertTrue(result.success)
        self.assertFalse(result.metadata['reconcile_performed'])
        self.assertFalse(result.metadata['next_activity_derived'])
        mock_mutate.assert_called_once()
        mock_reconcile.assert_not_called()


if __name__ == '__main__':
    unittest.main()

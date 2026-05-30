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

        with patch('paa_cli.command_adapters.materialize_component_spec', return_value=_Result()):
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
        with patch('paa_cli.command_adapters.implementation_plan_progress', return_value={'next_activity_key': 'dto'}):
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
        with patch('paa_cli.command_adapters.derive_next_activity_bundle', return_value=payload):
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


if __name__ == '__main__':
    unittest.main()

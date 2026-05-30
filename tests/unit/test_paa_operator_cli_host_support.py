from __future__ import annotations

import os
import sys
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-cli' / 'src'))

from paa_cli.environment import EnvironmentResolutionInput, EnvironmentResolver
from paa_cli.models import (
    OperatorCommand,
    OperatorCommandRequest,
    OperatorCommandResult,
    OperatorFailure,
    OperatorInvocationContext,
    OperatorOutputMessage,
    OperatorOutputSection,
    OperatorOutputTable,
)
from paa_cli.normalization import CommandResultNormalizer
from paa_cli.rendering import OutputRenderer
from paa_cli.router import CommandRegistration, CommandRouter


class _StubAdapter:
    def __init__(self, result: OperatorCommandResult) -> None:
        self.result = result
        self.last_request: OperatorCommandRequest | None = None

    def run(self, request: OperatorCommandRequest) -> OperatorCommandResult:
        self.last_request = request
        return self.result


class PAAOperatorCLIHostSupportTests(unittest.TestCase):
    def test_environment_resolver_uses_explicit_repo_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            context = EnvironmentResolver().resolve(EnvironmentResolutionInput(repo_root=tmpdir, output_mode='json'))
        self.assertEqual(context.repo_root, str(Path(tmpdir).resolve()))
        self.assertEqual(context.output_mode, 'json')
        self.assertEqual(context.metadata['resolved_repo_root'], str(Path(tmpdir).resolve()))

    def test_command_router_routes_supported_family(self) -> None:
        command = OperatorCommand(command_family='component', command_name='progress')
        result = OperatorCommandResult(command=command, supported=True, success=True, exit_code=0)
        adapter = _StubAdapter(result)
        router = CommandRouter((CommandRegistration(command_family='component', adapter=adapter),))
        request = OperatorCommandRequest(command=command, invocation_context=OperatorInvocationContext())
        routed = router.route(request)
        self.assertTrue(router.supports_command_family('component'))
        self.assertIs(adapter.last_request, request)
        self.assertEqual(routed.exit_code, 0)

    def test_command_router_fails_closed_for_unsupported_family(self) -> None:
        command = OperatorCommand(command_family='queue', command_name='inspect')
        router = CommandRouter(())
        request = OperatorCommandRequest(command=command, invocation_context=OperatorInvocationContext())
        with self.assertRaises(KeyError):
            router.route(request)

    def test_result_normalizer_accepts_mapping_payload(self) -> None:
        command = OperatorCommand(command_family='plan', command_name='progress')
        result = CommandResultNormalizer().normalize(
            command,
            {
                'success': True,
                'supported': True,
                'messages': ({'level': 'info', 'text': 'ok'},),
                'data': {'state': 'active'},
            },
        )
        self.assertTrue(result.success)
        self.assertEqual(result.sections[0].messages[0].text, 'ok')
        self.assertEqual(result.sections[0].data['state'], 'active')

    def test_result_normalizer_rejects_unsupported_result_shape(self) -> None:
        command = OperatorCommand(command_family='plan', command_name='progress')
        result = CommandResultNormalizer().normalize(command, object())
        self.assertFalse(result.success)
        self.assertEqual(result.failure.code, 'unsupported_result_shape')

    def test_output_renderer_supports_json_table_and_summary(self) -> None:
        command = OperatorCommand(command_family='component', command_name='next')
        result = OperatorCommandResult(
            command=command,
            supported=True,
            success=False,
            exit_code=2,
            sections=(
                OperatorOutputSection(
                    title='Summary',
                    messages=(OperatorOutputMessage(level='warning', text='blocked'),),
                    tables=(OperatorOutputTable(title='Plan', columns=('k', 'v'), rows=(('next', 'host-support'),)),),
                ),
            ),
            failure=OperatorFailure(code='blocked', summary='waiting'),
        )
        renderer = OutputRenderer()
        json_text = renderer.render(result, output_mode='json')
        table_text = renderer.render(result, output_mode='table')
        summary_text = renderer.render(result, output_mode='summary')
        self.assertIn('"command_family": "component"', json_text)
        self.assertIn('Plan', table_text)
        self.assertIn('FAILURE | blocked | waiting', table_text)
        self.assertIn('component:next', summary_text)


if __name__ == '__main__':
    unittest.main()

from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-cli' / 'src'))

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


class PAAOperatorCLIModelsTests(unittest.TestCase):
    def test_command_request_captures_command_and_context(self) -> None:
        command = OperatorCommand(command_family='component', command_name='materialize')
        context = OperatorInvocationContext(repo_root='/repo', output_mode='json', dry_run=True)
        request = OperatorCommandRequest(command=command, invocation_context=context, arguments={'spec': 'x.md'})
        self.assertEqual(request.command.command_family, 'component')
        self.assertTrue(request.invocation_context.dry_run)
        self.assertEqual(request.arguments['spec'], 'x.md')

    def test_result_can_carry_section_and_failure(self) -> None:
        command = OperatorCommand(command_family='plan', command_name='progress')
        table = OperatorOutputTable(title='Plan', columns=('k', 'v'), rows=(('state', 'active'),))
        section = OperatorOutputSection(
            title='Summary',
            messages=(OperatorOutputMessage(level='info', text='ok'),),
            tables=(table,),
        )
        failure = OperatorFailure(code='blocked', summary='no plan', details=('missing plan id',))
        result = OperatorCommandResult(
            command=command,
            supported=False,
            success=False,
            exit_code=2,
            sections=(section,),
            failure=failure,
        )
        self.assertFalse(result.supported)
        self.assertEqual(result.failure.code, 'blocked')
        self.assertEqual(result.sections[0].tables[0].title, 'Plan')


if __name__ == '__main__':
    unittest.main()

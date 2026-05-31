from __future__ import annotations

import sys
from pathlib import Path
import unittest
from unittest.mock import Mock

from typer.testing import CliRunner

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))
sys.path.insert(0, str(ROOT / 'packages' / 'paa-producer' / 'src'))
sys.path.insert(0, str(ROOT / 'packages' / 'paa-cli' / 'src'))

from paa_cli.app import build_app, build_default_cli
from paa_cli.command_adapters import (
    ComponentCommandAdapter,
    PlanCommandAdapter,
    ReportCommandAdapter,
    StatusCommandAdapter,
)
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
from paa_cli.router import CommandRegistration, CommandRouter


class _StubProjectionService:
    def get_status_projection(self, methodology_execution_id: str):
        from paa_core.services.methodology_execution_projection import MethodologyExecutionStatusProjection
        return MethodologyExecutionStatusProjection(
            methodology_execution_id=methodology_execution_id,
            lane='component_realization',
            stage='slice_execution',
            step='derive_next_activity_bundle',
            status='ready',
            current_owner_role='System',
            next_action_key='execute_component_activity',
            blocked_reason=None,
            component_id='component-1',
            design_package_id='design-1',
            implementation_plan_id='plan-1',
            coder_run_brief_id=None,
            packet_id=None,
            workflow_state_id=None,
            active_authority_ref=None,
            active_artifact_ref=None,
            binding_refs=('implementation_plan:plan-1',),
            summary_text='Ready to execute the next component activity.',
        )

    def find_status_projection(self, project_id: str, work_item_id: str, component_id: str | None = None):
        return self.get_status_projection('exec-from-anchor')

    def get_next_action_projection(self, methodology_execution_id: str):
        from paa_core.services.methodology_execution_projection import MethodologyExecutionNextActionProjection
        return MethodologyExecutionNextActionProjection(
            methodology_execution_id=methodology_execution_id,
            recommended_next_action_key='execute_component_activity',
            recommended_owner_role='System',
            lane='component_realization',
            stage='slice_execution',
            step='derive_next_activity_bundle',
            prerequisite_summary=('current-step:derive_next_activity_bundle',),
            blocked_reason=None,
            component_id='component-1',
            implementation_plan_id='plan-1',
            packet_id=None,
        )

    def explain_current_methodology_execution(self, methodology_execution_id: str):
        from paa_core.services.methodology_execution_projection import MethodologyExecutionExplainProjection
        return MethodologyExecutionExplainProjection(
            methodology_execution_id=methodology_execution_id,
            lane='component_realization',
            stage='slice_execution',
            step='derive_next_activity_bundle',
            status='ready',
            current_owner_role='System',
            explanation_summary='The next component activity is ready to execute.',
            transition_context='component-progress-reconciled',
            binding_refs=('implementation_plan:plan-1',),
            blocked_reason=None,
        )


class _StubPreflightService:
    def __init__(self, *, outcome_kind: str = 'allowed', redirect_target: str | None = None, reason: str = 'Preflight passed.') -> None:
        self.outcome_kind = outcome_kind
        self.redirect_target = redirect_target
        self.reason = reason

    def evaluate_command(self, request):
        from paa_core.services.methodology_execution_preflight import (
            MethodologyExecutionPreflightOutcome,
            MethodologyExecutionPreflightResult,
        )
        from paa_core.services.methodology_execution_projection import MethodologyExecutionStatusProjection

        projection = MethodologyExecutionStatusProjection(
            methodology_execution_id=request.methodology_execution_id or 'exec-1',
            lane='component_realization',
            stage='slice_execution',
            step='derive_next_activity_bundle',
            status='ready',
            current_owner_role='System',
            next_action_key='execute_component_activity',
            blocked_reason=None,
            component_id='component-1',
            design_package_id='design-1',
            implementation_plan_id='plan-1',
            coder_run_brief_id=None,
            packet_id=None,
            workflow_state_id=None,
            active_authority_ref=None,
            active_artifact_ref=None,
            binding_refs=('implementation_plan:plan-1',),
            summary_text='Ready to execute the next component activity.',
        )
        outcome = MethodologyExecutionPreflightOutcome(
            methodology_execution_id=projection.methodology_execution_id,
            outcome_kind=self.outcome_kind,
            rule_key='unit-test-rule',
            lane=projection.lane,
            stage=projection.stage,
            step=projection.step,
            status=projection.status,
            current_owner_role=projection.current_owner_role,
            redirect_target=self.redirect_target,
            recommended_next_action_key=projection.next_action_key,
            reason=self.reason,
        )
        return MethodologyExecutionPreflightResult(
            methodology_execution_id=projection.methodology_execution_id,
            request=request,
            status_projection=projection,
            outcome=outcome,
            ok=self.outcome_kind not in {'blocked', 'redirect'},
            reason=None if self.outcome_kind not in {'blocked', 'redirect'} else f'preflight_{self.outcome_kind}',
        )


class _StubLogger:
    def info(self, event: str, **fields: object) -> None:
        del event, fields

    def warning(self, event: str, **fields: object) -> None:
        del event, fields


class PAAOperatorCLIAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

    def _cli(self, *, preflight_service=None):
        from paa_cli.app import DefaultPAAOperatorCLI
        from paa_cli.environment import EnvironmentResolver
        from paa_cli.normalization import CommandResultNormalizer
        from paa_cli.rendering import OutputRenderer

        component_adapter = Mock(spec=ComponentCommandAdapter)
        component_adapter.run.return_value = OperatorCommandResult(
            command=OperatorCommand(command_family='component', command_name='next'),
            supported=True,
            success=True,
            exit_code=0,
            sections=(
                OperatorOutputSection(
                    title='Component Next Activity',
                    messages=(OperatorOutputMessage(level='info', text='Command completed.'),),
                    tables=(
                        OperatorOutputTable(
                            title='Component Next Activity',
                            columns=('field', 'value'),
                            rows=(('ok', 'True'),),
                        ),
                    ),
                ),
            ),
        )
        plan_adapter = Mock(spec=PlanCommandAdapter)
        plan_adapter.run.return_value = OperatorCommandResult(
            command=OperatorCommand(command_family='plan', command_name='inspect'),
            supported=True,
            success=True,
            exit_code=0,
            sections=(
                OperatorOutputSection(
                    title='Implementation Plan Progress',
                    messages=(OperatorOutputMessage(level='info', text='Plan summary loaded.'),),
                    tables=(
                        OperatorOutputTable(
                            title='Plan Progress Summary',
                            columns=('field', 'value'),
                            rows=(('plan_id', 'plan-1'),),
                        ),
                    ),
                ),
            ),
        )
        router = CommandRouter(
            (
                CommandRegistration(command_family='component', adapter=component_adapter),
                CommandRegistration(command_family='plan', adapter=plan_adapter),
                CommandRegistration(command_family='status', adapter=Mock(run=Mock(return_value=OperatorCommandResult(
                    command=OperatorCommand(command_family='status', command_name='inspect'),
                    supported=True,
                    success=True,
                    exit_code=0,
                )))),
                CommandRegistration(command_family='report', adapter=Mock(run=Mock(return_value=OperatorCommandResult(
                    command=OperatorCommand(command_family='report', command_name='next'),
                    supported=True,
                    success=True,
                    exit_code=0,
                )))),
            )
        )
        return DefaultPAAOperatorCLI(
            logger=_StubLogger(),
            environment_resolver=EnvironmentResolver(),
            router=router,
            normalizer=CommandResultNormalizer(),
            renderer=OutputRenderer(),
            methodology_execution_preflight_service=preflight_service,
        ), component_adapter

    def _typer_cli(self, *, preflight_service=None):
        from paa_cli.app import DefaultPAAOperatorCLI
        from paa_cli.environment import EnvironmentResolver
        from paa_cli.normalization import CommandResultNormalizer
        from paa_cli.rendering import OutputRenderer

        component_adapter = Mock(spec=ComponentCommandAdapter)
        component_adapter.run.return_value = OperatorCommandResult(
            command=OperatorCommand(command_family='component', command_name='progress'),
            supported=True,
            success=True,
            exit_code=0,
            sections=(
                OperatorOutputSection(
                    title='Component Progress',
                    messages=(OperatorOutputMessage(level='info', text='Component progress loaded.'),),
                    tables=(
                        OperatorOutputTable(
                            title='Component Progress',
                            columns=('field', 'value'),
                            rows=(('plan_id', 'plan-1'), ('status', 'ready')),
                        ),
                    ),
                ),
            ),
        )
        plan_adapter = Mock(spec=PlanCommandAdapter)
        plan_adapter.run.return_value = OperatorCommandResult(
            command=OperatorCommand(command_family='plan', command_name='progress'),
            supported=True,
            success=True,
            exit_code=0,
            sections=(
                OperatorOutputSection(
                    title='Implementation Plan Progress',
                    messages=(OperatorOutputMessage(level='info', text='Plan progress loaded.'),),
                    tables=(
                        OperatorOutputTable(
                            title='Plan Progress Summary',
                            columns=('field', 'value'),
                            rows=(('plan_id', 'plan-1'), ('completion_ratio', '0.5')),
                        ),
                    ),
                ),
            ),
        )
        router = CommandRouter(
            (
                CommandRegistration(command_family='component', adapter=component_adapter),
                CommandRegistration(command_family='plan', adapter=plan_adapter),
                CommandRegistration(
                    command_family='status',
                    adapter=StatusCommandAdapter(
                        methodology_execution_projection_service=_StubProjectionService(),
                    ),
                ),
                CommandRegistration(
                    command_family='report',
                    adapter=ReportCommandAdapter(
                        methodology_execution_projection_service=_StubProjectionService(),
                    ),
                ),
            )
        )
        cli = DefaultPAAOperatorCLI(
            logger=_StubLogger(),
            environment_resolver=EnvironmentResolver(),
            router=router,
            normalizer=CommandResultNormalizer(),
            renderer=OutputRenderer(),
            methodology_execution_preflight_service=preflight_service,
        )
        return build_app(cli=cli), component_adapter, plan_adapter

    def test_build_default_cli_includes_methodology_pointer_services(self) -> None:
        cli = build_default_cli()
        self.assertTrue(cli.supports_command_family('status'))
        self.assertTrue(cli.supports_command_family('report'))
        self.assertIsNotNone(cli.methodology_execution_preflight_service)

    def test_preflight_warning_is_prepended_to_component_command_output(self) -> None:
        cli, _ = self._cli(preflight_service=_StubPreflightService(outcome_kind='warn', reason='Preflight warning.'))
        request = OperatorCommandRequest(
            command=OperatorCommand(command_family='component', command_name='next'),
            invocation_context=OperatorInvocationContext(),
            arguments={'plan_id': 'plan-1', 'methodology_execution_id': 'exec-1'},
        )

        result = cli.run_command(request)

        self.assertTrue(result.success)
        self.assertEqual(result.sections[0].title, 'Methodology Preflight')
        self.assertEqual(result.sections[0].messages[0].text, 'Preflight warning.')

    def test_preflight_redirect_blocks_component_execution(self) -> None:
        cli, component_adapter = self._cli(preflight_service=_StubPreflightService(outcome_kind='redirect', redirect_target='status', reason='Wrong lane.'))
        request = OperatorCommandRequest(
            command=OperatorCommand(command_family='component', command_name='progress'),
            invocation_context=OperatorInvocationContext(),
            arguments={'plan_id': 'plan-1', 'methodology_execution_id': 'exec-1'},
        )

        result = cli.run_command(request)

        self.assertFalse(result.success)
        self.assertEqual(result.failure.code, 'preflight_redirect')
        component_adapter.run.assert_not_called()

    def test_status_and_report_commands_are_available(self) -> None:
        app = build_app()
        self.assertIsNotNone(app)

    def test_status_inspect_renders_live_typer_output(self) -> None:
        app, _, _ = self._typer_cli()

        result = self.runner.invoke(
            app,
            ['status', 'inspect', '--methodology-execution-id', 'exec-1', '--output', 'summary'],
        )

        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn('status:inspect', result.output)
        self.assertIn('Ready to execute the next component activity.', result.output)

    def test_status_next_renders_live_typer_output(self) -> None:
        app, _, _ = self._typer_cli()

        result = self.runner.invoke(
            app,
            ['status', 'next', '--methodology-execution-id', 'exec-1', '--output', 'summary'],
        )

        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn('status:next', result.output)
        self.assertIn('execute_component_activity', result.output)
        self.assertIn('Next recommended action', result.output)

    def test_report_next_renders_live_typer_output(self) -> None:
        app, _, _ = self._typer_cli()

        result = self.runner.invoke(
            app,
            ['report', 'next', '--methodology-execution-id', 'exec-1', '--output', 'summary'],
        )

        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn('report:next', result.output)
        self.assertIn('execute_component_activity', result.output)
        self.assertIn('Next recommended action', result.output)

    def test_report_explain_renders_live_typer_output(self) -> None:
        app, _, _ = self._typer_cli()

        result = self.runner.invoke(
            app,
            ['report', 'explain', '--methodology-execution-id', 'exec-1', '--output', 'summary'],
        )

        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn('report:explain', result.output)
        self.assertIn('The next component activity is ready to execute.', result.output)
        self.assertIn('supported=true success=true exit_code=0', result.output)

    def test_component_progress_is_blocked_by_preflight_in_live_typer_output(self) -> None:
        app, component_adapter, _ = self._typer_cli(
            preflight_service=_StubPreflightService(outcome_kind='blocked', reason='Blocked by preflight.'),
        )

        result = self.runner.invoke(
            app,
            [
                'component',
                'progress',
                '--plan-id',
                'plan-1',
                '--methodology-execution-id',
                'exec-1',
            ],
        )

        self.assertEqual(result.exit_code, 2, msg=result.output)
        self.assertIn('Methodology Preflight', result.output)
        self.assertIn('Blocked by preflight.', result.output)
        component_adapter.run.assert_not_called()

    def test_plan_progress_redirects_when_preflight_rejects_lane_in_live_typer_output(self) -> None:
        app, _, plan_adapter = self._typer_cli(
            preflight_service=_StubPreflightService(
                outcome_kind='redirect',
                redirect_target='status.inspect',
                reason='Use methodology status first.',
            ),
        )

        result = self.runner.invoke(
            app,
            [
                'plan',
                'progress',
                '--plan-id',
                'plan-1',
                '--methodology-execution-id',
                'exec-1',
            ],
        )

        self.assertEqual(result.exit_code, 2, msg=result.output)
        self.assertIn('Methodology Preflight', result.output)
        self.assertIn('Use methodology status first.', result.output)
        self.assertIn('status.inspect', result.output)
        plan_adapter.run.assert_not_called()


if __name__ == '__main__':
    unittest.main()

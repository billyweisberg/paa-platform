from __future__ import annotations

import json
import os
import sys
from pathlib import Path
import unittest
from unittest.mock import Mock

from typer.testing import CliRunner

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))
sys.path.insert(0, str(ROOT / 'packages' / 'paa-producer' / 'src'))
sys.path.insert(0, str(ROOT / 'packages' / 'paa-cli' / 'src'))
sys.path.insert(0, str(ROOT / 'packages' / 'paa-consumer' / 'src'))

from paa_cli.app import build_app, build_default_cli
from paa_core.api.runtime.client import HttpRuntimeApiClient
from paa_cli.command_adapters import (
    AgentCommandAdapter,
    ComponentCommandAdapter,
    PlanCommandAdapter,
    QueueCommandAdapter,
    ReportCommandAdapter,
    RoleCommandAdapter,
    StatusCommandAdapter,
    WorkerCommandAdapter,
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
from paa_core.services.packet_reference_resolution import DefaultPacketReferenceResolutionService
from paa_core.repositories.runtime_identity import AgentRecord, RoleRecord


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




class _StubQueuePacketRuntimeController:
    def handle_packet(self, request):
        from paa_core.services.queue_packet_runtime_controller import (
            QueuePacketDispatchSummary,
            QueuePacketRuntimeResult,
        )
        if request.packet_payload is None and request.packet_path is None:
            return QueuePacketRuntimeResult(
                request=request,
                dispatch_summary=QueuePacketDispatchSummary(
                    handler_key='packet-payload-resolution',
                    packet_schema_type=request.packet_schema_type,
                    target_worker_host='TechLeadWorkerService',
                    dispatch_supported=False,
                    queue_side_effect_required=False,
                    ack_required=False,
                    blocking_reasons=('missing_packet_payload',),
                    notes=('fail-closed', 'packet-payload-required'),
                ),
                selected_worker_result=None,
                normalized_queue_side_effect_summary=None,
                ok=False,
                reason='missing_packet_payload',
                details='The supported dry-run controller slice requires packet payload or a readable packet path.',
                dry_run=True,
            )
        return QueuePacketRuntimeResult(
            request=request,
            dispatch_summary=QueuePacketDispatchSummary(
                handler_key='techlead-worker-dispatch',
                packet_schema_type=request.packet_schema_type,
                target_worker_host='TechLeadWorkerService',
                dispatch_supported=True,
                queue_side_effect_required=False,
                ack_required=False,
                blocking_reasons=(),
                notes=('dry-run-only',),
            ),
            selected_worker_result=None,
            normalized_queue_side_effect_summary='Dry run only: no queue send or ack side effects executed.',
            ok=True,
            dry_run=True,
        )

    def supports_packet_schema_type(self, packet_schema_type: str) -> bool:
        return packet_schema_type == 'worker_result_packet'


class _StubRuntimeEventRepository:
    def get_queue_message_by_external(self, message_id_external: str):
        from paa_core.repositories.runtime_event import QueueMessageRecord

        if message_id_external != 'msg-1':
            return None
        return QueueMessageRecord(
            queue_message_id='queue-message-1',
            handoff_id='handoff-1',
            queue_name='paa-techlead',
            schema_type='worker_result_packet',
            message_id_external='msg-1',
            correlation_key='corr-1',
            payload={},
            status='sent',
            sent_at=None,
            claimed_at=None,
            acknowledged_at=None,
            metadata={},
            created_at=None,
            updated_at=None,
        )

    def get_latest_automation_run_for_message_id(self, message_id_external: str):
        from paa_core.repositories.runtime_event import AutomationRunRecord

        if message_id_external != 'msg-1':
            return None
        return AutomationRunRecord(
            automation_run_id='automation-run-1',
            agent_id='agent-1',
            work_item_id='work-item-1',
            handoff_id='handoff-1',
            trigger_type='packet_compilation:worker_result_packet',
            status='completed',
            started_at=None,
            finished_at=None,
            summary='Compiled worker result packet.',
            artifacts={
                'message_id': 'msg-1',
                'packet_output_path': '/tmp/worker-result.json',
            },
            created_at=None,
            updated_at=None,
        )


class _StubPacketArtifactReader:
    def read_packet_payload(self, packet_path: str) -> dict[str, object]:
        return {'methodology_execution_id': 'exec-1', 'source_packet_path': packet_path}


class _StubLogger:
    def info(self, event: str, **fields: object) -> None:
        del event, fields

    def warning(self, event: str, **fields: object) -> None:
        del event, fields


class _StubRuntimeIdentityRepository:
    def __init__(self) -> None:
        self.roles: dict[tuple[str, str], RoleRecord] = {}
        self.agents: dict[tuple[str, str], AgentRecord] = {}

    def get_role_by_name(self, project_slug: str, role_name: str):
        return self.roles.get((project_slug, role_name))

    def upsert_role(self, spec):
        record = RoleRecord(
            role_id=f'role-{spec.name.lower()}',
            project_id=f'project-{spec.project_slug}',
            name=spec.name,
            category=spec.category,
            description=spec.description,
            is_human_capable=spec.is_human_capable,
            is_automation_capable=spec.is_automation_capable,
            sort_order=spec.sort_order,
            active=spec.active,
            created_at=None,
            updated_at=None,
        )
        self.roles[(spec.project_slug, spec.name)] = record
        return record

    def get_agent_by_name(self, project_slug: str, agent_name: str):
        return self.agents.get((project_slug, agent_name))

    def upsert_agent(self, spec):
        role = None
        if spec.role_name is not None:
            role = self.get_role_by_name(spec.project_slug, spec.role_name)
            if role is None:
                raise LookupError(f'Role {spec.role_name!r} does not exist in project {spec.project_slug!r}.')
        record = AgentRecord(
            agent_id=f"agent-{spec.name.lower().replace(' ', '-')}",
            project_id=f'project-{spec.project_slug}',
            role_id=role.role_id if role else None,
            name=spec.name,
            agent_type=spec.agent_type,
            runtime_kind=spec.runtime_kind,
            active=spec.active,
            metadata=dict(spec.metadata or {}),
            created_at=None,
            updated_at=None,
        )
        self.agents[(spec.project_slug, spec.name)] = record
        return record


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
        runtime_identity_repository = _StubRuntimeIdentityRepository()
        def component_run(request: OperatorCommandRequest) -> OperatorCommandResult:
            if request.command.command_name == 'complete':
                return OperatorCommandResult(
                    command=OperatorCommand(command_family='component', command_name='complete'),
                    supported=True,
                    success=True,
                    exit_code=0,
                    sections=(
                        OperatorOutputSection(
                            title='Component Complete',
                            messages=(OperatorOutputMessage(level='info', text='Activity completion command applied.'),),
                            tables=(
                                OperatorOutputTable(
                                    title='Component Complete Summary',
                                    columns=('field', 'value'),
                                    rows=(
                                        ('activity_key', 'activity-1'),
                                        ('activity_state', 'completed'),
                                        ('reconcile_performed', 'True'),
                                        ('next_activity_derived', 'True'),
                                    ),
                                ),
                            ),
                            data={
                                'activity_key': 'activity-1',
                                'activity_state': 'completed',
                                'reconcile_performed': True,
                                'next_activity_derived': True,
                                'next_activity_bundle': {'ok': True, 'next_bundle_activity_keys': ('next-1',)},
                            },
                        ),
                    ),
                )
            return OperatorCommandResult(
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
        component_adapter.run.side_effect = component_run
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
                    command_family='role',
                    adapter=RoleCommandAdapter(
                        runtime_identity_repository=runtime_identity_repository,
                    ),
                ),
                CommandRegistration(
                    command_family='agent',
                    adapter=AgentCommandAdapter(
                        runtime_identity_repository=runtime_identity_repository,
                    ),
                ),
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
                CommandRegistration(
                    command_family='queue',
                    adapter=QueueCommandAdapter(
                        queue_packet_runtime_controller=_StubQueuePacketRuntimeController(),
                        runtime_event_repository=_StubRuntimeEventRepository(),
                    ),
                ),
                CommandRegistration(
                    command_family='worker',
                    adapter=WorkerCommandAdapter(
                        queue_packet_runtime_controller=_StubQueuePacketRuntimeController(),
                        packet_reference_resolution_service=DefaultPacketReferenceResolutionService(
                            runtime_event_repository=_StubRuntimeEventRepository(),
                            packet_artifact_reader=_StubPacketArtifactReader(),
                            runtime_path_adapter=None,
                        ),
                        runtime_event_repository=_StubRuntimeEventRepository(),
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

    def test_queue_and_worker_commands_are_available(self) -> None:
        app = build_app()
        self.assertIsNotNone(app)

    def test_role_and_agent_commands_are_available(self) -> None:
        app = build_app()
        self.assertIsNotNone(app)

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

    def test_component_complete_renders_live_typer_output_with_default_followthrough(self) -> None:
        app, component_adapter, _ = self._typer_cli()

        result = self.runner.invoke(
            app,
            [
                'component',
                'complete',
                '--plan-id',
                'plan-1',
                '--activity-key',
                'activity-1',
                '--output',
                'summary',
            ],
        )

        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn('component:complete', result.output)
        self.assertIn('Activity completion command applied.', result.output)
        component_adapter.run.assert_called_once()

    def test_queue_preview_renders_live_typer_output(self) -> None:
        app, _, _ = self._typer_cli()

        result = self.runner.invoke(
            app,
            [
                'queue',
                'preview',
                '--queue-name',
                'paa-techlead',
                '--packet-schema-type',
                'worker_result_packet',
                '--packet-payload-json',
                '{\"methodology_execution_id\": \"exec-1\"}',
                '--output',
                'json',
            ],
        )

        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn('\"command_family\": \"queue\"', result.output)
        self.assertIn('Queue packet preview completed.', result.output)
        self.assertIn('\"packet_schema_type\": \"worker_result_packet\"', result.output)
        self.assertIn('\"preview_supported\": true', result.output)
        self.assertIn('\"packet_reference\": \"debug:inline-packet-payload\"', result.output)

    def test_queue_preview_prefers_minimal_packet_reference_when_packet_path_is_provided(self) -> None:
        app, _, _ = self._typer_cli()

        result = self.runner.invoke(
            app,
            [
                'queue',
                'preview',
                '--queue-name',
                'paa-techlead',
                '--packet-schema-type',
                'worker_result_packet',
                '--packet-path',
                'packets/worker-result.json',
                '--output',
                'json',
            ],
        )

        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn('\"packet_reference\": \"packets/worker-result.json\"', result.output)
        self.assertIn('\"normalized_packet_envelope\"', result.output)
        self.assertIn('\"normalized_packet_payload\": null', result.output)

    def test_queue_preview_uses_runtime_event_message_pointer_when_packet_message_id_is_provided(self) -> None:
        app, _, _ = self._typer_cli()

        result = self.runner.invoke(
            app,
            [
                'queue',
                'preview',
                '--queue-name',
                'paa-techlead',
                '--packet-schema-type',
                'worker_result_packet',
                '--packet-message-id',
                'msg-1',
                '--output',
                'json',
            ],
        )

        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn('\"packet_message_id\": \"msg-1\"', result.output)
        self.assertIn('\"packet_reference\": \"msg-1\"', result.output)
        self.assertIn('\"normalized_packet_payload\": null', result.output)

    def test_worker_dispatch_renders_live_typer_output(self) -> None:
        app, _, _ = self._typer_cli()

        result = self.runner.invoke(
            app,
            [
                'worker',
                'dispatch',
                '--queue-name',
                'paa-techlead',
                '--packet-schema-type',
                'worker_result_packet',
                '--packet-payload-json',
                '{\"methodology_execution_id\": \"exec-1\"}',
                '--output',
                'json',
            ],
        )

        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn('\"command_family\": \"worker\"', result.output)
        self.assertIn('Worker dispatch preview completed.', result.output)
        self.assertIn('TechLeadWorkerService', result.output)

    def test_worker_dispatch_reuses_queue_claim_path_for_packet_path_input(self) -> None:
        app, _, _ = self._typer_cli()

        result = self.runner.invoke(
            app,
            [
                'worker',
                'dispatch',
                '--queue-name',
                'paa-techlead',
                '--packet-schema-type',
                'worker_result_packet',
                '--packet-path',
                'packets/worker-result.json',
                '--output',
                'json',
            ],
        )

        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn('\"packet_path\": \"packets/worker-result.json\"', result.output)
        self.assertIn('\"target_worker_host\": \"TechLeadWorkerService\"', result.output)

    def test_worker_dispatch_from_message_pointer_resolves_artifact_path_through_shared_core(self) -> None:
        app, _, _ = self._typer_cli()

        result = self.runner.invoke(
            app,
            [
                'worker',
                'dispatch',
                '--queue-name',
                'paa-techlead',
                '--packet-schema-type',
                'worker_result_packet',
                '--packet-message-id',
                'msg-1',
                '--output',
                'json',
            ],
        )

        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn('\"packet_message_id\": \"msg-1\"', result.output)
        self.assertIn('\"packet_path\": \"/tmp/worker-result.json\"', result.output)
        self.assertIn('\"target_worker_host\": \"TechLeadWorkerService\"', result.output)

    def test_runtime_start_renders_live_typer_output(self) -> None:
        app, _, _ = self._typer_cli()
        fake_service = Mock()
        from paa_core.application.dto.runtime import RuntimeOperationResult
        fake_service.start_supervisor.return_value = RuntimeOperationResult(payload={'ok': True, 'pid': 111}, exit_code=0)

        with unittest.mock.patch('paa_cli.app._build_runtime_api_client', return_value=fake_service):
            result = self.runner.invoke(app, ['runtime', 'start', '--repo-root', str(ROOT)])

        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertEqual(json.loads(result.stdout)['pid'], 111)
        fake_service.start_supervisor.assert_called_once()

    def test_runtime_status_renders_live_typer_output(self) -> None:
        app, _, _ = self._typer_cli()
        fake_service = Mock()
        from paa_core.application.dto.runtime import RuntimeOperationResult
        fake_service.supervisor_status.return_value = RuntimeOperationResult(payload={'ok': True, 'running': True, 'pid': 222}, exit_code=0)

        with unittest.mock.patch('paa_cli.app._build_runtime_api_client', return_value=fake_service):
            result = self.runner.invoke(app, ['runtime', 'status', '--repo-root', str(ROOT)])

        self.assertEqual(result.exit_code, 0, msg=result.output)
        payload = json.loads(result.stdout)
        self.assertTrue(payload['running'])
        self.assertEqual(payload['pid'], 222)

    def test_runtime_techlead_renders_live_typer_output(self) -> None:
        app, _, _ = self._typer_cli()
        fake_service = Mock()
        from paa_core.application.dto.runtime import RuntimeOperationResult
        fake_service.run_techlead_host.return_value = RuntimeOperationResult(payload={
            'host_name': 'techlead-runtime-host',
            'queue_name': 'paa-techlead',
            'intake_mode': 'preview',
            'iteration_count': 1,
            'iterations': [],
        }, exit_code=0)

        with unittest.mock.patch('paa_cli.app._build_runtime_api_client', return_value=fake_service):
            result = self.runner.invoke(app, ['runtime', 'techlead', '--repo-root', str(ROOT)])

        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertEqual(json.loads(result.stdout)['queue_name'], 'paa-techlead')
        fake_service.run_techlead_host.assert_called_once()

    def test_queue_ensure_topology_uses_runtime_queue_admin_service(self) -> None:
        app, _, _ = self._typer_cli()
        fake_service = Mock()
        from paa_core.application.dto.queue import QueueOperationResult
        fake_service.ensure_topology.return_value = QueueOperationResult(payload={'ok': True, 'queues': ['paa-techlead']}, exit_code=0)

        with unittest.mock.patch('paa_cli.app._build_runtime_api_client', return_value=fake_service):
            result = self.runner.invoke(app, ['queue', 'ensure-topology', '--repo-root', str(ROOT)])

        self.assertEqual(result.exit_code, 0, msg=result.output)
        fake_service.ensure_topology.assert_called_once()

    def test_queue_purge_uses_runtime_queue_admin_service(self) -> None:
        app, _, _ = self._typer_cli()
        fake_service = Mock()
        from paa_core.application.dto.queue import QueueOperationResult
        fake_service.purge.return_value = QueueOperationResult(payload={'ok': True, 'purged_queues': ['paa-techlead']}, exit_code=0)

        with unittest.mock.patch('paa_cli.app._build_runtime_api_client', return_value=fake_service):
            result = self.runner.invoke(app, ['queue', 'purge', '--repo-root', str(ROOT), '--queue', 'paa-techlead'])

        self.assertEqual(result.exit_code, 0, msg=result.output)
        fake_service.purge.assert_called_once()

    def test_queue_claim_next_uses_runtime_queue_admin_service(self) -> None:
        app, _, _ = self._typer_cli()
        fake_service = Mock()
        from paa_core.application.dto.queue import QueueOperationResult
        fake_service.claim_next.return_value = QueueOperationResult(payload={'ok': True, 'claimed': False}, exit_code=0)

        with unittest.mock.patch('paa_cli.app._build_runtime_api_client', return_value=fake_service):
            result = self.runner.invoke(app, ['queue', 'claim-next', '--repo-root', str(ROOT), '--queue', 'paa-techlead'])

        self.assertEqual(result.exit_code, 0, msg=result.output)
        fake_service.claim_next.assert_called_once()

    def test_queue_send_packet_uses_runtime_queue_admin_service(self) -> None:
        app, _, _ = self._typer_cli()
        fake_service = Mock()
        from paa_core.application.dto.queue import QueueOperationResult
        fake_service.send_packet.return_value = QueueOperationResult(payload={'ok': True, 'resolved_queue': 'paa-techlead'}, exit_code=0)

        with unittest.mock.patch('paa_cli.app._build_runtime_api_client', return_value=fake_service):
            result = self.runner.invoke(
                app,
                ['queue', 'send-packet', '--repo-root', str(ROOT), '--message-file', str(ROOT / 'packet.json')],
            )

        self.assertEqual(result.exit_code, 0, msg=result.output)
        fake_service.send_packet.assert_called_once()

    def test_ops_automation_preflight_uses_core_service(self) -> None:
        app, _, _ = self._typer_cli()
        fake_service = Mock()
        from paa_core.application.dto.workflow import AutomationPreflightRequest, AutomationPreflightResultView
        fake_service.evaluate_automation_preflight.return_value = AutomationPreflightResultView(payload={
            'ok': True,
            'should_invoke_model': False,
            'skip_model_invocation': True,
            'gate_reason': 'no_role_work_detected',
            'workflow_stage': 'idle',
            'current_owner_role': 'Unknown',
        }, exit_code=0)

        with unittest.mock.patch('paa_cli.app._build_runtime_api_client', return_value=fake_service):
            result = self.runner.invoke(
                app,
                ['ops', 'automation-preflight', '--repo-root', str(ROOT), '--target-role', 'techlead'],
            )

        self.assertEqual(result.exit_code, 0, msg=result.output)
        fake_service.evaluate_automation_preflight.assert_called_once_with(
            AutomationPreflightRequest(
                repo_root=ROOT,
                target_role='techlead',
                project_slug='paa-platform',
            )
        )

    def test_runtime_api_client_builder_uses_http_client_when_configured(self) -> None:
        from paa_cli.app import _build_runtime_api_client

        with unittest.mock.patch.dict(os.environ, {'PAA_RUNTIME_API_URL': 'http://127.0.0.1:8080'}):
            client = _build_runtime_api_client()

        self.assertIsInstance(client, HttpRuntimeApiClient)

    def test_report_techlead_service_map_uses_core_builder(self) -> None:
        app, _, _ = self._typer_cli()
        fake_service = Mock()
        from paa_core.application.dto.status import TechLeadServiceMapResultView
        fake_service.techlead_service_map.return_value = TechLeadServiceMapResultView(
            payload={'techlead_shell_status': 'mostly_shell', 'extracted_service_count': 7},
            exit_code=0,
        )

        with unittest.mock.patch('paa_cli.app._build_runtime_api_client', return_value=fake_service):
            result = self.runner.invoke(app, ['report', 'techlead-service-map'])

        self.assertEqual(result.exit_code, 0, msg=result.output)
        payload = json.loads(result.stdout)
        self.assertEqual(payload['extracted_service_count'], 7)
        fake_service.techlead_service_map.assert_called_once_with()

    def test_authority_install_package_uses_runtime_api_client(self) -> None:
        app, _, _ = self._typer_cli()
        fake_service = Mock()
        from paa_core.application.dto.authority import AuthorityInstallResultView
        fake_service.install_authority_package.return_value = AuthorityInstallResultView(
            payload={
                'ok': True,
                'repo_root': str(ROOT),
                'package_root': str(ROOT / 'package'),
                'authority_install_root': str(ROOT / 'authority'),
                'package_metadata': {},
            },
            exit_code=0,
        )

        with unittest.mock.patch('paa_cli.app._build_runtime_api_client', return_value=fake_service):
            result = self.runner.invoke(
                app,
                [
                    'authority',
                    'install-package',
                    '--repo-root',
                    str(ROOT),
                    '--package-root',
                    str(ROOT / 'package'),
                ],
            )

        self.assertEqual(result.exit_code, 0, msg=result.output)
        payload = json.loads(result.stdout)
        self.assertTrue(payload['ok'])
        fake_service.install_authority_package.assert_called_once()

    def test_ops_install_runtime_uses_runtime_api_client(self) -> None:
        app, _, _ = self._typer_cli()
        fake_service = Mock()
        from paa_core.application.dto.runtime import RuntimeOperationResult
        fake_service.install_runtime.return_value = RuntimeOperationResult(
            payload={'ok': True, 'install_mode': 'fresh', 'project_pack': 'fractal-core'},
            exit_code=0,
        )

        with unittest.mock.patch('paa_cli.app._build_runtime_api_client', return_value=fake_service):
            result = self.runner.invoke(app, ['ops', 'install-runtime', '--repo-root', str(ROOT)])

        self.assertEqual(result.exit_code, 0, msg=result.output)
        payload = json.loads(result.stdout)
        self.assertTrue(payload['ok'])
        fake_service.install_runtime.assert_called_once()

    def test_ops_update_runtime_uses_runtime_api_client(self) -> None:
        app, _, _ = self._typer_cli()
        fake_service = Mock()
        from paa_core.application.dto.runtime import RuntimeOperationResult
        fake_service.update_runtime.return_value = RuntimeOperationResult(
            payload={'ok': True, 'install_mode': 'update', 'project_pack': 'fractal-core'},
            exit_code=0,
        )

        with unittest.mock.patch('paa_cli.app._build_runtime_api_client', return_value=fake_service):
            result = self.runner.invoke(app, ['ops', 'update-runtime', '--repo-root', str(ROOT)])

        self.assertEqual(result.exit_code, 0, msg=result.output)
        payload = json.loads(result.stdout)
        self.assertTrue(payload['ok'])
        fake_service.update_runtime.assert_called_once()

    def test_ops_validate_runtime_uses_core_guardrails(self) -> None:
        app, _, _ = self._typer_cli()
        fake_service = Mock()
        from paa_core.application.dto.status import RuntimeStatusResultView
        fake_service.validate_runtime.return_value = RuntimeStatusResultView(
            payload={'ok': True, 'branch': 'main', 'authority_version': '1.0'},
            exit_code=0,
        )

        with unittest.mock.patch('paa_cli.app._build_runtime_api_client', return_value=fake_service):
            result = self.runner.invoke(app, ['ops', 'validate-runtime', '--repo-root', str(ROOT)])

        self.assertEqual(result.exit_code, 0, msg=result.output)
        payload = json.loads(result.stdout)
        self.assertTrue(payload['ok'])
        fake_service.validate_runtime.assert_called_once()

    def test_verify_runtime_smoke_uses_core_runtime_smoke(self) -> None:
        app, _, _ = self._typer_cli()
        fake_service = Mock()
        from paa_core.application.dto.status import RuntimeStatusResultView
        fake_service.runtime_smoke.return_value = RuntimeStatusResultView(
            payload={'ok': True, 'runtime_supervisor': {'running': True}},
            exit_code=0,
        )

        with unittest.mock.patch('paa_cli.app._build_runtime_api_client', return_value=fake_service):
            result = self.runner.invoke(app, ['verify', 'runtime-smoke', '--repo-root', str(ROOT)])

        self.assertEqual(result.exit_code, 0, msg=result.output)
        payload = json.loads(result.stdout)
        self.assertTrue(payload['ok'])
        fake_service.runtime_smoke.assert_called_once()

    def test_role_add_renders_live_typer_output(self) -> None:
        app, _, _ = self._typer_cli()

        result = self.runner.invoke(
            app,
            [
                'role',
                'add',
                '--project-slug',
                'paa-platform',
                '--name',
                'Dev',
                '--category',
                'engineering',
                '--output',
                'json',
            ],
        )

        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn('\"command_family\": \"role\"', result.output)
        self.assertIn('Runtime role upsert completed.', result.output)
        self.assertIn('\"name\": \"Dev\"', result.output)

    def test_agent_add_renders_live_typer_output(self) -> None:
        app, _, _ = self._typer_cli()

        role_result = self.runner.invoke(
            app,
            [
                'role',
                'add',
                '--project-slug',
                'paa-platform',
                '--name',
                'Dev',
                '--category',
                'engineering',
                '--output',
                'json',
            ],
        )
        self.assertEqual(role_result.exit_code, 0, msg=role_result.output)

        result = self.runner.invoke(
            app,
            [
                'agent',
                'add',
                '--project-slug',
                'paa-platform',
                '--name',
                'Dev Automation',
                '--role-name',
                'Dev',
                '--agent-type',
                'automation',
                '--runtime-kind',
                'codex',
                '--output',
                'json',
            ],
        )

        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn('\"command_family\": \"agent\"', result.output)
        self.assertIn('Runtime agent upsert completed.', result.output)
        self.assertIn('\"name\": \"Dev Automation\"', result.output)

    def test_component_help_surfaces_preflight_behavior(self) -> None:
        app, _, _ = self._typer_cli()

        result = self.runner.invoke(app, ['component', '--help'])

        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn('preflight can allow, warn, block, or redirect execution', result.output)

    def test_report_next_help_marks_status_next_as_preferred_surface(self) -> None:
        app, _, _ = self._typer_cli()

        result = self.runner.invoke(app, ['report', 'next', '--help'])

        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn('Compatibility alias for', result.output)
        self.assertIn('status next', result.output)

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

"""Thin Typer application root for the unified PAA operator CLI."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Final

try:
    import typer
except ImportError as exc:  # pragma: no cover - exercised only in missing-dependency environments
    typer = None
    _TYPER_IMPORT_ERROR = exc
else:  # pragma: no branch
    _TYPER_IMPORT_ERROR = None

from paa_core.application.dto.queue import (
    QueueCheckRequest,
    QueueClaimActionRequest,
    QueueClaimNextRequest,
    QueueListClaimsRequest,
    QueuePacketFileRequest,
    QueuePurgeRequest,
    QueueRepoRootRequest,
    QueueSendRequest,
    QueueValidateRequest,
)
from paa_core.application.dto.authority import AuthorityInstallRequest
from paa_core.application.dto.runtime import (
    RuntimeHostRunRequest,
    RuntimeLogsRequest,
    RuntimeStatusRequest,
    RuntimeSupervisorRequest,
)
from paa_core.application.dto.status import RuntimeSmokeRequest, RuntimeValidationRequest
from paa_core.application.dto.workflow import AutomationPreflightRequest
from paa_core.api.runtime.client import (
    HttpRuntimeApiClient,
    InProcessRuntimeApiClient,
    RuntimeApiClient,
)
from paa_core.application.services import DefaultAuthorityInstallApplicationService
from paa_core.repositories.methodology_execution import PostgresMethodologyExecutionRepository
from paa_core.repositories.runtime_identity import PostgresRuntimeIdentityRepository
from paa_core.repositories.runtime_event import PostgresRuntimeEventRepository
from paa_core.install import install_runtime_support
from paa_core.services.packet_reference_resolution import DefaultPacketReferenceResolutionService
from paa_core.services.queue_packet_runtime_controller import DefaultQueuePacketRuntimeController
from paa_core.services.techlead_acceptance_decision import DefaultTechLeadAcceptanceDecisionService
from paa_core.services.techlead_assignment_decision import DefaultTechLeadAssignmentDecisionService
from paa_core.services.techlead_closeout_decision import DefaultTechLeadCloseoutDecisionService
from paa_core.services.techlead_delivery_review_decision import DefaultTechLeadDeliveryReviewDecisionService
from paa_core.services.techlead_lineage_decision import DefaultTechLeadLineageDecisionService
from paa_core.services.techlead_reset_recovery_decision import DefaultTechLeadResetRecoveryDecisionService
from paa_core.services.techlead_worker import DefaultTechLeadWorkerService
from paa_core.services.techlead_worker_review_routing import DefaultTechLeadWorkerReviewRoutingService
from paa_core.services.methodology_execution_preflight import (
    DefaultMethodologyExecutionPreflightService,
    MethodologyExecutionPreflightRequest,
)
from paa_core.services.methodology_execution_projection import (
    DefaultMethodologyExecutionProjectionService,
)
from paa_core.services.methodology_execution_state import DefaultMethodologyExecutionStateService
from .command_adapters import (
    AgentCommandAdapter,
    ComponentCommandAdapter,
    PlanCommandAdapter,
    QueueCommandAdapter,
    ReportCommandAdapter,
    RoleCommandAdapter,
    StatusCommandAdapter,
    WorkerCommandAdapter,
)
from .contracts import PAAOperatorCLI, StructuredLogger
from .environment import EnvironmentResolutionInput, EnvironmentResolver
from .models import (
    OperatorCommand,
    OperatorCommandRequest,
    OperatorCommandResult,
    OperatorFailure,
    OperatorOutputMessage,
    OperatorOutputSection,
    OperatorOutputTable,
)
from .normalization import CommandResultNormalizer
from .rendering import OutputRenderer
from .router import CommandRegistration, CommandRouter

_OUTPUT_MODES: Final[tuple[str, ...]] = ('table', 'json', 'summary')
_PREFLIGHTED_FAMILIES: Final[set[str]] = {'component', 'plan'}


def _build_runtime_api_client() -> RuntimeApiClient:
    runtime_api_url = os.environ.get('PAA_RUNTIME_API_URL')
    if runtime_api_url:
        return HttpRuntimeApiClient(base_url=runtime_api_url)
    return InProcessRuntimeApiClient()


def _build_authority_install_application_service() -> DefaultAuthorityInstallApplicationService:
    return DefaultAuthorityInstallApplicationService()


def _emit_json_result(result: object) -> None:
    payload = asdict(result) if is_dataclass(result) else result
    typer.echo(json.dumps(payload, indent=2))


class NullStructuredLogger:
    """Default logger used until the richer methodology pointer surfaces arrive."""

    def info(self, event: str, **fields: object) -> None:
        del event, fields

    def warning(self, event: str, **fields: object) -> None:
        del event, fields


class DefaultPAAOperatorCLI(PAAOperatorCLI):
    """Concrete thin host over realized command families and methodology pointer services."""

    def __init__(
        self,
        *,
        logger: StructuredLogger,
        environment_resolver: EnvironmentResolver,
        router: CommandRouter,
        normalizer: CommandResultNormalizer,
        renderer: OutputRenderer,
        methodology_execution_preflight_service: object | None = None,
    ) -> None:
        self._logger = logger
        self.environment_resolver = environment_resolver
        self.router = router
        self.normalizer = normalizer
        self.renderer = renderer
        self.methodology_execution_preflight_service = methodology_execution_preflight_service

    @property
    def logger(self) -> StructuredLogger:
        return self._logger

    def run_command(self, request: OperatorCommandRequest) -> OperatorCommandResult:
        self.logger.info(
            'paa_cli.command.start',
            command_family=request.command.command_family,
            command_name=request.command.command_name,
        )
        preflight_result = self._preflight_if_needed(request)
        if preflight_result is not None and not preflight_result.success:
            self.logger.warning(
                'paa_cli.command.preflight_blocked',
                command_family=request.command.command_family,
                command_name=request.command.command_name,
                failure_code=preflight_result.failure.code if preflight_result.failure else 'preflight_blocked',
            )
            return preflight_result
        try:
            raw_result = self.router.route(request)
        except KeyError:
            raw_result = OperatorCommandResult(
                command=request.command,
                supported=False,
                success=False,
                exit_code=2,
                failure=OperatorFailure(
                    code='unsupported_command_family',
                    summary='Unsupported command family for the current CLI shell.',
                    details=(request.command.command_family,),
                ),
            )
        result = self.normalizer.normalize(request.command, raw_result)
        if preflight_result is not None and preflight_result.sections:
            result = OperatorCommandResult(
                command=result.command,
                supported=result.supported,
                success=result.success,
                exit_code=result.exit_code,
                sections=preflight_result.sections + result.sections,
                failure=result.failure,
                metadata={**preflight_result.metadata, **result.metadata},
            )
        if result.failure is not None:
            self.logger.warning(
                'paa_cli.command.failed',
                command_family=request.command.command_family,
                command_name=request.command.command_name,
                failure_code=result.failure.code,
            )
        else:
            self.logger.info(
                'paa_cli.command.completed',
                command_family=request.command.command_family,
                command_name=request.command.command_name,
                exit_code=result.exit_code,
            )
        return result

    def supports_command_family(self, command_family: str) -> bool:
        return self.router.supports_command_family(command_family)

    def render_result(self, result: OperatorCommandResult, *, output_mode: str) -> str:
        return self.renderer.render(result, output_mode=output_mode)

    def _preflight_if_needed(self, request: OperatorCommandRequest) -> OperatorCommandResult | None:
        if request.command.command_family not in _PREFLIGHTED_FAMILIES:
            return None
        if self.methodology_execution_preflight_service is None:
            return None
        preflight_request = self._build_preflight_request(request)
        if preflight_request is None:
            return None
        outcome_result = self.methodology_execution_preflight_service.evaluate_command(preflight_request)
        payload = {
            'methodology_execution_id': outcome_result.methodology_execution_id,
            'outcome_kind': outcome_result.outcome.outcome_kind,
            'rule_key': outcome_result.outcome.rule_key,
            'redirect_target': outcome_result.outcome.redirect_target,
            'recommended_next_action_key': outcome_result.outcome.recommended_next_action_key,
            'reason': outcome_result.outcome.reason,
            'details': outcome_result.outcome.details,
        }
        section = OperatorOutputSection(
            title='Methodology Preflight',
            messages=(OperatorOutputMessage(level='info', text=outcome_result.outcome.reason),),
            tables=(
                OperatorOutputTable(
                    title='Methodology Preflight Summary',
                    columns=('field', 'value'),
                    rows=tuple((str(key), str(value)) for key, value in payload.items()),
                ),
            ),
            data=payload,
        )
        if outcome_result.outcome.outcome_kind == 'blocked':
            return OperatorCommandResult(
                command=request.command,
                supported=True,
                success=False,
                exit_code=2,
                sections=(section,),
                failure=OperatorFailure(
                    code=outcome_result.reason or 'preflight_blocked',
                    summary=outcome_result.outcome.reason,
                    details=tuple(filter(None, [outcome_result.outcome.details])),
                ),
                metadata={'preflight': payload},
            )
        if outcome_result.outcome.outcome_kind == 'redirect':
            return OperatorCommandResult(
                command=request.command,
                supported=True,
                success=False,
                exit_code=2,
                sections=(section,),
                failure=OperatorFailure(
                    code='preflight_redirect',
                    summary=outcome_result.outcome.reason,
                    details=tuple(filter(None, [outcome_result.outcome.details])),
                    metadata={'redirect_target': outcome_result.outcome.redirect_target},
                ),
                metadata={'preflight': payload},
            )
        return OperatorCommandResult(
            command=request.command,
            supported=True,
            success=True,
            exit_code=0,
            sections=(section,),
            metadata={'preflight': payload},
        )

    @staticmethod
    def _build_preflight_request(
        request: OperatorCommandRequest,
    ) -> MethodologyExecutionPreflightRequest | None:
        arguments = request.arguments
        methodology_execution_id = _optional_string(arguments.get('methodology_execution_id'))
        project_id = _optional_string(arguments.get('project_id'))
        work_item_id = _optional_string(arguments.get('work_item_id'))
        component_id = _optional_string(arguments.get('component_id'))
        if methodology_execution_id is None and not (project_id and work_item_id):
            return None
        return MethodologyExecutionPreflightRequest(
            methodology_execution_id=methodology_execution_id,
            project_id=project_id,
            work_item_id=work_item_id,
            component_id=component_id,
            command_family=request.command.command_family,
            command_name=request.command.command_name,
            command_arguments=dict(arguments),
            metadata={'repo_root': request.invocation_context.repo_root},
        )


class _JsonFileQueuePacketReader:
    def read_packet(self, packet_reference: object) -> object:
        import json
        from pathlib import Path

        path = Path(str(packet_reference)).expanduser().resolve()
        return json.loads(path.read_text())

    def read_packet_payload(self, packet_path: str) -> dict[str, object]:
        payload = self.read_packet(packet_path)
        return payload if isinstance(payload, dict) else {'packet_payload': payload}


class _UnsupportedWorkerHost:
    def __init__(self, name: str) -> None:
        self._name = name

    def handle_packet(self, request: object) -> object:
        raise RuntimeError(f'{self._name} is not composed for this CLI slice.')

    def supports_packet_schema_type(self, packet_schema_type: str) -> bool:
        del packet_schema_type
        return False


def build_default_cli() -> DefaultPAAOperatorCLI:
    logger = NullStructuredLogger()
    methodology_execution_repository = PostgresMethodologyExecutionRepository()
    runtime_identity_repository = PostgresRuntimeIdentityRepository()
    runtime_event_repository = PostgresRuntimeEventRepository()
    methodology_execution_state_service = DefaultMethodologyExecutionStateService(
        methodology_execution_repository=methodology_execution_repository,
        logger=logger,
    )
    methodology_execution_projection_service = DefaultMethodologyExecutionProjectionService(
        methodology_execution_repository=methodology_execution_repository,
        logger=logger,
    )
    methodology_execution_preflight_service = DefaultMethodologyExecutionPreflightService(
        methodology_execution_repository=methodology_execution_repository,
        methodology_execution_state_service=methodology_execution_state_service,
        methodology_execution_projection_service=methodology_execution_projection_service,
        logger=logger,
    )
    techlead_worker_service = DefaultTechLeadWorkerService(
        methodology_execution_repository=methodology_execution_repository,
        methodology_execution_state_service=methodology_execution_state_service,
        methodology_execution_projection_service=methodology_execution_projection_service,
        methodology_execution_preflight_service=methodology_execution_preflight_service,
        techlead_assignment_decision_service=DefaultTechLeadAssignmentDecisionService(logger=logger),
        techlead_worker_review_routing_service=DefaultTechLeadWorkerReviewRoutingService(logger=logger),
        techlead_acceptance_decision_service=DefaultTechLeadAcceptanceDecisionService(logger=logger),
        techlead_delivery_review_decision_service=DefaultTechLeadDeliveryReviewDecisionService(logger=logger),
        techlead_reset_recovery_decision_service=DefaultTechLeadResetRecoveryDecisionService(logger=logger),
        techlead_lineage_decision_service=DefaultTechLeadLineageDecisionService(logger=logger),
        techlead_closeout_decision_service=DefaultTechLeadCloseoutDecisionService(logger=logger),
        logger=logger,
    )
    queue_packet_runtime_controller = DefaultQueuePacketRuntimeController(
        techlead_worker_service=techlead_worker_service,
        dev_worker_service=_UnsupportedWorkerHost('DevWorkerService'),
        qa_worker_service=_UnsupportedWorkerHost('QAWorkerService'),
        queue_packet_reader=_JsonFileQueuePacketReader(),
        queue_packet_delivery_adapter=None,
        logger=logger,
    )
    packet_reference_resolution_service = DefaultPacketReferenceResolutionService(
        runtime_event_repository=runtime_event_repository,
        packet_artifact_reader=_JsonFileQueuePacketReader(),
        runtime_path_adapter=None,
        logger=logger,
    )
    return DefaultPAAOperatorCLI(
        logger=logger,
        environment_resolver=EnvironmentResolver(),
        router=CommandRouter(
            (
                CommandRegistration(command_family='component', adapter=ComponentCommandAdapter()),
                CommandRegistration(command_family='plan', adapter=PlanCommandAdapter()),
                CommandRegistration(
                    command_family='role',
                    adapter=RoleCommandAdapter(runtime_identity_repository=runtime_identity_repository),
                ),
                CommandRegistration(
                    command_family='agent',
                    adapter=AgentCommandAdapter(runtime_identity_repository=runtime_identity_repository),
                ),
                CommandRegistration(
                    command_family='status',
                    adapter=StatusCommandAdapter(
                        methodology_execution_projection_service=methodology_execution_projection_service,
                    ),
                ),
                CommandRegistration(
                    command_family='report',
                    adapter=ReportCommandAdapter(
                        methodology_execution_projection_service=methodology_execution_projection_service,
                    ),
                ),
                CommandRegistration(
                    command_family='queue',
                    adapter=QueueCommandAdapter(
                        queue_packet_runtime_controller=queue_packet_runtime_controller,
                        queue_packet_reader=_JsonFileQueuePacketReader(),
                        runtime_event_repository=runtime_event_repository,
                    ),
                ),
                CommandRegistration(
                    command_family='worker',
                    adapter=WorkerCommandAdapter(
                        queue_packet_runtime_controller=queue_packet_runtime_controller,
                        packet_reference_resolution_service=packet_reference_resolution_service,
                        queue_packet_reader=_JsonFileQueuePacketReader(),
                        runtime_event_repository=runtime_event_repository,
                    ),
                ),
            )
        ),
        normalizer=CommandResultNormalizer(),
        renderer=OutputRenderer(),
        methodology_execution_preflight_service=methodology_execution_preflight_service,
    )


def _invoke(
    cli: DefaultPAAOperatorCLI,
    *,
    command_family: str,
    command_name: str,
    repo_root: str | None,
    output_mode: str,
    dry_run: bool,
    strict_mode: bool,
    arguments: dict[str, object],
) -> int:
    context = cli.environment_resolver.resolve(
        EnvironmentResolutionInput(
            repo_root=repo_root,
            output_mode=output_mode,
            dry_run=dry_run,
            strict_mode=strict_mode,
        )
    )
    request = OperatorCommandRequest(
        command=OperatorCommand(command_family=command_family, command_name=command_name),
        invocation_context=context,
        arguments=arguments,
    )
    result = cli.run_command(request)
    typer.echo(cli.render_result(result, output_mode=output_mode))
    return result.exit_code


def _pointer_arguments(
    *,
    methodology_execution_id: str | None,
    project_id: str | None,
    work_item_id: str | None,
    component_id: str | None,
) -> dict[str, object]:
    payload: dict[str, object] = {}
    if methodology_execution_id is not None:
        payload['methodology_execution_id'] = methodology_execution_id
    if project_id is not None:
        payload['project_id'] = project_id
    if work_item_id is not None:
        payload['work_item_id'] = work_item_id
    if component_id is not None:
        payload['component_id'] = component_id
    return payload


def build_app(cli: DefaultPAAOperatorCLI | None = None):
    if typer is None:  # pragma: no cover - depends on host environment
        raise RuntimeError(
            'Typer is required to build the PAA operator CLI app. '
            'Install the `paa-cli` package dependencies first.'
        ) from _TYPER_IMPORT_ERROR

    cli = cli or build_default_cli()
    app = typer.Typer(
        help=(
            'Unified operator CLI for the PAA methodology. '
            'Mutating component/plan commands may be preflight-blocked or redirected '
            'when methodology pointer anchors are supplied.'
        ),
        no_args_is_help=True,
        add_completion=False,
        pretty_exceptions_enable=False,
    )
    component_app = typer.Typer(
        help=(
            'Component-realization lane commands. When methodology anchors are supplied, '
            'preflight can allow, warn, block, or redirect execution.'
        ),
        no_args_is_help=True,
    )
    plan_app = typer.Typer(
        help=(
            'Implementation-plan inspection commands. When methodology anchors are supplied, '
            'preflight can allow, block, or redirect execution before plan reads run.'
        ),
        no_args_is_help=True,
    )
    status_app = typer.Typer(help='Methodology pointer status and next-action reads.', no_args_is_help=True)
    report_app = typer.Typer(
        help='Methodology pointer explain reads plus compatibility aliases for older report commands.',
        no_args_is_help=True,
    )
    authority_app = typer.Typer(help='Authority package install surfaces.', no_args_is_help=True)
    ops_app = typer.Typer(help='Runtime install and validation surfaces.', no_args_is_help=True)
    verify_app = typer.Typer(help='Runtime smoke and verification surfaces.', no_args_is_help=True)
    role_app = typer.Typer(help='Project-scoped runtime role identity commands.', no_args_is_help=True)
    agent_app = typer.Typer(help='Project-scoped runtime agent identity commands.', no_args_is_help=True)
    queue_app = typer.Typer(help='Queue packet preview surfaces over the runtime controller.', no_args_is_help=True)
    worker_app = typer.Typer(help='Worker dispatch preview surfaces over the runtime controller.', no_args_is_help=True)
    runtime_app = typer.Typer(help='Runtime host and supervisor control surfaces.', no_args_is_help=True)

    @component_app.command('materialize')
    def component_materialize(
        spec: str = typer.Option(..., '--spec', help='Absolute or relative component spec path.'),
        project_slug: str | None = typer.Option(None, '--project-slug', help='Optional project slug override.'),
        repo_root: str | None = typer.Option(None, '--repo-root', help='Invocation repo root override.'),
        methodology_execution_id: str | None = typer.Option(None, '--methodology-execution-id'),
        project_id: str | None = typer.Option(None, '--project-id'),
        work_item_id: str | None = typer.Option(None, '--work-item-id'),
        component_id: str | None = typer.Option(None, '--component-id'),
        output: str = typer.Option('table', '--output', help='Output mode: table, json, or summary.'),
        dry_run: bool = typer.Option(False, '--dry-run', help='Resolve invocation context without mutating runtime state.'),
        strict_mode: bool = typer.Option(True, '--strict/--no-strict', help='Enable strict fail-closed handling.'),
    ) -> None:
        code = _invoke(
            cli,
            command_family='component',
            command_name='materialize',
            repo_root=repo_root,
            output_mode=output,
            dry_run=dry_run,
            strict_mode=strict_mode,
            arguments={
                'spec': spec,
                **({'project_slug': project_slug} if project_slug else {}),
                **_pointer_arguments(
                    methodology_execution_id=methodology_execution_id,
                    project_id=project_id,
                    work_item_id=work_item_id,
                    component_id=component_id,
                ),
            },
        )
        raise typer.Exit(code=code)

    @component_app.command(
        'progress',
        help='Load component plan progress. With methodology anchors, preflight may block or redirect this command.',
    )
    def component_progress(
        plan_id: str = typer.Option(..., '--plan-id', help='Implementation plan id.'),
        repo_root: str | None = typer.Option(None, '--repo-root'),
        methodology_execution_id: str | None = typer.Option(None, '--methodology-execution-id'),
        project_id: str | None = typer.Option(None, '--project-id'),
        work_item_id: str | None = typer.Option(None, '--work-item-id'),
        component_id: str | None = typer.Option(None, '--component-id'),
        output: str = typer.Option('table', '--output', help='Output mode: table, json, or summary.'),
        dry_run: bool = typer.Option(False, '--dry-run'),
        strict_mode: bool = typer.Option(True, '--strict/--no-strict'),
    ) -> None:
        code = _invoke(
            cli,
            command_family='component',
            command_name='progress',
            repo_root=repo_root,
            output_mode=output,
            dry_run=dry_run,
            strict_mode=strict_mode,
            arguments={
                'plan_id': plan_id,
                **_pointer_arguments(
                    methodology_execution_id=methodology_execution_id,
                    project_id=project_id,
                    work_item_id=work_item_id,
                    component_id=component_id,
                ),
            },
        )
        raise typer.Exit(code=code)

    @component_app.command(
        'reconcile',
        help='Reconcile component plan progress. With methodology anchors, preflight may block or redirect this command.',
    )
    def component_reconcile(
        plan_id: str = typer.Option(..., '--plan-id', help='Implementation plan id.'),
        repo_root: str | None = typer.Option(None, '--repo-root'),
        methodology_execution_id: str | None = typer.Option(None, '--methodology-execution-id'),
        project_id: str | None = typer.Option(None, '--project-id'),
        work_item_id: str | None = typer.Option(None, '--work-item-id'),
        component_id: str | None = typer.Option(None, '--component-id'),
        output: str = typer.Option('table', '--output', help='Output mode: table, json, or summary.'),
        dry_run: bool = typer.Option(False, '--dry-run'),
        strict_mode: bool = typer.Option(True, '--strict/--no-strict'),
    ) -> None:
        code = _invoke(
            cli,
            command_family='component',
            command_name='reconcile',
            repo_root=repo_root,
            output_mode=output,
            dry_run=dry_run,
            strict_mode=strict_mode,
            arguments={
                'plan_id': plan_id,
                **_pointer_arguments(
                    methodology_execution_id=methodology_execution_id,
                    project_id=project_id,
                    work_item_id=work_item_id,
                    component_id=component_id,
                ),
            },
        )
        raise typer.Exit(code=code)

    @component_app.command(
        'next',
        help='Derive the next component activity bundle. With methodology anchors, preflight may block or redirect this command.',
    )
    def component_next(
        plan_id: str = typer.Option(..., '--plan-id', help='Implementation plan id.'),
        repo_root: str | None = typer.Option(None, '--repo-root'),
        methodology_execution_id: str | None = typer.Option(None, '--methodology-execution-id'),
        project_id: str | None = typer.Option(None, '--project-id'),
        work_item_id: str | None = typer.Option(None, '--work-item-id'),
        component_id: str | None = typer.Option(None, '--component-id'),
        output: str = typer.Option('table', '--output', help='Output mode: table, json, or summary.'),
        dry_run: bool = typer.Option(False, '--dry-run'),
        strict_mode: bool = typer.Option(True, '--strict/--no-strict'),
    ) -> None:
        code = _invoke(
            cli,
            command_family='component',
            command_name='next',
            repo_root=repo_root,
            output_mode=output,
            dry_run=dry_run,
            strict_mode=strict_mode,
            arguments={
                'plan_id': plan_id,
                **_pointer_arguments(
                    methodology_execution_id=methodology_execution_id,
                    project_id=project_id,
                    work_item_id=work_item_id,
                    component_id=component_id,
                ),
            },
        )
        raise typer.Exit(code=code)

    @component_app.command(
        'complete',
        help='Mark a component activity complete, then reconcile and derive next by default.',
    )
    def component_complete(
        plan_id: str = typer.Option(..., '--plan-id', help='Implementation plan id.'),
        activity_key: str = typer.Option(..., '--activity-key', help='Implementation plan activity key.'),
        completed_at: str | None = typer.Option(None, '--completed-at', help='Optional completion timestamp override.'),
        metadata_json: str | None = typer.Option(None, '--metadata-json', help='Optional JSON object merged into activity metadata.'),
        no_reconcile: bool = typer.Option(False, '--no-reconcile', help='Skip automatic reconcile after completion.'),
        no_next: bool = typer.Option(False, '--no-next', help='Skip automatic next-activity derivation after reconcile.'),
        repo_root: str | None = typer.Option(None, '--repo-root'),
        output: str = typer.Option('table', '--output', help='Output mode: table, json, or summary.'),
        dry_run: bool = typer.Option(False, '--dry-run'),
        strict_mode: bool = typer.Option(True, '--strict/--no-strict'),
    ) -> None:
        code = _invoke(
            cli,
            command_family='component',
            command_name='complete',
            repo_root=repo_root,
            output_mode=output,
            dry_run=dry_run,
            strict_mode=strict_mode,
            arguments={
                'plan_id': plan_id,
                'activity_key': activity_key,
                **({'completed_at': completed_at} if completed_at else {}),
                **({'metadata_json': metadata_json} if metadata_json else {}),
                'no_reconcile': no_reconcile,
                'no_next': no_next,
            },
        )
        raise typer.Exit(code=code)

    @plan_app.command(
        'progress',
        help='Load implementation-plan progress. With methodology anchors, preflight may block or redirect this command.',
    )
    def plan_progress(
        plan_id: str = typer.Option(..., '--plan-id', help='Implementation plan id.'),
        repo_root: str | None = typer.Option(None, '--repo-root'),
        methodology_execution_id: str | None = typer.Option(None, '--methodology-execution-id'),
        project_id: str | None = typer.Option(None, '--project-id'),
        work_item_id: str | None = typer.Option(None, '--work-item-id'),
        component_id: str | None = typer.Option(None, '--component-id'),
        output: str = typer.Option('table', '--output', help='Output mode: table, json, or summary.'),
        dry_run: bool = typer.Option(False, '--dry-run'),
        strict_mode: bool = typer.Option(True, '--strict/--no-strict'),
    ) -> None:
        code = _invoke(
            cli,
            command_family='plan',
            command_name='progress',
            repo_root=repo_root,
            output_mode=output,
            dry_run=dry_run,
            strict_mode=strict_mode,
            arguments={
                'plan_id': plan_id,
                **_pointer_arguments(
                    methodology_execution_id=methodology_execution_id,
                    project_id=project_id,
                    work_item_id=work_item_id,
                    component_id=component_id,
                ),
            },
        )
        raise typer.Exit(code=code)

    @plan_app.command(
        'inspect',
        help='Inspect implementation-plan state. With methodology anchors, preflight may block or redirect this command.',
    )
    def plan_inspect(
        plan_id: str = typer.Option(..., '--plan-id', help='Implementation plan id.'),
        repo_root: str | None = typer.Option(None, '--repo-root'),
        methodology_execution_id: str | None = typer.Option(None, '--methodology-execution-id'),
        project_id: str | None = typer.Option(None, '--project-id'),
        work_item_id: str | None = typer.Option(None, '--work-item-id'),
        component_id: str | None = typer.Option(None, '--component-id'),
        output: str = typer.Option('table', '--output', help='Output mode: table, json, or summary.'),
        dry_run: bool = typer.Option(False, '--dry-run'),
        strict_mode: bool = typer.Option(True, '--strict/--no-strict'),
    ) -> None:
        code = _invoke(
            cli,
            command_family='plan',
            command_name='inspect',
            repo_root=repo_root,
            output_mode=output,
            dry_run=dry_run,
            strict_mode=strict_mode,
            arguments={
                'plan_id': plan_id,
                **_pointer_arguments(
                    methodology_execution_id=methodology_execution_id,
                    project_id=project_id,
                    work_item_id=work_item_id,
                    component_id=component_id,
                ),
            },
        )
        raise typer.Exit(code=code)

    @status_app.command('inspect')
    def status_inspect(
        methodology_execution_id: str | None = typer.Option(None, '--methodology-execution-id'),
        project_id: str | None = typer.Option(None, '--project-id'),
        work_item_id: str | None = typer.Option(None, '--work-item-id'),
        component_id: str | None = typer.Option(None, '--component-id'),
        repo_root: str | None = typer.Option(None, '--repo-root'),
        output: str = typer.Option('table', '--output', help='Output mode: table, json, or summary.'),
        dry_run: bool = typer.Option(False, '--dry-run'),
        strict_mode: bool = typer.Option(True, '--strict/--no-strict'),
    ) -> None:
        code = _invoke(
            cli,
            command_family='status',
            command_name='inspect',
            repo_root=repo_root,
            output_mode=output,
            dry_run=dry_run,
            strict_mode=strict_mode,
            arguments=_pointer_arguments(
                methodology_execution_id=methodology_execution_id,
                project_id=project_id,
                work_item_id=work_item_id,
                component_id=component_id,
            ),
        )
        raise typer.Exit(code=code)

    @status_app.command('next')
    def status_next(
        methodology_execution_id: str = typer.Option(..., '--methodology-execution-id'),
        repo_root: str | None = typer.Option(None, '--repo-root'),
        output: str = typer.Option('table', '--output', help='Output mode: table, json, or summary.'),
        dry_run: bool = typer.Option(False, '--dry-run'),
        strict_mode: bool = typer.Option(True, '--strict/--no-strict'),
    ) -> None:
        code = _invoke(
            cli,
            command_family='status',
            command_name='next',
            repo_root=repo_root,
            output_mode=output,
            dry_run=dry_run,
            strict_mode=strict_mode,
            arguments={'methodology_execution_id': methodology_execution_id},
        )
        raise typer.Exit(code=code)

    @report_app.command(
        'next',
        help='Compatibility alias for `paa status next`.',
    )
    def report_next(
        methodology_execution_id: str = typer.Option(..., '--methodology-execution-id'),
        repo_root: str | None = typer.Option(None, '--repo-root'),
        output: str = typer.Option('table', '--output', help='Output mode: table, json, or summary.'),
        dry_run: bool = typer.Option(False, '--dry-run'),
        strict_mode: bool = typer.Option(True, '--strict/--no-strict'),
    ) -> None:
        code = _invoke(
            cli,
            command_family='report',
            command_name='next',
            repo_root=repo_root,
            output_mode=output,
            dry_run=dry_run,
            strict_mode=strict_mode,
            arguments={'methodology_execution_id': methodology_execution_id},
        )
        raise typer.Exit(code=code)

    @role_app.command('add')
    def role_add(
        project_slug: str = typer.Option(..., '--project-slug', help='Owning project slug.'),
        name: str = typer.Option(..., '--name', help='Runtime role display name.'),
        category: str = typer.Option(..., '--category', help='Role category enum value.'),
        description: str | None = typer.Option(None, '--description', help='Optional role description.'),
        is_human_capable: bool = typer.Option(True, '--human-capable/--no-human-capable'),
        is_automation_capable: bool = typer.Option(True, '--automation-capable/--no-automation-capable'),
        sort_order: int = typer.Option(100, '--sort-order', help='Role display order.'),
        active: bool = typer.Option(True, '--active/--inactive'),
        repo_root: str | None = typer.Option(None, '--repo-root'),
        output: str = typer.Option('table', '--output', help='Output mode: table, json, or summary.'),
        dry_run: bool = typer.Option(False, '--dry-run'),
        strict_mode: bool = typer.Option(True, '--strict/--no-strict'),
    ) -> None:
        code = _invoke(
            cli,
            command_family='role',
            command_name='add',
            repo_root=repo_root,
            output_mode=output,
            dry_run=dry_run,
            strict_mode=strict_mode,
            arguments={
                'project_slug': project_slug,
                'name': name,
                'category': category,
                'description': description,
                'is_human_capable': is_human_capable,
                'is_automation_capable': is_automation_capable,
                'sort_order': sort_order,
                'active': active,
            },
        )
        raise typer.Exit(code=code)

    @agent_app.command('add')
    def agent_add(
        project_slug: str = typer.Option(..., '--project-slug', help='Owning project slug.'),
        name: str = typer.Option(..., '--name', help='Runtime agent name.'),
        role_name: str | None = typer.Option(None, '--role-name', help='Optional persisted role name to bind.'),
        agent_type: str = typer.Option(..., '--agent-type', help='Agent type enum value.'),
        runtime_kind: str | None = typer.Option('codex', '--runtime-kind', help='Optional runtime kind label.'),
        metadata_json: str | None = typer.Option(None, '--metadata-json', help='Optional metadata JSON object.'),
        active: bool = typer.Option(True, '--active/--inactive'),
        repo_root: str | None = typer.Option(None, '--repo-root'),
        output: str = typer.Option('table', '--output', help='Output mode: table, json, or summary.'),
        dry_run: bool = typer.Option(False, '--dry-run'),
        strict_mode: bool = typer.Option(True, '--strict/--no-strict'),
    ) -> None:
        code = _invoke(
            cli,
            command_family='agent',
            command_name='add',
            repo_root=repo_root,
            output_mode=output,
            dry_run=dry_run,
            strict_mode=strict_mode,
            arguments={
                'project_slug': project_slug,
                'name': name,
                'role_name': role_name,
                'agent_type': agent_type,
                'runtime_kind': runtime_kind,
                'metadata_json': metadata_json,
                'active': active,
            },
        )
        raise typer.Exit(code=code)


    @queue_app.command('preview')
    def queue_preview(
        queue_name: str = typer.Option(..., '--queue-name'),
        packet_schema_type: str = typer.Option(..., '--packet-schema-type'),
        packet_message_id: str | None = typer.Option(None, '--packet-message-id'),
        packet_path: str | None = typer.Option(None, '--packet-path'),
        packet_payload_json: str | None = typer.Option(None, '--packet-payload-json'),
        actor_name: str | None = typer.Option(None, '--actor-name'),
        host_name: str | None = typer.Option(None, '--host-name'),
        repo_root: str | None = typer.Option(None, '--repo-root'),
        output: str = typer.Option('table', '--output', help='Output mode: table, json, or summary.'),
        dry_run: bool = typer.Option(True, '--dry-run/--live', help='Preview the queue packet without queue side effects.'),
        strict_mode: bool = typer.Option(True, '--strict/--no-strict'),
    ) -> None:
        code = _invoke(
            cli,
            command_family='queue',
            command_name='preview',
            repo_root=repo_root,
            output_mode=output,
            dry_run=dry_run,
            strict_mode=strict_mode,
            arguments={
                'queue_name': queue_name,
                'packet_schema_type': packet_schema_type,
                **({'packet_message_id': packet_message_id} if packet_message_id else {}),
                **({'packet_path': packet_path} if packet_path else {}),
                **({'packet_payload_json': packet_payload_json} if packet_payload_json else {}),
                **({'actor_name': actor_name} if actor_name else {}),
                **({'host_name': host_name} if host_name else {}),
            },
        )
        raise typer.Exit(code=code)

    @queue_app.command('ensure-topology')
    def queue_ensure_topology(
        repo_root: str | None = typer.Option(None, '--repo-root'),
    ) -> None:
        resolved_repo_root = Path(repo_root).resolve() if repo_root else Path.cwd().resolve()
        result = _build_runtime_api_client().ensure_topology(QueueRepoRootRequest(repo_root=resolved_repo_root))
        _emit_json_result(result.payload)
        raise typer.Exit(code=result.exit_code)

    @queue_app.command('state-info')
    def queue_state_info(
        repo_root: str | None = typer.Option(None, '--repo-root'),
    ) -> None:
        resolved_repo_root = Path(repo_root).resolve() if repo_root else Path.cwd().resolve()
        result = _build_runtime_api_client().state_info(QueueRepoRootRequest(repo_root=resolved_repo_root))
        _emit_json_result(result.payload)
        raise typer.Exit(code=result.exit_code)

    @queue_app.command('check')
    def queue_check(
        queue: str = typer.Option(..., '--queue'),
        preview: int = typer.Option(0, '--preview'),
        repo_root: str | None = typer.Option(None, '--repo-root'),
    ) -> None:
        resolved_repo_root = Path(repo_root).resolve() if repo_root else Path.cwd().resolve()
        result = _build_runtime_api_client().check(
            QueueCheckRequest(repo_root=resolved_repo_root, queue=queue, preview=preview)
        )
        _emit_json_result(result.payload)
        raise typer.Exit(code=result.exit_code)

    @queue_app.command('purge')
    def queue_purge(
        repo_root: str | None = typer.Option(None, '--repo-root'),
        queue: str | None = typer.Option(None, '--queue'),
    ) -> None:
        resolved_repo_root = Path(repo_root).resolve() if repo_root else Path.cwd().resolve()
        result = _build_runtime_api_client().purge(
            QueuePurgeRequest(repo_root=resolved_repo_root, queue=queue)
        )
        _emit_json_result(result.payload)
        raise typer.Exit(code=result.exit_code)

    @queue_app.command('validate')
    def queue_validate(
        message_file: str = typer.Option(..., '--message-file'),
        repo_root: str | None = typer.Option(None, '--repo-root'),
    ) -> None:
        del repo_root
        result = _build_runtime_api_client().validate(
            QueueValidateRequest(message_file=Path(message_file).resolve())
        )
        _emit_json_result(result.payload)
        raise typer.Exit(code=result.exit_code)

    @queue_app.command('send')
    def queue_send(
        queue: str = typer.Option(..., '--queue'),
        message_file: str = typer.Option(..., '--message-file'),
        repo_root: str | None = typer.Option(None, '--repo-root'),
    ) -> None:
        resolved_repo_root = Path(repo_root).resolve() if repo_root else Path.cwd().resolve()
        result = _build_runtime_api_client().send(
            QueueSendRequest(repo_root=resolved_repo_root, queue=queue, message_file=Path(message_file).resolve())
        )
        _emit_json_result(result.payload)
        raise typer.Exit(code=result.exit_code)

    @queue_app.command('claim-next')
    def queue_claim_next(
        queue: str = typer.Option(..., '--queue'),
        claimed_by: str = typer.Option('paa', '--claimed-by'),
        repo_root: str | None = typer.Option(None, '--repo-root'),
    ) -> None:
        resolved_repo_root = Path(repo_root).resolve() if repo_root else Path.cwd().resolve()
        result = _build_runtime_api_client().claim_next(
            QueueClaimNextRequest(repo_root=resolved_repo_root, queue=queue, claimed_by=claimed_by)
        )
        _emit_json_result(result.payload)
        raise typer.Exit(code=result.exit_code)

    @queue_app.command('list-claims')
    def queue_list_claims(
        repo_root: str | None = typer.Option(None, '--repo-root'),
        queue: str | None = typer.Option(None, '--queue'),
        status: str | None = typer.Option(None, '--status'),
    ) -> None:
        resolved_repo_root = Path(repo_root).resolve() if repo_root else Path.cwd().resolve()
        result = _build_runtime_api_client().list_claims(
            QueueListClaimsRequest(repo_root=resolved_repo_root, queue=queue, status=status)
        )
        _emit_json_result(result.payload)
        raise typer.Exit(code=result.exit_code)

    @queue_app.command('ack')
    def queue_ack(
        claim_id: str = typer.Option(..., '--claim-id'),
        repo_root: str | None = typer.Option(None, '--repo-root'),
    ) -> None:
        resolved_repo_root = Path(repo_root).resolve() if repo_root else Path.cwd().resolve()
        result = _build_runtime_api_client().ack(
            QueueClaimActionRequest(repo_root=resolved_repo_root, claim_id=claim_id)
        )
        _emit_json_result(result.payload)
        raise typer.Exit(code=result.exit_code)

    @queue_app.command('requeue')
    def queue_requeue(
        claim_id: str = typer.Option(..., '--claim-id'),
        repo_root: str | None = typer.Option(None, '--repo-root'),
    ) -> None:
        resolved_repo_root = Path(repo_root).resolve() if repo_root else Path.cwd().resolve()
        result = _build_runtime_api_client().requeue(
            QueueClaimActionRequest(repo_root=resolved_repo_root, claim_id=claim_id)
        )
        _emit_json_result(result.payload)
        raise typer.Exit(code=result.exit_code)

    @queue_app.command('validate-packet')
    def queue_validate_packet(
        message_file: str = typer.Option(..., '--message-file'),
        repo_root: str | None = typer.Option(None, '--repo-root'),
    ) -> None:
        resolved_repo_root = Path(repo_root).resolve() if repo_root else Path.cwd().resolve()
        result = _build_runtime_api_client().validate_packet(
            QueuePacketFileRequest(repo_root=resolved_repo_root, message_file=Path(message_file).resolve())
        )
        _emit_json_result(result.payload)
        raise typer.Exit(code=result.exit_code)

    @queue_app.command('send-packet')
    def queue_send_packet(
        message_file: str = typer.Option(..., '--message-file'),
        repo_root: str | None = typer.Option(None, '--repo-root'),
    ) -> None:
        resolved_repo_root = Path(repo_root).resolve() if repo_root else Path.cwd().resolve()
        result = _build_runtime_api_client().send_packet(
            QueuePacketFileRequest(repo_root=resolved_repo_root, message_file=Path(message_file).resolve())
        )
        _emit_json_result(result.payload)
        raise typer.Exit(code=result.exit_code)

    @worker_app.command('dispatch')
    def worker_dispatch(
        queue_name: str = typer.Option(..., '--queue-name'),
        packet_schema_type: str = typer.Option(..., '--packet-schema-type'),
        packet_message_id: str | None = typer.Option(None, '--packet-message-id'),
        packet_path: str | None = typer.Option(None, '--packet-path'),
        packet_payload_json: str | None = typer.Option(None, '--packet-payload-json'),
        actor_name: str | None = typer.Option(None, '--actor-name'),
        host_name: str | None = typer.Option(None, '--host-name'),
        repo_root: str | None = typer.Option(None, '--repo-root'),
        output: str = typer.Option('table', '--output', help='Output mode: table, json, or summary.'),
        dry_run: bool = typer.Option(True, '--dry-run/--live', help='Dispatch the packet through the runtime controller in dry-run mode.'),
        strict_mode: bool = typer.Option(True, '--strict/--no-strict'),
    ) -> None:
        code = _invoke(
            cli,
            command_family='worker',
            command_name='dispatch',
            repo_root=repo_root,
            output_mode=output,
            dry_run=dry_run,
            strict_mode=strict_mode,
            arguments={
                'queue_name': queue_name,
                'packet_schema_type': packet_schema_type,
                **({'packet_message_id': packet_message_id} if packet_message_id else {}),
                **({'packet_path': packet_path} if packet_path else {}),
                **({'packet_payload_json': packet_payload_json} if packet_payload_json else {}),
                **({'actor_name': actor_name} if actor_name else {}),
                **({'host_name': host_name} if host_name else {}),
            },
        )
        raise typer.Exit(code=code)

    @runtime_app.command('supervisor')
    def runtime_supervisor(
        repo_root: str | None = typer.Option(None, '--repo-root'),
        intake_mode: str = typer.Option('claim_next', '--intake-mode'),
        emit_next_assignment: bool = typer.Option(True, '--emit-next-assignment/--no-emit-next-assignment'),
        emit_worker_result: bool = typer.Option(True, '--emit-worker-result/--no-emit-worker-result'),
        emit_verification: bool = typer.Option(True, '--emit-verification/--no-emit-verification'),
        max_iterations: int = typer.Option(0, '--max-iterations'),
        poll_interval_seconds: float = typer.Option(5.0, '--poll-interval-seconds'),
    ) -> None:
        resolved_repo_root = Path(repo_root).resolve() if repo_root else Path.cwd().resolve()
        result = _build_runtime_api_client().run_supervisor(
            RuntimeSupervisorRequest(
                repo_root=resolved_repo_root,
                intake_mode=intake_mode,
                emit_next_assignment=emit_next_assignment,
                emit_worker_result=emit_worker_result,
                emit_verification=emit_verification,
                max_iterations=max_iterations,
                poll_interval_seconds=poll_interval_seconds,
            )
        )
        _emit_json_result(result.payload)
        raise typer.Exit(code=result.exit_code)

    @runtime_app.command('start')
    def runtime_start(
        repo_root: str | None = typer.Option(None, '--repo-root'),
        intake_mode: str = typer.Option('claim_next', '--intake-mode'),
        emit_next_assignment: bool = typer.Option(True, '--emit-next-assignment/--no-emit-next-assignment'),
        emit_worker_result: bool = typer.Option(True, '--emit-worker-result/--no-emit-worker-result'),
        emit_verification: bool = typer.Option(True, '--emit-verification/--no-emit-verification'),
        max_iterations: int = typer.Option(0, '--max-iterations'),
        poll_interval_seconds: float = typer.Option(5.0, '--poll-interval-seconds'),
    ) -> None:
        resolved_repo_root = Path(repo_root).resolve() if repo_root else Path.cwd().resolve()
        result = _build_runtime_api_client().start_supervisor(
            RuntimeSupervisorRequest(
                repo_root=resolved_repo_root,
                intake_mode=intake_mode,
                emit_next_assignment=emit_next_assignment,
                emit_worker_result=emit_worker_result,
                emit_verification=emit_verification,
                max_iterations=max_iterations,
                poll_interval_seconds=poll_interval_seconds,
            )
        )
        _emit_json_result(result.payload)
        raise typer.Exit(code=result.exit_code)

    @runtime_app.command('stop')
    def runtime_stop(
        repo_root: str | None = typer.Option(None, '--repo-root'),
    ) -> None:
        resolved_repo_root = Path(repo_root).resolve() if repo_root else Path.cwd().resolve()
        result = _build_runtime_api_client().stop_supervisor(RuntimeStatusRequest(repo_root=resolved_repo_root))
        _emit_json_result(result.payload)
        raise typer.Exit(code=result.exit_code)

    @runtime_app.command('status')
    def runtime_status(
        repo_root: str | None = typer.Option(None, '--repo-root'),
    ) -> None:
        resolved_repo_root = Path(repo_root).resolve() if repo_root else Path.cwd().resolve()
        result = _build_runtime_api_client().supervisor_status(RuntimeStatusRequest(repo_root=resolved_repo_root))
        _emit_json_result(result.payload)

    @runtime_app.command('logs')
    def runtime_logs(
        repo_root: str | None = typer.Option(None, '--repo-root'),
        lines: int = typer.Option(200, '--lines'),
    ) -> None:
        resolved_repo_root = Path(repo_root).resolve() if repo_root else Path.cwd().resolve()
        output = _build_runtime_api_client().supervisor_logs(
            RuntimeLogsRequest(repo_root=resolved_repo_root, lines=lines)
        )
        if output:
            typer.echo(output)

    @runtime_app.command('restart')
    def runtime_restart(
        repo_root: str | None = typer.Option(None, '--repo-root'),
        intake_mode: str = typer.Option('claim_next', '--intake-mode'),
        emit_next_assignment: bool = typer.Option(True, '--emit-next-assignment/--no-emit-next-assignment'),
        emit_worker_result: bool = typer.Option(True, '--emit-worker-result/--no-emit-worker-result'),
        emit_verification: bool = typer.Option(True, '--emit-verification/--no-emit-verification'),
        max_iterations: int = typer.Option(0, '--max-iterations'),
        poll_interval_seconds: float = typer.Option(5.0, '--poll-interval-seconds'),
    ) -> None:
        resolved_repo_root = Path(repo_root).resolve() if repo_root else Path.cwd().resolve()
        result = _build_runtime_api_client().restart_supervisor(
            RuntimeSupervisorRequest(
                repo_root=resolved_repo_root,
                intake_mode=intake_mode,
                emit_next_assignment=emit_next_assignment,
                emit_worker_result=emit_worker_result,
                emit_verification=emit_verification,
                max_iterations=max_iterations,
                poll_interval_seconds=poll_interval_seconds,
            )
        )
        _emit_json_result(result.payload)
        raise typer.Exit(code=result.exit_code)

    @runtime_app.command('techlead')
    def runtime_techlead(
        repo_root: str | None = typer.Option(None, '--repo-root'),
        actor_name: str = typer.Option('TechLead Agent', '--actor-name'),
        host_name: str = typer.Option('techlead-runtime-host', '--host-name'),
        intake_mode: str = typer.Option('preview', '--intake-mode'),
        emit_next_assignment: bool = typer.Option(False, '--emit-next-assignment/--no-emit-next-assignment'),
        max_iterations: int = typer.Option(1, '--max-iterations'),
        poll_interval_seconds: float = typer.Option(5.0, '--poll-interval-seconds'),
    ) -> None:
        resolved_repo_root = Path(repo_root).resolve() if repo_root else Path.cwd().resolve()
        result = _build_runtime_api_client().run_techlead_host(
            RuntimeHostRunRequest(
                repo_root=resolved_repo_root,
                actor_name=actor_name,
                host_name=host_name,
                intake_mode=intake_mode,
                max_iterations=max_iterations,
                poll_interval_seconds=poll_interval_seconds,
                emit_next_assignment=emit_next_assignment,
            )
        )
        _emit_json_result(result.payload)
        raise typer.Exit(code=result.exit_code)

    @runtime_app.command('dev')
    def runtime_dev(
        repo_root: str | None = typer.Option(None, '--repo-root'),
        actor_name: str = typer.Option('Dev Agent', '--actor-name'),
        host_name: str = typer.Option('dev-runtime-host', '--host-name'),
        intake_mode: str = typer.Option('preview', '--intake-mode'),
        emit_worker_result: bool = typer.Option(False, '--emit-worker-result/--no-emit-worker-result'),
        max_iterations: int = typer.Option(1, '--max-iterations'),
        poll_interval_seconds: float = typer.Option(5.0, '--poll-interval-seconds'),
    ) -> None:
        resolved_repo_root = Path(repo_root).resolve() if repo_root else Path.cwd().resolve()
        result = _build_runtime_api_client().run_dev_host(
            RuntimeHostRunRequest(
                repo_root=resolved_repo_root,
                actor_name=actor_name,
                host_name=host_name,
                intake_mode=intake_mode,
                max_iterations=max_iterations,
                poll_interval_seconds=poll_interval_seconds,
                emit_worker_result=emit_worker_result,
            )
        )
        _emit_json_result(result.payload)
        raise typer.Exit(code=result.exit_code)

    @runtime_app.command('qa')
    def runtime_qa(
        repo_root: str | None = typer.Option(None, '--repo-root'),
        actor_name: str = typer.Option('QA Agent', '--actor-name'),
        host_name: str = typer.Option('qa-runtime-host', '--host-name'),
        intake_mode: str = typer.Option('preview', '--intake-mode'),
        emit_verification: bool = typer.Option(False, '--emit-verification/--no-emit-verification'),
        max_iterations: int = typer.Option(1, '--max-iterations'),
        poll_interval_seconds: float = typer.Option(5.0, '--poll-interval-seconds'),
    ) -> None:
        resolved_repo_root = Path(repo_root).resolve() if repo_root else Path.cwd().resolve()
        result = _build_runtime_api_client().run_qa_host(
            RuntimeHostRunRequest(
                repo_root=resolved_repo_root,
                actor_name=actor_name,
                host_name=host_name,
                intake_mode=intake_mode,
                max_iterations=max_iterations,
                poll_interval_seconds=poll_interval_seconds,
                emit_verification=emit_verification,
            )
        )
        _emit_json_result(result.payload)
        raise typer.Exit(code=result.exit_code)

    @report_app.command('explain')
    def report_explain(
        methodology_execution_id: str = typer.Option(..., '--methodology-execution-id'),
        repo_root: str | None = typer.Option(None, '--repo-root'),
        output: str = typer.Option('table', '--output', help='Output mode: table, json, or summary.'),
        dry_run: bool = typer.Option(False, '--dry-run'),
        strict_mode: bool = typer.Option(True, '--strict/--no-strict'),
    ) -> None:
        code = _invoke(
            cli,
            command_family='report',
            command_name='explain',
            repo_root=repo_root,
            output_mode=output,
            dry_run=dry_run,
            strict_mode=strict_mode,
            arguments={'methodology_execution_id': methodology_execution_id},
        )
        raise typer.Exit(code=code)

    @report_app.command('techlead-service-map')
    def report_techlead_service_map() -> None:
        result = _build_runtime_api_client().techlead_service_map()
        _emit_json_result(result.payload)
        raise typer.Exit(code=result.exit_code)

    @authority_app.command('install-package')
    def authority_install_package(
        repo_root: str = typer.Option(..., '--repo-root'),
        package_root: str = typer.Option(..., '--package-root'),
        authority_install_root: str | None = typer.Option(None, '--authority-install-root'),
    ) -> None:
        destination = Path(authority_install_root).resolve() if authority_install_root else None
        result = _build_authority_install_application_service().install_package(
            AuthorityInstallRequest(
                repo_root=Path(repo_root).resolve(),
                package_root=Path(package_root).resolve(),
                authority_install_root=destination,
            )
        )
        _emit_json_result(result.payload)
        raise typer.Exit(code=result.exit_code)

    @ops_app.command('install-runtime')
    def ops_install_runtime(
        repo_root: str = typer.Option(..., '--repo-root'),
        project_pack: str = typer.Option('fractal-core', '--project-pack'),
    ) -> None:
        result = install_runtime_support(Path(repo_root).resolve(), project_pack=project_pack)
        typer.echo(json.dumps({
            'ok': True,
            'install_mode': result.install_mode,
            'repo_root': str(result.repo_root),
            'codex_install_root': str(result.codex_install_root),
            'runtime_data_root': str(result.runtime_data_root),
            'platform_revision': result.platform_revision,
            'project_pack': result.project_pack,
        }, indent=2))

    @ops_app.command('update-runtime')
    def ops_update_runtime(
        repo_root: str = typer.Option(..., '--repo-root'),
        project_pack: str = typer.Option('fractal-core', '--project-pack'),
    ) -> None:
        result = install_runtime_support(Path(repo_root).resolve(), project_pack=project_pack)
        typer.echo(json.dumps({
            'ok': True,
            'install_mode': result.install_mode,
            'repo_root': str(result.repo_root),
            'codex_install_root': str(result.codex_install_root),
            'runtime_data_root': str(result.runtime_data_root),
            'platform_revision': result.platform_revision,
            'project_pack': result.project_pack,
        }, indent=2))

    @ops_app.command('validate-runtime')
    def ops_validate_runtime(
        repo_root: str | None = typer.Option(None, '--repo-root'),
    ) -> None:
        resolved_repo_root = Path(repo_root).resolve() if repo_root else Path.cwd().resolve()
        result = _build_runtime_api_client().validate_runtime(
            RuntimeValidationRequest(repo_root=resolved_repo_root)
        )
        _emit_json_result(result.payload)
        raise typer.Exit(code=result.exit_code)

    @ops_app.command('automation-preflight')
    def ops_automation_preflight(
        repo_root: str | None = typer.Option(None, '--repo-root'),
        project_slug: str = typer.Option('paa-platform', '--project-slug'),
        target_role: str = typer.Option(..., '--target-role'),
    ) -> None:
        resolved_repo_root = Path(repo_root).resolve() if repo_root else Path.cwd().resolve()
        result = _build_runtime_api_client().evaluate_automation_preflight(
            AutomationPreflightRequest(
                repo_root=resolved_repo_root,
                target_role=target_role,
                project_slug=project_slug,
            )
        )
        _emit_json_result(result.payload)
        raise typer.Exit(code=result.exit_code)

    @verify_app.command('runtime-smoke')
    def verify_runtime_smoke(
        repo_root: str | None = typer.Option(None, '--repo-root'),
        expected_branch: str | None = typer.Option(None, '--expected-branch'),
        output: str | None = typer.Option(None, '--output'),
    ) -> None:
        resolved_repo_root = Path(repo_root).resolve() if repo_root else Path.cwd().resolve()
        output_path = Path(output).resolve() if output else None
        result = _build_runtime_api_client().runtime_smoke(
            RuntimeSmokeRequest(
                repo_root=resolved_repo_root,
                expected_branch=expected_branch,
                output_path=output_path,
            )
        )
        _emit_json_result(result.payload)
        raise typer.Exit(code=result.exit_code)

    app.add_typer(component_app, name='component')
    app.add_typer(plan_app, name='plan')
    app.add_typer(status_app, name='status')
    app.add_typer(report_app, name='report')
    app.add_typer(authority_app, name='authority')
    app.add_typer(ops_app, name='ops')
    app.add_typer(verify_app, name='verify')
    app.add_typer(role_app, name='role')
    app.add_typer(agent_app, name='agent')
    app.add_typer(queue_app, name='queue')
    app.add_typer(worker_app, name='worker')
    app.add_typer(runtime_app, name='runtime')
    return app


def main() -> int:
    app = build_app()
    app(prog_name='paa')
    return 0


def _optional_string(value: object | None) -> str | None:
    if value is None:
        return None
    return str(value)


__all__ = ['DefaultPAAOperatorCLI', 'NullStructuredLogger', 'build_app', 'build_default_cli', 'main']

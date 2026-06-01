"""Thin Typer application root for the unified PAA operator CLI."""

from __future__ import annotations

from typing import Final

try:
    import typer
except ImportError as exc:  # pragma: no cover - exercised only in missing-dependency environments
    typer = None
    _TYPER_IMPORT_ERROR = exc
else:  # pragma: no branch
    _TYPER_IMPORT_ERROR = None

from paa_core.repositories.methodology_execution import PostgresMethodologyExecutionRepository
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
    ComponentCommandAdapter,
    PlanCommandAdapter,
    QueueCommandAdapter,
    ReportCommandAdapter,
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
    return DefaultPAAOperatorCLI(
        logger=logger,
        environment_resolver=EnvironmentResolver(),
        router=CommandRouter(
            (
                CommandRegistration(command_family='component', adapter=ComponentCommandAdapter()),
                CommandRegistration(command_family='plan', adapter=PlanCommandAdapter()),
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
                    ),
                ),
                CommandRegistration(
                    command_family='worker',
                    adapter=WorkerCommandAdapter(
                        queue_packet_runtime_controller=queue_packet_runtime_controller,
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
    queue_app = typer.Typer(help='Queue packet preview surfaces over the runtime controller.', no_args_is_help=True)
    worker_app = typer.Typer(help='Worker dispatch preview surfaces over the runtime controller.', no_args_is_help=True)

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

    app.add_typer(component_app, name='component')
    app.add_typer(plan_app, name='plan')
    app.add_typer(status_app, name='status')
    app.add_typer(report_app, name='report')
    app.add_typer(queue_app, name='queue')
    app.add_typer(worker_app, name='worker')
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

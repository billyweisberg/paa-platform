# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownParameterType=false, reportAttributeAccessIssue=false, reportArgumentType=false
from __future__ import annotations

from paa_core.application.contracts.operator_commands import OperatorCommandService
from paa_core.application.dto.operator import (
    OperatorCommandRequest,
    OperatorCommandResult,
    OperatorFailure,
    OperatorOutputMessage,
    OperatorOutputSection,
    OperatorOutputTable,
)
from paa_core.application.operator_command_adapters import (
    AgentCommandAdapter,
    ComponentCommandAdapter,
    PlanCommandAdapter,
    QueueCommandAdapter,
    ReportCommandAdapter,
    RoleCommandAdapter,
    StatusCommandAdapter,
    WorkerCommandAdapter,
)
from paa_core.application.operator_result_normalizer import CommandResultNormalizer
from paa_core.application.operator_router import CommandRegistration, CommandRouter
from paa_core.repositories.methodology_execution import PostgresMethodologyExecutionRepository
from paa_core.repositories.runtime_identity import PostgresRuntimeIdentityRepository
from paa_core.repositories.runtime_event import PostgresRuntimeEventRepository
from paa_core.services.implementation_plan_derivation.contracts import StructuredLogger
from paa_core.services.methodology_execution_preflight import (
    DefaultMethodologyExecutionPreflightService,
    MethodologyExecutionPreflightRequest,
)
from paa_core.services.methodology_execution_projection import DefaultMethodologyExecutionProjectionService
from paa_core.services.methodology_execution_state import DefaultMethodologyExecutionStateService
from paa_core.runtime.packets.reference_resolution import DefaultPacketReferenceResolutionService
from paa_core.services.queue_packet_runtime_controller import DefaultQueuePacketRuntimeController
from paa_core.services.techlead_acceptance_decision import DefaultTechLeadAcceptanceDecisionService
from paa_core.services.techlead_assignment_decision import DefaultTechLeadAssignmentDecisionService
from paa_core.services.techlead_closeout_decision import DefaultTechLeadCloseoutDecisionService
from paa_core.services.techlead_delivery_review_decision import DefaultTechLeadDeliveryReviewDecisionService
from paa_core.services.techlead_lineage_decision import DefaultTechLeadLineageDecisionService
from paa_core.services.techlead_reset_recovery_decision import DefaultTechLeadResetRecoveryDecisionService
from paa_core.services.techlead_worker import DefaultTechLeadWorkerService
from paa_core.services.techlead_worker_review_routing import DefaultTechLeadWorkerReviewRoutingService

_PREFLIGHTED_FAMILIES = {'component', 'plan'}


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


class DefaultOperatorCommandApplicationService(OperatorCommandService):
    def __init__(
        self,
        *,
        logger: StructuredLogger,
        router: CommandRouter,
        normalizer: CommandResultNormalizer,
        methodology_execution_preflight_service: object | None = None,
    ) -> None:
        self._logger = logger
        self._router = router
        self._normalizer = normalizer
        self.methodology_execution_preflight_service = methodology_execution_preflight_service

    def run_command(self, request: OperatorCommandRequest) -> OperatorCommandResult:
        self._logger.info('paa_cli.command.start', command_family=request.command.command_family, command_name=request.command.command_name)
        preflight_result = self._preflight_if_needed(request)
        if preflight_result is not None and not preflight_result.success:
            self._logger.warning('paa_cli.command.preflight_blocked', command_family=request.command.command_family, command_name=request.command.command_name, failure_code=preflight_result.failure.code if preflight_result.failure else 'preflight_blocked')
            return preflight_result
        try:
            raw_result = self._router.route(request)
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
        result = self._normalizer.normalize(request.command, raw_result)
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
            self._logger.warning('paa_cli.command.failed', command_family=request.command.command_family, command_name=request.command.command_name, failure_code=result.failure.code)
        else:
            self._logger.info('paa_cli.command.completed', command_family=request.command.command_family, command_name=request.command.command_name, exit_code=result.exit_code)
        return result

    def supports_command_family(self, command_family: str) -> bool:
        return self._router.supports_command_family(command_family)

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
            tables=(OperatorOutputTable(title='Methodology Preflight Summary', columns=('field', 'value'), rows=tuple((str(key), str(value)) for key, value in payload.items())),),
            data=payload,
        )
        if outcome_result.outcome.outcome_kind == 'blocked':
            return OperatorCommandResult(command=request.command, supported=True, success=False, exit_code=2, sections=(section,), failure=OperatorFailure(code=outcome_result.reason or 'preflight_blocked', summary=outcome_result.outcome.reason, details=tuple(filter(None, [outcome_result.outcome.details]))), metadata={'preflight': payload})
        if outcome_result.outcome.outcome_kind == 'redirect':
            return OperatorCommandResult(command=request.command, supported=True, success=False, exit_code=2, sections=(section,), failure=OperatorFailure(code='preflight_redirect', summary=outcome_result.outcome.reason, details=tuple(filter(None, [outcome_result.outcome.details])), metadata={'redirect_target': outcome_result.outcome.redirect_target}), metadata={'preflight': payload})
        return OperatorCommandResult(command=request.command, supported=True, success=True, exit_code=0, sections=(section,), metadata={'preflight': payload})

    @staticmethod
    def _build_preflight_request(request: OperatorCommandRequest) -> MethodologyExecutionPreflightRequest | None:
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


def _optional_string(value: object | None) -> str | None:
    if value is None:
        return None
    return str(value)


def build_default_operator_command_service(*, logger: StructuredLogger) -> DefaultOperatorCommandApplicationService:
    methodology_execution_repository = PostgresMethodologyExecutionRepository()
    runtime_identity_repository = PostgresRuntimeIdentityRepository()
    runtime_event_repository = PostgresRuntimeEventRepository()
    methodology_execution_state_service = DefaultMethodologyExecutionStateService(methodology_execution_repository=methodology_execution_repository, logger=logger)
    methodology_execution_projection_service = DefaultMethodologyExecutionProjectionService(methodology_execution_repository=methodology_execution_repository, logger=logger)
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
    return DefaultOperatorCommandApplicationService(
        logger=logger,
        router=CommandRouter(
            (
                CommandRegistration(command_family='component', adapter=ComponentCommandAdapter()),
                CommandRegistration(command_family='plan', adapter=PlanCommandAdapter()),
                CommandRegistration(command_family='role', adapter=RoleCommandAdapter(runtime_identity_repository=runtime_identity_repository)),
                CommandRegistration(command_family='agent', adapter=AgentCommandAdapter(runtime_identity_repository=runtime_identity_repository)),
                CommandRegistration(command_family='status', adapter=StatusCommandAdapter(methodology_execution_projection_service=methodology_execution_projection_service)),
                CommandRegistration(command_family='report', adapter=ReportCommandAdapter(methodology_execution_projection_service=methodology_execution_projection_service)),
                CommandRegistration(command_family='queue', adapter=QueueCommandAdapter(queue_packet_runtime_controller=queue_packet_runtime_controller, queue_packet_reader=_JsonFileQueuePacketReader(), runtime_event_repository=runtime_event_repository)),
                CommandRegistration(command_family='worker', adapter=WorkerCommandAdapter(queue_packet_runtime_controller=queue_packet_runtime_controller, packet_reference_resolution_service=packet_reference_resolution_service, queue_packet_reader=_JsonFileQueuePacketReader(), runtime_event_repository=runtime_event_repository)),
            )
        ),
        normalizer=CommandResultNormalizer(),
        methodology_execution_preflight_service=methodology_execution_preflight_service,
    )


__all__ = ['DefaultOperatorCommandApplicationService', 'build_default_operator_command_service']

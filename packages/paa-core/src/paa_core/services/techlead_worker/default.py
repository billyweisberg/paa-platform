"""Default implementation for the TechLead worker service."""

from __future__ import annotations

from paa_core.repositories.methodology_execution import MethodologyExecutionRepository
from paa_core.services.implementation_plan_derivation.contracts import StructuredLogger
from paa_core.services.methodology_execution_preflight import MethodologyExecutionPreflightService
from paa_core.services.methodology_execution_projection import (
    MethodologyExecutionProjectionService,
    MethodologyExecutionStatusProjection,
)
from paa_core.services.methodology_execution_state import MethodologyExecutionStateService
from paa_core.services.techlead_acceptance_decision import TechLeadAcceptanceDecisionService
from paa_core.services.techlead_assignment_decision import TechLeadAssignmentDecisionService
from paa_core.services.techlead_closeout_decision import TechLeadCloseoutDecisionService
from paa_core.services.techlead_delivery_review_decision import TechLeadDeliveryReviewDecisionService
from paa_core.services.techlead_lineage_decision import TechLeadLineageDecisionService
from paa_core.services.techlead_reset_recovery_decision import TechLeadResetRecoveryDecisionService
from paa_core.services.techlead_worker_review_routing import (
    TechLeadWorkerReviewRoutingRequest,
    TechLeadWorkerReviewRoutingResult,
    TechLeadWorkerReviewRoutingService,
)

from .models import (
    TechLeadWorkerDispatchSummary,
    TechLeadWorkerRequest,
    TechLeadWorkerResult,
)


class _NullStructuredLogger:
    def info(self, event: str, **fields: object) -> None:
        return None

    def warning(self, event: str, **fields: object) -> None:
        return None


class DefaultTechLeadWorkerService:
    """Coordinate the first supported deterministic TechLead worker-host slice."""

    _SUPPORTED_PACKET_SCHEMA_TYPES = frozenset({'worker_result_packet'})

    def __init__(
        self,
        *,
        methodology_execution_repository: MethodologyExecutionRepository,
        methodology_execution_state_service: MethodologyExecutionStateService,
        methodology_execution_projection_service: MethodologyExecutionProjectionService,
        methodology_execution_preflight_service: MethodologyExecutionPreflightService,
        techlead_assignment_decision_service: TechLeadAssignmentDecisionService,
        techlead_worker_review_routing_service: TechLeadWorkerReviewRoutingService,
        techlead_acceptance_decision_service: TechLeadAcceptanceDecisionService,
        techlead_delivery_review_decision_service: TechLeadDeliveryReviewDecisionService,
        techlead_reset_recovery_decision_service: TechLeadResetRecoveryDecisionService,
        techlead_lineage_decision_service: TechLeadLineageDecisionService,
        techlead_closeout_decision_service: TechLeadCloseoutDecisionService,
        logger: StructuredLogger | None = None,
    ) -> None:
        self._methodology_execution_repository = methodology_execution_repository
        self._methodology_execution_state_service = methodology_execution_state_service
        self._methodology_execution_projection_service = methodology_execution_projection_service
        self._methodology_execution_preflight_service = methodology_execution_preflight_service
        self._techlead_assignment_decision_service = techlead_assignment_decision_service
        self._techlead_worker_review_routing_service = techlead_worker_review_routing_service
        self._techlead_acceptance_decision_service = techlead_acceptance_decision_service
        self._techlead_delivery_review_decision_service = techlead_delivery_review_decision_service
        self._techlead_reset_recovery_decision_service = techlead_reset_recovery_decision_service
        self._techlead_lineage_decision_service = techlead_lineage_decision_service
        self._techlead_closeout_decision_service = techlead_closeout_decision_service
        self._logger = logger if logger is not None else _NullStructuredLogger()

    @property
    def methodology_execution_repository(self) -> MethodologyExecutionRepository:
        return self._methodology_execution_repository

    @property
    def methodology_execution_state_service(self) -> MethodologyExecutionStateService:
        return self._methodology_execution_state_service

    @property
    def methodology_execution_projection_service(self) -> MethodologyExecutionProjectionService:
        return self._methodology_execution_projection_service

    @property
    def methodology_execution_preflight_service(self) -> MethodologyExecutionPreflightService:
        return self._methodology_execution_preflight_service

    @property
    def techlead_assignment_decision_service(self) -> TechLeadAssignmentDecisionService:
        return self._techlead_assignment_decision_service

    @property
    def techlead_worker_review_routing_service(self) -> TechLeadWorkerReviewRoutingService:
        return self._techlead_worker_review_routing_service

    @property
    def techlead_acceptance_decision_service(self) -> TechLeadAcceptanceDecisionService:
        return self._techlead_acceptance_decision_service

    @property
    def techlead_delivery_review_decision_service(self) -> TechLeadDeliveryReviewDecisionService:
        return self._techlead_delivery_review_decision_service

    @property
    def techlead_reset_recovery_decision_service(self) -> TechLeadResetRecoveryDecisionService:
        return self._techlead_reset_recovery_decision_service

    @property
    def techlead_lineage_decision_service(self) -> TechLeadLineageDecisionService:
        return self._techlead_lineage_decision_service

    @property
    def techlead_closeout_decision_service(self) -> TechLeadCloseoutDecisionService:
        return self._techlead_closeout_decision_service

    @property
    def logger(self) -> StructuredLogger:
        return self._logger

    def supports_packet_schema_type(self, packet_schema_type: str) -> bool:
        return packet_schema_type.strip() in self._SUPPORTED_PACKET_SCHEMA_TYPES

    def handle_packet(self, request: TechLeadWorkerRequest) -> TechLeadWorkerResult:
        packet_schema_type = request.packet_schema_type.strip()
        self._logger.info(
            'techlead_worker.handle_packet.start',
            packet_schema_type=packet_schema_type,
            runtime_mode=request.runtime_mode,
            packet_message_id=request.packet_message_id,
        )

        if request.runtime_mode != 'dry_run':
            return self._build_blocked_result(
                request,
                reason='unsupported_runtime_mode',
                details='Live packet handling is not supported in the first TechLead worker slice.',
                handler_key='runtime-mode-check',
                blocking_reasons=('unsupported_runtime_mode',),
                notes=('fail-closed', 'dry-run-only'),
            )

        if not self.supports_packet_schema_type(packet_schema_type):
            return self._build_blocked_result(
                request,
                reason='unsupported_packet_schema_type',
                details=(
                    f'Packet schema type {packet_schema_type!r} is not supported by the first '
                    'TechLead worker slice.'
                ),
                handler_key='packet-classification',
                blocking_reasons=('unsupported_packet_schema_type',),
                notes=('fail-closed',),
            )

        methodology_execution_id = self._resolve_methodology_execution_id(request)
        if not methodology_execution_id:
            return self._build_blocked_result(
                request,
                reason='missing_methodology_execution_id',
                details='The supported worker-result slice requires a methodology execution id.',
                handler_key='execution-resolution',
                blocking_reasons=('missing_methodology_execution_id',),
                notes=('methodology-execution-required', 'fail-closed'),
            )

        current_execution_summary = self.methodology_execution_projection_service.get_status_projection(
            methodology_execution_id
        )
        routing_request = self._build_worker_review_routing_request(request)
        routing_result = self.techlead_worker_review_routing_service.derive_worker_review_routing(routing_request)
        dispatch_summary = self._build_dispatch_summary(
            packet_schema_type=packet_schema_type,
            routing_result=routing_result,
        )
        normalized_packet_output_summary = self._build_packet_output_summary(routing_result)
        result = TechLeadWorkerResult(
            request=request,
            methodology_execution_id=methodology_execution_id,
            current_execution_summary=current_execution_summary,
            dispatch_summary=dispatch_summary,
            worker_review_routing_result=routing_result,
            methodology_transition_result=None,
            normalized_packet_output_summary=normalized_packet_output_summary,
            ok=routing_result.ok,
            reason=routing_result.reason,
            details=routing_result.details,
            dry_run=True,
            metadata={
                'service_component': 'TechLeadWorkerService',
                'supported_packet_schema_type': packet_schema_type,
                'routing_decision_supported': routing_result.summary.decision_supported,
            },
        )
        self._logger.info(
            'techlead_worker.handle_packet.complete',
            packet_schema_type=packet_schema_type,
            methodology_execution_id=methodology_execution_id,
            ok=result.ok,
            recommended_next_action=dispatch_summary.recommended_next_action,
        )
        return result

    def _resolve_methodology_execution_id(self, request: TechLeadWorkerRequest) -> str | None:
        if request.methodology_execution_id:
            return request.methodology_execution_id
        payload = request.packet_payload or {}
        value = payload.get('methodology_execution_id')
        return value if isinstance(value, str) and value else None

    def _build_worker_review_routing_request(
        self,
        request: TechLeadWorkerRequest,
    ) -> TechLeadWorkerReviewRoutingRequest:
        payload = request.packet_payload or {}
        issue_number = payload.get('issue_number')
        if not isinstance(issue_number, int):
            issue_number = 0
        pr_number = payload.get('pr_number')
        if not isinstance(pr_number, int):
            pr_number = None
        return TechLeadWorkerReviewRoutingRequest(
            project_slug=str(payload.get('project_slug') or ''),
            issue_number=issue_number,
            pr_number=pr_number,
            workflow_stage=str(payload.get('workflow_stage') or ''),
            worker_role=str(payload.get('worker_role') or ''),
            worker_result_type=str(payload.get('worker_result_type') or ''),
            source_packet_schema_type=request.packet_schema_type,
            source_packet_message_id=request.packet_message_id,
            metadata=request.metadata,
        )

    def _build_dispatch_summary(
        self,
        *,
        packet_schema_type: str,
        routing_result: TechLeadWorkerReviewRoutingResult,
    ) -> TechLeadWorkerDispatchSummary:
        return TechLeadWorkerDispatchSummary(
            handler_key='worker-review-routing',
            packet_schema_type=packet_schema_type,
            decision_service_used='TechLeadWorkerReviewRoutingService',
            decision_supported=routing_result.summary.decision_supported,
            recommended_next_action=routing_result.summary.recommended_next_decision,
            recommended_target_role=routing_result.summary.recommended_target_role,
            packet_emission_required=False,
            methodology_transition_required=False,
            blocking_reasons=routing_result.summary.blocking_reasons,
            notes=routing_result.summary.notes,
        )

    def _build_packet_output_summary(self, routing_result: TechLeadWorkerReviewRoutingResult) -> str | None:
        if not routing_result.ok or not routing_result.summary.recommended_next_decision:
            return None
        target_role = routing_result.summary.recommended_target_role or 'unassigned-role'
        return (
            'Dry run only: would emit the next packet or assignment for '
            f'{target_role} via {routing_result.summary.recommended_next_decision}.'
        )

    def _build_blocked_result(
        self,
        request: TechLeadWorkerRequest,
        *,
        reason: str,
        details: str,
        handler_key: str,
        blocking_reasons: tuple[str, ...],
        notes: tuple[str, ...],
    ) -> TechLeadWorkerResult:
        self._logger.warning(
            'techlead_worker.handle_packet.blocked',
            packet_schema_type=request.packet_schema_type,
            runtime_mode=request.runtime_mode,
            reason=reason,
        )
        dispatch_summary = TechLeadWorkerDispatchSummary(
            handler_key=handler_key,
            packet_schema_type=request.packet_schema_type,
            decision_service_used=None,
            decision_supported=False,
            recommended_next_action=None,
            recommended_target_role=None,
            packet_emission_required=False,
            methodology_transition_required=False,
            blocking_reasons=blocking_reasons,
            notes=notes,
        )
        return TechLeadWorkerResult(
            request=request,
            methodology_execution_id=self._resolve_methodology_execution_id(request),
            current_execution_summary=None,
            dispatch_summary=dispatch_summary,
            worker_review_routing_result=None,
            methodology_transition_result=None,
            normalized_packet_output_summary=None,
            ok=False,
            reason=reason,
            details=details,
            dry_run=request.runtime_mode == 'dry_run',
            metadata={
                'service_component': 'TechLeadWorkerService',
                'supported_packet_schema_type': request.packet_schema_type,
            },
        )


__all__ = ['DefaultTechLeadWorkerService']

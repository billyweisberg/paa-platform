"""Default implementation for the QA worker service."""

from __future__ import annotations

from paa_core.services.implementation_plan_derivation.contracts import StructuredLogger
from paa_core.services.methodology_execution_projection import (
    MethodologyExecutionProjectionService,
    MethodologyExecutionStatusProjection,
)
from paa_core.services.methodology_execution_state import MethodologyExecutionStateService
from paa_core.services.packet_context_assembly import (
    PacketContextAssemblyRequest,
    PacketContextAssemblyResult,
    PacketContextAssemblyService,
)

from .contracts import QAVerificationPacketAssembler, QAVerificationRunner
from .models import QAWorkerRequest, QAWorkerResult, QAWorkerVerificationSummary


class _NullStructuredLogger:
    def info(self, event: str, **fields: object) -> None:
        return None

    def warning(self, event: str, **fields: object) -> None:
        return None


class DefaultQAWorkerService:
    """Coordinate the first supported deterministic QA worker-host slice."""

    _SUPPORTED_PACKET_SCHEMA_TYPES = frozenset({'techlead_assignment_packet'})

    def __init__(
        self,
        *,
        packet_context_assembly_service: PacketContextAssemblyService,
        methodology_execution_state_service: MethodologyExecutionStateService,
        methodology_execution_projection_service: MethodologyExecutionProjectionService,
        verification_runner: QAVerificationRunner,
        qa_verification_packet_assembler: QAVerificationPacketAssembler,
        logger: StructuredLogger | None = None,
    ) -> None:
        self._packet_context_assembly_service = packet_context_assembly_service
        self._methodology_execution_state_service = methodology_execution_state_service
        self._methodology_execution_projection_service = methodology_execution_projection_service
        self._verification_runner = verification_runner
        self._qa_verification_packet_assembler = qa_verification_packet_assembler
        self._logger = logger if logger is not None else _NullStructuredLogger()

    @property
    def packet_context_assembly_service(self) -> PacketContextAssemblyService:
        return self._packet_context_assembly_service

    @property
    def methodology_execution_state_service(self) -> MethodologyExecutionStateService:
        return self._methodology_execution_state_service

    @property
    def methodology_execution_projection_service(self) -> MethodologyExecutionProjectionService:
        return self._methodology_execution_projection_service

    @property
    def verification_runner(self) -> QAVerificationRunner:
        return self._verification_runner

    @property
    def qa_verification_packet_assembler(self) -> QAVerificationPacketAssembler:
        return self._qa_verification_packet_assembler

    @property
    def logger(self) -> StructuredLogger:
        return self._logger

    def supports_packet_schema_type(self, packet_schema_type: str) -> bool:
        return packet_schema_type.strip() in self._SUPPORTED_PACKET_SCHEMA_TYPES

    def handle_packet(self, request: QAWorkerRequest) -> QAWorkerResult:
        packet_schema_type = request.packet_schema_type.strip()
        self._logger.info(
            'qa_worker.handle_packet.start',
            packet_schema_type=packet_schema_type,
            runtime_mode=request.runtime_mode,
            packet_message_id=request.packet_message_id,
        )

        if request.runtime_mode != 'dry_run':
            return self._build_blocked_result(
                request,
                reason='unsupported_runtime_mode',
                details='Live QA worker verification is not supported in the first service slice.',
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
                    'QA worker slice.'
                ),
                handler_key='packet-classification',
                blocking_reasons=('unsupported_packet_schema_type',),
                notes=('fail-closed',),
            )

        packet_context_result = self.packet_context_assembly_service.assemble_packet_context(
            PacketContextAssemblyRequest(
                packet_schema_type=packet_schema_type,
                packet_message_id=request.packet_message_id,
                packet_path=request.packet_path,
                packet_payload=request.packet_payload,
                methodology_execution_id=request.methodology_execution_id,
                project_id=request.project_id,
                work_item_id=request.work_item_id,
                component_id=request.component_id,
                runtime_surface='qa',
                actor_name=request.actor_name,
                host_name=request.host_name,
                metadata=request.metadata,
            )
        )
        if not packet_context_result.ok:
            return self._build_context_blocked_result(request, packet_context_result)

        methodology_execution_id = (
            packet_context_result.methodology_execution_status.methodology_execution_id
            if packet_context_result.methodology_execution_status is not None
            else request.methodology_execution_id
        )
        current_execution_summary = self._resolve_current_execution_summary(
            methodology_execution_id,
            packet_context_result=packet_context_result,
        )
        verification_result = self.verification_runner.run_qa_verification(packet_context_result)
        packet_output = self.qa_verification_packet_assembler.assemble_qa_verification_packet(verification_result)
        verification_summary = QAWorkerVerificationSummary(
            handler_key='qa-verification-dry-run',
            packet_schema_type=packet_schema_type,
            runtime_mode=request.runtime_mode,
            verification_supported=True,
            verification_runner_used=type(self.verification_runner).__name__,
            packet_context_required=True,
            packet_context_ok=True,
            qa_verification_packet_required=True,
            methodology_transition_required=False,
            blocking_reasons=(),
            notes=('dry-run-only', 'qa-packet-normalized'),
        )
        result = QAWorkerResult(
            request=request,
            methodology_execution_id=methodology_execution_id,
            current_execution_summary=current_execution_summary,
            packet_context_result=packet_context_result,
            verification_summary=verification_summary,
            verification_result=verification_result,
            methodology_transition_result=None,
            normalized_packet_output_summary=self._normalize_packet_output_summary(packet_output),
            ok=True,
            dry_run=True,
            metadata={
                'service_component': 'QAWorkerService',
                'supported_packet_schema_type': packet_schema_type,
                'result_packet_output_type': type(packet_output).__name__,
            },
        )
        self._logger.info(
            'qa_worker.handle_packet.complete',
            packet_schema_type=packet_schema_type,
            methodology_execution_id=methodology_execution_id,
            ok=result.ok,
        )
        return result

    def _resolve_current_execution_summary(
        self,
        methodology_execution_id: str | None,
        *,
        packet_context_result: PacketContextAssemblyResult,
    ) -> MethodologyExecutionStatusProjection | None:
        if methodology_execution_id is None:
            return None
        if (
            packet_context_result.methodology_execution_status is not None
            and packet_context_result.methodology_execution_status.methodology_execution_id == methodology_execution_id
        ):
            return packet_context_result.methodology_execution_status
        return self.methodology_execution_projection_service.get_status_projection(methodology_execution_id)

    def _build_context_blocked_result(
        self,
        request: QAWorkerRequest,
        packet_context_result: PacketContextAssemblyResult,
    ) -> QAWorkerResult:
        self._logger.warning(
            'qa_worker.handle_packet.context_blocked',
            packet_schema_type=request.packet_schema_type,
            reason=packet_context_result.reason,
        )
        return QAWorkerResult(
            request=request,
            methodology_execution_id=request.methodology_execution_id,
            current_execution_summary=packet_context_result.methodology_execution_status,
            packet_context_result=packet_context_result,
            verification_summary=QAWorkerVerificationSummary(
                handler_key='packet-context-assembly',
                packet_schema_type=request.packet_schema_type,
                runtime_mode=request.runtime_mode,
                verification_supported=False,
                verification_runner_used=None,
                packet_context_required=True,
                packet_context_ok=False,
                qa_verification_packet_required=True,
                methodology_transition_required=False,
                blocking_reasons=packet_context_result.assembly_summary.blocking_gaps,
                notes=('fail-closed', 'packet-context-blocked'),
            ),
            verification_result=None,
            methodology_transition_result=None,
            normalized_packet_output_summary=None,
            ok=False,
            reason=packet_context_result.reason,
            details=packet_context_result.details,
            dry_run=request.runtime_mode == 'dry_run',
            metadata={
                'service_component': 'QAWorkerService',
                'blocked_by': 'PacketContextAssemblyService',
            },
        )

    def _build_blocked_result(
        self,
        request: QAWorkerRequest,
        *,
        reason: str,
        details: str,
        handler_key: str,
        blocking_reasons: tuple[str, ...],
        notes: tuple[str, ...],
    ) -> QAWorkerResult:
        self._logger.warning(
            'qa_worker.handle_packet.blocked',
            packet_schema_type=request.packet_schema_type,
            reason=reason,
        )
        return QAWorkerResult(
            request=request,
            methodology_execution_id=request.methodology_execution_id,
            current_execution_summary=None,
            packet_context_result=None,
            verification_summary=QAWorkerVerificationSummary(
                handler_key=handler_key,
                packet_schema_type=request.packet_schema_type,
                runtime_mode=request.runtime_mode,
                verification_supported=False,
                verification_runner_used=None,
                packet_context_required=True,
                packet_context_ok=False,
                qa_verification_packet_required=True,
                methodology_transition_required=False,
                blocking_reasons=blocking_reasons,
                notes=notes,
            ),
            verification_result=None,
            methodology_transition_result=None,
            normalized_packet_output_summary=None,
            ok=False,
            reason=reason,
            details=details,
            dry_run=request.runtime_mode == 'dry_run',
            metadata={
                'service_component': 'QAWorkerService',
                'supported_packet_schema_type': request.packet_schema_type,
            },
        )

    def _normalize_packet_output_summary(self, packet_output: object) -> str:
        if isinstance(packet_output, str):
            return packet_output
        return f'Dry run only: QA verification output prepared as {type(packet_output).__name__}.'


__all__ = ['DefaultQAWorkerService']

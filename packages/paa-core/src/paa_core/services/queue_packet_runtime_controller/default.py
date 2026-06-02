"""Default implementation for the queue packet runtime controller."""

from __future__ import annotations

from typing import Any

from paa_core.services.dev_worker import DevWorkerService
from paa_core.services.implementation_plan_derivation.contracts import StructuredLogger
from paa_core.services.qa_worker import QAWorkerService
from paa_core.services.techlead_worker import (
    TechLeadWorkerRequest,
    TechLeadWorkerResult,
    TechLeadWorkerService,
)

from .contracts import QueuePacketDeliveryAdapter, QueuePacketReader
from .models import (
    QueuePacketDispatchSummary,
    QueuePacketRuntimeRequest,
    QueuePacketRuntimeResult,
)


class _NullStructuredLogger:
    def info(self, event: str, **fields: object) -> None:
        return None

    def warning(self, event: str, **fields: object) -> None:
        return None


class DefaultQueuePacketRuntimeController:
    """Coordinate the first supported deterministic queue runtime-controller slice."""

    _SUPPORTED_PACKET_SCHEMA_TYPES = frozenset(
        {'worker_result_packet', 'qa_verification_packet', 'techlead_decision_packet'}
    )

    def __init__(
        self,
        *,
        techlead_worker_service: TechLeadWorkerService,
        dev_worker_service: DevWorkerService,
        qa_worker_service: QAWorkerService,
        queue_packet_reader: QueuePacketReader | None = None,
        queue_packet_delivery_adapter: QueuePacketDeliveryAdapter | None = None,
        logger: StructuredLogger | None = None,
    ) -> None:
        self._techlead_worker_service = techlead_worker_service
        self._dev_worker_service = dev_worker_service
        self._qa_worker_service = qa_worker_service
        self._queue_packet_reader = queue_packet_reader
        self._queue_packet_delivery_adapter = queue_packet_delivery_adapter
        self._logger = logger if logger is not None else _NullStructuredLogger()

    @property
    def techlead_worker_service(self) -> TechLeadWorkerService:
        return self._techlead_worker_service

    @property
    def dev_worker_service(self) -> DevWorkerService:
        return self._dev_worker_service

    @property
    def qa_worker_service(self) -> QAWorkerService:
        return self._qa_worker_service

    @property
    def queue_packet_reader(self) -> QueuePacketReader | None:
        return self._queue_packet_reader

    @property
    def queue_packet_delivery_adapter(self) -> QueuePacketDeliveryAdapter | None:
        return self._queue_packet_delivery_adapter

    @property
    def logger(self) -> StructuredLogger:
        return self._logger

    def supports_packet_schema_type(self, packet_schema_type: str) -> bool:
        return packet_schema_type.strip() in self._SUPPORTED_PACKET_SCHEMA_TYPES

    def handle_packet(self, request: QueuePacketRuntimeRequest) -> QueuePacketRuntimeResult:
        packet_schema_type = request.packet_schema_type.strip()
        self._logger.info(
            'queue_packet_runtime_controller.handle_packet.start',
            queue_name=request.queue_name,
            packet_schema_type=packet_schema_type,
            runtime_mode=request.runtime_mode,
            packet_message_id=request.packet_message_id,
        )

        if request.runtime_mode != 'dry_run':
            return self._build_blocked_result(
                request,
                reason='unsupported_runtime_mode',
                details='Live queue packet handling is not supported in the first controller slice.',
                handler_key='runtime-mode-check',
                target_worker_host=None,
                blocking_reasons=('unsupported_runtime_mode',),
                notes=('fail-closed', 'dry-run-only'),
            )

        if not self.supports_packet_schema_type(packet_schema_type):
            return self._build_blocked_result(
                request,
                reason='unsupported_packet_schema_type',
                details=(
                    f'Packet schema type {packet_schema_type!r} is not supported by the first '
                    'queue runtime-controller slice.'
                ),
                handler_key='packet-classification',
                target_worker_host=None,
                blocking_reasons=('unsupported_packet_schema_type',),
                notes=('fail-closed',),
            )

        packet_payload = self._resolve_packet_payload(request)
        if packet_payload is None:
            return self._build_blocked_result(
                request,
                reason='missing_packet_payload',
                details='The supported dry-run controller slice requires packet payload or a readable packet path.',
                handler_key='packet-payload-resolution',
                target_worker_host='TechLeadWorkerService',
                blocking_reasons=('missing_packet_payload',),
                notes=('fail-closed', 'packet-payload-required'),
            )

        worker_request = TechLeadWorkerRequest(
            packet_schema_type=packet_schema_type,
            packet_message_id=request.packet_message_id,
            packet_path=request.packet_path,
            packet_payload=packet_payload,
            methodology_execution_id=self._resolve_methodology_execution_id(packet_payload),
            runtime_mode=request.runtime_mode,
            actor_name=request.actor_name,
            host_name=request.host_name,
            metadata=request.metadata,
        )
        worker_result = self.techlead_worker_service.handle_packet(worker_request)
        dispatch_summary = self._build_dispatch_summary(packet_schema_type=packet_schema_type, worker_result=worker_result)
        result = QueuePacketRuntimeResult(
            request=request,
            dispatch_summary=dispatch_summary,
            selected_worker_result=worker_result,
            normalized_queue_side_effect_summary=self._build_queue_side_effect_summary(worker_result),
            ok=worker_result.ok,
            reason=worker_result.reason,
            details=worker_result.details,
            dry_run=True,
            metadata={
                'service_component': 'QueuePacketRuntimeController',
                'selected_worker_host': 'TechLeadWorkerService',
                'queue_name': request.queue_name,
            },
        )
        self._logger.info(
            'queue_packet_runtime_controller.handle_packet.complete',
            queue_name=request.queue_name,
            packet_schema_type=packet_schema_type,
            ok=result.ok,
            target_worker_host=dispatch_summary.target_worker_host,
        )
        return result

    def _resolve_packet_payload(self, request: QueuePacketRuntimeRequest) -> dict[str, Any] | None:
        if request.packet_payload is not None:
            return request.packet_payload
        if request.packet_path and self.queue_packet_reader is not None:
            payload = self.queue_packet_reader.read_packet(request.packet_path)
            return payload if isinstance(payload, dict) else {'packet_payload': payload}
        return None

    def _resolve_methodology_execution_id(self, packet_payload: dict[str, Any]) -> str | None:
        value = packet_payload.get('methodology_execution_id')
        return value if isinstance(value, str) and value else None

    def _build_dispatch_summary(
        self,
        *,
        packet_schema_type: str,
        worker_result: TechLeadWorkerResult,
    ) -> QueuePacketDispatchSummary:
        notes = ('dry-run-only', 'techlead-worker-dispatch')
        if worker_result.dispatch_summary.notes:
            notes = notes + worker_result.dispatch_summary.notes
        return QueuePacketDispatchSummary(
            handler_key='techlead-worker-dispatch',
            packet_schema_type=packet_schema_type,
            target_worker_host='TechLeadWorkerService',
            dispatch_supported=worker_result.ok,
            queue_side_effect_required=False,
            ack_required=False,
            blocking_reasons=worker_result.dispatch_summary.blocking_reasons,
            notes=notes,
        )

    def _build_queue_side_effect_summary(self, worker_result: TechLeadWorkerResult) -> str:
        if worker_result.ok:
            return 'Dry run only: no queue send or ack side effects executed.'
        return 'Dry run only: queue side effects suppressed because dispatch did not succeed.'

    def _build_blocked_result(
        self,
        request: QueuePacketRuntimeRequest,
        *,
        reason: str,
        details: str,
        handler_key: str,
        target_worker_host: str | None,
        blocking_reasons: tuple[str, ...],
        notes: tuple[str, ...],
    ) -> QueuePacketRuntimeResult:
        self._logger.warning(
            'queue_packet_runtime_controller.handle_packet.blocked',
            queue_name=request.queue_name,
            packet_schema_type=request.packet_schema_type,
            reason=reason,
        )
        return QueuePacketRuntimeResult(
            request=request,
            dispatch_summary=QueuePacketDispatchSummary(
                handler_key=handler_key,
                packet_schema_type=request.packet_schema_type,
                target_worker_host=target_worker_host,
                dispatch_supported=False,
                queue_side_effect_required=False,
                ack_required=False,
                blocking_reasons=blocking_reasons,
                notes=notes,
            ),
            selected_worker_result=None,
            normalized_queue_side_effect_summary=None,
            ok=False,
            reason=reason,
            details=details,
            dry_run=request.runtime_mode == 'dry_run',
            metadata={
                'service_component': 'QueuePacketRuntimeController',
                'queue_name': request.queue_name,
            },
        )


__all__ = ['DefaultQueuePacketRuntimeController']

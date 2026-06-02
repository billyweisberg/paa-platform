"""Default implementation for the queue claim runtime service."""

from __future__ import annotations

from typing import Any

from paa_core.services.implementation_plan_derivation.contracts import StructuredLogger

from .contracts import PacketEnvelopeValidator, QueueClaimStateAdapter, QueueTransportAdapter
from .models import (
    QueueClaimRuntimeRequest,
    QueueClaimRuntimeResult,
    QueuePacketClaimSummary,
    QueuePacketPreviewSummary,
)


class _NullStructuredLogger:
    def info(self, event: str, **fields: object) -> None:
        return None

    def warning(self, event: str, **fields: object) -> None:
        return None


class DefaultQueueClaimRuntimeService:
    """Preview or claim the first supported queue packet slice."""

    _SUPPORTED_INTAKE_MODES = frozenset({'preview', 'claim_next'})
    _SUPPORTED_PACKET_SCHEMA_TYPES = frozenset(
        {
            'worker_result_packet',
            'techlead_assignment_packet',
            'techlead_decision_packet',
            'qa_verification_packet',
        }
    )

    def __init__(
        self,
        *,
        queue_transport_adapter: QueueTransportAdapter,
        packet_envelope_validator: PacketEnvelopeValidator,
        queue_claim_state_adapter: QueueClaimStateAdapter | None = None,
        supported_queue_names: tuple[str, ...] | None = None,
        logger: StructuredLogger | None = None,
    ) -> None:
        self._queue_transport_adapter = queue_transport_adapter
        self._packet_envelope_validator = packet_envelope_validator
        self._queue_claim_state_adapter = queue_claim_state_adapter
        self._supported_queue_names = tuple(supported_queue_names or ('fractal-core-architecture',))
        self._logger = logger if logger is not None else _NullStructuredLogger()

    @property
    def queue_transport_adapter(self) -> QueueTransportAdapter:
        return self._queue_transport_adapter

    @property
    def queue_claim_state_adapter(self) -> QueueClaimStateAdapter | None:
        return self._queue_claim_state_adapter

    @property
    def packet_envelope_validator(self) -> PacketEnvelopeValidator:
        return self._packet_envelope_validator

    @property
    def logger(self) -> StructuredLogger:
        return self._logger

    @property
    def supported_queue_names(self) -> tuple[str, ...]:
        return self._supported_queue_names

    def supports_intake_mode(self, intake_mode: str) -> bool:
        return intake_mode.strip() in self._SUPPORTED_INTAKE_MODES

    def assemble_queue_intake(self, request: QueueClaimRuntimeRequest) -> QueueClaimRuntimeResult:
        intake_mode = request.intake_mode.strip()
        self._logger.info(
            'queue_claim_runtime_service.assemble_queue_intake.start',
            queue_name=request.queue_name,
            intake_mode=intake_mode,
            claimant_name=request.claimant_name,
        )

        if request.queue_name not in self.supported_queue_names:
            return self._build_blocked_result(
                request,
                reason='unsupported_queue_name',
                details=(
                    f'Queue {request.queue_name!r} is not supported in the first queue-claim slice. '
                    f'Supported queues: {", ".join(self.supported_queue_names)}.'
                ),
                preview_supported=False,
                claim_supported=False,
                blocking_reasons=('unsupported_queue_name',),
                notes=('fail-closed',),
            )

        if not self.supports_intake_mode(intake_mode):
            return self._build_blocked_result(
                request,
                reason='unsupported_intake_mode',
                details=f'Intake mode {intake_mode!r} is not supported in the first queue-claim slice.',
                preview_supported=False,
                claim_supported=False,
                blocking_reasons=('unsupported_intake_mode',),
                notes=('fail-closed',),
            )

        if intake_mode == 'claim_next' and not request.claimant_name:
            return self._build_blocked_result(
                request,
                reason='missing_claimant_name',
                details='Claim-next intake requires claimant_name in the first queue-claim slice.',
                preview_supported=True,
                claim_supported=False,
                blocking_reasons=('missing_claimant_name',),
                notes=('fail-closed', 'claimant-required'),
            )

        packet = self._load_packet(request, intake_mode)
        if packet is None:
            return self._build_blocked_result(
                request,
                reason='missing_queue_packet',
                details='No queue packet is available for the requested preview or claim.',
                preview_supported=True,
                claim_supported=True,
                blocking_reasons=('missing_queue_packet',),
                notes=('fail-closed', 'queue-empty'),
            )

        envelope = self.packet_envelope_validator.validate_packet_envelope(packet)
        if not self._validation_ok(envelope):
            return self._build_blocked_result(
                request,
                reason='invalid_packet_envelope',
                details='The queue packet envelope failed validation for the supported slice.',
                preview_supported=intake_mode == 'preview',
                claim_supported=intake_mode == 'claim_next',
                blocking_reasons=('invalid_packet_envelope',),
                notes=('fail-closed', 'validation-blocked'),
                metadata={'validation_result': envelope},
            )

        packet_message_id = self._packet_message_id(packet)
        packet_schema_type = self._packet_schema_type(packet)
        packet_reference = self._packet_reference(packet)
        normalized_envelope = self._normalized_envelope(packet)
        normalized_payload = self._normalized_payload(packet)
        if packet_schema_type not in self._SUPPORTED_PACKET_SCHEMA_TYPES:
            return self._build_blocked_result(
                request,
                reason='unsupported_packet_schema_type',
                details=(
                    f'Packet schema type {packet_schema_type!r} is not supported by the first '
                    'queue-claim slice.'
                ),
                preview_supported=intake_mode == 'preview',
                claim_supported=intake_mode == 'claim_next',
                blocking_reasons=('unsupported_packet_schema_type',),
                notes=('fail-closed',),
                metadata={'packet_schema_type': packet_schema_type},
            )

        preview_summary = QueuePacketPreviewSummary(
            queue_name=request.queue_name,
            packet_message_id=packet_message_id,
            packet_schema_type=packet_schema_type,
            packet_reference=packet_reference,
            preview_supported=True,
            claim_supported=True,
            blocking_reasons=(),
            notes=('preview',) if intake_mode == 'preview' else ('claimed-preview',),
        )
        claim_summary = None
        metadata: dict[str, Any] = {
            'service_component': 'QueueClaimRuntimeService',
            'intake_mode': intake_mode,
        }

        if intake_mode == 'claim_next':
            claim_record = {
                'queue_name': request.queue_name,
                'claimant_name': request.claimant_name,
                'packet_message_id': packet_message_id,
                'packet_schema_type': packet_schema_type,
                'packet_reference': packet_reference,
            }
            claim_result = (
                self.queue_claim_state_adapter.record_claim(claim_record)
                if self.queue_claim_state_adapter is not None
                else {'claim_id': None}
            )
            claim_id = claim_result.get('claim_id') if isinstance(claim_result, dict) else None
            claim_summary = QueuePacketClaimSummary(
                queue_name=request.queue_name,
                claim_id=str(claim_id) if claim_id is not None else None,
                claimant_name=request.claimant_name,
                packet_message_id=packet_message_id,
                packet_reference=packet_reference,
                claim_supported=True,
                blocking_reasons=(),
                notes=('claimed',),
            )
            metadata['claim_result'] = claim_result

        result = QueueClaimRuntimeResult(
            request=request,
            preview_summary=preview_summary,
            claim_summary=claim_summary,
            normalized_packet_envelope=normalized_envelope,
            normalized_packet_payload=normalized_payload,
            ok=True,
            metadata=metadata,
        )
        self._logger.info(
            'queue_claim_runtime_service.assemble_queue_intake.complete',
            queue_name=request.queue_name,
            intake_mode=intake_mode,
            packet_message_id=packet_message_id,
            ok=True,
        )
        return result

    def _load_packet(self, request: QueueClaimRuntimeRequest, intake_mode: str) -> object | None:
        if intake_mode == 'preview':
            return self.queue_transport_adapter.preview_queue(request.queue_name, limit=1)
        return self.queue_transport_adapter.claim_next_packet(
            request.queue_name,
            claimant_name=request.claimant_name,
        )

    @staticmethod
    def _validation_ok(validation_result: object) -> bool:
        if isinstance(validation_result, dict):
            ok = validation_result.get('ok')
            return bool(ok) if ok is not None else True
        return bool(validation_result)

    @staticmethod
    def _packet_message_id(packet: object) -> str | None:
        if not isinstance(packet, dict):
            return None
        value = packet.get('packet_message_id') or packet.get('message_id')
        return value if isinstance(value, str) and value else None

    @staticmethod
    def _packet_schema_type(packet: object) -> str | None:
        if not isinstance(packet, dict):
            return None
        value = packet.get('packet_schema_type')
        return value if isinstance(value, str) and value else None


    @staticmethod
    def _packet_reference(packet: object) -> str | None:
        if not isinstance(packet, dict):
            return None
        value = packet.get('packet_path') or packet.get('packet_reference')
        return value if isinstance(value, str) and value else None

    @staticmethod
    def _normalized_envelope(packet: object) -> dict[str, Any] | None:
        if not isinstance(packet, dict):
            return None
        return {
            'packet_message_id': DefaultQueueClaimRuntimeService._packet_message_id(packet),
            'packet_schema_type': DefaultQueueClaimRuntimeService._packet_schema_type(packet),
            'packet_reference': DefaultQueueClaimRuntimeService._packet_reference(packet),
        }

    @staticmethod
    def _normalized_payload(packet: object) -> dict[str, Any] | None:
        if not isinstance(packet, dict):
            return None
        payload = packet.get('packet_payload')
        if isinstance(payload, dict):
            return payload
        return None

    def _build_blocked_result(
        self,
        request: QueueClaimRuntimeRequest,
        *,
        reason: str,
        details: str,
        preview_supported: bool,
        claim_supported: bool,
        blocking_reasons: tuple[str, ...],
        notes: tuple[str, ...],
        metadata: dict[str, Any] | None = None,
    ) -> QueueClaimRuntimeResult:
        self._logger.warning(
            'queue_claim_runtime_service.assemble_queue_intake.blocked',
            queue_name=request.queue_name,
            intake_mode=request.intake_mode,
            reason=reason,
        )
        preview_summary = QueuePacketPreviewSummary(
            queue_name=request.queue_name,
            packet_message_id=request.packet_message_id,
            packet_schema_type=request.packet_schema_type,
            packet_reference=None,
            preview_supported=preview_supported,
            claim_supported=claim_supported,
            blocking_reasons=blocking_reasons,
            notes=notes,
        )
        claim_summary = None
        if request.intake_mode.strip() == 'claim_next':
            claim_summary = QueuePacketClaimSummary(
                queue_name=request.queue_name,
                claim_id=None,
                claimant_name=request.claimant_name,
                packet_message_id=request.packet_message_id,
                packet_reference=None,
                claim_supported=claim_supported,
                blocking_reasons=blocking_reasons,
                notes=notes,
            )
        return QueueClaimRuntimeResult(
            request=request,
            preview_summary=preview_summary,
            claim_summary=claim_summary,
            normalized_packet_envelope=None,
            normalized_packet_payload=None,
            ok=False,
            reason=reason,
            details=details,
            metadata={'service_component': 'QueueClaimRuntimeService', **(metadata or {})},
        )


__all__ = ['DefaultQueueClaimRuntimeService']

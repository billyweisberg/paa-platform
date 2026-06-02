"""Default implementation for the packet reference resolution service."""

from __future__ import annotations

from typing import Any

from paa_core.repositories.runtime_event import RuntimeEventRepository
from paa_core.services.implementation_plan_derivation.contracts import StructuredLogger

from .contracts import PacketArtifactReader, RuntimePathAdapter
from .models import (
    PacketReferenceResolutionRequest,
    PacketReferenceResolutionResult,
    PacketReferenceResolutionSummary,
)


class _NullStructuredLogger:
    def info(self, event: str, **fields: object) -> None:
        return None

    def warning(self, event: str, **fields: object) -> None:
        return None


class DefaultPacketReferenceResolutionService:
    """Resolve the first supported minimal packet-reference slice."""

    _SUPPORTED_PACKET_SCHEMA_TYPES = frozenset(
        {'worker_result_packet', 'techlead_assignment_packet', 'qa_verification_packet'}
    )

    def __init__(
        self,
        *,
        runtime_event_repository: RuntimeEventRepository,
        packet_artifact_reader: PacketArtifactReader | None = None,
        runtime_path_adapter: RuntimePathAdapter | None = None,
        logger: StructuredLogger | None = None,
    ) -> None:
        self._runtime_event_repository = runtime_event_repository
        self._packet_artifact_reader = packet_artifact_reader
        self._runtime_path_adapter = runtime_path_adapter
        self._logger = logger if logger is not None else _NullStructuredLogger()

    @property
    def runtime_event_repository(self) -> RuntimeEventRepository:
        return self._runtime_event_repository

    @property
    def packet_artifact_reader(self) -> PacketArtifactReader | None:
        return self._packet_artifact_reader

    @property
    def runtime_path_adapter(self) -> RuntimePathAdapter | None:
        return self._runtime_path_adapter

    @property
    def logger(self) -> StructuredLogger:
        return self._logger

    def supports_packet_schema_type(self, packet_schema_type: str) -> bool:
        return packet_schema_type.strip() in self._SUPPORTED_PACKET_SCHEMA_TYPES

    def resolve_packet_reference(
        self,
        request: PacketReferenceResolutionRequest,
    ) -> PacketReferenceResolutionResult:
        self._logger.info(
            'packet_reference_resolution.resolve.start',
            packet_message_id=request.packet_message_id,
            packet_path=request.packet_path,
            packet_reference=request.packet_reference,
            packet_schema_type=request.packet_schema_type,
        )

        if request.packet_schema_type and not self.supports_packet_schema_type(request.packet_schema_type):
            return self._build_blocked_result(
                request,
                reason='unsupported_packet_schema_type',
                details=(
                    f'Packet schema type {request.packet_schema_type!r} is not supported by the first '
                    'packet-reference-resolution slice.'
                ),
                resolution_source='schema-check',
                packet_reference=request.packet_reference or request.packet_path,
                resolved_packet_path=None,
                blocking_reasons=('unsupported_packet_schema_type',),
                notes=('fail-closed',),
                metadata={'packet_schema_type': request.packet_schema_type},
            )

        if request.packet_message_id:
            return self._resolve_message_id(request)
        if request.packet_path:
            return self._resolve_packet_path(request)
        if request.packet_reference:
            return self._resolve_packet_reference(request)
        return self._build_blocked_result(
            request,
            reason='missing_packet_reference_identity',
            details='The supported slice requires packet_message_id, packet_path, or packet_reference.',
            resolution_source='identity-check',
            packet_reference=None,
            resolved_packet_path=None,
            blocking_reasons=('missing_packet_reference_identity',),
            notes=('fail-closed',),
        )

    def _resolve_message_id(self, request: PacketReferenceResolutionRequest) -> PacketReferenceResolutionResult:
        queue_message = self.runtime_event_repository.get_queue_message_by_external(request.packet_message_id or '')
        if queue_message is None:
            return self._build_blocked_result(
                request,
                reason='unresolved_packet_message_id',
                details='No persisted queue message was found for the provided packet message id.',
                resolution_source='message-id',
                packet_reference=request.packet_message_id,
                resolved_packet_path=None,
                blocking_reasons=('unresolved_packet_message_id',),
                notes=('fail-closed',),
            )

        if request.queue_name and queue_message.queue_name != request.queue_name:
            return self._build_blocked_result(
                request,
                reason='queue_name_mismatch',
                details='The resolved queue message does not belong to the requested queue.',
                resolution_source='message-id',
                packet_reference=queue_message.message_id_external or queue_message.queue_message_id,
                resolved_packet_path=None,
                blocking_reasons=('queue_name_mismatch',),
                notes=('fail-closed',),
                metadata={'resolved_queue_name': queue_message.queue_name},
            )

        if not self.supports_packet_schema_type(queue_message.schema_type):
            return self._build_blocked_result(
                request,
                reason='unsupported_packet_schema_type',
                details=(
                    f'Persisted queue message schema type {queue_message.schema_type!r} is not supported by the first '
                    'packet-reference-resolution slice.'
                ),
                resolution_source='message-id',
                packet_reference=queue_message.message_id_external or queue_message.queue_message_id,
                resolved_packet_path=None,
                blocking_reasons=('unsupported_packet_schema_type',),
                notes=('fail-closed',),
                metadata={'packet_schema_type': queue_message.schema_type},
            )

        automation_run = self.runtime_event_repository.get_latest_automation_run_for_message_id(
            queue_message.message_id_external or queue_message.queue_message_id
        )
        resolved_packet_path = self._extract_artifact_packet_path(automation_run.artifacts) if automation_run else None
        normalized_payload = self._read_payload(resolved_packet_path) if resolved_packet_path else None
        notes = ['message-id']
        if resolved_packet_path:
            notes.append('resolved-artifact-path')
        else:
            notes.append('pointer-only')

        result = PacketReferenceResolutionResult(
            request=request,
            resolution_summary=PacketReferenceResolutionSummary(
                resolution_source='message-id',
                packet_message_id=queue_message.message_id_external or queue_message.queue_message_id,
                packet_schema_type=queue_message.schema_type,
                queue_name=queue_message.queue_name,
                packet_reference=queue_message.message_id_external or queue_message.queue_message_id,
                resolved_packet_path=resolved_packet_path,
                resolution_supported=True,
                blocking_reasons=(),
                notes=tuple(notes),
            ),
            normalized_packet_payload=normalized_payload,
            ok=True,
            metadata={
                'service_component': 'PacketReferenceResolutionService',
                'queue_message_id': queue_message.queue_message_id,
                'queue_message_status': queue_message.status,
                'automation_run_id': automation_run.automation_run_id if automation_run else None,
            },
        )
        self._logger.info(
            'packet_reference_resolution.resolve.complete',
            resolution_source='message-id',
            packet_message_id=result.resolution_summary.packet_message_id,
            resolved_packet_path=resolved_packet_path,
            ok=True,
        )
        return result

    def _resolve_packet_path(self, request: PacketReferenceResolutionRequest) -> PacketReferenceResolutionResult:
        normalized_payload = self._read_payload(request.packet_path or '')
        result = PacketReferenceResolutionResult(
            request=request,
            resolution_summary=PacketReferenceResolutionSummary(
                resolution_source='packet-path',
                packet_message_id=request.packet_message_id,
                packet_schema_type=request.packet_schema_type,
                queue_name=request.queue_name,
                packet_reference=request.packet_path,
                resolved_packet_path=request.packet_path,
                resolution_supported=True,
                blocking_reasons=(),
                notes=('packet-path',),
            ),
            normalized_packet_payload=normalized_payload,
            ok=True,
            metadata={'service_component': 'PacketReferenceResolutionService'},
        )
        self._logger.info(
            'packet_reference_resolution.resolve.complete',
            resolution_source='packet-path',
            resolved_packet_path=request.packet_path,
            ok=True,
        )
        return result

    def _resolve_packet_reference(self, request: PacketReferenceResolutionRequest) -> PacketReferenceResolutionResult:
        resolved_path = (
            self.runtime_path_adapter.resolve_packet_path(request.packet_reference or '')
            if self.runtime_path_adapter is not None
            else None
        )
        if not resolved_path:
            return self._build_blocked_result(
                request,
                reason='unresolved_packet_reference',
                details='The provided packet reference could not be resolved into a durable packet path.',
                resolution_source='packet-reference',
                packet_reference=request.packet_reference,
                resolved_packet_path=None,
                blocking_reasons=('unresolved_packet_reference',),
                notes=('fail-closed',),
            )

        normalized_payload = self._read_payload(resolved_path)
        result = PacketReferenceResolutionResult(
            request=request,
            resolution_summary=PacketReferenceResolutionSummary(
                resolution_source='packet-reference',
                packet_message_id=request.packet_message_id,
                packet_schema_type=request.packet_schema_type,
                queue_name=request.queue_name,
                packet_reference=request.packet_reference,
                resolved_packet_path=resolved_path,
                resolution_supported=True,
                blocking_reasons=(),
                notes=('resolved-reference',),
            ),
            normalized_packet_payload=normalized_payload,
            ok=True,
            metadata={'service_component': 'PacketReferenceResolutionService'},
        )
        self._logger.info(
            'packet_reference_resolution.resolve.complete',
            resolution_source='packet-reference',
            packet_reference=request.packet_reference,
            resolved_packet_path=resolved_path,
            ok=True,
        )
        return result

    def _read_payload(self, packet_path: str) -> dict[str, Any] | None:
        if self.packet_artifact_reader is None:
            return None
        payload = self.packet_artifact_reader.read_packet_payload(packet_path)
        return payload if isinstance(payload, dict) else {'packet_payload': payload}

    @staticmethod
    def _extract_artifact_packet_path(artifacts: dict[str, Any]) -> str | None:
        for key in ('packet_output_path', 'output_path', 'review_output_path'):
            value = artifacts.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    def _build_blocked_result(
        self,
        request: PacketReferenceResolutionRequest,
        *,
        reason: str,
        details: str,
        resolution_source: str,
        packet_reference: str | None,
        resolved_packet_path: str | None,
        blocking_reasons: tuple[str, ...],
        notes: tuple[str, ...],
        metadata: dict[str, Any] | None = None,
    ) -> PacketReferenceResolutionResult:
        self._logger.warning(
            'packet_reference_resolution.resolve.blocked',
            reason=reason,
            packet_message_id=request.packet_message_id,
            packet_path=request.packet_path,
            packet_reference=request.packet_reference,
        )
        return PacketReferenceResolutionResult(
            request=request,
            resolution_summary=PacketReferenceResolutionSummary(
                resolution_source=resolution_source,
                packet_message_id=request.packet_message_id,
                packet_schema_type=request.packet_schema_type,
                queue_name=request.queue_name,
                packet_reference=packet_reference,
                resolved_packet_path=resolved_packet_path,
                resolution_supported=False,
                blocking_reasons=blocking_reasons,
                notes=notes,
            ),
            normalized_packet_payload=None,
            ok=False,
            reason=reason,
            details=details,
            metadata={'service_component': 'PacketReferenceResolutionService', **(metadata or {})},
        )


__all__ = ['DefaultPacketReferenceResolutionService']

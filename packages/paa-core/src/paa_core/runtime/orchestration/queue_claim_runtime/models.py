"""Models for the queue claim runtime service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class QueueClaimRuntimeRequest:
    queue_name: str
    intake_mode: str
    packet_message_id: str | None = None
    packet_schema_type: str | None = None
    claimant_name: str | None = None
    host_name: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class QueuePacketPreviewSummary:
    queue_name: str
    packet_message_id: str | None
    packet_schema_type: str | None
    packet_reference: str | None
    preview_supported: bool
    claim_supported: bool
    blocking_reasons: tuple[str, ...]
    notes: tuple[str, ...]


@dataclass(frozen=True)
class QueuePacketClaimSummary:
    queue_name: str
    claim_id: str | None
    claimant_name: str | None
    packet_message_id: str | None
    packet_reference: str | None
    claim_supported: bool
    blocking_reasons: tuple[str, ...]
    notes: tuple[str, ...]


@dataclass(frozen=True)
class QueueClaimRuntimeResult:
    request: QueueClaimRuntimeRequest
    preview_summary: QueuePacketPreviewSummary | None
    claim_summary: QueuePacketClaimSummary | None
    normalized_packet_envelope: dict[str, Any] | None
    normalized_packet_payload: dict[str, Any] | None
    ok: bool
    reason: str | None = None
    details: str | None = None
    metadata: dict[str, Any] | None = None


__all__ = [
    'QueueClaimRuntimeRequest',
    'QueueClaimRuntimeResult',
    'QueuePacketClaimSummary',
    'QueuePacketPreviewSummary',
]

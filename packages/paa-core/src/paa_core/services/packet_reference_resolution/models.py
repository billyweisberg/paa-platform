"""Models for the packet reference resolution service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PacketReferenceResolutionRequest:
    packet_message_id: str | None = None
    packet_path: str | None = None
    packet_reference: str | None = None
    queue_name: str | None = None
    packet_schema_type: str | None = None
    actor_name: str | None = None
    host_name: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class PacketReferenceResolutionSummary:
    resolution_source: str | None
    packet_message_id: str | None
    packet_schema_type: str | None
    queue_name: str | None
    packet_reference: str | None
    resolved_packet_path: str | None
    resolution_supported: bool
    blocking_reasons: tuple[str, ...]
    notes: tuple[str, ...]


@dataclass(frozen=True)
class PacketReferenceResolutionResult:
    request: PacketReferenceResolutionRequest
    resolution_summary: PacketReferenceResolutionSummary
    normalized_packet_payload: dict[str, Any] | None
    ok: bool
    reason: str | None = None
    details: str | None = None
    metadata: dict[str, Any] | None = None


__all__ = [
    'PacketReferenceResolutionRequest',
    'PacketReferenceResolutionResult',
    'PacketReferenceResolutionSummary',
]

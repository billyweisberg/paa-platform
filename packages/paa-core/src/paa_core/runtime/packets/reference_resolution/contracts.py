"""Contracts for the packet reference resolution service."""

from __future__ import annotations

from typing import Protocol

from paa_core.repositories.runtime_event import RuntimeEventRepository
from paa_core.services.implementation_plan_derivation.contracts import StructuredLogger

from .models import PacketReferenceResolutionRequest, PacketReferenceResolutionResult


class PacketArtifactReader(Protocol):
    """Read a resolved packet artifact when a later slice needs payload hydration."""

    def read_packet_payload(self, packet_path: str) -> dict[str, object]:
        """Return one decoded packet payload for the provided packet path."""
        ...


class RuntimePathAdapter(Protocol):
    """Resolve runtime-local packet reference keys into durable packet paths."""

    def resolve_packet_path(self, packet_reference: str) -> str | None:
        """Return one durable packet path for the provided packet reference key."""
        ...


class PacketReferenceResolutionService(Protocol):
    """Resolve one minimal packet reference into one normalized packet artifact result."""

    @property
    def runtime_event_repository(self) -> RuntimeEventRepository:
        """Return the injected runtime-event repository."""
        ...

    @property
    def packet_artifact_reader(self) -> PacketArtifactReader | None:
        """Return the injected packet artifact reader when payload hydration is supported."""
        ...

    @property
    def runtime_path_adapter(self) -> RuntimePathAdapter | None:
        """Return the injected runtime path adapter when runtime-local references are supported."""
        ...

    @property
    def logger(self) -> StructuredLogger:
        """Return the injected structured logger."""
        ...

    def resolve_packet_reference(
        self,
        request: PacketReferenceResolutionRequest,
    ) -> PacketReferenceResolutionResult:
        """Resolve one packet message id, path, or packet reference into one normalized result."""
        ...

    def supports_packet_schema_type(self, packet_schema_type: str) -> bool:
        """Return whether one packet schema type is supported in the current slice."""
        ...


__all__ = [
    'PacketArtifactReader',
    'PacketReferenceResolutionRequest',
    'PacketReferenceResolutionResult',
    'PacketReferenceResolutionService',
    'RuntimeEventRepository',
    'RuntimePathAdapter',
    'StructuredLogger',
]

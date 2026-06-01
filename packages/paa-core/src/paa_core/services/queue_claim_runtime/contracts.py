"""Contracts for the queue claim runtime service."""

from __future__ import annotations

from typing import Protocol

from paa_core.services.implementation_plan_derivation.contracts import StructuredLogger

from .models import QueueClaimRuntimeRequest, QueueClaimRuntimeResult


class QueueTransportAdapter(Protocol):
    """Preview or claim one queue packet through the injected transport."""

    def preview_queue(self, queue_name: str, *, limit: int = 1) -> object:
        """Return one normalized queue preview result for the provided queue."""
        ...

    def claim_next_packet(self, queue_name: str, *, claimant_name: str | None = None) -> object:
        """Return one normalized queue claim result for the next packet."""
        ...


class QueueClaimStateAdapter(Protocol):
    """Persist or expose claim metadata when queue intake requires it."""

    def record_claim(self, claim_record: object) -> object:
        """Persist one normalized claim record or return a pass-through result."""
        ...


class PacketEnvelopeValidator(Protocol):
    """Validate one queue packet envelope before downstream runtime handling."""

    def validate_packet_envelope(self, packet: object) -> object:
        """Return one normalized validation result for the provided queue packet."""
        ...


class QueueClaimRuntimeService(Protocol):
    """Preview or claim one supported queue packet through a deterministic runtime boundary."""

    @property
    def queue_transport_adapter(self) -> QueueTransportAdapter:
        """Return the injected queue transport adapter."""
        ...

    @property
    def queue_claim_state_adapter(self) -> QueueClaimStateAdapter | None:
        """Return the injected claim-state adapter when claim metadata persistence is supported."""
        ...

    @property
    def packet_envelope_validator(self) -> PacketEnvelopeValidator:
        """Return the injected packet envelope validator."""
        ...

    @property
    def logger(self) -> StructuredLogger:
        """Return the injected structured logger."""
        ...

    def assemble_queue_intake(self, request: QueueClaimRuntimeRequest) -> QueueClaimRuntimeResult:
        """Preview or claim one queue packet through one supported runtime intake pass."""
        ...

    def supports_intake_mode(self, intake_mode: str) -> bool:
        """Return whether one intake mode is supported in the current slice."""
        ...


__all__ = [
    'PacketEnvelopeValidator',
    'QueueClaimRuntimeRequest',
    'QueueClaimRuntimeResult',
    'QueueClaimRuntimeService',
    'QueueClaimStateAdapter',
    'QueueTransportAdapter',
    'StructuredLogger',
]

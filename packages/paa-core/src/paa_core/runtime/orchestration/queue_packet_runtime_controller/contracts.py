"""Contracts for the queue packet runtime controller."""

from __future__ import annotations

from typing import Protocol

from paa_core.runtime.workers.dev_worker import DevWorkerService
from paa_core.services.implementation_plan_derivation.contracts import StructuredLogger
from paa_core.runtime.workers.qa_worker import QAWorkerService
from paa_core.runtime.workers.techlead_worker import TechLeadWorkerService

from .models import QueuePacketRuntimeRequest, QueuePacketRuntimeResult


class QueuePacketReader(Protocol):
    """Load or preview one claimed queue packet for runtime dispatch."""

    def read_packet(self, packet_reference: object) -> object:
        """Return one normalized queue packet payload or summary for the reference."""
        ...


class QueuePacketDeliveryAdapter(Protocol):
    """Provide normalized future queue send and ack side-effect hooks."""

    def send_packet(self, packet: object) -> object:
        """Return one normalized send result for the provided packet."""
        ...

    def acknowledge_packet(self, packet_message_id: str) -> None:
        """Acknowledge one handled queue packet by message id."""
        ...


class QueuePacketRuntimeController(Protocol):
    """Coordinate one deterministic queue-packet runtime dispatch pass."""

    @property
    def techlead_worker_service(self) -> TechLeadWorkerService:
        """Return the injected TechLead worker service."""
        ...

    @property
    def dev_worker_service(self) -> DevWorkerService:
        """Return the injected Dev worker service."""
        ...

    @property
    def qa_worker_service(self) -> QAWorkerService:
        """Return the injected QA worker service."""
        ...

    @property
    def queue_packet_reader(self) -> QueuePacketReader | None:
        """Return the injected queue packet reader when packet loading is supported."""
        ...

    @property
    def queue_packet_delivery_adapter(self) -> QueuePacketDeliveryAdapter | None:
        """Return the injected queue send and ack adapter when side effects are supported."""
        ...

    @property
    def logger(self) -> StructuredLogger:
        """Return the injected structured logger."""
        ...

    def handle_packet(self, request: QueuePacketRuntimeRequest) -> QueuePacketRuntimeResult:
        """Handle one supported queue packet request through one runtime dispatch pass."""
        ...

    def supports_packet_schema_type(self, packet_schema_type: str) -> bool:
        """Return whether the current slice supports one packet schema type."""
        ...


__all__ = [
    'DevWorkerService',
    'QAWorkerService',
    'QueuePacketDeliveryAdapter',
    'QueuePacketReader',
    'QueuePacketRuntimeController',
    'QueuePacketRuntimeRequest',
    'QueuePacketRuntimeResult',
    'StructuredLogger',
    'TechLeadWorkerService',
]

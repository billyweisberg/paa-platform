"""Contracts for the QA worker service."""

from __future__ import annotations

from typing import Protocol

from paa_core.services.implementation_plan_derivation.contracts import StructuredLogger
from paa_core.services.methodology_execution_projection import MethodologyExecutionProjectionService
from paa_core.services.methodology_execution_state import MethodologyExecutionStateService
from paa_core.runtime.packets.context_assembly import PacketContextAssemblyService

from .models import QAWorkerRequest, QAWorkerResult


class QAVerificationRunner(Protocol):
    """Execute one bounded QA worker verification run over assembled runtime context."""

    def run_qa_verification(self, context: object) -> object:
        """Return one structured raw verification result for the provided runtime context."""
        ...


class QAVerificationPacketAssembler(Protocol):
    """Normalize one QA verification result into qa-verification-packet-ready output."""

    def assemble_qa_verification_packet(self, verification_result: object) -> object:
        """Return one normalized qa-verification-packet-ready payload or summary."""
        ...


class QAWorkerService(Protocol):
    """Handle one bounded QA verification-packet execution slice."""

    @property
    def packet_context_assembly_service(self) -> PacketContextAssemblyService:
        """Return the injected packet-context assembly service."""
        ...

    @property
    def methodology_execution_state_service(self) -> MethodologyExecutionStateService:
        """Return the injected methodology-execution state service."""
        ...

    @property
    def methodology_execution_projection_service(self) -> MethodologyExecutionProjectionService:
        """Return the injected methodology-execution projection service."""
        ...

    @property
    def verification_runner(self) -> QAVerificationRunner:
        """Return the injected bounded QA verification runner."""
        ...

    @property
    def qa_verification_packet_assembler(self) -> QAVerificationPacketAssembler:
        """Return the injected QA verification packet assembler."""
        ...

    @property
    def logger(self) -> StructuredLogger:
        """Return the injected structured logger."""
        ...

    def handle_packet(self, request: QAWorkerRequest) -> QAWorkerResult:
        """Handle one supported QA-visible verification packet request."""
        ...

    def supports_packet_schema_type(self, packet_schema_type: str) -> bool:
        """Return whether the service slice supports one packet schema type."""
        ...


__all__ = [
    'MethodologyExecutionProjectionService',
    'MethodologyExecutionStateService',
    'PacketContextAssemblyService',
    'QAVerificationPacketAssembler',
    'QAVerificationRunner',
    'QAWorkerRequest',
    'QAWorkerResult',
    'QAWorkerService',
    'StructuredLogger',
]

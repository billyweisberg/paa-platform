"""Contracts for the Dev worker service."""

from __future__ import annotations

from typing import Protocol

from paa_core.services.implementation_plan_derivation.contracts import StructuredLogger
from paa_core.services.methodology_execution_projection import MethodologyExecutionProjectionService
from paa_core.services.methodology_execution_state import MethodologyExecutionStateService
from paa_core.services.packet_context_assembly import PacketContextAssemblyService

from .models import DevWorkerRequest, DevWorkerResult


class DevExecutionRunner(Protocol):
    """Execute one bounded Dev worker run over an assembled runtime context."""

    def run_dev_execution(self, context: object) -> object:
        """Return one structured raw execution result for the provided runtime context."""
        ...


class WorkerResultPacketAssembler(Protocol):
    """Normalize one Dev execution result into worker-result packet-ready output."""

    def assemble_worker_result_packet(self, execution_result: object) -> object:
        """Return one normalized worker-result packet-ready payload or summary."""
        ...


class DevWorkerService(Protocol):
    """Handle one bounded Dev assignment-packet execution slice."""

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
    def execution_runner(self) -> DevExecutionRunner:
        """Return the injected bounded Dev execution runner."""
        ...

    @property
    def worker_result_packet_assembler(self) -> WorkerResultPacketAssembler:
        """Return the injected worker-result packet assembler."""
        ...

    @property
    def logger(self) -> StructuredLogger:
        """Return the injected structured logger."""
        ...

    def handle_packet(self, request: DevWorkerRequest) -> DevWorkerResult:
        """Handle one supported Dev-visible assignment packet request."""
        ...

    def supports_packet_schema_type(self, packet_schema_type: str) -> bool:
        """Return whether the service slice supports one packet schema type."""
        ...


__all__ = [
    'DevExecutionRunner',
    'DevWorkerService',
    'DevWorkerRequest',
    'DevWorkerResult',
    'MethodologyExecutionProjectionService',
    'MethodologyExecutionStateService',
    'PacketContextAssemblyService',
    'StructuredLogger',
    'WorkerResultPacketAssembler',
]

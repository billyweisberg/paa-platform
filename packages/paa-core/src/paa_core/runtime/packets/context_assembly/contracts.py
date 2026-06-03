"""Contracts for the packet context assembly service."""

from __future__ import annotations

from typing import Protocol

from paa_core.repositories.methodology_execution import MethodologyExecutionRepository
from paa_core.runtime.packets.execution_package_resolution import ExecutionPackageResolutionService
from paa_core.services.implementation_plan_derivation.contracts import StructuredLogger
from paa_core.services.methodology_execution_projection import MethodologyExecutionProjectionService

from .models import PacketContextAssemblyRequest, PacketContextAssemblyResult


class PacketPayloadReader(Protocol):
    """Load packet payload content when the runtime host only has a packet path."""

    def read_packet_payload(self, packet_path: str) -> dict[str, object]:
        """Return one normalized packet payload mapping for the provided packet path."""
        ...


class PacketContextAssemblyService(Protocol):
    """Assemble one deterministic worker-runtime context package from thin packet inputs."""

    @property
    def methodology_execution_repository(self) -> MethodologyExecutionRepository:
        """Return the injected methodology-execution repository."""
        ...

    @property
    def methodology_execution_projection_service(self) -> MethodologyExecutionProjectionService:
        """Return the injected methodology-execution projection service."""
        ...

    @property
    def execution_package_resolution_service(self) -> ExecutionPackageResolutionService:
        """Return the injected execution-package resolution service."""
        ...

    @property
    def packet_payload_reader(self) -> PacketPayloadReader | None:
        """Return the injected packet payload reader when packet-path loading is supported."""
        ...

    @property
    def logger(self) -> StructuredLogger:
        """Return the injected structured logger."""
        ...

    def assemble_packet_context(
        self,
        request: PacketContextAssemblyRequest,
    ) -> PacketContextAssemblyResult:
        """Return one structured packet-context assembly result for the supported slice."""
        ...

    def supports_packet_context(self, packet_schema_type: str, runtime_surface: str) -> bool:
        """Return whether the current slice supports this packet schema and runtime surface."""
        ...


__all__ = [
    'ExecutionPackageResolutionService',
    'MethodologyExecutionProjectionService',
    'MethodologyExecutionRepository',
    'PacketContextAssemblyRequest',
    'PacketContextAssemblyResult',
    'PacketContextAssemblyService',
    'PacketPayloadReader',
    'StructuredLogger',
]

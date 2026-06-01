"""Models for the packet context assembly service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from paa_core.services.execution_package_resolution import ExecutionPackageResolutionView
from paa_core.services.methodology_execution_projection import MethodologyExecutionStatusProjection


@dataclass(frozen=True)
class PacketContextAssemblyRequest:
    packet_schema_type: str
    packet_message_id: str | None = None
    packet_path: str | None = None
    packet_payload: dict[str, Any] | None = None
    methodology_execution_id: str | None = None
    project_id: str | None = None
    work_item_id: str | None = None
    component_id: str | None = None
    runtime_surface: str = 'techlead'
    actor_name: str | None = None
    host_name: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class PacketContextGapSummary:
    gap_key: str
    gap_summary: str
    blocking: bool
    recommended_next_action: str | None
    notes: tuple[str, ...]


@dataclass(frozen=True)
class PacketContextAssemblySummary:
    packet_schema_type: str
    runtime_surface: str
    methodology_execution_id: str | None
    execution_package_id: str | None
    context_kind: str
    assembly_supported: bool
    required_capabilities: tuple[str, ...]
    resolved_capabilities: tuple[str, ...]
    blocking_gaps: tuple[str, ...]
    notes: tuple[str, ...]


@dataclass(frozen=True)
class PacketContextAssemblyResult:
    request: PacketContextAssemblyRequest
    methodology_execution_status: MethodologyExecutionStatusProjection | None
    execution_package_resolution: ExecutionPackageResolutionView | None
    packet_payload: dict[str, Any] | None
    assembly_summary: PacketContextAssemblySummary
    gaps: tuple[PacketContextGapSummary, ...]
    ok: bool
    reason: str | None = None
    details: str | None = None
    metadata: dict[str, Any] | None = None


__all__ = [
    'PacketContextAssemblyRequest',
    'PacketContextAssemblyGapSummary',
    'PacketContextAssemblyResult',
    'PacketContextAssemblySummary',
    'PacketContextGapSummary',
]

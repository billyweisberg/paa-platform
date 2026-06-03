"""Models for the Dev worker service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from paa_core.services.methodology_execution_projection import MethodologyExecutionStatusProjection
from paa_core.services.methodology_execution_state import MethodologyExecutionStateResult
from paa_core.runtime.packets.context_assembly import PacketContextAssemblyResult


@dataclass(frozen=True)
class DevWorkerRequest:
    packet_schema_type: str
    packet_message_id: str | None = None
    packet_path: str | None = None
    packet_payload: dict[str, Any] | None = None
    methodology_execution_id: str | None = None
    project_id: str | None = None
    work_item_id: str | None = None
    component_id: str | None = None
    runtime_mode: str = 'dry_run'
    actor_name: str | None = None
    host_name: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class DevWorkerExecutionSummary:
    handler_key: str
    packet_schema_type: str
    runtime_mode: str
    execution_supported: bool
    execution_runner_used: str | None
    packet_context_required: bool
    packet_context_ok: bool
    worker_result_packet_required: bool
    methodology_transition_required: bool
    blocking_reasons: tuple[str, ...]
    notes: tuple[str, ...]


@dataclass(frozen=True)
class DevWorkerResult:
    request: DevWorkerRequest
    methodology_execution_id: str | None
    current_execution_summary: MethodologyExecutionStatusProjection | None
    packet_context_result: PacketContextAssemblyResult | None
    execution_summary: DevWorkerExecutionSummary
    execution_result: object | None
    methodology_transition_result: MethodologyExecutionStateResult | None
    normalized_packet_output_summary: str | None
    ok: bool
    reason: str | None = None
    details: str | None = None
    dry_run: bool = True
    metadata: dict[str, Any] | None = None


__all__ = [
    'DevWorkerExecutionSummary',
    'DevWorkerRequest',
    'DevWorkerResult',
]

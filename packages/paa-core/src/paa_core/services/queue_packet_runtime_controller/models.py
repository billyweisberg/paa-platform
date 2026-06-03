"""Models for the queue packet runtime controller."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from paa_core.runtime.workers.dev_worker import DevWorkerResult
from paa_core.runtime.workers.qa_worker import QAWorkerResult
from paa_core.runtime.workers.techlead_worker import TechLeadWorkerResult


@dataclass(frozen=True)
class QueuePacketRuntimeRequest:
    queue_name: str
    packet_schema_type: str
    packet_message_id: str | None = None
    packet_path: str | None = None
    packet_payload: dict[str, Any] | None = None
    runtime_mode: str = 'dry_run'
    actor_name: str | None = None
    host_name: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class QueuePacketDispatchSummary:
    handler_key: str
    packet_schema_type: str
    target_worker_host: str | None
    dispatch_supported: bool
    queue_side_effect_required: bool
    ack_required: bool
    blocking_reasons: tuple[str, ...]
    notes: tuple[str, ...]


@dataclass(frozen=True)
class QueuePacketRuntimeResult:
    request: QueuePacketRuntimeRequest
    dispatch_summary: QueuePacketDispatchSummary
    selected_worker_result: TechLeadWorkerResult | DevWorkerResult | QAWorkerResult | None
    normalized_queue_side_effect_summary: str | None
    ok: bool
    reason: str | None = None
    details: str | None = None
    dry_run: bool = True
    metadata: dict[str, Any] | None = None


__all__ = [
    'QueuePacketDispatchSummary',
    'QueuePacketRuntimeRequest',
    'QueuePacketRuntimeResult',
]

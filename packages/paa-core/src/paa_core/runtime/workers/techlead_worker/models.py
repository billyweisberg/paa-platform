"""Models for the TechLead worker service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from paa_core.runtime.workflow.methodology_execution_projection import MethodologyExecutionStatusProjection
from paa_core.runtime.workflow.methodology_execution_state import MethodologyExecutionStateResult
from paa_core.services.techlead_assignment_decision import TechLeadAssignmentDecisionResult
from paa_core.services.techlead_worker_review_routing import TechLeadWorkerReviewRoutingResult


@dataclass(frozen=True)
class TechLeadWorkerRequest:
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
class TechLeadWorkerDispatchSummary:
    handler_key: str
    packet_schema_type: str
    decision_service_used: str | None
    decision_supported: bool
    recommended_next_action: str | None
    recommended_target_role: str | None
    packet_emission_required: bool
    methodology_transition_required: bool
    blocking_reasons: tuple[str, ...]
    notes: tuple[str, ...]


@dataclass(frozen=True)
class TechLeadWorkerResult:
    request: TechLeadWorkerRequest
    methodology_execution_id: str | None
    current_execution_summary: MethodologyExecutionStatusProjection | None
    dispatch_summary: TechLeadWorkerDispatchSummary
    worker_review_routing_result: TechLeadWorkerReviewRoutingResult | None
    assignment_decision_result: TechLeadAssignmentDecisionResult | None
    methodology_transition_result: MethodologyExecutionStateResult | None
    normalized_packet_output_summary: str | None
    ok: bool
    reason: str | None = None
    details: str | None = None
    dry_run: bool = True
    metadata: dict[str, Any] | None = None


__all__ = [
    'TechLeadWorkerDispatchSummary',
    'TechLeadWorkerRequest',
    'TechLeadWorkerResult',
]

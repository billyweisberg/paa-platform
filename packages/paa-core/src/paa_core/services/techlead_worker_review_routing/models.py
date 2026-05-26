"""Models for the TechLead worker review routing service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from paa_core.services.workflow_lifecycle.models import WorkflowLifecycleResult


@dataclass(frozen=True)
class TechLeadWorkerReviewRoutingRequest:
    project_slug: str
    issue_number: int
    pr_number: int | None = None
    workflow_stage: str = ''
    worker_role: str = ''
    worker_result_type: str = ''
    source_packet_schema_type: str | None = None
    source_packet_message_id: str | None = None
    workflow_lifecycle_result: WorkflowLifecycleResult | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class TechLeadWorkerReviewRoutingSummary:
    decision_supported: bool
    recommended_next_decision: str | None
    recommended_target_role: str | None
    qa_assignment_allowed: bool
    review_summary: str
    blocking_reasons: tuple[str, ...]
    notes: tuple[str, ...]


@dataclass(frozen=True)
class TechLeadWorkerReviewRoutingResult:
    project_slug: str
    issue_number: int
    pr_number: int | None
    workflow_stage: str
    worker_role: str
    worker_result_type: str
    source_packet_schema_type: str | None
    source_packet_message_id: str | None
    summary: TechLeadWorkerReviewRoutingSummary
    ok: bool
    reason: str | None = None
    details: str | None = None
    recommended_actions: tuple[str, ...] | None = None
    unattended_safe: bool | None = None
    metadata: dict[str, Any] | None = None


__all__ = [
    'TechLeadWorkerReviewRoutingRequest',
    'TechLeadWorkerReviewRoutingResult',
    'TechLeadWorkerReviewRoutingSummary',
]

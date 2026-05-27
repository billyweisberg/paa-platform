"""Models for the TechLead delivery review decision service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TechLeadDeliveryReviewDecisionRequest:
    project_slug: str
    issue_number: int
    issue_url: str | None = None
    pr_number: int | None = None
    pr_url: str | None = None
    workflow_stage: str = ''
    delivery_review_result_type: str = ''
    recommended_action_name: str | None = None
    recommended_target_role: str | None = None
    recommended_reason: str | None = None
    resolved_team_worker_key: str | None = None
    resolved_team_worker_display_name: str | None = None
    source_packet_schema_type: str | None = None
    source_packet_message_id: str | None = None
    source_packet_path: str | None = None
    branch_name: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class TechLeadDeliveryReviewDecisionSummary:
    decision_supported: bool
    recommended_next_decision: str | None
    recommended_target_role: str | None
    assignment_allowed: bool
    delivery_review_summary: str
    blocking_reasons: tuple[str, ...]
    notes: tuple[str, ...]


@dataclass(frozen=True)
class TechLeadDeliveryReviewDecisionResult:
    project_slug: str
    issue_number: int
    issue_url: str | None
    pr_number: int | None
    pr_url: str | None
    workflow_stage: str
    delivery_review_result_type: str
    recommended_action_name: str | None
    recommended_target_role: str | None
    resolved_team_worker_key: str | None
    resolved_team_worker_display_name: str | None
    source_packet_schema_type: str | None
    source_packet_message_id: str | None
    source_packet_path: str | None
    branch_name: str | None
    summary: TechLeadDeliveryReviewDecisionSummary
    ok: bool
    reason: str | None = None
    details: str | None = None
    recommended_actions: tuple[str, ...] | None = None
    unattended_safe: bool | None = None
    metadata: dict[str, Any] | None = None


__all__ = [
    'TechLeadDeliveryReviewDecisionRequest',
    'TechLeadDeliveryReviewDecisionResult',
    'TechLeadDeliveryReviewDecisionSummary',
]

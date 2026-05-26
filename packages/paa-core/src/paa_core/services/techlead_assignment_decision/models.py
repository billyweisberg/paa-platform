"""Models for the TechLead assignment decision service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from paa_core.services.workflow_lifecycle.models import WorkflowLifecycleResult


@dataclass(frozen=True)
class TechLeadAssignmentDecisionRequest:
    project_slug: str
    issue_number: int
    issue_url: str | None = None
    pr_number: int | None = None
    pr_url: str | None = None
    branch_name: str | None = None
    workflow_stage: str = ''
    source_packet_schema_type: str | None = None
    source_packet_message_id: str | None = None
    source_packet_queue_name: str | None = None
    source_packet_path: str | None = None
    explicit_target_role: str | None = None
    workflow_lifecycle_result: WorkflowLifecycleResult | None = None
    recommended_actions: tuple[str, ...] | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class TechLeadAssignmentDecisionSummary:
    decision_supported: bool
    target_role: str | None
    target_role_cli: str | None
    assignment_type: str | None
    allowed_result_types: tuple[str, ...]
    assignment_summary: str
    decision_reason: str
    blocking_reasons: tuple[str, ...]
    notes: tuple[str, ...]


@dataclass(frozen=True)
class TechLeadAssignmentDecisionResult:
    project_slug: str
    issue_number: int
    issue_url: str | None
    pr_number: int | None
    pr_url: str | None
    branch_name: str | None
    workflow_stage: str
    source_packet_schema_type: str | None
    source_packet_message_id: str | None
    source_packet_queue_name: str | None
    source_packet_path: str | None
    summary: TechLeadAssignmentDecisionSummary
    ok: bool
    reason: str | None = None
    details: str | None = None
    recommended_actions: tuple[str, ...] | None = None
    unattended_safe: bool | None = None
    metadata: dict[str, Any] | None = None


__all__ = [
    'TechLeadAssignmentDecisionRequest',
    'TechLeadAssignmentDecisionResult',
    'TechLeadAssignmentDecisionSummary',
]

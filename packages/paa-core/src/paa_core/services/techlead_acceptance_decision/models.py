"""Models for the TechLead acceptance decision service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from paa_core.runtime.workflow.workflow_lifecycle.models import WorkflowLifecycleResult


@dataclass(frozen=True)
class TechLeadAcceptanceDecisionRequest:
    project_slug: str
    issue_number: int
    pr_number: int | None = None
    workflow_stage: str = ''
    qa_result_type: str = ''
    source_packet_schema_type: str | None = None
    source_packet_message_id: str | None = None
    workflow_lifecycle_result: WorkflowLifecycleResult | None = None
    merge_state: dict[str, Any] | None = None
    acceptance_event_state: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class TechLeadAcceptanceDecisionSummary:
    decision_supported: bool
    recommended_next_decision: str | None
    acceptance_allowed: bool
    closeout_allowed: bool
    decision_summary: str
    blocking_reasons: tuple[str, ...]
    notes: tuple[str, ...]


@dataclass(frozen=True)
class TechLeadAcceptanceDecisionResult:
    project_slug: str
    issue_number: int
    pr_number: int | None
    workflow_stage: str
    qa_result_type: str
    source_packet_schema_type: str | None
    source_packet_message_id: str | None
    summary: TechLeadAcceptanceDecisionSummary
    ok: bool
    reason: str | None = None
    details: str | None = None
    recommended_actions: tuple[str, ...] | None = None
    unattended_safe: bool | None = None
    metadata: dict[str, Any] | None = None


__all__ = [
    'TechLeadAcceptanceDecisionRequest',
    'TechLeadAcceptanceDecisionResult',
    'TechLeadAcceptanceDecisionSummary',
]

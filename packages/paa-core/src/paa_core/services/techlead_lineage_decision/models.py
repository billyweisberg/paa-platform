"""Models for the TechLead lineage decision service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TechLeadLineageDecisionRequest:
    project_slug: str
    issue_number: int
    issue_url: str | None = None
    pr_number: int | None = None
    pr_url: str | None = None
    workflow_stage: str = ''
    lineage_state: str = ''
    superseded_escalation_type: str | None = None
    superseded_escalation_summary: str | None = None
    superseded_escalation_details: dict[str, Any] | None = None
    source_packet_schema_type: str | None = None
    source_packet_message_id: str | None = None
    source_packet_path: str | None = None
    branch_name: str | None = None
    superseded_branch: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class TechLeadLineageDecisionSummary:
    decision_supported: bool
    recommended_next_decision: str | None
    recommended_target_role: str | None
    supersede_allowed: bool
    lineage_decision_summary: str
    blocking_reasons: tuple[str, ...]
    notes: tuple[str, ...]


@dataclass(frozen=True)
class TechLeadLineageDecisionResult:
    project_slug: str
    issue_number: int
    issue_url: str | None
    pr_number: int | None
    pr_url: str | None
    workflow_stage: str
    lineage_state: str
    superseded_escalation_type: str | None
    source_packet_schema_type: str | None
    source_packet_message_id: str | None
    source_packet_path: str | None
    branch_name: str | None
    superseded_branch: str | None
    summary: TechLeadLineageDecisionSummary
    ok: bool
    reason: str | None = None
    details: str | None = None
    recommended_actions: tuple[str, ...] | None = None
    unattended_safe: bool | None = None
    metadata: dict[str, Any] | None = None


__all__ = [
    'TechLeadLineageDecisionRequest',
    'TechLeadLineageDecisionResult',
    'TechLeadLineageDecisionSummary',
]

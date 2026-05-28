"""Models for the TechLead closeout decision service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TechLeadCloseoutDecisionRequest:
    project_slug: str
    issue_number: int
    issue_url: str | None = None
    pr_number: int | None = None
    pr_url: str | None = None
    workflow_stage: str = ''
    decision_type: str = ''
    proof_only_mode: bool = False
    source_packet_schema_type: str | None = None
    source_packet_message_id: str | None = None
    source_packet_path: str | None = None
    branch_name: str | None = None
    canonical_branch: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class TechLeadCloseoutDecisionSummary:
    decision_supported: bool
    recommended_next_decision: str | None
    recommended_target_role: str | None
    closeout_allowed: bool
    closeout_decision_summary: str
    blocking_reasons: tuple[str, ...]
    notes: tuple[str, ...]


@dataclass(frozen=True)
class TechLeadCloseoutDecisionResult:
    project_slug: str
    issue_number: int
    issue_url: str | None
    pr_number: int | None
    pr_url: str | None
    workflow_stage: str
    decision_type: str
    source_packet_schema_type: str | None
    source_packet_message_id: str | None
    source_packet_path: str | None
    branch_name: str | None
    canonical_branch: str | None
    summary: TechLeadCloseoutDecisionSummary
    ok: bool
    reason: str | None = None
    details: str | None = None
    recommended_actions: tuple[str, ...] | None = None
    unattended_safe: bool | None = None
    metadata: dict[str, Any] | None = None


__all__ = [
    'TechLeadCloseoutDecisionRequest',
    'TechLeadCloseoutDecisionResult',
    'TechLeadCloseoutDecisionSummary',
]

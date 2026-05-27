"""Models for the TechLead reset recovery decision service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TechLeadResetRecoveryDecisionRequest:
    project_slug: str
    issue_number: int
    issue_url: str | None = None
    pr_number: int | None = None
    pr_url: str | None = None
    workflow_stage: str = ''
    lineage_state: str = ''
    reset_escalation_type: str | None = None
    reset_escalation_summary: str | None = None
    reset_escalation_details: dict[str, Any] | None = None
    source_packet_schema_type: str | None = None
    source_packet_message_id: str | None = None
    source_packet_path: str | None = None
    branch_name: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class TechLeadResetRecoveryDecisionSummary:
    decision_supported: bool
    recommended_next_decision: str | None
    recommended_target_role: str | None
    reset_allowed: bool
    reset_recovery_summary: str
    blocking_reasons: tuple[str, ...]
    notes: tuple[str, ...]


@dataclass(frozen=True)
class TechLeadResetRecoveryDecisionResult:
    project_slug: str
    issue_number: int
    issue_url: str | None
    pr_number: int | None
    pr_url: str | None
    workflow_stage: str
    lineage_state: str
    reset_escalation_type: str | None
    source_packet_schema_type: str | None
    source_packet_message_id: str | None
    source_packet_path: str | None
    branch_name: str | None
    summary: TechLeadResetRecoveryDecisionSummary
    ok: bool
    reason: str | None = None
    details: str | None = None
    recommended_actions: tuple[str, ...] | None = None
    unattended_safe: bool | None = None
    metadata: dict[str, Any] | None = None


__all__ = [
    'TechLeadResetRecoveryDecisionRequest',
    'TechLeadResetRecoveryDecisionResult',
    'TechLeadResetRecoveryDecisionSummary',
]

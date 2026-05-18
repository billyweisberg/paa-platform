"""Models for the workflow lifecycle service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class WorkflowLifecycleRequest:
    project_id: str
    work_item_id: str
    workflow_state_id: str | None = None
    requested_transition_type: str | None = None
    requested_from_stage: str | None = None
    requested_to_stage: str | None = None
    source_queue_message_id: str | None = None
    source_message_id_external: str | None = None
    source_packet_schema_type: str | None = None
    automation_run_id: str | None = None
    execution_surface_key: str | None = None
    repo_root_path: str | None = None
    runtime_root_path: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class WorkflowLifecycleStateView:
    workflow_state_id: str
    project_id: str
    work_item_id: str
    workflow_stage: str
    current_owner_role_id: str | None
    lineage_state: str
    terminal_decision: str
    state_consistency: str
    blocking_reason_code: str | None
    blocking_reason_text: str | None
    current_issue_number: int | None
    current_pr_number: int | None
    canonical_branch: str | None
    active_role_branch: str | None
    active_handoff_id: str | None
    active_queue_message_id: str | None
    active_message_id_external: str | None
    active_queue_claim_id: str | None
    closed_at: str | None
    metadata: dict[str, Any]


@dataclass(frozen=True)
class WorkflowLifecycleDecisionSummary:
    transition_allowed: bool
    acceptance_allowed: bool
    requires_manual_repair: bool
    should_reset: bool
    should_retry: bool
    blocking_reasons: tuple[str, ...]
    notes: tuple[str, ...]
    metadata: dict[str, Any]


@dataclass(frozen=True)
class WorkflowLifecycleResult:
    project_id: str
    work_item_id: str
    requested_transition_type: str | None
    applied: bool
    state_view: WorkflowLifecycleStateView | None
    decision_summary: WorkflowLifecycleDecisionSummary
    resolved_execution_surface_key: str | None
    recommended_next_action: str | None
    metadata: dict[str, Any]


__all__ = [
    'WorkflowLifecycleDecisionSummary',
    'WorkflowLifecycleRequest',
    'WorkflowLifecycleResult',
    'WorkflowLifecycleStateView',
]

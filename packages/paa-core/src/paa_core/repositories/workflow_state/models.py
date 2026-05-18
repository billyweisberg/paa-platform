"""DTOs for workflow-state repository records."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class WorkflowStateRecord:
    workflow_state_id: str
    project_id: str
    work_item_id: str
    authority_version_id: str | None
    design_package_id: str | None
    coder_run_brief_id: str | None
    workflow_stage: str
    current_owner_role_id: str | None
    lineage_state: str
    blocking_reason_code: str | None
    blocking_reason_text: str | None
    terminal_decision: str
    state_consistency: str
    current_issue_number: int | None
    current_pr_number: int | None
    canonical_branch: str | None
    active_role_branch: str | None
    active_handoff_id: str | None
    active_queue_message_id: str | None
    active_message_id_external: str | None
    active_assignment_role_id: str | None
    active_result_role_id: str | None
    active_queue_claim_id: str | None
    state_entered_at: str | None
    last_transition_at: str | None
    closed_at: str | None
    metadata: dict[str, Any]
    created_at: str | None
    updated_at: str | None


@dataclass(frozen=True)
class WorkflowTransitionRecord:
    workflow_transition_id: str
    workflow_state_id: str
    project_id: str
    work_item_id: str
    transition_type: str
    transition_status: str
    from_workflow_stage: str | None
    to_workflow_stage: str | None
    from_owner_role_id: str | None
    to_owner_role_id: str | None
    reason_code: str | None
    reason_text: str | None
    source_handoff_id: str | None
    source_queue_message_id: str | None
    source_queue_claim_id: str | None
    source_message_id_external: str | None
    source_packet_schema_type: str | None
    source_role_id: str | None
    source_transition_input_id: str | None
    result_handoff_id: str | None
    result_queue_message_id: str | None
    result_queue_claim_id: str | None
    result_message_id_external: str | None
    result_packet_schema_type: str | None
    result_role_id: str | None
    performed_by_role_id: str | None
    performed_by_agent_id: str | None
    automation_run_id: str | None
    error_code: str | None
    error_details: str | None
    transition_requested_at: str | None
    transition_applied_at: str | None
    metadata: dict[str, Any]
    created_at: str | None


@dataclass(frozen=True)
class QueueClaimRecord:
    queue_claim_id: str
    queue_message_id: str
    handoff_id: str | None
    project_id: str
    work_item_id: str
    claimed_by_role_id: str | None
    claimed_by_agent_id: str | None
    claim_attempt_source: str
    claim_status: str
    ack_outcome: str
    release_reason_code: str | None
    release_reason_text: str | None
    claimed_at: str | None
    lease_expires_at: str | None
    released_at: str | None
    acked_at: str | None
    metadata: dict[str, Any]
    created_at: str | None


@dataclass(frozen=True)
class WorkflowStateUpsertSpec:
    project_id: str
    work_item_id: str
    workflow_stage: str
    lineage_state: str
    current_owner_role_id: str | None = None
    authority_version_id: str | None = None
    design_package_id: str | None = None
    coder_run_brief_id: str | None = None
    blocking_reason_code: str | None = None
    blocking_reason_text: str | None = None
    terminal_decision: str = 'none'
    state_consistency: str = 'consistent'
    current_issue_number: int | None = None
    current_pr_number: int | None = None
    canonical_branch: str | None = None
    active_role_branch: str | None = None
    active_handoff_id: str | None = None
    active_queue_message_id: str | None = None
    active_message_id_external: str | None = None
    active_assignment_role_id: str | None = None
    active_result_role_id: str | None = None
    active_queue_claim_id: str | None = None
    state_entered_at: str | None = None
    last_transition_at: str | None = None
    closed_at: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class WorkflowTransitionAppendSpec:
    workflow_state_id: str
    project_id: str
    work_item_id: str
    transition_type: str
    transition_status: str
    from_workflow_stage: str | None = None
    to_workflow_stage: str | None = None
    from_owner_role_id: str | None = None
    to_owner_role_id: str | None = None
    reason_code: str | None = None
    reason_text: str | None = None
    source_handoff_id: str | None = None
    source_queue_message_id: str | None = None
    source_queue_claim_id: str | None = None
    source_message_id_external: str | None = None
    source_packet_schema_type: str | None = None
    source_role_id: str | None = None
    source_transition_input_id: str | None = None
    result_handoff_id: str | None = None
    result_queue_message_id: str | None = None
    result_queue_claim_id: str | None = None
    result_message_id_external: str | None = None
    result_packet_schema_type: str | None = None
    result_role_id: str | None = None
    performed_by_role_id: str | None = None
    performed_by_agent_id: str | None = None
    automation_run_id: str | None = None
    error_code: str | None = None
    error_details: str | None = None
    transition_requested_at: str | None = None
    transition_applied_at: str | None = None
    metadata: dict[str, Any] | None = None


__all__ = [
    'QueueClaimRecord',
    'WorkflowStateRecord',
    'WorkflowStateUpsertSpec',
    'WorkflowTransitionAppendSpec',
    'WorkflowTransitionRecord',
]

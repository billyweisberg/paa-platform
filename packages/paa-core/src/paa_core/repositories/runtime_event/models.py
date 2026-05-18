"""DTOs for runtime-event repository records."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class HandoffRecord:
    handoff_id: str
    project_id: str
    work_item_id: str
    from_role_id: str
    to_role_id: str
    handoff_type: str
    status: str
    created_at: str | None
    claimed_at: str | None
    acknowledged_at: str | None
    closed_at: str | None
    notes: str | None


@dataclass(frozen=True)
class QueueMessageRecord:
    queue_message_id: str
    handoff_id: str
    queue_name: str
    schema_type: str
    message_id_external: str | None
    correlation_key: str | None
    payload: dict[str, Any]
    status: str
    sent_at: str | None
    claimed_at: str | None
    acknowledged_at: str | None
    metadata: dict[str, Any]
    created_at: str | None
    updated_at: str | None


@dataclass(frozen=True)
class AutomationRunRecord:
    automation_run_id: str
    agent_id: str
    work_item_id: str | None
    handoff_id: str | None
    trigger_type: str | None
    status: str
    started_at: str | None
    finished_at: str | None
    summary: str | None
    artifacts: dict[str, Any]
    created_at: str | None
    updated_at: str | None


@dataclass(frozen=True)
class TransitionInputRecord:
    transition_input_id: str
    project_id: str
    work_item_id: str
    workflow_state_id: str | None
    workflow_transition_id: str | None
    automation_run_id: str | None
    input_type: str
    input_schema_type: str | None
    input_source_surface: str
    input_key: str | None
    input_hash: str | None
    source_queue_message_id: str | None
    source_handoff_id: str | None
    source_message_id_external: str | None
    source_report_path: str | None
    payload: dict[str, Any]
    content_summary: dict[str, Any]
    schema_version: str | None
    captured_at: str | None
    metadata: dict[str, Any]
    created_at: str | None


@dataclass(frozen=True)
class AutomationRunEventRecord:
    automation_run_event_id: str
    automation_run_id: str
    project_id: str
    work_item_id: str | None
    workflow_state_id: str | None
    workflow_transition_id: str | None
    event_type: str
    event_status: str
    event_phase: str
    event_reason_code: str | None
    event_reason_text: str | None
    role_id: str | None
    agent_id: str | None
    handoff_id: str | None
    queue_message_id: str | None
    queue_claim_id: str | None
    message_id_external: str | None
    event_summary: dict[str, Any]
    evidence_ref: str | None
    raw_log_pointer: str | None
    event_recorded_at: str | None
    metadata: dict[str, Any]
    created_at: str | None


@dataclass(frozen=True)
class AcceptanceEventRecord:
    acceptance_event_id: str
    project_id: str
    work_item_id: str
    handoff_id: str | None
    accepted_by_agent_id: str | None
    accepted_by_role_id: str | None
    decision: str
    notes: str | None
    merge_commit_sha: str | None
    metadata: dict[str, Any]
    created_at: str | None


__all__ = [
    'AcceptanceEventRecord',
    'AutomationRunEventRecord',
    'AutomationRunRecord',
    'HandoffRecord',
    'QueueMessageRecord',
    'TransitionInputRecord',
]

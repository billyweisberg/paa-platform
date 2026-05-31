"""DTOs for MethodologyExecution repository records."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MethodologyExecutionRecord:
    methodology_execution_id: str
    project_id: str
    work_item_id: str | None
    lane: str
    stage: str
    step: str
    status: str
    current_owner_role: str
    next_action_key: str | None
    blocked_reason: str | None
    component_id: str | None
    design_package_id: str | None
    implementation_plan_id: str | None
    coder_run_brief_id: str | None
    packet_id: str | None
    workflow_state_id: str | None
    active_authority_ref: str | None
    active_artifact_ref: str | None
    metadata: dict[str, Any]
    created_at: str | None
    updated_at: str | None


@dataclass(frozen=True)
class MethodologyExecutionEventRecord:
    methodology_execution_event_id: str
    methodology_execution_id: str
    from_lane: str | None
    to_lane: str
    from_stage: str | None
    to_stage: str
    from_step: str | None
    to_step: str
    from_status: str | None
    to_status: str
    transition_kind: str
    actor_role_id: str | None
    actor_name: str | None
    notes: str | None
    evidence: dict[str, Any]
    created_at: str | None


@dataclass(frozen=True)
class MethodologyExecutionBindingRecord:
    methodology_execution_binding_id: str
    methodology_execution_id: str
    binding_kind: str
    bound_record_id: str | None
    bound_record_key: str | None
    bound_record_ref: str | None
    is_primary: bool
    notes: str | None
    metadata: dict[str, Any]
    created_at: str | None
    updated_at: str | None


@dataclass(frozen=True)
class MethodologyExecutionProjectionInputRecord:
    execution: MethodologyExecutionRecord
    events: tuple[MethodologyExecutionEventRecord, ...]
    bindings: tuple[MethodologyExecutionBindingRecord, ...]
    related_records: dict[str, Any]


@dataclass(frozen=True)
class MethodologyExecutionUpsertSpec:
    methodology_execution_id: str
    project_id: str
    lane: str
    stage: str
    step: str
    status: str
    current_owner_role: str
    work_item_id: str | None = None
    next_action_key: str | None = None
    blocked_reason: str | None = None
    component_id: str | None = None
    design_package_id: str | None = None
    implementation_plan_id: str | None = None
    coder_run_brief_id: str | None = None
    packet_id: str | None = None
    workflow_state_id: str | None = None
    active_authority_ref: str | None = None
    active_artifact_ref: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class MethodologyExecutionEventAppendSpec:
    methodology_execution_id: str
    to_lane: str
    to_stage: str
    to_step: str
    to_status: str
    transition_kind: str
    from_lane: str | None = None
    from_stage: str | None = None
    from_step: str | None = None
    from_status: str | None = None
    actor_role_id: str | None = None
    actor_name: str | None = None
    notes: str | None = None
    evidence: dict[str, Any] | None = None


@dataclass(frozen=True)
class MethodologyExecutionBindingEntrySpec:
    binding_kind: str
    bound_record_id: str | None = None
    bound_record_key: str | None = None
    bound_record_ref: str | None = None
    is_primary: bool = False
    notes: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class MethodologyExecutionBindingReplaceSpec:
    methodology_execution_id: str
    bindings: tuple[MethodologyExecutionBindingEntrySpec, ...]
    replace_scope: str = 'replace_all'


__all__ = [
    'MethodologyExecutionBindingEntrySpec',
    'MethodologyExecutionBindingRecord',
    'MethodologyExecutionBindingReplaceSpec',
    'MethodologyExecutionEventAppendSpec',
    'MethodologyExecutionEventRecord',
    'MethodologyExecutionProjectionInputRecord',
    'MethodologyExecutionRecord',
    'MethodologyExecutionUpsertSpec',
]

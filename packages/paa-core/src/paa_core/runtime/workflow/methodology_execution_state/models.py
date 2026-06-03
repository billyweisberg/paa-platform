"""Models for the methodology execution state service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from paa_core.repositories.methodology_execution import MethodologyExecutionBindingEntrySpec


@dataclass(frozen=True)
class MethodologyExecutionStateRequest:
    methodology_execution_id: str | None = None
    project_id: str | None = None
    work_item_id: str | None = None
    component_id: str | None = None
    transition_key: str | None = None
    to_lane: str | None = None
    to_stage: str | None = None
    to_step: str | None = None
    to_status: str | None = None
    actor_role_id: str | None = None
    actor_name: str | None = None
    notes: str | None = None
    evidence: dict[str, Any] | None = None
    binding_entries: tuple[MethodologyExecutionBindingEntrySpec, ...] = ()
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class MethodologyExecutionStateSummary:
    methodology_execution_id: str
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
    binding_refs: tuple[str, ...]
    notes: tuple[str, ...]
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class MethodologyExecutionTransitionSummary:
    transition_key: str
    transition_kind: str
    from_lane: str | None
    to_lane: str
    from_stage: str | None
    to_stage: str
    from_step: str | None
    to_step: str
    from_status: str | None
    to_status: str
    current_owner_role: str | None
    next_owner_role: str | None
    prerequisites_satisfied: bool
    blocking_reasons: tuple[str, ...]
    recommended_next_action: str | None = None


@dataclass(frozen=True)
class MethodologyExecutionStateResult:
    methodology_execution_id: str | None
    request: MethodologyExecutionStateRequest
    current_state: MethodologyExecutionStateSummary | None
    transition: MethodologyExecutionTransitionSummary | None
    ok: bool
    reason: str | None = None
    details: str | None = None
    binding_update_applied: bool | None = None
    metadata: dict[str, Any] | None = None


__all__ = [
    'MethodologyExecutionStateRequest',
    'MethodologyExecutionStateResult',
    'MethodologyExecutionStateSummary',
    'MethodologyExecutionTransitionSummary',
]

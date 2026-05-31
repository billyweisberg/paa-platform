"""Models for the methodology execution projection service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MethodologyExecutionProjectionRequest:
    methodology_execution_id: str | None = None
    project_id: str | None = None
    work_item_id: str | None = None
    component_id: str | None = None
    projection_mode: str | None = None
    actor_role_id: str | None = None
    actor_name: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class MethodologyExecutionStatusProjection:
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
    summary_text: str
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class MethodologyExecutionNextActionProjection:
    methodology_execution_id: str
    recommended_next_action_key: str | None
    recommended_owner_role: str | None
    lane: str
    stage: str
    step: str
    prerequisite_summary: tuple[str, ...]
    blocked_reason: str | None
    component_id: str | None
    implementation_plan_id: str | None
    packet_id: str | None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class MethodologyExecutionExplainProjection:
    methodology_execution_id: str
    lane: str
    stage: str
    step: str
    status: str
    current_owner_role: str
    explanation_summary: str
    transition_context: str | None
    binding_refs: tuple[str, ...]
    blocked_reason: str | None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class MethodologyExecutionProjectionResult:
    methodology_execution_id: str | None
    request: MethodologyExecutionProjectionRequest
    status_projection: MethodologyExecutionStatusProjection | None
    next_action_projection: MethodologyExecutionNextActionProjection | None
    explain_projection: MethodologyExecutionExplainProjection | None
    ok: bool
    reason: str | None = None
    details: str | None = None
    metadata: dict[str, Any] | None = None


__all__ = [
    'MethodologyExecutionExplainProjection',
    'MethodologyExecutionNextActionProjection',
    'MethodologyExecutionProjectionRequest',
    'MethodologyExecutionProjectionResult',
    'MethodologyExecutionStatusProjection',
]

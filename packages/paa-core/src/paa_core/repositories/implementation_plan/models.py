"""DTOs for ImplementationPlan repository records."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ImplementationPlanRecord:
    implementation_plan_id: str
    project_id: str
    work_item_id: str | None
    design_package_id: str
    spec_fragment_id: str | None
    implementation_target_id: str | None
    authority_version_id: str | None
    primary_component_id: str | None
    plan_id_external: str
    schema_version: str
    consumer_context_key: str
    plan_title: str
    plan_kind: str
    status: str
    authority_state: str
    authority_state_updated_at: str | None
    plan: dict[str, Any]
    build_sequence: dict[str, Any]
    touch_surfaces: dict[str, Any]
    protected_constraints: dict[str, Any]
    verification_plan: dict[str, Any]
    provenance: dict[str, Any]
    metadata: dict[str, Any]
    created_by_role_id: str | None
    created_by_agent_id: str | None
    approved_at: str | None
    activated_at: str | None
    completed_at: str | None
    created_at: str | None
    updated_at: str | None


@dataclass(frozen=True)
class ImplementationPlanActivityRecord:
    implementation_plan_activity_id: str
    implementation_plan_id: str
    component_element_id: str | None
    component_element_realization_id: str | None
    assigned_role_id: str | None
    activity_key: str
    activity_title: str
    activity_kind: str
    activity_state: str
    sequence_order: int
    target_path: str | None
    target_module: str | None
    planned_artifact_type_key: str | None
    blocking_reason: str | None
    metadata: dict[str, Any]
    started_at: str | None
    completed_at: str | None
    created_at: str | None
    updated_at: str | None


@dataclass(frozen=True)
class ImplementationPlanActivityDependencyRecord:
    implementation_plan_activity_dependency_id: str
    implementation_plan_id: str
    predecessor_activity_id: str
    predecessor_activity_key: str
    successor_activity_id: str
    successor_activity_key: str
    sequencing_requirement: str
    dependency_strength: str
    notes: str | None
    metadata: dict[str, Any]
    created_at: str | None


@dataclass(frozen=True)
class ImplementationPlanVerificationSurfaceRecord:
    implementation_plan_verification_surface_id: str
    implementation_plan_id: str
    implementation_plan_activity_id: str | None
    verification_obligation_id: str | None
    surface_kind: str
    surface_ref: str
    required: bool
    sequence_order: int
    status: str
    metadata: dict[str, Any]
    created_at: str | None
    updated_at: str | None


@dataclass(frozen=True)
class ImplementationPlanAuthorityEventRecord:
    implementation_plan_authority_event_id: str
    project_id: str
    work_item_id: str | None
    implementation_plan_id: str
    from_state: str | None
    to_state: str
    transition_kind: str
    actor_role_id: str | None
    actor_name: str | None
    notes: str | None
    evidence: dict[str, Any]
    created_at: str | None


@dataclass(frozen=True)
class ImplementationPlanUpsertSpec:
    project_id: str
    design_package_id: str
    plan_id_external: str
    consumer_context_key: str
    plan_title: str
    plan_kind: str
    status: str = 'draft'
    authority_state: str = 'draft_plan'
    work_item_id: str | None = None
    spec_fragment_id: str | None = None
    implementation_target_id: str | None = None
    authority_version_id: str | None = None
    primary_component_id: str | None = None
    schema_version: str = '1.0'
    plan: dict[str, Any] | None = None
    build_sequence: dict[str, Any] | None = None
    touch_surfaces: dict[str, Any] | None = None
    protected_constraints: dict[str, Any] | None = None
    verification_plan: dict[str, Any] | None = None
    provenance: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    created_by_role_id: str | None = None
    created_by_agent_id: str | None = None
    approved_at: str | None = None
    activated_at: str | None = None
    completed_at: str | None = None


@dataclass(frozen=True)
class ImplementationPlanActivityUpsertSpec:
    implementation_plan_id: str
    activity_key: str
    activity_title: str
    activity_kind: str
    activity_state: str = 'planned'
    sequence_order: int = 0
    component_element_id: str | None = None
    component_element_realization_id: str | None = None
    assigned_role_id: str | None = None
    target_path: str | None = None
    target_module: str | None = None
    planned_artifact_type_key: str | None = None
    blocking_reason: str | None = None
    metadata: dict[str, Any] | None = None
    started_at: str | None = None
    completed_at: str | None = None


@dataclass(frozen=True)
class ImplementationPlanActivityDependencyUpsertSpec:
    implementation_plan_id: str
    predecessor_activity_key: str
    successor_activity_key: str
    sequencing_requirement: str = 'hard'
    dependency_strength: str = 'required'
    notes: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class ImplementationPlanProgressUpdateSpec:
    implementation_plan_id: str
    component_completion: dict[str, Any]
    authority_state: str | None = None
    status: str | None = None
    completed_at: str | None = None


@dataclass(frozen=True)
class ImplementationPlanActivityStateUpdateSpec:
    implementation_plan_id: str
    activity_key: str
    activity_state: str
    blocking_reason: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class ImplementationPlanAuthorityEventAppendSpec:
    project_id: str
    implementation_plan_id: str
    to_state: str
    transition_kind: str
    work_item_id: str | None = None
    from_state: str | None = None
    actor_role_id: str | None = None
    actor_name: str | None = None
    notes: str | None = None
    evidence: dict[str, Any] | None = None


__all__ = [
    'ImplementationPlanActivityStateUpdateSpec',
    'ImplementationPlanAuthorityEventAppendSpec',
    'ImplementationPlanAuthorityEventRecord',
    'ImplementationPlanActivityDependencyRecord',
    'ImplementationPlanActivityDependencyUpsertSpec',
    'ImplementationPlanActivityRecord',
    'ImplementationPlanActivityUpsertSpec',
    'ImplementationPlanProgressUpdateSpec',
    'ImplementationPlanRecord',
    'ImplementationPlanUpsertSpec',
    'ImplementationPlanVerificationSurfaceRecord',
]

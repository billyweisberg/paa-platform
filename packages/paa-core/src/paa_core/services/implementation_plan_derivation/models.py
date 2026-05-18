"""Models for the Implementation Plan Derivation service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from paa_core.repositories.implementation_plan import (
    ImplementationPlanActivityDependencyUpsertSpec,
    ImplementationPlanActivityUpsertSpec,
    ImplementationPlanRecord,
    ImplementationPlanUpsertSpec,
)


@dataclass(frozen=True)
class ImplementationPlanActivityBlueprint:
    activity_key: str
    activity_title: str
    activity_kind: str
    sequence_order: int
    component_element_id: str | None
    component_element_key: str | None
    component_element_realization_id: str | None
    code_artifact_target_key: str | None
    target_path: str | None
    target_module: str | None
    assigned_role_id: str | None = None
    blocking_reason: str | None = None
    metadata: dict[str, Any] | None = None
    predecessor_activity_keys: tuple[str, ...] = ()
    activity_state: str = 'planned'


@dataclass(frozen=True)
class ImplementationPlanVerificationSurfaceDraft:
    activity_key: str | None
    surface_kind: str
    surface_ref: str
    required: bool = True
    sequence_order: int = 0
    verification_obligation_id: str | None = None
    metadata: dict[str, Any] | None = None
    status: str = 'planned'


@dataclass(frozen=True)
class ImplementationPlanDerivationRequest:
    plan: ImplementationPlanUpsertSpec
    activity_blueprints: tuple[ImplementationPlanActivityBlueprint, ...]
    verification_surfaces: tuple[ImplementationPlanVerificationSurfaceDraft, ...] = ()
    persist: bool = True
    replace_existing_draft: bool = True
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class ImplementationPlanDerivationResult:
    plan_record: ImplementationPlanRecord
    activity_specs: tuple[ImplementationPlanActivityUpsertSpec, ...]
    dependency_specs: tuple[ImplementationPlanActivityDependencyUpsertSpec, ...]
    verification_surfaces: tuple[ImplementationPlanVerificationSurfaceDraft, ...]
    warnings: tuple[str, ...]
    gaps: tuple[str, ...]
    persisted: bool


__all__ = [
    'ImplementationPlanActivityBlueprint',
    'ImplementationPlanDerivationRequest',
    'ImplementationPlanDerivationResult',
    'ImplementationPlanVerificationSurfaceDraft',
]

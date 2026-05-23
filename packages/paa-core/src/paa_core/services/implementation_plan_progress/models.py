"""Models for implementation-plan progress and successor derivation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

ActivityProgressClassification = Literal['completed', 'remaining', 'blocked', 'deferred']
ComponentRealizationState = Literal[
    'not_started',
    'partially_realized',
    'substantially_realized',
    'fully_realized',
    'blocked',
    'deferred',
]
PlanAuthorityStateSummary = Literal[
    'draft_plan',
    'active_plan',
    'partially_realized_plan',
    'completed_plan',
    'blocked_plan',
    'deferred_plan',
]


@dataclass(frozen=True)
class ImplementationPlanProgressRequest:
    implementation_plan_id: str
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class ActivityProgressDetail:
    activity_key: str
    activity_state: str
    classification: ActivityProgressClassification
    sequence_order: int
    blocking_reason: str | None
    required_verification_statuses: tuple[str, ...]
    missing_required_verification: tuple[str, ...]


@dataclass(frozen=True)
class ImplementationPlanProgressSummary:
    implementation_plan_id: str
    plan_id_external: str
    primary_component_id: str | None
    authority_state_summary: PlanAuthorityStateSummary
    realization_state: ComponentRealizationState
    completion_ratio: float
    completed_activity_keys: tuple[str, ...]
    deferred_activity_keys: tuple[str, ...]
    blocked_activity_keys: tuple[str, ...]
    remaining_activity_keys: tuple[str, ...]
    current_activity_key: str | None
    next_activity_key: str | None
    remaining_activity_count: int
    deferred_activity_count: int
    blocked_activity_count: int
    last_completed_activity_key: str | None
    activity_details: tuple[ActivityProgressDetail, ...]
    metadata: dict[str, Any]


@dataclass(frozen=True)
class NextActivityBundleRequest:
    implementation_plan_id: str
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class NextActivityBundleResult:
    implementation_plan_id: str
    plan_id_external: str | None
    ok: bool
    next_bundle_activity_keys: tuple[str, ...]
    bundle_kind: str
    decision_reason: str
    blocking_reasons: tuple[str, ...]
    unattended_safe: bool
    recommended_next_authority_action: str | None
    realization_state: ComponentRealizationState | None
    metadata: dict[str, Any]


__all__ = [
    'ActivityProgressClassification',
    'ActivityProgressDetail',
    'ComponentRealizationState',
    'ImplementationPlanProgressRequest',
    'ImplementationPlanProgressSummary',
    'NextActivityBundleRequest',
    'NextActivityBundleResult',
    'PlanAuthorityStateSummary',
]

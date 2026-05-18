"""Models for the component design planning service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


PlanningGapSeverity = Literal['info', 'warning', 'blocker']


@dataclass(frozen=True)
class ComponentPlanningRequest:
    project_id: str
    component_id: str | None = None
    component_name: str | None = None
    include_elements: bool = True
    include_realization_options: bool = True
    coder_run_brief_id: str | None = None
    design_package_id: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class RealizationOptionView:
    realization_type_key: str
    realization_label: str
    category: str
    description: str | None
    is_allowed: bool
    is_default: bool
    has_instances: bool
    is_brief_targetable: bool
    instance_count: int
    metadata: dict[str, Any]


@dataclass(frozen=True)
class PlanningGap:
    gap_code: str
    severity: PlanningGapSeverity
    affected_component_id: str | None
    affected_component_element_id: str | None
    note: str
    recommended_next_action: str | None
    metadata: dict[str, Any]


@dataclass(frozen=True)
class ComponentElementPlanningView:
    component_element_id: str
    component_element_type_id: str
    element_key: str
    element_label: str
    category: str
    title: str | None
    status: str
    definition: dict[str, Any]
    current_realization_keys: tuple[str, ...]
    realization_options: tuple[RealizationOptionView, ...]
    planning_warnings: tuple[str, ...]
    downstream_use_hints: tuple[str, ...]
    metadata: dict[str, Any]


@dataclass(frozen=True)
class ComponentPlanningView:
    component_id: str
    project_id: str
    component_name: str
    component_role: str
    system_layer: str
    tier: str | None
    description: str | None
    status: str
    element_plans: tuple[ComponentElementPlanningView, ...]
    design_completeness_warnings: tuple[str, ...]
    planning_notes: tuple[str, ...]
    gaps: tuple[PlanningGap, ...]
    metadata: dict[str, Any]


@dataclass(frozen=True)
class BriefPlanningPayload:
    component_id: str
    component_name: str
    coder_run_brief_id: str | None
    component_aspects: tuple[str, ...]
    target_modules: tuple[str, ...]
    element_plans: tuple[ComponentElementPlanningView, ...]
    gaps: tuple[PlanningGap, ...]
    warnings: tuple[str, ...]
    metadata: dict[str, Any]


__all__ = [
    'BriefPlanningPayload',
    'ComponentElementPlanningView',
    'ComponentPlanningRequest',
    'ComponentPlanningView',
    'PlanningGap',
    'PlanningGapSeverity',
    'RealizationOptionView',
]

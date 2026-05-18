"""Contracts for the component design planning service."""

from __future__ import annotations

from typing import Protocol

from paa_core.repositories.component_design import ComponentDesignRepository
from paa_core.services.implementation_plan_derivation.contracts import StructuredLogger

from .models import (
    BriefPlanningPayload,
    ComponentElementPlanningView,
    ComponentPlanningRequest,
    ComponentPlanningView,
    PlanningGap,
    RealizationOptionView,
)


class ComponentDesignPlanningService(Protocol):
    """Interpret component-design truth into planning-friendly structures."""

    @property
    def repository(self) -> ComponentDesignRepository:
        """Return the injected component-design repository."""

    @property
    def logger(self) -> StructuredLogger:
        """Return the injected structured logger."""

    def plan_component(self, request: ComponentPlanningRequest) -> ComponentPlanningView:
        """Build one planning view from component identity or name."""

    def plan_component_by_name(self, project_id: str, component_name: str) -> ComponentPlanningView:
        """Build one planning view using stable project/name identity."""

    def list_component_element_plans(self, component_id: str) -> tuple[ComponentElementPlanningView, ...]:
        """Return planning views for the component's element set."""

    def list_realization_options(self, component_element_id: str) -> tuple[RealizationOptionView, ...]:
        """Return allowed realization options for one component element."""

    def build_brief_planning_payload(
        self, component_id: str, coder_run_brief_id: str | None = None
    ) -> BriefPlanningPayload:
        """Return a brief-planning payload for downstream derivation."""

    def detect_component_design_gaps(self, component_id: str) -> tuple[PlanningGap, ...]:
        """Return explicit design gaps without mutating repository state."""


__all__ = ['ComponentDesignPlanningService', 'StructuredLogger']

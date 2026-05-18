"""Contracts for the ImplementationPlan repository."""

from __future__ import annotations

from typing import Protocol

from .models import (
    ImplementationPlanActivityDependencyRecord,
    ImplementationPlanActivityDependencyUpsertSpec,
    ImplementationPlanActivityRecord,
    ImplementationPlanActivityUpsertSpec,
    ImplementationPlanRecord,
    ImplementationPlanUpsertSpec,
    ImplementationPlanVerificationSurfaceRecord,
)


class ImplementationPlanRepository(Protocol):
    """Persistence boundary for ImplementationPlan project-design truth."""

    def get_implementation_plan(self, implementation_plan_id: str) -> ImplementationPlanRecord | None:
        """Return one implementation plan by primary id."""

    def get_implementation_plan_by_external(
        self, project_id: str, plan_id_external: str
    ) -> ImplementationPlanRecord | None:
        """Return one implementation plan by stable project/external identity."""

    def get_implementation_plan_for_design_package(
        self, design_package_id: str, consumer_context_key: str
    ) -> ImplementationPlanRecord | None:
        """Return the implementation plan bound to one design-package consumer context."""

    def list_implementation_plan_activities(
        self, implementation_plan_id: str
    ) -> list[ImplementationPlanActivityRecord]:
        """Return activities for one implementation plan in stable execution order."""

    def list_implementation_plan_activity_dependencies(
        self, implementation_plan_id: str
    ) -> list[ImplementationPlanActivityDependencyRecord]:
        """Return activity dependencies for one implementation plan."""

    def list_implementation_plan_verification_surfaces(
        self, implementation_plan_id: str
    ) -> list[ImplementationPlanVerificationSurfaceRecord]:
        """Return verification surfaces for one implementation plan."""

    def upsert_implementation_plan(self, spec: ImplementationPlanUpsertSpec) -> None:
        """Create or update one implementation plan root."""

    def upsert_implementation_plan_activity(self, spec: ImplementationPlanActivityUpsertSpec) -> None:
        """Create or update one implementation plan activity."""

    def upsert_implementation_plan_activity_dependency(
        self, spec: ImplementationPlanActivityDependencyUpsertSpec
    ) -> None:
        """Create or update one activity dependency using stable activity keys."""


__all__ = ['ImplementationPlanRepository']

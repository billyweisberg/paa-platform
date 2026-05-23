"""Contracts for the ImplementationPlan repository."""

from __future__ import annotations

from typing import Protocol

from .models import (
    ImplementationPlanActivityStateUpdateSpec,
    ImplementationPlanAuthorityEventAppendSpec,
    ImplementationPlanAuthorityEventRecord,
    ImplementationPlanActivityDependencyRecord,
    ImplementationPlanActivityDependencyUpsertSpec,
    ImplementationPlanActivityRecord,
    ImplementationPlanActivityUpsertSpec,
    ImplementationPlanProgressUpdateSpec,
    ImplementationPlanRecord,
    ImplementationPlanUpsertSpec,
    ImplementationPlanVerificationSurfaceRecord,
)


class ImplementationPlanRepository(Protocol):
    """Persistence boundary for ImplementationPlan project-design truth."""

    def get_implementation_plan(self, implementation_plan_id: str) -> ImplementationPlanRecord | None:
        """Return one implementation plan by primary id."""
        ...

    def get_implementation_plan_by_external(
        self, project_id: str, plan_id_external: str
    ) -> ImplementationPlanRecord | None:
        """Return one implementation plan by stable project/external identity."""
        ...

    def get_implementation_plan_for_design_package(
        self, design_package_id: str, consumer_context_key: str
    ) -> ImplementationPlanRecord | None:
        """Return the implementation plan bound to one design-package consumer context."""
        ...

    def list_implementation_plan_activities(
        self, implementation_plan_id: str
    ) -> list[ImplementationPlanActivityRecord]:
        """Return activities for one implementation plan in stable execution order."""
        ...

    def get_implementation_plan_activity_by_key(
        self,
        implementation_plan_id: str,
        activity_key: str,
    ) -> ImplementationPlanActivityRecord | None:
        """Return one implementation-plan activity by stable key."""
        ...

    def list_implementation_plan_activities_by_state(
        self,
        implementation_plan_id: str,
        activity_state: str,
    ) -> list[ImplementationPlanActivityRecord]:
        """Return activities for one implementation plan filtered by activity state."""
        ...

    def list_implementation_plan_activity_dependencies(
        self, implementation_plan_id: str
    ) -> list[ImplementationPlanActivityDependencyRecord]:
        """Return activity dependencies for one implementation plan."""
        ...

    def list_implementation_plan_verification_surfaces(
        self, implementation_plan_id: str
    ) -> list[ImplementationPlanVerificationSurfaceRecord]:
        """Return verification surfaces for one implementation plan."""
        ...

    def list_implementation_plan_verification_surfaces_for_activity(
        self,
        implementation_plan_id: str,
        activity_key: str,
    ) -> list[ImplementationPlanVerificationSurfaceRecord]:
        """Return verification surfaces bound to one implementation-plan activity."""
        ...

    def list_implementation_plan_authority_events(
        self, implementation_plan_id: str
    ) -> list[ImplementationPlanAuthorityEventRecord]:
        """Return authority-state transition events for one implementation plan."""
        ...

    def upsert_implementation_plan(self, spec: ImplementationPlanUpsertSpec) -> None:
        """Create or update one implementation plan root."""
        ...

    def update_implementation_plan_progress(self, spec: ImplementationPlanProgressUpdateSpec) -> None:
        """Persist computed component-completion truth on one implementation plan root."""
        ...

    def upsert_implementation_plan_activity(self, spec: ImplementationPlanActivityUpsertSpec) -> None:
        """Create or update one implementation plan activity."""
        ...

    def set_implementation_plan_activity_state(self, spec: ImplementationPlanActivityStateUpdateSpec) -> None:
        """Change one implementation-plan activity state and related progress fields."""
        ...

    def upsert_implementation_plan_activity_dependency(
        self, spec: ImplementationPlanActivityDependencyUpsertSpec
    ) -> None:
        """Create or update one activity dependency using stable activity keys."""
        ...

    def append_implementation_plan_authority_event(
        self,
        spec: ImplementationPlanAuthorityEventAppendSpec,
    ) -> None:
        """Append one durable implementation-plan authority transition event."""
        ...


__all__ = ['ImplementationPlanRepository']

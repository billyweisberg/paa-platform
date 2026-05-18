"""Interfaces for Component Design repository access."""

from __future__ import annotations

from typing import Protocol

from .models import (
    BriefRealizationTargetUpsertSpec,
    ComponentElementUpsertSpec,
    CoderBriefRealizationTargetRecord,
    ComponentElementRealizationRecord,
    ComponentElementRealizationTypeRecord,
    ComponentElementRealizationUpsertSpec,
    ComponentElementRecord,
    ComponentElementTypeRecord,
    ComponentRecord,
    ElementTypeRealizationLinkSpec,
    RealizationTypeUpsertSpec,
)


class ComponentDesignRepository(Protocol):
    def get_component_by_id(self, component_id: str) -> ComponentRecord | None:
        """Return one component by primary id."""

    def get_component_by_name(self, project_id: str, name: str) -> ComponentRecord | None:
        """Return one component by stable project/name identity."""

    def list_component_element_types(self) -> list[ComponentElementTypeRecord]:
        """Return all canonical component element types in stable sort order."""

    def get_component_element_by_id(self, component_element_id: str) -> ComponentElementRecord | None:
        """Return one component element by primary id."""

    def list_component_elements_for_component(self, component_id: str) -> list[ComponentElementRecord]:
        """Return component element instances for one component."""

    def upsert_component_element(self, spec: ComponentElementUpsertSpec) -> None:
        """Create or update one component element instance."""

    def list_realization_types_for_element_type(
        self, element_type_key: str
    ) -> list[ComponentElementRealizationTypeRecord]:
        """Return allowed realization kinds for one component element type."""

    def list_realizations_for_component_element(
        self, component_element_id: str
    ) -> list[ComponentElementRealizationRecord]:
        """Return concrete realization instances for one component element."""

    def list_brief_realization_targets(
        self, coder_run_brief_id: str
    ) -> list[CoderBriefRealizationTargetRecord]:
        """Return brief realization targets in execution order."""


    def upsert_realization_type(self, spec: RealizationTypeUpsertSpec) -> None:
        """Create or update one realization taxonomy row by stable key."""

    def upsert_element_type_realization_link(self, spec: ElementTypeRealizationLinkSpec) -> None:
        """Create or update one allowed realization mapping for a component element type."""

    def upsert_component_element_realization(
        self, spec: ComponentElementRealizationUpsertSpec
    ) -> None:
        """Create or update one concrete realization instance."""

    def upsert_brief_realization_target(self, spec: BriefRealizationTargetUpsertSpec) -> None:
        """Create or update one brief realization target binding."""

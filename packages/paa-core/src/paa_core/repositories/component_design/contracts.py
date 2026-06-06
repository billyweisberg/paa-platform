"""Interfaces for Component Design repository access."""

from __future__ import annotations

from typing import Protocol

from .models import (
    BriefRealizationTargetUpsertSpec,
    ComponentUpsertSpec,
    ComponentElementUpsertSpec,
    CoderBriefRealizationTargetRecord,
    ComponentElementRealizationRecord,
    ComponentElementRealizationTypeRecord,
    ComponentElementRealizationUpsertSpec,
    ComponentElementRecord,
    ComponentElementTypeRecord,
    ComponentRecord,
    DesignPackageRecord,
    DesignPackageSignoffRecord,
    DesignPackageSignoffUpsertSpec,
    DesignPackageUpsertSpec,
    ElementTypeRealizationLinkRecord,
    ElementTypeRealizationLinkSpec,
    RealizationTypeUpsertSpec,
)


class ComponentDesignRepository(Protocol):
    def get_component_by_id(self, component_id: str) -> ComponentRecord | None:
        """Return one component by primary id."""
        ...

    def get_component_by_name(self, project_id: str, name: str) -> ComponentRecord | None:
        """Return one component by stable project/name identity."""
        ...

    def upsert_component(self, spec: ComponentUpsertSpec) -> ComponentRecord:
        """Create or update one component by stable project/name identity."""
        ...

    def list_component_element_types(self) -> list[ComponentElementTypeRecord]:
        """Return all canonical component element types in stable sort order."""
        ...

    def get_component_element_type_by_key(self, element_type_key: str) -> ComponentElementTypeRecord | None:
        """Return one component element type by stable key."""
        ...

    def list_realization_types(self) -> list[ComponentElementRealizationTypeRecord]:
        """Return all canonical realization types in stable sort order."""
        ...

    def get_realization_type_by_key(
        self, realization_key: str
    ) -> ComponentElementRealizationTypeRecord | None:
        """Return one realization type by stable key."""
        ...

    def get_component_element_by_id(self, component_element_id: str) -> ComponentElementRecord | None:
        """Return one component element by primary id."""
        ...

    def list_component_elements_for_component(self, component_id: str) -> list[ComponentElementRecord]:
        """Return component element instances for one component."""
        ...

    def upsert_component_element(self, spec: ComponentElementUpsertSpec) -> None:
        """Create or update one component element instance."""
        ...

    def list_realization_types_for_element_type(
        self, element_type_key: str
    ) -> list[ComponentElementRealizationTypeRecord]:
        """Return allowed realization kinds for one component element type."""
        ...

    def list_element_type_realization_links(
        self, element_type_key: str
    ) -> list[ElementTypeRealizationLinkRecord]:
        """Return allowed realization mapping rows for one component element type."""
        ...

    def list_realizations_for_component_element(
        self, component_element_id: str
    ) -> list[ComponentElementRealizationRecord]:
        """Return concrete realization instances for one component element."""
        ...

    def list_brief_realization_targets(
        self, coder_run_brief_id: str
    ) -> list[CoderBriefRealizationTargetRecord]:
        """Return brief realization targets in execution order."""
        ...

    def get_design_package_by_id(self, design_package_id: str) -> DesignPackageRecord | None:
        """Return one design package by primary id."""
        ...

    def get_design_package_by_project_and_external_id(
        self, project_slug: str, package_id_external: str
    ) -> DesignPackageRecord | None:
        """Return one design package by stable project/external identity."""
        ...

    def get_active_design_package_for_work_item(self, work_item_id: str) -> DesignPackageRecord | None:
        """Return the latest non-superseded design package for one work item."""
        ...

    def list_design_package_signoffs(self, design_package_id: str) -> list[DesignPackageSignoffRecord]:
        """Return package signoffs in stable role order."""
        ...

    def upsert_design_package(self, spec: DesignPackageUpsertSpec) -> DesignPackageRecord:
        """Create or update one design package by stable project/external identity."""
        ...

    def upsert_design_package_signoff(
        self, spec: DesignPackageSignoffUpsertSpec
    ) -> DesignPackageSignoffRecord:
        """Create or update one design-package signoff for a role."""
        ...

    def upsert_realization_type(self, spec: RealizationTypeUpsertSpec) -> None:
        """Create or update one realization taxonomy row by stable key."""
        ...

    def upsert_element_type_realization_link(self, spec: ElementTypeRealizationLinkSpec) -> None:
        """Create or update one allowed realization mapping for a component element type."""
        ...

    def upsert_component_element_realization(
        self, spec: ComponentElementRealizationUpsertSpec
    ) -> None:
        """Create or update one concrete realization instance."""
        ...

    def upsert_brief_realization_target(self, spec: BriefRealizationTargetUpsertSpec) -> None:
        """Create or update one brief realization target binding."""
        ...

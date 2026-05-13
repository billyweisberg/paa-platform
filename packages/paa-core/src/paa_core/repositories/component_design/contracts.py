"""Interfaces for Component Design repository access."""

from __future__ import annotations

from typing import Protocol

from .models import (
    CoderBriefRealizationTargetRecord,
    ComponentElementRealizationRecord,
    ComponentElementRealizationTypeRecord,
    ComponentElementRecord,
    ComponentElementTypeRecord,
    ComponentRecord,
)


class ComponentDesignRepository(Protocol):
    def get_component_by_name(self, project_id: str, name: str) -> ComponentRecord | None:
        """Return one component by stable project/name identity."""

    def list_component_element_types(self) -> list[ComponentElementTypeRecord]:
        """Return all canonical component element types in stable sort order."""

    def list_component_elements_for_component(self, component_id: str) -> list[ComponentElementRecord]:
        """Return component element instances for one component."""

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

"""DTOs for Component Design repository records."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ComponentRecord:
    component_id: str
    project_id: str
    name: str
    role: str
    system_layer: str
    tier: str | None
    description: str | None
    status: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class ComponentElementTypeRecord:
    component_element_type_id: str
    element_key: str
    label: str
    category: str
    description: str | None
    is_brief_targetable: bool
    is_multi_instance: bool
    sort_order: int
    metadata: dict[str, Any]


@dataclass(frozen=True)
class ComponentElementRecord:
    component_element_id: str
    project_id: str
    component_id: str
    component_element_type_id: str
    element_key: str
    title: str | None
    status: str
    definition: dict[str, Any]
    provenance: dict[str, Any]
    metadata: dict[str, Any]


@dataclass(frozen=True)
class ComponentElementRealizationTypeRecord:
    component_element_realization_type_id: str
    realization_key: str
    label: str
    category: str
    description: str | None
    is_brief_targetable: bool
    is_multi_instance: bool
    sort_order: int
    metadata: dict[str, Any]
    is_default_for_element_type: bool = False
    element_type_sort_order: int = 0


@dataclass(frozen=True)
class ComponentElementRealizationRecord:
    component_element_realization_id: str
    project_id: str
    component_id: str
    component_element_id: str
    component_element_realization_type_id: str
    realization_key: str
    title: str | None
    status: str
    sequence_order: int
    definition: dict[str, Any]
    artifact_ref: dict[str, Any]
    provenance: dict[str, Any]
    metadata: dict[str, Any]


@dataclass(frozen=True)
class CoderBriefRealizationTargetRecord:
    coder_brief_realization_target_id: str
    project_id: str
    work_item_id: str | None
    coder_run_brief_id: str
    component_id: str
    component_element_id: str
    component_element_realization_id: str
    depends_on_target_id: str | None
    target_intent: str
    sequence_order: int
    is_required: bool
    target_notes: str | None
    target_contract: dict[str, Any]
    metadata: dict[str, Any]


@dataclass(frozen=True)
class RealizationTypeUpsertSpec:
    realization_key: str
    label: str
    category: str
    description: str | None = None
    is_brief_targetable: bool = True
    is_multi_instance: bool = True
    sort_order: int = 0
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class ElementTypeRealizationLinkSpec:
    element_type_key: str
    realization_key: str
    is_default: bool = False
    sort_order: int = 0
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class ComponentElementRealizationUpsertSpec:
    project_id: str
    component_id: str
    component_element_id: str
    realization_type_key: str
    realization_key: str
    title: str | None = None
    status: str = 'draft'
    sequence_order: int = 0
    definition: dict[str, Any] | None = None
    artifact_ref: dict[str, Any] | None = None
    provenance: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    created_by_role_id: str | None = None
    created_by_agent_id: str | None = None


@dataclass(frozen=True)
class BriefRealizationTargetUpsertSpec:
    project_id: str
    coder_run_brief_id: str
    component_id: str
    component_element_id: str
    component_element_realization_id: str
    target_intent: str = 'implement'
    work_item_id: str | None = None
    depends_on_target_id: str | None = None
    sequence_order: int = 0
    is_required: bool = True
    target_notes: str | None = None
    target_contract: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None

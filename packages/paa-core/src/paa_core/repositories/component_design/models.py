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
class ComponentUpsertSpec:
    project_id: str
    name: str
    role: str
    system_layer: str
    tier: str | None = None
    description: str | None = None
    status: str = 'active'
    metadata: dict[str, Any] | None = None


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
class ComponentElementUpsertSpec:
    project_id: str
    component_id: str
    element_type_key: str
    element_key: str
    title: str | None = None
    status: str = 'active'
    definition: dict[str, Any] | None = None
    provenance: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    created_by_role_id: str | None = None
    created_by_agent_id: str | None = None


@dataclass(frozen=True)
class DesignPackageRecord:
    design_package_id: str
    project_id: str
    work_item_id: str | None
    spec_fragment_id: str | None
    implementation_target_id: str | None
    authority_version_id: str | None
    primary_component_id: str | None
    package_id_external: str | None
    schema_version: str
    status: str
    package_json: dict[str, Any]
    provenance: dict[str, Any]
    metadata: dict[str, Any]
    created_by_role_id: str | None
    created_by_agent_id: str | None
    created_at: str | None
    updated_at: str | None


@dataclass(frozen=True)
class DesignPackageUpsertSpec:
    project_id: str
    work_item_id: str | None
    spec_fragment_id: str | None
    implementation_target_id: str | None
    authority_version_id: str | None
    primary_component_id: str | None
    package_id_external: str | None
    schema_version: str
    status: str
    package_json: dict[str, Any]
    provenance: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    created_by_role_id: str | None = None
    created_by_agent_id: str | None = None


@dataclass(frozen=True)
class DesignPackageSignoffRecord:
    design_package_signoff_id: str
    design_package_id: str
    role_id: str
    role_name: str
    role_sort_order: int
    signer_name: str | None
    signoff_status: str
    notes: str | None
    signed_at: str | None
    metadata: dict[str, Any]


@dataclass(frozen=True)
class DesignPackageSignoffUpsertSpec:
    design_package_id: str
    role_id: str
    signer_name: str | None = None
    signoff_status: str = 'approved'
    notes: str | None = None
    signed_at: str | None = None
    metadata: dict[str, Any] | None = None


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
class ElementTypeRealizationLinkRecord:
    component_element_type_realization_type_id: str
    component_element_type_id: str
    component_element_realization_type_id: str
    element_type_key: str
    realization_key: str
    realization_label: str
    realization_category: str
    is_default: bool
    sort_order: int
    metadata: dict[str, Any]


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

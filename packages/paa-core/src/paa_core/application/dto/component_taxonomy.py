from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ComponentTaxonomyOperationResult:
    payload: dict[str, Any]
    exit_code: int = 0


@dataclass(frozen=True)
class ListRealizationTypesRequest:
    pass


@dataclass(frozen=True)
class GetRealizationTypeRequest:
    realization_key: str


@dataclass(frozen=True)
class ListElementTypeRealizationLinksRequest:
    element_type_key: str


@dataclass(frozen=True)
class UpsertRealizationTypeRequest:
    realization_key: str
    label: str
    category: str
    description: str | None = None
    is_brief_targetable: bool = True
    is_multi_instance: bool = True
    sort_order: int = 0
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class UpsertElementTypeRealizationLinkRequest:
    element_type_key: str
    realization_key: str
    is_default: bool = False
    sort_order: int = 0
    metadata: dict[str, Any] | None = None

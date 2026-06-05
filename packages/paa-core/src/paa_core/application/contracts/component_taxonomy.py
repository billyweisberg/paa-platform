from __future__ import annotations

from typing import Protocol

from paa_core.application.dto.component_taxonomy import (
    ComponentTaxonomyOperationResult,
    GetRealizationTypeRequest,
    ListElementTypeRealizationLinksRequest,
    ListRealizationTypesRequest,
    UpsertElementTypeRealizationLinkRequest,
    UpsertRealizationTypeRequest,
)


class ComponentTaxonomyService(Protocol):
    def list_realization_types(self, request: ListRealizationTypesRequest) -> ComponentTaxonomyOperationResult: ...
    def get_realization_type(self, request: GetRealizationTypeRequest) -> ComponentTaxonomyOperationResult: ...
    def list_element_type_realization_links(
        self, request: ListElementTypeRealizationLinksRequest
    ) -> ComponentTaxonomyOperationResult: ...
    def upsert_element_type_realization_link(
        self, request: UpsertElementTypeRealizationLinkRequest
    ) -> ComponentTaxonomyOperationResult: ...
    def upsert_realization_type(self, request: UpsertRealizationTypeRequest) -> ComponentTaxonomyOperationResult: ...

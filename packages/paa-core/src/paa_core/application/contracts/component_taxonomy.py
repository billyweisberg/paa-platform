from __future__ import annotations

from typing import Protocol

from paa_core.application.dto.component_taxonomy import (
    ComponentTaxonomyOperationResult,
    GetRealizationTypeRequest,
    ListRealizationTypesRequest,
    UpsertRealizationTypeRequest,
)


class ComponentTaxonomyService(Protocol):
    def list_realization_types(self, request: ListRealizationTypesRequest) -> ComponentTaxonomyOperationResult: ...
    def get_realization_type(self, request: GetRealizationTypeRequest) -> ComponentTaxonomyOperationResult: ...
    def upsert_realization_type(self, request: UpsertRealizationTypeRequest) -> ComponentTaxonomyOperationResult: ...

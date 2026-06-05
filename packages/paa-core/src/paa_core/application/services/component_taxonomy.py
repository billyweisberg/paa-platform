from __future__ import annotations

from typing import Any

from paa_core.application.dto.component_taxonomy import (
    ComponentTaxonomyOperationResult,
    GetRealizationTypeRequest,
    ListRealizationTypesRequest,
    UpsertRealizationTypeRequest,
)
from paa_core.repositories.component_design import (
    ComponentDesignRepository,
    ComponentElementRealizationTypeRecord,
    PostgresComponentDesignRepository,
    RealizationTypeUpsertSpec,
)


class DefaultComponentTaxonomyApplicationService:
    def __init__(self, *, repository: ComponentDesignRepository | None = None) -> None:
        self._repository = repository or PostgresComponentDesignRepository()

    def list_realization_types(self, request: ListRealizationTypesRequest) -> ComponentTaxonomyOperationResult:
        del request
        items = [self._serialize_realization_type(row) for row in self._repository.list_realization_types()]
        return ComponentTaxonomyOperationResult(payload={'ok': True, 'items': items, 'count': len(items)})

    def get_realization_type(self, request: GetRealizationTypeRequest) -> ComponentTaxonomyOperationResult:
        row = self._repository.get_realization_type_by_key(request.realization_key)
        if row is None:
            return ComponentTaxonomyOperationResult(
                payload={
                    'ok': False,
                    'code': 'realization_type_not_found',
                    'realization_key': request.realization_key,
                },
                exit_code=1,
            )
        return ComponentTaxonomyOperationResult(payload={'ok': True, 'item': self._serialize_realization_type(row)})

    def upsert_realization_type(self, request: UpsertRealizationTypeRequest) -> ComponentTaxonomyOperationResult:
        self._repository.upsert_realization_type(
            RealizationTypeUpsertSpec(
                realization_key=request.realization_key,
                label=request.label,
                category=request.category,
                description=request.description,
                is_brief_targetable=request.is_brief_targetable,
                is_multi_instance=request.is_multi_instance,
                sort_order=request.sort_order,
                metadata=request.metadata,
            )
        )
        return ComponentTaxonomyOperationResult(
            payload={
                'ok': True,
                'realization_key': request.realization_key,
                'action': 'upserted',
            }
        )

    @staticmethod
    def _serialize_realization_type(row: ComponentElementRealizationTypeRecord) -> dict[str, Any]:
        return {
            'component_element_realization_type_id': row.component_element_realization_type_id,
            'realization_key': row.realization_key,
            'label': row.label,
            'category': row.category,
            'description': row.description,
            'is_brief_targetable': row.is_brief_targetable,
            'is_multi_instance': row.is_multi_instance,
            'sort_order': row.sort_order,
            'metadata': row.metadata,
            'is_default_for_element_type': row.is_default_for_element_type,
            'element_type_sort_order': row.element_type_sort_order,
        }


def build_default_component_taxonomy_application_service() -> DefaultComponentTaxonomyApplicationService:
    return DefaultComponentTaxonomyApplicationService()

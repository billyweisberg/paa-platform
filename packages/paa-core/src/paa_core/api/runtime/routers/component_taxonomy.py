from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from paa_core.api.runtime.dependencies import get_component_taxonomy_service
from paa_core.application.dto.component_taxonomy import (
    GetRealizationTypeRequest,
    ListRealizationTypesRequest,
    UpsertRealizationTypeRequest,
)
from paa_core.application.services import DefaultComponentTaxonomyApplicationService

router = APIRouter(prefix='/runtime/component-taxonomy', tags=['runtime-component-taxonomy'])


class UpsertRealizationTypeModel(BaseModel):
    realization_key: str
    label: str
    category: str
    description: str | None = None
    is_brief_targetable: bool = True
    is_multi_instance: bool = True
    sort_order: int = 0
    metadata: dict[str, object] | None = None


def _metadata_object(value: dict[str, object] | None) -> dict[str, Any] | None:
    if value is None:
        return None
    return {str(key): item for key, item in value.items()}


@router.get('/realization-types')
def list_realization_types(
    service: DefaultComponentTaxonomyApplicationService = Depends(get_component_taxonomy_service),
) -> dict[str, object]:
    return service.list_realization_types(ListRealizationTypesRequest()).payload


@router.get('/realization-types/{realization_key}')
def get_realization_type(
    realization_key: str,
    service: DefaultComponentTaxonomyApplicationService = Depends(get_component_taxonomy_service),
) -> dict[str, object]:
    result = service.get_realization_type(GetRealizationTypeRequest(realization_key=realization_key))
    if result.payload.get('ok'):
        return result.payload
    if result.payload.get('code') == 'realization_type_not_found':
        raise HTTPException(status_code=404, detail=result.payload)
    raise HTTPException(status_code=500, detail=result.payload)


@router.post('/realization-types')
def upsert_realization_type(
    request: UpsertRealizationTypeModel,
    service: DefaultComponentTaxonomyApplicationService = Depends(get_component_taxonomy_service),
) -> dict[str, object]:
    return service.upsert_realization_type(
        UpsertRealizationTypeRequest(
            realization_key=request.realization_key,
            label=request.label,
            category=request.category,
            description=request.description,
            is_brief_targetable=request.is_brief_targetable,
            is_multi_instance=request.is_multi_instance,
            sort_order=request.sort_order,
            metadata=_metadata_object(request.metadata),
        )
    ).payload


__all__ = ['router']

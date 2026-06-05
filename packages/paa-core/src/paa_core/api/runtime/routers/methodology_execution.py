from __future__ import annotations

from typing import Any, NoReturn

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from paa_core.api.runtime.dependencies import get_methodology_execution_service
from paa_core.application.dto.methodology_execution import (
    ApplyMethodologyExecutionTransitionRequest,
    EvaluateMethodologyExecutionPreflightRequest,
    ExplainMethodologyExecutionRequest,
    GetMethodologyExecutionNextActionRequest,
    GetMethodologyExecutionStatusRequest,
    MethodologyExecutionBindingEntryInput,
)
from paa_core.application.services import DefaultMethodologyExecutionApplicationService

router = APIRouter(prefix='/runtime/methodology-execution', tags=['runtime-methodology-execution'])


class MethodologyExecutionBindingEntryInputModel(BaseModel):
    binding_kind: str
    bound_record_id: str | None = None
    bound_record_key: str | None = None
    bound_record_ref: str | None = None
    is_primary: bool = False
    notes: str | None = None
    metadata: dict[str, object] | None = None


class ApplyMethodologyExecutionTransitionRequestModel(BaseModel):
    transition_key: str
    methodology_execution_id: str | None = None
    project_id: str | None = None
    work_item_id: str | None = None
    component_id: str | None = None
    actor_role_id: str | None = None
    actor_name: str | None = None
    notes: str | None = None
    evidence: dict[str, object] | None = None
    binding_entries: list[MethodologyExecutionBindingEntryInputModel] = []
    metadata: dict[str, object] | None = None


class EvaluateMethodologyExecutionPreflightRequestModel(BaseModel):
    command_family: str
    command_name: str
    methodology_execution_id: str | None = None
    project_id: str | None = None
    work_item_id: str | None = None
    component_id: str | None = None
    command_arguments: dict[str, object] | None = None
    actor_role_id: str | None = None
    actor_name: str | None = None
    metadata: dict[str, object] | None = None


def _metadata_object(value: dict[str, object] | None) -> dict[str, Any] | None:
    if value is None:
        return None
    return {str(key): item for key, item in value.items()}


def _binding_entry_from_model(
    entry: MethodologyExecutionBindingEntryInputModel,
) -> MethodologyExecutionBindingEntryInput:
    return MethodologyExecutionBindingEntryInput(
        binding_kind=entry.binding_kind,
        bound_record_id=entry.bound_record_id,
        bound_record_key=entry.bound_record_key,
        bound_record_ref=entry.bound_record_ref,
        is_primary=entry.is_primary,
        notes=entry.notes,
        metadata=_metadata_object(entry.metadata),
    )


def _raise_for_identity_or_not_found(payload: dict[str, object]) -> NoReturn:
    code = payload.get('code')
    if code == 'missing_methodology_identity':
        raise HTTPException(status_code=400, detail=payload)
    if code == 'methodology_execution_not_found':
        raise HTTPException(status_code=404, detail=payload)
    raise HTTPException(status_code=500, detail=payload)


@router.get('/status')
def get_methodology_execution_status(
    methodology_execution_id: str | None = None,
    project_id: str | None = None,
    work_item_id: str | None = None,
    component_id: str | None = None,
    service: DefaultMethodologyExecutionApplicationService = Depends(get_methodology_execution_service),
) -> dict[str, object]:
    result = service.get_status(
        GetMethodologyExecutionStatusRequest(
            methodology_execution_id=methodology_execution_id,
            project_id=project_id,
            work_item_id=work_item_id,
            component_id=component_id,
        )
    )
    if result.payload.get('ok'):
        return result.payload
    _raise_for_identity_or_not_found(result.payload)


@router.get('/next')
def get_methodology_execution_next_action(
    methodology_execution_id: str | None = None,
    project_id: str | None = None,
    work_item_id: str | None = None,
    component_id: str | None = None,
    service: DefaultMethodologyExecutionApplicationService = Depends(get_methodology_execution_service),
) -> dict[str, object]:
    result = service.get_next_action(
        GetMethodologyExecutionNextActionRequest(
            methodology_execution_id=methodology_execution_id,
            project_id=project_id,
            work_item_id=work_item_id,
            component_id=component_id,
        )
    )
    if result.payload.get('ok'):
        return result.payload
    _raise_for_identity_or_not_found(result.payload)


@router.get('/explain')
def explain_methodology_execution(
    methodology_execution_id: str | None = None,
    project_id: str | None = None,
    work_item_id: str | None = None,
    component_id: str | None = None,
    service: DefaultMethodologyExecutionApplicationService = Depends(get_methodology_execution_service),
) -> dict[str, object]:
    result = service.explain(
        ExplainMethodologyExecutionRequest(
            methodology_execution_id=methodology_execution_id,
            project_id=project_id,
            work_item_id=work_item_id,
            component_id=component_id,
        )
    )
    if result.payload.get('ok'):
        return result.payload
    _raise_for_identity_or_not_found(result.payload)


@router.post('/transitions')
def apply_methodology_execution_transition(
    request: ApplyMethodologyExecutionTransitionRequestModel,
    service: DefaultMethodologyExecutionApplicationService = Depends(get_methodology_execution_service),
) -> dict[str, object]:
    result = service.apply_transition(
        ApplyMethodologyExecutionTransitionRequest(
            transition_key=request.transition_key,
            methodology_execution_id=request.methodology_execution_id,
            project_id=request.project_id,
            work_item_id=request.work_item_id,
            component_id=request.component_id,
            actor_role_id=request.actor_role_id,
            actor_name=request.actor_name,
            notes=request.notes,
            evidence=_metadata_object(request.evidence),
            binding_entries=tuple(_binding_entry_from_model(entry) for entry in request.binding_entries),
            metadata=_metadata_object(request.metadata),
        )
    )
    if result.payload.get('ok'):
        return result.payload
    code = result.payload.get('code')
    if code == 'missing_methodology_identity':
        raise HTTPException(status_code=400, detail=result.payload)
    if code == 'methodology_execution_not_found':
        raise HTTPException(status_code=404, detail=result.payload)
    raise HTTPException(status_code=409, detail=result.payload)


@router.post('/preflight')
def evaluate_methodology_execution_preflight(
    request: EvaluateMethodologyExecutionPreflightRequestModel,
    service: DefaultMethodologyExecutionApplicationService = Depends(get_methodology_execution_service),
) -> dict[str, object]:
    result = service.evaluate_preflight(
        EvaluateMethodologyExecutionPreflightRequest(
            command_family=request.command_family,
            command_name=request.command_name,
            methodology_execution_id=request.methodology_execution_id,
            project_id=request.project_id,
            work_item_id=request.work_item_id,
            component_id=request.component_id,
            command_arguments=_metadata_object(request.command_arguments),
            actor_role_id=request.actor_role_id,
            actor_name=request.actor_name,
            metadata=_metadata_object(request.metadata),
        )
    )
    if result.payload.get('code') == 'missing_methodology_identity':
        raise HTTPException(status_code=400, detail=result.payload)
    return result.payload


__all__ = ['router']

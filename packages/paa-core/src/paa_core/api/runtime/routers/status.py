# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from paa_core.api.runtime.dependencies import get_runtime_validation_service
from paa_core.application.dto.status import RuntimeSmokeRequest, RuntimeValidationRequest
from paa_core.application.services import DefaultRuntimeValidationApplicationService

router = APIRouter(prefix='/runtime/status', tags=['runtime-status'])


class RuntimeValidationModel(BaseModel):
    repo_root: str
    expected_branch: str | None = None


class RuntimeSmokeModel(BaseModel):
    repo_root: str
    expected_branch: str | None = None
    output_path: str | None = None


@router.post('/validate')
def validate_runtime(
    request: RuntimeValidationModel,
    service: DefaultRuntimeValidationApplicationService = Depends(get_runtime_validation_service),
) -> dict[str, object]:
    return service.validate_runtime(
        RuntimeValidationRequest(repo_root=Path(request.repo_root).resolve(), expected_branch=request.expected_branch)
    ).payload


@router.post('/smoke')
def runtime_smoke(
    request: RuntimeSmokeModel,
    service: DefaultRuntimeValidationApplicationService = Depends(get_runtime_validation_service),
) -> dict[str, object]:
    return service.runtime_smoke(
        RuntimeSmokeRequest(
            repo_root=Path(request.repo_root).resolve(),
            expected_branch=request.expected_branch,
            output_path=Path(request.output_path).resolve() if request.output_path else None,
        )
    ).payload

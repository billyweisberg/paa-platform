# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from paa_core.api.runtime.dependencies import get_runtime_install_service
from paa_core.application.dto.runtime import RuntimeInstallRequest
from paa_core.application.services import DefaultRuntimeInstallApplicationService

router = APIRouter(prefix='/runtime/ops', tags=['runtime-ops'])


class RuntimeInstallModel(BaseModel):
    repo_root: str
    project_pack: str = 'fractal-core'


@router.post('/install-runtime')
def install_runtime(
    request: RuntimeInstallModel,
    service: DefaultRuntimeInstallApplicationService = Depends(get_runtime_install_service),
) -> dict[str, object]:
    return service.install_runtime(
        RuntimeInstallRequest(repo_root=Path(request.repo_root).resolve(), project_pack=request.project_pack)
    ).payload


@router.post('/update-runtime')
def update_runtime(
    request: RuntimeInstallModel,
    service: DefaultRuntimeInstallApplicationService = Depends(get_runtime_install_service),
) -> dict[str, object]:
    return service.update_runtime(
        RuntimeInstallRequest(repo_root=Path(request.repo_root).resolve(), project_pack=request.project_pack)
    ).payload


__all__ = ['router']

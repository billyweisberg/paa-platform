# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from paa_core.api.runtime.dependencies import get_runtime_admin_service
from paa_core.application.dto.runtime import RuntimeHostRunRequest
from paa_core.application.services import DefaultRuntimeAdminApplicationService

router = APIRouter(prefix='/runtime/hosts', tags=['runtime-hosts'])


class HostRunModel(BaseModel):
    repo_root: str
    actor_name: str
    host_name: str
    intake_mode: str = 'preview'
    max_iterations: int = 1
    poll_interval_seconds: float = 5.0
    emit_next_assignment: bool = False
    emit_worker_result: bool = False
    emit_verification: bool = False


def _build_host_request(request: HostRunModel) -> RuntimeHostRunRequest:
    return RuntimeHostRunRequest(
        repo_root=Path(request.repo_root).resolve(),
        actor_name=request.actor_name,
        host_name=request.host_name,
        intake_mode=request.intake_mode,
        max_iterations=request.max_iterations,
        poll_interval_seconds=request.poll_interval_seconds,
        emit_next_assignment=request.emit_next_assignment,
        emit_worker_result=request.emit_worker_result,
        emit_verification=request.emit_verification,
    )


@router.post('/techlead')
def run_techlead_host(
    request: HostRunModel,
    service: DefaultRuntimeAdminApplicationService = Depends(get_runtime_admin_service),
) -> dict[str, object]:
    return service.run_techlead_host(_build_host_request(request)).payload


@router.post('/dev')
def run_dev_host(
    request: HostRunModel,
    service: DefaultRuntimeAdminApplicationService = Depends(get_runtime_admin_service),
) -> dict[str, object]:
    return service.run_dev_host(_build_host_request(request)).payload


@router.post('/qa')
def run_qa_host(
    request: HostRunModel,
    service: DefaultRuntimeAdminApplicationService = Depends(get_runtime_admin_service),
) -> dict[str, object]:
    return service.run_qa_host(_build_host_request(request)).payload

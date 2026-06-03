# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from paa_core.api.runtime.dependencies import get_runtime_admin_service
from paa_core.application.services import DefaultRuntimeAdminApplicationService
from paa_core.application.dto.runtime import RuntimeLogsRequest, RuntimeStatusRequest, RuntimeSupervisorRequest

router = APIRouter(prefix='/runtime/supervisor', tags=['runtime-supervisor'])


class SupervisorRequestModel(BaseModel):
    repo_root: str
    intake_mode: str = 'claim_next'
    emit_next_assignment: bool = True
    emit_worker_result: bool = True
    emit_verification: bool = True
    max_iterations: int = 0
    poll_interval_seconds: float = 5.0


class StatusRequestModel(BaseModel):
    repo_root: str


class LogsRequestModel(BaseModel):
    repo_root: str
    lines: int = 200


@router.post('/run')
def run_supervisor(
    request: SupervisorRequestModel,
    service: DefaultRuntimeAdminApplicationService = Depends(get_runtime_admin_service),
) -> dict[str, object]:
    result = service.run_supervisor(RuntimeSupervisorRequest(repo_root=Path(request.repo_root).resolve(), intake_mode=request.intake_mode, emit_next_assignment=request.emit_next_assignment, emit_worker_result=request.emit_worker_result, emit_verification=request.emit_verification, max_iterations=request.max_iterations, poll_interval_seconds=request.poll_interval_seconds))
    return result.payload


@router.post('/start')
def start_supervisor(
    request: SupervisorRequestModel,
    service: DefaultRuntimeAdminApplicationService = Depends(get_runtime_admin_service),
) -> dict[str, object]:
    result = service.start_supervisor(RuntimeSupervisorRequest(repo_root=Path(request.repo_root).resolve(), intake_mode=request.intake_mode, emit_next_assignment=request.emit_next_assignment, emit_worker_result=request.emit_worker_result, emit_verification=request.emit_verification, max_iterations=request.max_iterations, poll_interval_seconds=request.poll_interval_seconds))
    return result.payload


@router.post('/stop')
def stop_supervisor(
    request: StatusRequestModel,
    service: DefaultRuntimeAdminApplicationService = Depends(get_runtime_admin_service),
) -> dict[str, object]:
    result = service.stop_supervisor(RuntimeStatusRequest(repo_root=Path(request.repo_root).resolve()))
    return result.payload


@router.post('/restart')
def restart_supervisor(
    request: SupervisorRequestModel,
    service: DefaultRuntimeAdminApplicationService = Depends(get_runtime_admin_service),
) -> dict[str, object]:
    result = service.restart_supervisor(RuntimeSupervisorRequest(repo_root=Path(request.repo_root).resolve(), intake_mode=request.intake_mode, emit_next_assignment=request.emit_next_assignment, emit_worker_result=request.emit_worker_result, emit_verification=request.emit_verification, max_iterations=request.max_iterations, poll_interval_seconds=request.poll_interval_seconds))
    return result.payload


@router.get('/status')
def supervisor_status(
    repo_root: str,
    service: DefaultRuntimeAdminApplicationService = Depends(get_runtime_admin_service),
) -> dict[str, object]:
    result = service.supervisor_status(RuntimeStatusRequest(repo_root=Path(repo_root).resolve()))
    return result.payload


@router.get('/logs')
def supervisor_logs(
    repo_root: str,
    lines: int = 200,
    service: DefaultRuntimeAdminApplicationService = Depends(get_runtime_admin_service),
) -> dict[str, object]:
    output = service.supervisor_logs(RuntimeLogsRequest(repo_root=Path(repo_root).resolve(), lines=lines))
    return {'ok': True, 'output': output}

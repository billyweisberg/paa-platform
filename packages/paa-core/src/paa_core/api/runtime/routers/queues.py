# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from paa_core.api.runtime.dependencies import get_queue_admin_service
from paa_core.application.dto.queue import (
    QueueCheckRequest,
    QueueClaimActionRequest,
    QueueClaimNextRequest,
    QueueListClaimsRequest,
    QueuePacketFileRequest,
    QueuePurgeRequest,
    QueueRepoRootRequest,
    QueueSendRequest,
    QueueValidateRequest,
)
from paa_core.application.services import DefaultQueueAdminApplicationService

router = APIRouter(prefix='/runtime/queues', tags=['runtime-queues'])


class RepoRootModel(BaseModel):
    repo_root: str


class QueueCheckModel(BaseModel):
    repo_root: str
    queue: str
    preview: int = 0


class QueuePurgeModel(BaseModel):
    repo_root: str
    queue: str | None = None


class QueueValidateModel(BaseModel):
    message_file: str


class QueueSendModel(BaseModel):
    repo_root: str
    queue: str
    message_file: str


class QueueClaimNextModel(BaseModel):
    repo_root: str
    queue: str
    claimed_by: str = 'paa'


class QueueListClaimsModel(BaseModel):
    repo_root: str
    queue: str | None = None
    status: str | None = None


class QueueClaimActionModel(BaseModel):
    repo_root: str
    claim_id: str


class QueuePacketFileModel(BaseModel):
    repo_root: str
    message_file: str


@router.post('/ensure-topology')
def ensure_topology(request: RepoRootModel, service: DefaultQueueAdminApplicationService = Depends(get_queue_admin_service)) -> dict[str, object]:
    return service.ensure_topology(QueueRepoRootRequest(repo_root=Path(request.repo_root).resolve())).payload


@router.get('/state-info')
def state_info(repo_root: str, service: DefaultQueueAdminApplicationService = Depends(get_queue_admin_service)) -> dict[str, object]:
    return service.state_info(QueueRepoRootRequest(repo_root=Path(repo_root).resolve())).payload


@router.post('/check')
def check_queue(request: QueueCheckModel, service: DefaultQueueAdminApplicationService = Depends(get_queue_admin_service)) -> dict[str, object]:
    return service.check(QueueCheckRequest(repo_root=Path(request.repo_root).resolve(), queue=request.queue, preview=request.preview)).payload


@router.post('/purge')
def purge_queue(request: QueuePurgeModel, service: DefaultQueueAdminApplicationService = Depends(get_queue_admin_service)) -> dict[str, object]:
    return service.purge(QueuePurgeRequest(repo_root=Path(request.repo_root).resolve(), queue=request.queue)).payload


@router.post('/validate')
def validate_queue_message(request: QueueValidateModel, service: DefaultQueueAdminApplicationService = Depends(get_queue_admin_service)) -> dict[str, object]:
    return service.validate(QueueValidateRequest(message_file=Path(request.message_file).resolve())).payload


@router.post('/send')
def send_queue_message(request: QueueSendModel, service: DefaultQueueAdminApplicationService = Depends(get_queue_admin_service)) -> dict[str, object]:
    return service.send(QueueSendRequest(repo_root=Path(request.repo_root).resolve(), queue=request.queue, message_file=Path(request.message_file).resolve())).payload


@router.post('/claim-next')
def claim_next(request: QueueClaimNextModel, service: DefaultQueueAdminApplicationService = Depends(get_queue_admin_service)) -> dict[str, object]:
    return service.claim_next(QueueClaimNextRequest(repo_root=Path(request.repo_root).resolve(), queue=request.queue, claimed_by=request.claimed_by)).payload


@router.post('/list-claims')
def list_claims(request: QueueListClaimsModel, service: DefaultQueueAdminApplicationService = Depends(get_queue_admin_service)) -> dict[str, object]:
    return service.list_claims(QueueListClaimsRequest(repo_root=Path(request.repo_root).resolve(), queue=request.queue, status=request.status)).payload


@router.post('/ack')
def ack_claim(request: QueueClaimActionModel, service: DefaultQueueAdminApplicationService = Depends(get_queue_admin_service)) -> dict[str, object]:
    return service.ack(QueueClaimActionRequest(repo_root=Path(request.repo_root).resolve(), claim_id=request.claim_id)).payload


@router.post('/requeue')
def requeue_claim(request: QueueClaimActionModel, service: DefaultQueueAdminApplicationService = Depends(get_queue_admin_service)) -> dict[str, object]:
    return service.requeue(QueueClaimActionRequest(repo_root=Path(request.repo_root).resolve(), claim_id=request.claim_id)).payload


@router.post('/validate-packet')
def validate_packet(request: QueuePacketFileModel, service: DefaultQueueAdminApplicationService = Depends(get_queue_admin_service)) -> dict[str, object]:
    return service.validate_packet(QueuePacketFileRequest(repo_root=Path(request.repo_root).resolve(), message_file=Path(request.message_file).resolve())).payload


@router.post('/send-packet')
def send_packet(request: QueuePacketFileModel, service: DefaultQueueAdminApplicationService = Depends(get_queue_admin_service)) -> dict[str, object]:
    return service.send_packet(QueuePacketFileRequest(repo_root=Path(request.repo_root).resolve(), message_file=Path(request.message_file).resolve())).payload

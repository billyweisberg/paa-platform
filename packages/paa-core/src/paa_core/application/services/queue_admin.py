from __future__ import annotations

from paa_core.application.dto.queue import (
    QueueCheckRequest,
    QueueClaimActionRequest,
    QueueClaimNextRequest,
    QueueListClaimsRequest,
    QueueOperationResult,
    QueuePacketFileRequest,
    QueuePurgeRequest,
    QueueRepoRootRequest,
    QueueSendRequest,
    QueueValidateRequest,
)
from paa_core.runtime.transport.queue_admin import DefaultRuntimeQueueAdminService


class DefaultQueueAdminApplicationService:
    def __init__(self, *, queue_admin: DefaultRuntimeQueueAdminService | None = None) -> None:
        self._queue_admin = queue_admin or DefaultRuntimeQueueAdminService()

    def ensure_topology(self, request: QueueRepoRootRequest) -> QueueOperationResult:
        return QueueOperationResult(payload=self._queue_admin.ensure_topology(repo_root=request.repo_root), exit_code=0)

    def state_info(self, request: QueueRepoRootRequest) -> QueueOperationResult:
        return QueueOperationResult(payload=self._queue_admin.state_info(repo_root=request.repo_root), exit_code=0)

    def check(self, request: QueueCheckRequest) -> QueueOperationResult:
        return QueueOperationResult(
            payload=self._queue_admin.check(repo_root=request.repo_root, queue=request.queue, preview=request.preview),
            exit_code=0,
        )

    def purge(self, request: QueuePurgeRequest) -> QueueOperationResult:
        result = self._queue_admin.purge(repo_root=request.repo_root, queue=request.queue)
        return QueueOperationResult(payload=result, exit_code=0 if result.get('ok') else 1)

    def validate(self, request: QueueValidateRequest) -> QueueOperationResult:
        result = self._queue_admin.validate(message_file=request.message_file)
        return QueueOperationResult(payload=result, exit_code=0 if result.get('ok') else 1)

    def send(self, request: QueueSendRequest) -> QueueOperationResult:
        result = self._queue_admin.send(repo_root=request.repo_root, queue=request.queue, message_file=request.message_file)
        return QueueOperationResult(payload=result, exit_code=0 if result.get('ok') else 1)

    def claim_next(self, request: QueueClaimNextRequest) -> QueueOperationResult:
        result, exit_code = self._queue_admin.claim_next(
            repo_root=request.repo_root,
            queue=request.queue,
            claimed_by=request.claimed_by,
        )
        return QueueOperationResult(payload=result, exit_code=exit_code)

    def list_claims(self, request: QueueListClaimsRequest) -> QueueOperationResult:
        return QueueOperationResult(
            payload=self._queue_admin.list_claims(repo_root=request.repo_root, queue=request.queue, status=request.status),
            exit_code=0,
        )

    def ack(self, request: QueueClaimActionRequest) -> QueueOperationResult:
        result = self._queue_admin.ack(repo_root=request.repo_root, claim_id=request.claim_id)
        return QueueOperationResult(payload=result, exit_code=0 if result.get('ok') else 1)

    def requeue(self, request: QueueClaimActionRequest) -> QueueOperationResult:
        result, exit_code = self._queue_admin.requeue(repo_root=request.repo_root, claim_id=request.claim_id)
        return QueueOperationResult(payload=result, exit_code=exit_code)

    def validate_packet(self, request: QueuePacketFileRequest) -> QueueOperationResult:
        result, exit_code = self._queue_admin.validate_packet(repo_root=request.repo_root, message_file=request.message_file)
        return QueueOperationResult(payload=result, exit_code=exit_code)

    def send_packet(self, request: QueuePacketFileRequest) -> QueueOperationResult:
        result, exit_code = self._queue_admin.send_packet(repo_root=request.repo_root, message_file=request.message_file)
        return QueueOperationResult(payload=result, exit_code=exit_code)

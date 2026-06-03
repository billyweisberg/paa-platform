from __future__ import annotations

from dataclasses import asdict, is_dataclass
import json
from pathlib import Path
from typing import Any, Protocol, cast
from urllib.parse import urlencode
from urllib.request import Request, urlopen

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
from paa_core.application.dto.runtime import (
    RuntimeHostRunRequest,
    RuntimeLogsRequest,
    RuntimeOperationResult,
    RuntimeStatusRequest,
    RuntimeSupervisorRequest,
)
from paa_core.application.dto.status import RuntimeSmokeRequest, RuntimeStatusResultView, RuntimeValidationRequest, TechLeadServiceMapResultView
from paa_core.application.dto.workflow import AutomationPreflightRequest, AutomationPreflightResultView
from paa_core.application.services import (
    DefaultAutomationPreflightApplicationService,
    DefaultQueueAdminApplicationService,
    DefaultRuntimeAdminApplicationService,
    DefaultRuntimeReportApplicationService,
    DefaultRuntimeValidationApplicationService,
)


def _to_jsonable(value: object) -> object:
    if isinstance(value, Path):
        return str(value)
    if is_dataclass(value) and not isinstance(value, type):
        dataclass_payload = cast(dict[str, object], asdict(cast(Any, value)))
        return {key: _to_jsonable(item) for key, item in dataclass_payload.items()}
    if isinstance(value, dict):
        dict_payload = cast(dict[object, object], value)
        return {str(key): _to_jsonable(item) for key, item in dict_payload.items()}
    if isinstance(value, (list, tuple)):
        sequence_payload = cast(list[object] | tuple[object, ...], value)
        return [_to_jsonable(item) for item in sequence_payload]
    return value


class RuntimeApiClient(Protocol):
    def ensure_topology(self, request: QueueRepoRootRequest) -> QueueOperationResult: ...
    def state_info(self, request: QueueRepoRootRequest) -> QueueOperationResult: ...
    def check(self, request: QueueCheckRequest) -> QueueOperationResult: ...
    def purge(self, request: QueuePurgeRequest) -> QueueOperationResult: ...
    def validate(self, request: QueueValidateRequest) -> QueueOperationResult: ...
    def send(self, request: QueueSendRequest) -> QueueOperationResult: ...
    def claim_next(self, request: QueueClaimNextRequest) -> QueueOperationResult: ...
    def list_claims(self, request: QueueListClaimsRequest) -> QueueOperationResult: ...
    def ack(self, request: QueueClaimActionRequest) -> QueueOperationResult: ...
    def requeue(self, request: QueueClaimActionRequest) -> QueueOperationResult: ...
    def validate_packet(self, request: QueuePacketFileRequest) -> QueueOperationResult: ...
    def send_packet(self, request: QueuePacketFileRequest) -> QueueOperationResult: ...
    def run_supervisor(self, request: RuntimeSupervisorRequest) -> RuntimeOperationResult: ...
    def start_supervisor(self, request: RuntimeSupervisorRequest) -> RuntimeOperationResult: ...
    def stop_supervisor(self, request: RuntimeStatusRequest) -> RuntimeOperationResult: ...
    def supervisor_status(self, request: RuntimeStatusRequest) -> RuntimeOperationResult: ...
    def supervisor_logs(self, request: RuntimeLogsRequest) -> str: ...
    def restart_supervisor(self, request: RuntimeSupervisorRequest) -> RuntimeOperationResult: ...
    def run_techlead_host(self, request: RuntimeHostRunRequest) -> RuntimeOperationResult: ...
    def run_dev_host(self, request: RuntimeHostRunRequest) -> RuntimeOperationResult: ...
    def run_qa_host(self, request: RuntimeHostRunRequest) -> RuntimeOperationResult: ...
    def techlead_service_map(self) -> TechLeadServiceMapResultView: ...
    def validate_runtime(self, request: RuntimeValidationRequest) -> RuntimeStatusResultView: ...
    def runtime_smoke(self, request: RuntimeSmokeRequest) -> RuntimeStatusResultView: ...
    def evaluate_automation_preflight(self, request: AutomationPreflightRequest) -> AutomationPreflightResultView: ...


class InProcessRuntimeApiClient:
    def __init__(
        self,
        *,
        queue_admin: DefaultQueueAdminApplicationService | None = None,
        runtime_admin: DefaultRuntimeAdminApplicationService | None = None,
        runtime_report: DefaultRuntimeReportApplicationService | None = None,
        runtime_validation: DefaultRuntimeValidationApplicationService | None = None,
        automation_preflight: DefaultAutomationPreflightApplicationService | None = None,
    ) -> None:
        self._queue_admin = queue_admin or DefaultQueueAdminApplicationService()
        self._runtime_admin = runtime_admin or DefaultRuntimeAdminApplicationService()
        self._runtime_report = runtime_report or DefaultRuntimeReportApplicationService()
        self._runtime_validation = runtime_validation or DefaultRuntimeValidationApplicationService()
        self._automation_preflight = automation_preflight or DefaultAutomationPreflightApplicationService()

    def ensure_topology(self, request: QueueRepoRootRequest) -> QueueOperationResult:
        return self._queue_admin.ensure_topology(request)

    def state_info(self, request: QueueRepoRootRequest) -> QueueOperationResult:
        return self._queue_admin.state_info(request)

    def check(self, request: QueueCheckRequest) -> QueueOperationResult:
        return self._queue_admin.check(request)

    def purge(self, request: QueuePurgeRequest) -> QueueOperationResult:
        return self._queue_admin.purge(request)

    def validate(self, request: QueueValidateRequest) -> QueueOperationResult:
        return self._queue_admin.validate(request)

    def send(self, request: QueueSendRequest) -> QueueOperationResult:
        return self._queue_admin.send(request)

    def claim_next(self, request: QueueClaimNextRequest) -> QueueOperationResult:
        return self._queue_admin.claim_next(request)

    def list_claims(self, request: QueueListClaimsRequest) -> QueueOperationResult:
        return self._queue_admin.list_claims(request)

    def ack(self, request: QueueClaimActionRequest) -> QueueOperationResult:
        return self._queue_admin.ack(request)

    def requeue(self, request: QueueClaimActionRequest) -> QueueOperationResult:
        return self._queue_admin.requeue(request)

    def validate_packet(self, request: QueuePacketFileRequest) -> QueueOperationResult:
        return self._queue_admin.validate_packet(request)

    def send_packet(self, request: QueuePacketFileRequest) -> QueueOperationResult:
        return self._queue_admin.send_packet(request)

    def run_supervisor(self, request: RuntimeSupervisorRequest) -> RuntimeOperationResult:
        return self._runtime_admin.run_supervisor(request)

    def start_supervisor(self, request: RuntimeSupervisorRequest) -> RuntimeOperationResult:
        return self._runtime_admin.start_supervisor(request)

    def stop_supervisor(self, request: RuntimeStatusRequest) -> RuntimeOperationResult:
        return self._runtime_admin.stop_supervisor(request)

    def supervisor_status(self, request: RuntimeStatusRequest) -> RuntimeOperationResult:
        return self._runtime_admin.supervisor_status(request)

    def supervisor_logs(self, request: RuntimeLogsRequest) -> str:
        return self._runtime_admin.supervisor_logs(request)

    def restart_supervisor(self, request: RuntimeSupervisorRequest) -> RuntimeOperationResult:
        return self._runtime_admin.restart_supervisor(request)

    def run_techlead_host(self, request: RuntimeHostRunRequest) -> RuntimeOperationResult:
        return self._runtime_admin.run_techlead_host(request)

    def run_dev_host(self, request: RuntimeHostRunRequest) -> RuntimeOperationResult:
        return self._runtime_admin.run_dev_host(request)

    def run_qa_host(self, request: RuntimeHostRunRequest) -> RuntimeOperationResult:
        return self._runtime_admin.run_qa_host(request)

    def techlead_service_map(self) -> TechLeadServiceMapResultView:
        return self._runtime_report.techlead_service_map()

    def validate_runtime(self, request: RuntimeValidationRequest) -> RuntimeStatusResultView:
        return self._runtime_validation.validate_runtime(request)

    def runtime_smoke(self, request: RuntimeSmokeRequest) -> RuntimeStatusResultView:
        return self._runtime_validation.runtime_smoke(request)

    def evaluate_automation_preflight(self, request: AutomationPreflightRequest) -> AutomationPreflightResultView:
        return self._automation_preflight.evaluate(request)


class HttpRuntimeApiClient:
    def __init__(self, *, base_url: str) -> None:
        self._base_url = base_url.rstrip('/')

    def _get_json(self, path: str, *, params: dict[str, object] | None = None) -> dict[str, Any]:
        url = f'{self._base_url}{path}'
        if params:
            encoded = urlencode({key: str(value) for key, value in params.items() if value is not None})
            if encoded:
                url = f'{url}?{encoded}'
        with urlopen(url) as response:  # noqa: S310
            return json.loads(response.read().decode('utf-8'))

    def _post_json(self, path: str, payload: object) -> dict[str, Any]:
        body = json.dumps(_to_jsonable(payload)).encode('utf-8')
        request = Request(
            f'{self._base_url}{path}',
            data=body,
            headers={'Content-Type': 'application/json'},
            method='POST',
        )
        with urlopen(request) as response:  # noqa: S310
            return json.loads(response.read().decode('utf-8'))

    def ensure_topology(self, request: QueueRepoRootRequest) -> QueueOperationResult:
        payload = self._post_json('/runtime/queues/ensure-topology', request)
        return QueueOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def state_info(self, request: QueueRepoRootRequest) -> QueueOperationResult:
        payload = self._get_json('/runtime/queues/state-info', params={'repo_root': request.repo_root})
        return QueueOperationResult(payload=payload, exit_code=0)

    def check(self, request: QueueCheckRequest) -> QueueOperationResult:
        payload = self._post_json('/runtime/queues/check', request)
        return QueueOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def purge(self, request: QueuePurgeRequest) -> QueueOperationResult:
        payload = self._post_json('/runtime/queues/purge', request)
        return QueueOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def validate(self, request: QueueValidateRequest) -> QueueOperationResult:
        payload = self._post_json('/runtime/queues/validate', request)
        return QueueOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def send(self, request: QueueSendRequest) -> QueueOperationResult:
        payload = self._post_json('/runtime/queues/send', request)
        return QueueOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def claim_next(self, request: QueueClaimNextRequest) -> QueueOperationResult:
        payload = self._post_json('/runtime/queues/claim-next', request)
        return QueueOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def list_claims(self, request: QueueListClaimsRequest) -> QueueOperationResult:
        payload = self._post_json('/runtime/queues/list-claims', request)
        return QueueOperationResult(payload=payload, exit_code=0)

    def ack(self, request: QueueClaimActionRequest) -> QueueOperationResult:
        payload = self._post_json('/runtime/queues/ack', request)
        return QueueOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def requeue(self, request: QueueClaimActionRequest) -> QueueOperationResult:
        payload = self._post_json('/runtime/queues/requeue', request)
        return QueueOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def validate_packet(self, request: QueuePacketFileRequest) -> QueueOperationResult:
        payload = self._post_json('/runtime/queues/validate-packet', request)
        return QueueOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def send_packet(self, request: QueuePacketFileRequest) -> QueueOperationResult:
        payload = self._post_json('/runtime/queues/send-packet', request)
        return QueueOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def run_supervisor(self, request: RuntimeSupervisorRequest) -> RuntimeOperationResult:
        payload = self._post_json('/runtime/supervisor/run', request)
        return RuntimeOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def start_supervisor(self, request: RuntimeSupervisorRequest) -> RuntimeOperationResult:
        payload = self._post_json('/runtime/supervisor/start', request)
        return RuntimeOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def stop_supervisor(self, request: RuntimeStatusRequest) -> RuntimeOperationResult:
        payload = self._post_json('/runtime/supervisor/stop', request)
        return RuntimeOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def supervisor_status(self, request: RuntimeStatusRequest) -> RuntimeOperationResult:
        payload = self._get_json('/runtime/supervisor/status', params={'repo_root': request.repo_root})
        return RuntimeOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def supervisor_logs(self, request: RuntimeLogsRequest) -> str:
        payload = self._get_json('/runtime/supervisor/logs', params={'repo_root': request.repo_root, 'lines': request.lines})
        return str(payload.get('output', ''))

    def restart_supervisor(self, request: RuntimeSupervisorRequest) -> RuntimeOperationResult:
        payload = self._post_json('/runtime/supervisor/restart', request)
        return RuntimeOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def run_techlead_host(self, request: RuntimeHostRunRequest) -> RuntimeOperationResult:
        payload = self._post_json('/runtime/hosts/techlead', request)
        return RuntimeOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def run_dev_host(self, request: RuntimeHostRunRequest) -> RuntimeOperationResult:
        payload = self._post_json('/runtime/hosts/dev', request)
        return RuntimeOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def run_qa_host(self, request: RuntimeHostRunRequest) -> RuntimeOperationResult:
        payload = self._post_json('/runtime/hosts/qa', request)
        return RuntimeOperationResult(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def techlead_service_map(self) -> TechLeadServiceMapResultView:
        payload = self._get_json('/runtime/reports/techlead-service-map')
        return TechLeadServiceMapResultView(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def validate_runtime(self, request: RuntimeValidationRequest) -> RuntimeStatusResultView:
        payload = self._post_json('/runtime/status/validate', request)
        return RuntimeStatusResultView(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def runtime_smoke(self, request: RuntimeSmokeRequest) -> RuntimeStatusResultView:
        payload = self._post_json('/runtime/status/smoke', request)
        return RuntimeStatusResultView(payload=payload, exit_code=0 if payload.get('ok', True) else 1)

    def evaluate_automation_preflight(self, request: AutomationPreflightRequest) -> AutomationPreflightResultView:
        payload = self._post_json('/runtime/workflow/automation-preflight', request)
        return AutomationPreflightResultView(payload=payload, exit_code=0 if payload.get('ok', True) else 1)


__all__ = ['HttpRuntimeApiClient', 'InProcessRuntimeApiClient', 'RuntimeApiClient']

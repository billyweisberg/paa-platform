from __future__ import annotations

from paa_core.application.dto.runtime import (
    RuntimeHostRunRequest,
    RuntimeLogsRequest,
    RuntimeOperationResult,
    RuntimeStatusRequest,
    RuntimeSupervisorRequest,
)
from paa_core.runtime_control import (
    restart_runtime_supervisor,
    runtime_supervisor_logs,
    runtime_supervisor_status,
    start_runtime_supervisor,
    stop_runtime_supervisor,
)
from paa_core.runtime_hosts import (
    build_dev_runtime_host,
    build_qa_runtime_host,
    build_runtime_supervisor,
    build_techlead_runtime_host,
)


class DefaultRuntimeAdminApplicationService:
    def run_supervisor(self, request: RuntimeSupervisorRequest) -> RuntimeOperationResult:
        supervisor = build_runtime_supervisor(request.repo_root)
        result = supervisor.run(
            intake_mode=request.intake_mode,
            emit_next_assignment=request.emit_next_assignment,
            emit_worker_result=request.emit_worker_result,
            emit_verification=request.emit_verification,
            max_iterations=request.max_iterations,
            poll_interval_seconds=request.poll_interval_seconds,
        )
        return RuntimeOperationResult(payload=result, exit_code=0 if result.get('ok') else 1)

    def start_supervisor(self, request: RuntimeSupervisorRequest) -> RuntimeOperationResult:
        result = start_runtime_supervisor(
            request.repo_root,
            intake_mode=request.intake_mode,
            emit_next_assignment=request.emit_next_assignment,
            emit_worker_result=request.emit_worker_result,
            emit_verification=request.emit_verification,
            max_iterations=request.max_iterations,
            poll_interval_seconds=request.poll_interval_seconds,
        )
        return RuntimeOperationResult(payload=result, exit_code=0 if result.get('ok') else 1)

    def stop_supervisor(self, request: RuntimeStatusRequest) -> RuntimeOperationResult:
        result = stop_runtime_supervisor(request.repo_root)
        return RuntimeOperationResult(payload=result, exit_code=0 if result.get('ok') else 1)

    def supervisor_status(self, request: RuntimeStatusRequest) -> RuntimeOperationResult:
        return RuntimeOperationResult(payload=runtime_supervisor_status(request.repo_root), exit_code=0)

    def supervisor_logs(self, request: RuntimeLogsRequest) -> str:
        return runtime_supervisor_logs(request.repo_root, lines=request.lines)

    def restart_supervisor(self, request: RuntimeSupervisorRequest) -> RuntimeOperationResult:
        result = restart_runtime_supervisor(
            request.repo_root,
            intake_mode=request.intake_mode,
            emit_next_assignment=request.emit_next_assignment,
            emit_worker_result=request.emit_worker_result,
            emit_verification=request.emit_verification,
            max_iterations=request.max_iterations,
            poll_interval_seconds=request.poll_interval_seconds,
        )
        return RuntimeOperationResult(payload=result, exit_code=0 if result.get('ok') else 1)

    def run_techlead_host(self, request: RuntimeHostRunRequest) -> RuntimeOperationResult:
        host = build_techlead_runtime_host(request.repo_root, actor_name=request.actor_name, host_name=request.host_name)
        result = host.run_loop(
            intake_mode=request.intake_mode,
            emit_next_assignment=request.emit_next_assignment,
            max_iterations=request.max_iterations,
            poll_interval_seconds=request.poll_interval_seconds,
        )
        return RuntimeOperationResult(payload=result, exit_code=0 if result.get('ok') else 1)

    def run_dev_host(self, request: RuntimeHostRunRequest) -> RuntimeOperationResult:
        host = build_dev_runtime_host(request.repo_root, actor_name=request.actor_name, host_name=request.host_name)
        result = host.run_loop(
            intake_mode=request.intake_mode,
            emit_worker_result=request.emit_worker_result,
            max_iterations=request.max_iterations,
            poll_interval_seconds=request.poll_interval_seconds,
        )
        return RuntimeOperationResult(payload=result, exit_code=0 if result.get('ok') else 1)

    def run_qa_host(self, request: RuntimeHostRunRequest) -> RuntimeOperationResult:
        host = build_qa_runtime_host(request.repo_root, actor_name=request.actor_name, host_name=request.host_name)
        result = host.run_loop(
            intake_mode=request.intake_mode,
            emit_verification=request.emit_verification,
            max_iterations=request.max_iterations,
            poll_interval_seconds=request.poll_interval_seconds,
        )
        return RuntimeOperationResult(payload=result, exit_code=0 if result.get('ok') else 1)

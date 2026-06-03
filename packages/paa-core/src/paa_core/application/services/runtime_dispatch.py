from __future__ import annotations

from paa_core.application.dto.runtime import RuntimeDispatchRequest, RuntimeOperationResult
from paa_core.runtime_packet_dispatch import dispatch_packet, dispatch_techlead_packet


class DefaultRuntimeDispatchApplicationService:
    def dispatch_packet(self, request: RuntimeDispatchRequest) -> RuntimeOperationResult:
        result = dispatch_packet(request.repo_root, request.message_file)
        return RuntimeOperationResult(payload=result, exit_code=0 if result.get('ok') else 1)

    def dispatch_techlead_packet(self, request: RuntimeDispatchRequest) -> RuntimeOperationResult:
        result = dispatch_techlead_packet(request.repo_root, request.message_file)
        return RuntimeOperationResult(payload=result, exit_code=0 if result.get('ok') else 1)

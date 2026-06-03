from __future__ import annotations

from typing import Protocol

from paa_core.application.dto.runtime import RuntimeDispatchRequest, RuntimeOperationResult


class RuntimeDispatchService(Protocol):
    def dispatch_packet(self, request: RuntimeDispatchRequest) -> RuntimeOperationResult: ...
    def dispatch_techlead_packet(self, request: RuntimeDispatchRequest) -> RuntimeOperationResult: ...

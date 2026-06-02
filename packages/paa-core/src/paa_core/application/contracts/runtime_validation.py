from __future__ import annotations

from typing import Protocol

from paa_core.application.dto.status import RuntimeSmokeRequest, RuntimeStatusResultView, RuntimeValidationRequest


class RuntimeValidationService(Protocol):
    def validate_runtime(self, request: RuntimeValidationRequest) -> RuntimeStatusResultView: ...
    def runtime_smoke(self, request: RuntimeSmokeRequest) -> RuntimeStatusResultView: ...

from __future__ import annotations

from typing import Protocol

from paa_core.application.dto.runtime import RuntimeInstallRequest, RuntimeOperationResult


class RuntimeInstallService(Protocol):
    def install_runtime(self, request: RuntimeInstallRequest) -> RuntimeOperationResult: ...
    def update_runtime(self, request: RuntimeInstallRequest) -> RuntimeOperationResult: ...

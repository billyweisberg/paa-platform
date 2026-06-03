from __future__ import annotations

from paa_core.application.dto.status import RuntimeSmokeRequest, RuntimeStatusResultView, RuntimeValidationRequest
from paa_core.runtime_guardrails import validate_runtime_install
from paa_core.runtime.control.smoke import run_runtime_smoke_test


class DefaultRuntimeValidationApplicationService:
    def validate_runtime(self, request: RuntimeValidationRequest) -> RuntimeStatusResultView:
        result = validate_runtime_install(request.repo_root, expected_branch=request.expected_branch)
        return RuntimeStatusResultView(payload=result, exit_code=0 if result.get('ok') else 1)

    def runtime_smoke(self, request: RuntimeSmokeRequest) -> RuntimeStatusResultView:
        result = run_runtime_smoke_test(
            request.repo_root,
            expected_branch=request.expected_branch,
            output_path=request.output_path,
        )
        return RuntimeStatusResultView(payload=result, exit_code=0 if result.get('ok') else 1)

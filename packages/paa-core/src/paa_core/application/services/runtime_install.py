from __future__ import annotations

from paa_core.application.dto.runtime import RuntimeInstallRequest, RuntimeOperationResult
from paa_core.install import install_runtime_support


class DefaultRuntimeInstallApplicationService:
    def install_runtime(self, request: RuntimeInstallRequest) -> RuntimeOperationResult:
        return self._run(request)

    def update_runtime(self, request: RuntimeInstallRequest) -> RuntimeOperationResult:
        return self._run(request)

    @staticmethod
    def _run(request: RuntimeInstallRequest) -> RuntimeOperationResult:
        result = install_runtime_support(request.repo_root, project_pack=request.project_pack)
        return RuntimeOperationResult(
            payload={
                'ok': True,
                'install_mode': result.install_mode,
                'repo_root': str(result.repo_root),
                'codex_install_root': str(result.codex_install_root),
                'runtime_data_root': str(result.runtime_data_root),
                'platform_revision': result.platform_revision,
                'project_pack': result.project_pack,
            },
            exit_code=0,
        )

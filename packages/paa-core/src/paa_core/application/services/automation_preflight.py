from __future__ import annotations

from paa_core.application.dto.workflow import AutomationPreflightRequest, AutomationPreflightResultView
from paa_core.services.automation_preflight import DefaultAutomationPreflightService


class DefaultAutomationPreflightApplicationService:
    def __init__(self, *, automation_preflight_service: DefaultAutomationPreflightService | None = None) -> None:
        self._automation_preflight_service = automation_preflight_service or DefaultAutomationPreflightService()

    def evaluate(self, request: AutomationPreflightRequest) -> AutomationPreflightResultView:
        result = self._automation_preflight_service.evaluate(
            repo_root=request.repo_root,
            target_role=request.target_role,
            project_slug=request.project_slug,
        )
        return AutomationPreflightResultView(payload=result, exit_code=0 if result.get('ok') else 1)

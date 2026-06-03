# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from paa_core.api.runtime.dependencies import get_automation_preflight_service
from paa_core.application.dto.workflow import AutomationPreflightRequest
from paa_core.application.services import DefaultAutomationPreflightApplicationService

router = APIRouter(prefix='/runtime/workflow', tags=['runtime-workflow'])


class AutomationPreflightModel(BaseModel):
    repo_root: str
    project_slug: str = 'paa-platform'
    target_role: str


@router.post('/automation-preflight')
def automation_preflight(
    request: AutomationPreflightModel,
    service: DefaultAutomationPreflightApplicationService = Depends(get_automation_preflight_service),
) -> dict[str, object]:
    return service.evaluate(
        AutomationPreflightRequest(
            repo_root=Path(request.repo_root).resolve(),
            project_slug=request.project_slug,
            target_role=request.target_role,
        )
    ).payload

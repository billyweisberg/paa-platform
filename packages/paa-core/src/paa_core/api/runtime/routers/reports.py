# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false
from __future__ import annotations

from fastapi import APIRouter, Depends

from paa_core.api.runtime.dependencies import get_runtime_report_service
from paa_core.application.services import DefaultRuntimeReportApplicationService

router = APIRouter(prefix='/runtime/reports', tags=['runtime-reports'])


@router.get('/techlead-service-map')
def techlead_service_map(
    service: DefaultRuntimeReportApplicationService = Depends(get_runtime_report_service),
) -> dict[str, object]:
    return service.techlead_service_map().payload

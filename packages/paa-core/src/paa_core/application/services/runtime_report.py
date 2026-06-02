from __future__ import annotations

from paa_core.application.dto.status import TechLeadServiceMapResultView
from paa_core.techlead_service_map import build_techlead_service_map


class DefaultRuntimeReportApplicationService:
    def techlead_service_map(self) -> TechLeadServiceMapResultView:
        return TechLeadServiceMapResultView(payload=build_techlead_service_map(), exit_code=0)

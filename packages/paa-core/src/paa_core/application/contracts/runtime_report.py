from __future__ import annotations

from typing import Protocol

from paa_core.application.dto.status import TechLeadServiceMapResultView


class RuntimeReportService(Protocol):
    def techlead_service_map(self) -> TechLeadServiceMapResultView: ...

from __future__ import annotations

from typing import Protocol

from paa_core.application.dto.workflow import AutomationPreflightRequest, AutomationPreflightResultView


class AutomationPreflightService(Protocol):
    def evaluate(self, request: AutomationPreflightRequest) -> AutomationPreflightResultView: ...

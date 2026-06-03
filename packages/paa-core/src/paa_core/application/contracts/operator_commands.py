from __future__ import annotations

from typing import Protocol

from paa_core.application.dto.operator import OperatorCommandRequest, OperatorCommandResult


class OperatorCommandService(Protocol):
    def run_command(self, request: OperatorCommandRequest) -> OperatorCommandResult: ...
    def supports_command_family(self, command_family: str) -> bool: ...

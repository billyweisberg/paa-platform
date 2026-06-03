from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from paa_core.application.dto.operator import OperatorCommandRequest, OperatorCommandResult


class OperatorCommandAdapter(Protocol):
    def run(self, request: OperatorCommandRequest) -> OperatorCommandResult: ...


@dataclass(frozen=True)
class CommandRegistration:
    command_family: str
    adapter: OperatorCommandAdapter


class CommandRouter:
    def __init__(self, registrations: tuple[CommandRegistration, ...]) -> None:
        self._registrations = {item.command_family: item.adapter for item in registrations}

    def supports_command_family(self, command_family: str) -> bool:
        return command_family in self._registrations

    def route(self, request: OperatorCommandRequest) -> OperatorCommandResult:
        adapter = self._registrations.get(request.command.command_family)
        if adapter is None:
            raise KeyError(f"Unsupported command family: {request.command.command_family}")
        return adapter.run(request)


__all__ = ['CommandRegistration', 'CommandRouter', 'OperatorCommandAdapter']

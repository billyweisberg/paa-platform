"""Command-routing support for the PAA operator CLI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .models import OperatorCommandRequest, OperatorCommandResult


class OperatorCommandAdapter(Protocol):
    """Handle one command-family request."""

    def run(self, request: OperatorCommandRequest) -> OperatorCommandResult:
        """Execute the request for one command family."""
        ...


@dataclass(frozen=True)
class CommandRegistration:
    """One routed command-family registration."""

    command_family: str
    adapter: OperatorCommandAdapter


class CommandRouter:
    """Route normalized operator requests to the correct adapter."""

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

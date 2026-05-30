"""Contracts for the PAA operator CLI host surface."""

from __future__ import annotations

from typing import Protocol

from paa_core.services.implementation_plan_derivation.contracts import StructuredLogger

from .models import OperatorCommandRequest, OperatorCommandResult


class PAAOperatorCLI(Protocol):
    """Run one normalized operator command against the unified PAA CLI boundary."""

    @property
    def logger(self) -> StructuredLogger:
        """Return the injected structured logger."""
        ...

    def run_command(self, request: OperatorCommandRequest) -> OperatorCommandResult:
        """Execute one normalized operator command request and return a structured result object."""
        ...

    def supports_command_family(self, command_family: str) -> bool:
        """Return whether this CLI host supports the named command family."""
        ...

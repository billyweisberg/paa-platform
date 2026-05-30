"""Contracts for the PAA operator CLI host surface."""

from __future__ import annotations

from typing import Any, Protocol

from paa_core.services.implementation_plan_derivation.contracts import StructuredLogger


class PAAOperatorCLI(Protocol):
    """Run one normalized operator command against the unified PAA CLI boundary."""

    @property
    def logger(self) -> StructuredLogger:
        """Return the injected structured logger."""
        ...

    def run_command(self, request: Any) -> Any:
        """Execute one normalized operator command request and return a structured result object."""
        ...

    def supports_command_family(self, command_family: str) -> bool:
        """Return whether this CLI host supports the named command family."""
        ...

"""Contracts for the methodology execution preflight service."""

from __future__ import annotations

from typing import Protocol

from paa_core.repositories.methodology_execution import MethodologyExecutionRepository
from paa_core.services.implementation_plan_derivation.contracts import StructuredLogger
from paa_core.services.methodology_execution_projection import MethodologyExecutionProjectionService
from paa_core.services.methodology_execution_state import MethodologyExecutionStateService

from .models import (
    MethodologyExecutionPreflightOutcome,
    MethodologyExecutionPreflightRequest,
    MethodologyExecutionPreflightResult,
)


class MethodologyExecutionPreflightService(Protocol):
    """Classify command requests against current methodology pointer truth."""

    @property
    def methodology_execution_repository(self) -> MethodologyExecutionRepository:
        """Return the injected methodology-execution repository."""
        ...

    @property
    def methodology_execution_state_service(self) -> MethodologyExecutionStateService:
        """Return the injected methodology-execution state service."""
        ...

    @property
    def methodology_execution_projection_service(self) -> MethodologyExecutionProjectionService:
        """Return the injected methodology-execution projection service."""
        ...

    @property
    def logger(self) -> StructuredLogger:
        """Return the injected structured logger."""
        ...

    def evaluate_command(
        self,
        request: MethodologyExecutionPreflightRequest,
    ) -> MethodologyExecutionPreflightResult:
        """Return a structured preflight result for one requested command action."""
        ...

    def supports_command_family(self, command_family: str) -> bool:
        """Return whether one command family is supported by the current preflight slice."""
        ...

    def supports_command(self, command_family: str, command_name: str) -> bool:
        """Return whether one command within a family is supported by the current preflight slice."""
        ...

    def blocked_outcome(
        self,
        request: MethodologyExecutionPreflightRequest,
        *,
        reason: str,
        details: str,
    ) -> MethodologyExecutionPreflightOutcome:
        """Return one structured blocked outcome for a request."""
        ...


__all__ = [
    'MethodologyExecutionPreflightOutcome',
    'MethodologyExecutionPreflightRequest',
    'MethodologyExecutionPreflightResult',
    'MethodologyExecutionPreflightService',
    'MethodologyExecutionProjectionService',
    'MethodologyExecutionStateService',
    'StructuredLogger',
]

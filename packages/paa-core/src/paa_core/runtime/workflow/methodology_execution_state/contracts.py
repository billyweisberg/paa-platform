"""Contracts for the methodology execution state service."""

from __future__ import annotations

from typing import Protocol

from paa_core.repositories.methodology_execution import MethodologyExecutionRepository
from paa_core.services.implementation_plan_derivation.contracts import StructuredLogger

from .models import (
    MethodologyExecutionStateRequest,
    MethodologyExecutionStateResult,
    MethodologyExecutionStateSummary,
)


class MethodologyExecutionStateService(Protocol):
    """Coordinate current methodology pointer loading and state transitions."""

    @property
    def methodology_execution_repository(self) -> MethodologyExecutionRepository:
        """Return the injected methodology-execution repository."""
        ...

    @property
    def logger(self) -> StructuredLogger:
        """Return the injected structured logger."""
        ...

    def get_current_methodology_execution(self, methodology_execution_id: str) -> MethodologyExecutionStateSummary:
        """Return a structured current-state view for one methodology execution thread."""
        ...

    def find_current_methodology_execution(
        self,
        project_id: str,
        work_item_id: str,
        component_id: str | None = None,
    ) -> MethodologyExecutionStateSummary | None:
        """Resolve current methodology state by primary business anchors."""
        ...

    def apply_transition(
        self,
        request: MethodologyExecutionStateRequest,
    ) -> MethodologyExecutionStateResult:
        """Apply one supported methodology state transition."""
        ...

    def supports_transition(self, transition_key: str) -> bool:
        """Return whether one transition key is supported by the current service slice."""
        ...

__all__ = [
    'MethodologyExecutionStateRequest',
    'MethodologyExecutionStateResult',
    'MethodologyExecutionStateService',
    'MethodologyExecutionStateSummary',
    'StructuredLogger',
]

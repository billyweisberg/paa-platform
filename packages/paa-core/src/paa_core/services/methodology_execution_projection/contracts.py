"""Contracts for the methodology execution projection service."""

from __future__ import annotations

from typing import Protocol

from paa_core.repositories.methodology_execution import MethodologyExecutionRepository
from paa_core.services.implementation_plan_derivation.contracts import StructuredLogger

from .models import (
    MethodologyExecutionExplainProjection,
    MethodologyExecutionNextActionProjection,
    MethodologyExecutionProjectionRequest,
    MethodologyExecutionProjectionResult,
    MethodologyExecutionStatusProjection,
)


class MethodologyExecutionProjectionService(Protocol):
    """Project current methodology pointer truth into operator-facing read surfaces."""

    @property
    def methodology_execution_repository(self) -> MethodologyExecutionRepository:
        """Return the injected methodology-execution repository."""
        ...

    @property
    def logger(self) -> StructuredLogger:
        """Return the injected structured logger."""
        ...

    def get_status_projection(self, methodology_execution_id: str) -> MethodologyExecutionStatusProjection:
        """Return a structured current-status projection for one methodology execution thread."""
        ...

    def find_status_projection(
        self,
        project_id: str,
        work_item_id: str,
        component_id: str | None = None,
    ) -> MethodologyExecutionStatusProjection | None:
        """Resolve a current-status projection by primary business anchors."""
        ...

    def get_next_action_projection(self, methodology_execution_id: str) -> MethodologyExecutionNextActionProjection:
        """Return a structured next-action projection for one methodology execution thread."""
        ...

    def explain_current_methodology_execution(
        self,
        methodology_execution_id: str,
    ) -> MethodologyExecutionExplainProjection:
        """Return a structured explanation projection for one methodology execution thread."""
        ...

    def get_projection(
        self,
        request: MethodologyExecutionProjectionRequest,
    ) -> MethodologyExecutionProjectionResult:
        """Return a structured projection result for the requested projection mode."""
        ...


__all__ = [
    'MethodologyExecutionExplainProjection',
    'MethodologyExecutionNextActionProjection',
    'MethodologyExecutionProjectionRequest',
    'MethodologyExecutionProjectionResult',
    'MethodologyExecutionProjectionService',
    'MethodologyExecutionStatusProjection',
    'StructuredLogger',
]

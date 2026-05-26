"""Contracts for the TechLead assignment decision service."""

from __future__ import annotations

from typing import Protocol

from paa_core.services.implementation_plan_derivation.contracts import StructuredLogger

from .models import (
    TechLeadAssignmentDecisionRequest,
    TechLeadAssignmentDecisionResult,
)


class TechLeadAssignmentDecisionService(Protocol):
    """Derive the next supported assignment decision for one active slice."""

    @property
    def logger(self) -> StructuredLogger:
        """Return the injected structured logger."""
        ...

    def derive_assignment_decision(
        self,
        request: TechLeadAssignmentDecisionRequest,
    ) -> TechLeadAssignmentDecisionResult:
        """Return one structured assignment-decision result from the provided request context."""
        ...

    def supports_assignment_for_stage(
        self,
        workflow_stage: str,
        source_packet_schema_type: str | None = None,
    ) -> bool:
        """Return whether the current slice supports assignment derivation for this stage."""
        ...


__all__ = [
    'StructuredLogger',
    'TechLeadAssignmentDecisionRequest',
    'TechLeadAssignmentDecisionResult',
    'TechLeadAssignmentDecisionService',
]

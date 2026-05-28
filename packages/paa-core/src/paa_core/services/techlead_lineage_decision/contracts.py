"""Contracts for the TechLead lineage decision service."""

from __future__ import annotations

from typing import Protocol

from paa_core.services.implementation_plan_derivation.contracts import StructuredLogger

from .models import TechLeadLineageDecisionRequest, TechLeadLineageDecisionResult


class TechLeadLineageDecisionService(Protocol):
    """Derive supported lineage decisions for one active slice."""

    @property
    def logger(self) -> StructuredLogger:
        """Return the injected structured logger."""
        ...

    def derive_lineage_decision(
        self,
        request: TechLeadLineageDecisionRequest,
    ) -> TechLeadLineageDecisionResult:
        """Return one structured lineage decision from the provided superseded-lineage context."""
        ...

    def supports_lineage_decision(
        self,
        workflow_stage: str,
        lineage_state: str | None = None,
        superseded_escalation_type: str | None = None,
    ) -> bool:
        """Return whether the current slice supports lineage routing for this stage."""
        ...


__all__ = [
    'StructuredLogger',
    'TechLeadLineageDecisionRequest',
    'TechLeadLineageDecisionResult',
    'TechLeadLineageDecisionService',
]

"""Contracts for the TechLead acceptance decision service."""

from __future__ import annotations

from typing import Protocol

from paa_core.services.implementation_plan_derivation.contracts import StructuredLogger

from .models import (
    TechLeadAcceptanceDecisionRequest,
    TechLeadAcceptanceDecisionResult,
)


class TechLeadAcceptanceDecisionService(Protocol):
    """Derive supported acceptance and closeout decisions for one active slice."""

    @property
    def logger(self) -> StructuredLogger:
        """Return the injected structured logger."""
        ...

    def derive_acceptance_decision(
        self,
        request: TechLeadAcceptanceDecisionRequest,
    ) -> TechLeadAcceptanceDecisionResult:
        """Return one structured acceptance-decision result from the provided QA-result context."""
        ...

    def supports_acceptance_decision(
        self,
        workflow_stage: str,
        qa_result_type: str | None = None,
    ) -> bool:
        """Return whether the current slice supports acceptance-decision derivation for this stage."""
        ...


__all__ = [
    'StructuredLogger',
    'TechLeadAcceptanceDecisionRequest',
    'TechLeadAcceptanceDecisionResult',
    'TechLeadAcceptanceDecisionService',
]

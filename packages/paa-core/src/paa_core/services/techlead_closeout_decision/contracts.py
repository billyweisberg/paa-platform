"""Contracts for the TechLead closeout decision service."""

from __future__ import annotations

from typing import Protocol

from paa_core.services.implementation_plan_derivation.contracts import StructuredLogger

from .models import (
    TechLeadCloseoutDecisionRequest,
    TechLeadCloseoutDecisionResult,
)


class TechLeadCloseoutDecisionService(Protocol):
    """Derive supported closeout decisions for one active slice."""

    @property
    def logger(self) -> StructuredLogger:
        """Return the injected structured logger."""
        ...

    def derive_closeout_decision(
        self,
        request: TechLeadCloseoutDecisionRequest,
    ) -> TechLeadCloseoutDecisionResult:
        """Return one structured closeout decision from the provided terminal QA-pass context."""
        ...

    def supports_closeout_decision(
        self,
        workflow_stage: str,
        decision_type: str | None = None,
        proof_only_mode: bool | None = None,
    ) -> bool:
        """Return whether the current slice supports closeout derivation for this stage."""
        ...


__all__ = [
    'StructuredLogger',
    'TechLeadCloseoutDecisionRequest',
    'TechLeadCloseoutDecisionResult',
    'TechLeadCloseoutDecisionService',
]

"""Contracts for the TechLead reset recovery decision service."""

from __future__ import annotations

from typing import Protocol

from paa_core.services.implementation_plan_derivation.contracts import StructuredLogger

from .models import (
    TechLeadResetRecoveryDecisionRequest,
    TechLeadResetRecoveryDecisionResult,
)


class TechLeadResetRecoveryDecisionService(Protocol):
    """Derive supported reset-recovery decisions for one active slice."""

    @property
    def logger(self) -> StructuredLogger:
        """Return the injected structured logger."""
        ...

    def derive_reset_recovery_decision(
        self,
        request: TechLeadResetRecoveryDecisionRequest,
    ) -> TechLeadResetRecoveryDecisionResult:
        """Return one structured reset-recovery decision from the provided lineage context."""
        ...

    def supports_reset_recovery_decision(
        self,
        workflow_stage: str,
        lineage_state: str | None = None,
        reset_escalation_type: str | None = None,
    ) -> bool:
        """Return whether the current slice supports reset-recovery routing for this stage."""
        ...


__all__ = [
    'StructuredLogger',
    'TechLeadResetRecoveryDecisionRequest',
    'TechLeadResetRecoveryDecisionResult',
    'TechLeadResetRecoveryDecisionService',
]

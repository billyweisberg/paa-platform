"""Contracts for the acceptance policy."""

from __future__ import annotations

from typing import Protocol

from .models import AcceptanceDecision, AcceptanceEvaluationContext, AcceptanceRequest


class AcceptancePolicy(Protocol):
    """Evaluate whether current evidence supports an acceptance outcome."""

    def evaluate_acceptance(
        self,
        request: AcceptanceRequest,
        context: AcceptanceEvaluationContext,
    ) -> AcceptanceDecision:
        """Return an allow/deny acceptance decision for one workflow result context."""
        ...


__all__ = ['AcceptancePolicy']

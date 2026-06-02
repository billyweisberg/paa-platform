"""Contracts for the reset recovery policy."""

from __future__ import annotations

from typing import Protocol

from .models import (
    ResetRecoveryDecision,
    ResetRecoveryEvaluationContext,
    ResetRecoveryRequest,
)


class ResetRecoveryPolicy(Protocol):
    """Evaluate whether workflow state requires retry, reset, or manual repair handling."""

    def evaluate_reset_recovery(
        self,
        request: ResetRecoveryRequest,
        context: ResetRecoveryEvaluationContext,
    ) -> ResetRecoveryDecision:
        """Return reset or repair guidance for one workflow state context."""
        ...


__all__ = ['ResetRecoveryPolicy']

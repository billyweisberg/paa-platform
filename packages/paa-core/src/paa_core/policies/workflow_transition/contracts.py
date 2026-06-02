"""Contracts for the workflow transition policy."""

from __future__ import annotations

from typing import Protocol

from .models import (
    WorkflowTransitionDecision,
    WorkflowTransitionEvaluationContext,
    WorkflowTransitionRequest,
)


class WorkflowTransitionPolicy(Protocol):
    """Evaluate whether a requested workflow transition is legal and what it implies."""

    def evaluate_transition(
        self,
        request: WorkflowTransitionRequest,
        context: WorkflowTransitionEvaluationContext,
    ) -> WorkflowTransitionDecision:
        """Return an allow/deny decision for one proposed workflow transition."""
        ...


__all__ = ['WorkflowTransitionPolicy']

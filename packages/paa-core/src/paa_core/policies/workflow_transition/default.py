"""Default implementation of the workflow transition policy."""

from __future__ import annotations

from .models import (
    WorkflowTransitionDecision,
    WorkflowTransitionEvaluationContext,
    WorkflowTransitionRequest,
)


class DefaultWorkflowTransitionPolicy:
    """Conservative first-slice transition policy.

    This policy intentionally stays narrow. It only:
    - enforces requested-from-stage alignment when provided
    - blocks transitions from obviously inconsistent state
    - passes through requested-to-stage when present
    """

    def evaluate_transition(
        self,
        request: WorkflowTransitionRequest,
        context: WorkflowTransitionEvaluationContext,
    ) -> WorkflowTransitionDecision:
        blocking: list[str] = []
        notes: list[str] = []

        if request.requested_from_stage and context.current_workflow_stage:
            if request.requested_from_stage != context.current_workflow_stage:
                blocking.append(
                    f"Requested from-stage {request.requested_from_stage!r} does not match current workflow stage {context.current_workflow_stage!r}."
                )

        if context.state_consistency in {'manual_repair_required', 'repair_required'}:
            blocking.append(
                f"Workflow state consistency {context.state_consistency!r} requires repair before transition."
            )

        resolved_to_stage = request.requested_to_stage
        if not resolved_to_stage:
            notes.append('No explicit requested_to_stage provided; caller must derive stage before applying workflow truth.')

        return WorkflowTransitionDecision(
            allowed=not blocking,
            resolved_to_stage=resolved_to_stage,
            rejection_code='illegal_transition' if blocking else None,
            blocking_reasons=tuple(blocking),
            notes=tuple(notes),
            metadata={
                'transition_type': request.transition_type,
                'current_workflow_stage': context.current_workflow_stage,
            },
        )


__all__ = ['DefaultWorkflowTransitionPolicy']

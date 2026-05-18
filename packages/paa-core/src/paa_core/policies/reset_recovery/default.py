"""Default implementation of the reset recovery policy."""

from __future__ import annotations

from .models import (
    ResetRecoveryDecision,
    ResetRecoveryEvaluationContext,
    ResetRecoveryRequest,
)


class DefaultResetRecoveryPolicy:
    """Conservative first-slice reset and recovery policy."""

    def evaluate_reset_recovery(
        self,
        request: ResetRecoveryRequest,
        context: ResetRecoveryEvaluationContext,
    ) -> ResetRecoveryDecision:
        blocking: list[str] = []
        notes: list[str] = []

        requires_manual_repair = context.state_consistency in {'manual_repair_required', 'repair_required'}
        should_reset = context.active_claim_status in {'abandoned', 'expired'}
        should_retry = bool(request.retry_requested and not requires_manual_repair and not should_reset)

        if requires_manual_repair:
            blocking.append(
                f"Workflow state consistency {context.state_consistency!r} requires manual repair."
            )
        if should_reset:
            notes.append(
                f"Active claim status {context.active_claim_status!r} suggests reset or reassignment handling."
            )
        if should_retry:
            notes.append('Retry is permitted for the provided reset/recovery request.')

        return ResetRecoveryDecision(
            requires_manual_repair=requires_manual_repair,
            should_reset=should_reset,
            should_retry=should_retry,
            blocking_reasons=tuple(blocking),
            notes=tuple(notes),
            metadata={
                'workflow_stage': request.workflow_stage,
                'blocking_reason_code': context.blocking_reason_code,
            },
        )


__all__ = ['DefaultResetRecoveryPolicy']

"""Default implementation of the acceptance policy."""

from __future__ import annotations

from .models import AcceptanceDecision, AcceptanceEvaluationContext, AcceptanceRequest


class DefaultAcceptancePolicy:
    """Conservative first-slice acceptance policy."""

    def evaluate_acceptance(
        self,
        request: AcceptanceRequest,
        context: AcceptanceEvaluationContext,
    ) -> AcceptanceDecision:
        blocking: list[str] = []
        notes: list[str] = []

        if context.has_blocking_findings:
            blocking.append('Blocking findings are still open.')
        if context.protected_path_checks_passed is False:
            blocking.append('Protected-path checks have not passed.')
        if context.approved_contract_change is False:
            blocking.append('Contract or tolerance changes are not approved.')
        if request.verification_status and request.verification_status != 'pass':
            blocking.append(
                f"Verification status {request.verification_status!r} does not satisfy acceptance."
            )
        if request.merge_ready is False:
            blocking.append('The slice is not marked merge-ready.')

        accepted = not blocking
        if accepted:
            notes.append('Acceptance criteria satisfied for the provided result context.')

        return AcceptanceDecision(
            accepted=accepted,
            terminal=accepted,
            acceptance_code='accepted' if accepted else None,
            blocking_reasons=tuple(blocking),
            notes=tuple(notes),
            metadata={
                'result_schema_type': request.result_schema_type,
                'workflow_stage': request.workflow_stage,
            },
        )


__all__ = ['DefaultAcceptancePolicy']

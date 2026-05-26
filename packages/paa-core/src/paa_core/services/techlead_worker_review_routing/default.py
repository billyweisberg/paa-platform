"""Default implementation for the TechLead worker review routing service."""

from __future__ import annotations

from datetime import datetime, timezone

from paa_core.services.implementation_plan_derivation.contracts import StructuredLogger
from paa_core.services.workflow_lifecycle import WorkflowLifecycleService

from .models import (
    TechLeadWorkerReviewRoutingRequest,
    TechLeadWorkerReviewRoutingResult,
    TechLeadWorkerReviewRoutingSummary,
)


class _NullStructuredLogger:
    def info(self, event: str, **fields: object) -> None:
        return None

    def warning(self, event: str, **fields: object) -> None:
        return None


class DefaultTechLeadWorkerReviewRoutingService:
    """Derive supported worker-review routing decisions from resolved runtime context."""

    _SUPPORTED_STAGES = frozenset({'techlead_dev_review_pending', 'techlead_worker_review_pending'})
    _SUPPORTED_RESULT_TYPES = frozenset(
        {
            'implemented_ready_for_qa',
            'blocked',
            'needs_clarification',
            'cannot_complete_without_scope_change',
            'superseded_by_branch_reset',
        }
    )
    _RECOMMENDATION_BY_RESULT_TYPE = {
        'implemented_ready_for_qa': ('assign_qa', 'QA', True, ('ready-for-qa',)),
        'blocked': ('return_to_delivery_architect', 'Delivery Architect', False, ('blocked-worker-result',)),
        'needs_clarification': ('return_to_delivery_architect', 'Delivery Architect', False, ('clarification-required',)),
        'cannot_complete_without_scope_change': (
            'escalate_to_authority_architect',
            'Architect',
            False,
            ('scope-change-required',),
        ),
        'superseded_by_branch_reset': ('reset_branch', 'Python Dev', False, ('branch-reset-required',)),
    }

    def __init__(
        self,
        *,
        logger: StructuredLogger | None = None,
        workflow_lifecycle_service: WorkflowLifecycleService | None = None,
        clock: callable | None = None,
    ) -> None:
        self._logger = logger if logger is not None else _NullStructuredLogger()
        self._workflow_lifecycle_service = workflow_lifecycle_service
        self._clock = clock if clock is not None else self._default_clock

    @property
    def logger(self) -> StructuredLogger:
        return self._logger

    @property
    def workflow_lifecycle_service(self) -> WorkflowLifecycleService | None:
        return self._workflow_lifecycle_service

    def derive_worker_review_routing(
        self,
        request: TechLeadWorkerReviewRoutingRequest,
    ) -> TechLeadWorkerReviewRoutingResult:
        normalized_stage = request.workflow_stage.strip()
        normalized_worker_role = request.worker_role.strip()
        normalized_result_type = request.worker_result_type.strip()

        self._logger.info(
            'techlead_worker_review_routing.derive_worker_review_routing.start',
            project_slug=request.project_slug,
            issue_number=request.issue_number,
            workflow_stage=normalized_stage,
            worker_role=normalized_worker_role,
            worker_result_type=normalized_result_type,
        )

        if request.issue_number <= 0:
            return self._build_rejected_result(
                request,
                reason='missing_issue_number',
                details='The worker-review routing request must include a positive issue number.',
                blocking_reasons=('missing_issue_number',),
                notes=('issue-number-required',),
            )

        if not normalized_stage:
            return self._build_rejected_result(
                request,
                reason='missing_workflow_stage',
                details='The worker-review routing request must include a workflow stage.',
                blocking_reasons=('missing_workflow_stage',),
                notes=('workflow-stage-required',),
            )

        if not normalized_worker_role:
            return self._build_rejected_result(
                request,
                reason='missing_worker_role',
                details='The worker-review routing request must include the returning worker role.',
                blocking_reasons=('missing_worker_role',),
                notes=('worker-role-required',),
            )

        if not normalized_result_type:
            return self._build_rejected_result(
                request,
                reason='missing_worker_result_type',
                details='The worker-review routing request must include a worker result type.',
                blocking_reasons=('missing_worker_result_type',),
                notes=('worker-result-type-required',),
            )

        if not self.supports_worker_review_routing(normalized_stage, normalized_result_type):
            return self._build_rejected_result(
                request,
                reason='unsupported_worker_review_routing',
                details=(
                    f'Current workflow stage {normalized_stage!r} and worker result type '
                    f'{normalized_result_type!r} are not supported in this slice.'
                ),
                blocking_reasons=('unsupported_worker_review_routing',),
                notes=('fail-closed',),
            )

        recommended_next_decision, recommended_target_role, qa_assignment_allowed, notes = (
            self._RECOMMENDATION_BY_RESULT_TYPE[normalized_result_type]
        )
        summary = TechLeadWorkerReviewRoutingSummary(
            decision_supported=True,
            recommended_next_decision=recommended_next_decision,
            recommended_target_role=recommended_target_role,
            qa_assignment_allowed=qa_assignment_allowed,
            review_summary=(
                f'TechLead reviewed the {normalized_worker_role} worker result for issue '
                f'#{request.issue_number} and recommends {recommended_next_decision}.'
            ),
            blocking_reasons=(),
            notes=notes,
        )
        result = self._build_supported_result(request, summary=summary)
        self._logger.info(
            'techlead_worker_review_routing.derive_worker_review_routing.supported',
            issue_number=request.issue_number,
            workflow_stage=normalized_stage,
            worker_role=normalized_worker_role,
            worker_result_type=normalized_result_type,
            recommended_next_decision=recommended_next_decision,
            recommended_target_role=recommended_target_role,
        )
        return result

    def supports_worker_review_routing(
        self,
        workflow_stage: str,
        worker_result_type: str | None = None,
    ) -> bool:
        normalized_stage = workflow_stage.strip()
        if normalized_stage not in self._SUPPORTED_STAGES:
            return False
        if worker_result_type is None:
            return True
        return worker_result_type.strip() in self._SUPPORTED_RESULT_TYPES

    def _build_supported_result(
        self,
        request: TechLeadWorkerReviewRoutingRequest,
        *,
        summary: TechLeadWorkerReviewRoutingSummary,
    ) -> TechLeadWorkerReviewRoutingResult:
        return TechLeadWorkerReviewRoutingResult(
            project_slug=request.project_slug,
            issue_number=request.issue_number,
            pr_number=request.pr_number,
            workflow_stage=request.workflow_stage,
            worker_role=request.worker_role,
            worker_result_type=request.worker_result_type,
            source_packet_schema_type=request.source_packet_schema_type,
            source_packet_message_id=request.source_packet_message_id,
            summary=summary,
            ok=True,
            reason=None,
            details=None,
            recommended_actions=(summary.recommended_next_decision,) if summary.recommended_next_decision else None,
            unattended_safe=True,
            metadata=self._base_metadata(request),
        )

    def _build_rejected_result(
        self,
        request: TechLeadWorkerReviewRoutingRequest,
        *,
        reason: str,
        details: str,
        blocking_reasons: tuple[str, ...],
        notes: tuple[str, ...],
    ) -> TechLeadWorkerReviewRoutingResult:
        self._logger.warning(
            'techlead_worker_review_routing.derive_worker_review_routing.rejected',
            issue_number=request.issue_number,
            workflow_stage=request.workflow_stage,
            worker_role=request.worker_role,
            worker_result_type=request.worker_result_type,
            reason=reason,
        )
        summary = TechLeadWorkerReviewRoutingSummary(
            decision_supported=False,
            recommended_next_decision=None,
            recommended_target_role=None,
            qa_assignment_allowed=False,
            review_summary='No supported worker-review routing decision is available for this slice.',
            blocking_reasons=blocking_reasons,
            notes=notes,
        )
        metadata = self._base_metadata(request)
        metadata['rejected_at'] = self._clock()
        return TechLeadWorkerReviewRoutingResult(
            project_slug=request.project_slug,
            issue_number=request.issue_number,
            pr_number=request.pr_number,
            workflow_stage=request.workflow_stage,
            worker_role=request.worker_role,
            worker_result_type=request.worker_result_type,
            source_packet_schema_type=request.source_packet_schema_type,
            source_packet_message_id=request.source_packet_message_id,
            summary=summary,
            ok=False,
            reason=reason,
            details=details,
            recommended_actions=None,
            unattended_safe=False,
            metadata=metadata,
        )

    def _base_metadata(
        self,
        request: TechLeadWorkerReviewRoutingRequest,
    ) -> dict[str, object]:
        metadata: dict[str, object] = dict(request.metadata or {})
        metadata.setdefault('workflow_lifecycle_result_supplied', request.workflow_lifecycle_result is not None)
        metadata.setdefault('service_component', 'TechLeadWorkerReviewRoutingService')
        return metadata

    def _default_clock(self) -> str:
        return datetime.now(timezone.utc).isoformat()


__all__ = ['DefaultTechLeadWorkerReviewRoutingService']

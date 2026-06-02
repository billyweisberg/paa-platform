"""Default implementation for the TechLead delivery review decision service."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from paa_core.services.implementation_plan_derivation.contracts import StructuredLogger

from .models import (
    TechLeadDeliveryReviewDecisionRequest,
    TechLeadDeliveryReviewDecisionResult,
    TechLeadDeliveryReviewDecisionSummary,
)


class _NullStructuredLogger:
    def info(self, event: str, **fields: object) -> None:
        return None

    def warning(self, event: str, **fields: object) -> None:
        return None


class DefaultTechLeadDeliveryReviewDecisionService:
    """Derive supported delivery-review routing decisions from resolved runtime context."""

    _SUPPORTED_STAGES = frozenset({'techlead_delivery_review_pending'})
    _SUPPORTED_RESULT_TYPES = frozenset({'ready_for_dev'})

    def __init__(
        self,
        *,
        logger: StructuredLogger | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._logger = logger if logger is not None else _NullStructuredLogger()
        self._clock = clock if clock is not None else self._default_clock

    @property
    def logger(self) -> StructuredLogger:
        return self._logger

    def derive_delivery_review_decision(
        self,
        request: TechLeadDeliveryReviewDecisionRequest,
    ) -> TechLeadDeliveryReviewDecisionResult:
        normalized_stage = request.workflow_stage.strip()
        normalized_result_type = request.delivery_review_result_type.strip()
        normalized_action_name = (request.recommended_action_name or '').strip()

        self._logger.info(
            'techlead_delivery_review_decision.derive_delivery_review_decision.start',
            project_slug=request.project_slug,
            issue_number=request.issue_number,
            workflow_stage=normalized_stage,
            delivery_review_result_type=normalized_result_type,
            recommended_action_name=normalized_action_name,
            recommended_target_role=request.recommended_target_role,
        )

        if request.issue_number <= 0:
            return self._build_rejected_result(
                request,
                reason='missing_issue_number',
                details='The delivery-review decision request must include a positive issue number.',
                blocking_reasons=('missing_issue_number',),
                notes=('issue-number-required',),
            )

        if not normalized_stage:
            return self._build_rejected_result(
                request,
                reason='missing_workflow_stage',
                details='The delivery-review decision request must include a workflow stage.',
                blocking_reasons=('missing_workflow_stage',),
                notes=('workflow-stage-required',),
            )

        if not normalized_result_type:
            return self._build_rejected_result(
                request,
                reason='missing_delivery_review_result_type',
                details='The delivery-review decision request must include a delivery review result type.',
                blocking_reasons=('missing_delivery_review_result_type',),
                notes=('delivery-review-result-type-required',),
            )

        if not self.supports_delivery_review_decision(normalized_stage, normalized_result_type):
            return self._build_rejected_result(
                request,
                reason='unsupported_delivery_review_decision',
                details=(
                    f'Current workflow stage {normalized_stage!r} and delivery review result type '
                    f'{normalized_result_type!r} are not supported in this slice.'
                ),
                blocking_reasons=('unsupported_delivery_review_decision',),
                notes=('fail-closed',),
            )

        if normalized_action_name != 'assign_worker':
            return self._build_rejected_result(
                request,
                reason='delivery_review_ready_for_dev_without_assign_worker',
                details='Delivery review reported ready_for_dev, but the recommended TechLead action was not assign_worker.',
                blocking_reasons=('delivery_review_ready_for_dev_without_assign_worker',),
                notes=('assign-worker-required',),
            )

        if not request.resolved_team_worker_key or not request.resolved_team_worker_display_name:
            return self._build_rejected_result(
                request,
                reason='delivery_review_ready_for_dev_target_not_supported',
                details=(
                    'Delivery review recommended assign_worker, but the target role did not resolve to an '
                    'active Team Worker Role in the registry.'
                ),
                blocking_reasons=('delivery_review_ready_for_dev_target_not_supported',),
                notes=('team-worker-resolution-required',),
            )

        summary = TechLeadDeliveryReviewDecisionSummary(
            decision_supported=True,
            recommended_next_decision='assign_worker',
            recommended_target_role=request.resolved_team_worker_display_name,
            assignment_allowed=True,
            delivery_review_summary=(
                f'TechLead reviewed Delivery Architect result {normalized_result_type} for issue '
                f'#{request.issue_number} and recommends assign_worker to '
                f'{request.resolved_team_worker_display_name}.'
            ),
            blocking_reasons=(),
            notes=('ready-for-dev',),
        )
        result = self._build_supported_result(request, summary=summary)
        self._logger.info(
            'techlead_delivery_review_decision.derive_delivery_review_decision.supported',
            issue_number=request.issue_number,
            workflow_stage=normalized_stage,
            delivery_review_result_type=normalized_result_type,
            recommended_target_role=request.resolved_team_worker_display_name,
        )
        return result

    def supports_delivery_review_decision(
        self,
        workflow_stage: str,
        delivery_review_result_type: str | None = None,
    ) -> bool:
        normalized_stage = workflow_stage.strip()
        if normalized_stage not in self._SUPPORTED_STAGES:
            return False
        if delivery_review_result_type is None:
            return True
        return delivery_review_result_type.strip() in self._SUPPORTED_RESULT_TYPES

    def _build_supported_result(
        self,
        request: TechLeadDeliveryReviewDecisionRequest,
        *,
        summary: TechLeadDeliveryReviewDecisionSummary,
    ) -> TechLeadDeliveryReviewDecisionResult:
        return TechLeadDeliveryReviewDecisionResult(
            project_slug=request.project_slug,
            issue_number=request.issue_number,
            issue_url=request.issue_url,
            pr_number=request.pr_number,
            pr_url=request.pr_url,
            workflow_stage=request.workflow_stage,
            delivery_review_result_type=request.delivery_review_result_type,
            recommended_action_name=request.recommended_action_name,
            recommended_target_role=request.recommended_target_role,
            resolved_team_worker_key=request.resolved_team_worker_key,
            resolved_team_worker_display_name=request.resolved_team_worker_display_name,
            source_packet_schema_type=request.source_packet_schema_type,
            source_packet_message_id=request.source_packet_message_id,
            source_packet_path=request.source_packet_path,
            branch_name=request.branch_name,
            summary=summary,
            ok=True,
            reason=request.recommended_reason,
            details=None,
            recommended_actions=(summary.recommended_next_decision,) if summary.recommended_next_decision else None,
            unattended_safe=True,
            metadata=self._base_metadata(request),
        )

    def _build_rejected_result(
        self,
        request: TechLeadDeliveryReviewDecisionRequest,
        *,
        reason: str,
        details: str,
        blocking_reasons: tuple[str, ...],
        notes: tuple[str, ...],
    ) -> TechLeadDeliveryReviewDecisionResult:
        self._logger.warning(
            'techlead_delivery_review_decision.derive_delivery_review_decision.rejected',
            issue_number=request.issue_number,
            workflow_stage=request.workflow_stage,
            delivery_review_result_type=request.delivery_review_result_type,
            reason=reason,
        )
        summary = TechLeadDeliveryReviewDecisionSummary(
            decision_supported=False,
            recommended_next_decision=None,
            recommended_target_role=None,
            assignment_allowed=False,
            delivery_review_summary='No supported delivery-review decision is available for this slice.',
            blocking_reasons=blocking_reasons,
            notes=notes,
        )
        metadata = self._base_metadata(request)
        metadata['rejected_at'] = self._clock()
        return TechLeadDeliveryReviewDecisionResult(
            project_slug=request.project_slug,
            issue_number=request.issue_number,
            issue_url=request.issue_url,
            pr_number=request.pr_number,
            pr_url=request.pr_url,
            workflow_stage=request.workflow_stage,
            delivery_review_result_type=request.delivery_review_result_type,
            recommended_action_name=request.recommended_action_name,
            recommended_target_role=request.recommended_target_role,
            resolved_team_worker_key=request.resolved_team_worker_key,
            resolved_team_worker_display_name=request.resolved_team_worker_display_name,
            source_packet_schema_type=request.source_packet_schema_type,
            source_packet_message_id=request.source_packet_message_id,
            source_packet_path=request.source_packet_path,
            branch_name=request.branch_name,
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
        request: TechLeadDeliveryReviewDecisionRequest,
    ) -> dict[str, object]:
        metadata: dict[str, object] = dict(request.metadata or {})
        metadata.setdefault('service_component', 'TechLeadDeliveryReviewDecisionService')
        metadata.setdefault('source_packet_present', request.source_packet_schema_type is not None)
        return metadata

    def _default_clock(self) -> str:
        return datetime.now(timezone.utc).isoformat()


__all__ = ['DefaultTechLeadDeliveryReviewDecisionService']

"""Default implementation for the TechLead acceptance decision service."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from paa_core.services.implementation_plan_derivation.contracts import StructuredLogger
from paa_core.runtime.workflow.workflow_lifecycle import WorkflowLifecycleService

from .models import (
    TechLeadAcceptanceDecisionRequest,
    TechLeadAcceptanceDecisionResult,
    TechLeadAcceptanceDecisionSummary,
)


class _NullStructuredLogger:
    def info(self, event: str, **fields: object) -> None:
        return None

    def warning(self, event: str, **fields: object) -> None:
        return None


class DefaultTechLeadAcceptanceDecisionService:
    """Derive supported acceptance and proof-close decisions from QA-result context."""

    _SUPPORTED_STAGES = frozenset({'techlead_qa_review_pending'})
    _SUPPORTED_QA_RESULT_TYPES = frozenset({'pass'})
    _SUPPORTED_SOURCE_SCHEMAS = frozenset({'qa_verification_packet'})

    def __init__(
        self,
        *,
        logger: StructuredLogger | None = None,
        workflow_lifecycle_service: WorkflowLifecycleService | None = None,
        clock: Callable[[], datetime] | None = None,
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

    def derive_acceptance_decision(
        self,
        request: TechLeadAcceptanceDecisionRequest,
    ) -> TechLeadAcceptanceDecisionResult:
        normalized_stage = request.workflow_stage.strip()
        normalized_result_type = request.qa_result_type.strip()
        source_schema = (request.source_packet_schema_type or '').strip() or None
        execution_mode = self._resolve_execution_mode(request)
        merge_ready = self._resolve_merge_ready(request)

        self._logger.info(
            'techlead_acceptance_decision.derive_acceptance_decision.start',
            project_slug=request.project_slug,
            issue_number=request.issue_number,
            workflow_stage=normalized_stage,
            qa_result_type=normalized_result_type,
            source_packet_schema_type=source_schema,
            execution_mode=execution_mode,
            merge_ready=merge_ready,
        )

        if request.issue_number <= 0:
            return self._build_rejected_result(
                request,
                reason='missing_issue_number',
                details='The acceptance decision request must include a positive issue number.',
                blocking_reasons=('missing_issue_number',),
                notes=('issue-number-required',),
            )

        if not normalized_stage:
            return self._build_rejected_result(
                request,
                reason='missing_workflow_stage',
                details='The acceptance decision request must include a workflow stage.',
                blocking_reasons=('missing_workflow_stage',),
                notes=('workflow-stage-required',),
            )

        if not normalized_result_type:
            return self._build_rejected_result(
                request,
                reason='missing_qa_result_type',
                details='The acceptance decision request must include a QA result type.',
                blocking_reasons=('missing_qa_result_type',),
                notes=('qa-result-type-required',),
            )

        if source_schema is not None and source_schema not in self._SUPPORTED_SOURCE_SCHEMAS:
            return self._build_rejected_result(
                request,
                reason='unsupported_source_packet_schema',
                details=(
                    f'Source packet schema {request.source_packet_schema_type!r} is not supported '
                    'by the current TechLeadAcceptanceDecisionService slice.'
                ),
                blocking_reasons=('unsupported_source_packet_schema',),
                notes=('fail-closed',),
            )

        if not self.supports_acceptance_decision(normalized_stage, normalized_result_type):
            return self._build_rejected_result(
                request,
                reason='unsupported_acceptance_decision',
                details=(
                    f'Current workflow stage {normalized_stage!r} and QA result type '
                    f'{normalized_result_type!r} are not supported in this slice.'
                ),
                blocking_reasons=('unsupported_acceptance_decision',),
                notes=('fail-closed',),
            )

        if execution_mode == 'proof_only':
            return self._derive_proof_only_closeout(request, execution_mode=execution_mode)

        if merge_ready is False:
            return self._build_rejected_result(
                request,
                reason='merge_not_ready_for_live_acceptance',
                details='Live-delivery acceptance requires merge-ready runtime context.',
                blocking_reasons=('merge_not_ready',),
                notes=('live-delivery-requires-merge-ready',),
            )

        return self._derive_prepare_merge(request, execution_mode=execution_mode)

    def supports_acceptance_decision(
        self,
        workflow_stage: str,
        qa_result_type: str | None = None,
    ) -> bool:
        normalized_stage = workflow_stage.strip()
        if normalized_stage not in self._SUPPORTED_STAGES:
            return False
        if qa_result_type is None:
            return True
        return qa_result_type.strip() in self._SUPPORTED_QA_RESULT_TYPES

    def _derive_prepare_merge(
        self,
        request: TechLeadAcceptanceDecisionRequest,
        *,
        execution_mode: str,
    ) -> TechLeadAcceptanceDecisionResult:
        summary = TechLeadAcceptanceDecisionSummary(
            decision_supported=True,
            recommended_next_decision='prepare_merge',
            acceptance_allowed=True,
            closeout_allowed=False,
            decision_summary=(
                f'TechLead may prepare merge acceptance for issue #{request.issue_number} '
                'because QA returned a passing verification result.'
            ),
            blocking_reasons=(),
            notes=('qa-pass', 'live-delivery'),
        )
        result = self._build_supported_result(request, summary=summary, execution_mode=execution_mode)
        self._logger.info(
            'techlead_acceptance_decision.derive_acceptance_decision.prepare_merge',
            issue_number=request.issue_number,
            workflow_stage=request.workflow_stage,
            qa_result_type=request.qa_result_type,
        )
        return result

    def _derive_proof_only_closeout(
        self,
        request: TechLeadAcceptanceDecisionRequest,
        *,
        execution_mode: str,
    ) -> TechLeadAcceptanceDecisionResult:
        summary = TechLeadAcceptanceDecisionSummary(
            decision_supported=True,
            recommended_next_decision='close_slice',
            acceptance_allowed=True,
            closeout_allowed=True,
            decision_summary=(
                f'TechLead may record proof-only closeout for issue #{request.issue_number} '
                'because QA returned a passing verification result in proof-only execution mode.'
            ),
            blocking_reasons=(),
            notes=('qa-pass', 'proof-only-closeout'),
        )
        result = self._build_supported_result(request, summary=summary, execution_mode=execution_mode)
        self._logger.info(
            'techlead_acceptance_decision.derive_acceptance_decision.close_slice',
            issue_number=request.issue_number,
            workflow_stage=request.workflow_stage,
            qa_result_type=request.qa_result_type,
        )
        return result

    def _build_supported_result(
        self,
        request: TechLeadAcceptanceDecisionRequest,
        *,
        summary: TechLeadAcceptanceDecisionSummary,
        execution_mode: str,
    ) -> TechLeadAcceptanceDecisionResult:
        return TechLeadAcceptanceDecisionResult(
            project_slug=request.project_slug,
            issue_number=request.issue_number,
            pr_number=request.pr_number,
            workflow_stage=request.workflow_stage,
            qa_result_type=request.qa_result_type,
            source_packet_schema_type=request.source_packet_schema_type,
            source_packet_message_id=request.source_packet_message_id,
            summary=summary,
            ok=True,
            reason=None,
            details=None,
            recommended_actions=(summary.recommended_next_decision,) if summary.recommended_next_decision else None,
            unattended_safe=True,
            metadata=self._base_metadata(request, execution_mode=execution_mode),
        )

    def _build_rejected_result(
        self,
        request: TechLeadAcceptanceDecisionRequest,
        *,
        reason: str,
        details: str,
        blocking_reasons: tuple[str, ...],
        notes: tuple[str, ...],
    ) -> TechLeadAcceptanceDecisionResult:
        self._logger.warning(
            'techlead_acceptance_decision.derive_acceptance_decision.rejected',
            issue_number=request.issue_number,
            workflow_stage=request.workflow_stage,
            qa_result_type=request.qa_result_type,
            reason=reason,
        )
        summary = TechLeadAcceptanceDecisionSummary(
            decision_supported=False,
            recommended_next_decision=None,
            acceptance_allowed=False,
            closeout_allowed=False,
            decision_summary='No supported acceptance decision is available for this slice.',
            blocking_reasons=blocking_reasons,
            notes=notes,
        )
        metadata = self._base_metadata(request, execution_mode=self._resolve_execution_mode(request))
        metadata['rejected_at'] = self._clock()
        return TechLeadAcceptanceDecisionResult(
            project_slug=request.project_slug,
            issue_number=request.issue_number,
            pr_number=request.pr_number,
            workflow_stage=request.workflow_stage,
            qa_result_type=request.qa_result_type,
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

    def _resolve_execution_mode(self, request: TechLeadAcceptanceDecisionRequest) -> str:
        metadata_mode = (request.metadata or {}).get('execution_mode')
        if isinstance(metadata_mode, str) and metadata_mode:
            return metadata_mode
        merge_mode = (request.merge_state or {}).get('execution_mode')
        if isinstance(merge_mode, str) and merge_mode:
            return merge_mode
        return 'live_delivery'

    def _resolve_merge_ready(self, request: TechLeadAcceptanceDecisionRequest) -> bool | None:
        merge_state = request.merge_state or {}
        for key in ('merge_ready', 'pr_merge_ready', 'ready_for_merge'):
            value = merge_state.get(key)
            if isinstance(value, bool):
                return value
        return None

    def _base_metadata(
        self,
        request: TechLeadAcceptanceDecisionRequest,
        *,
        execution_mode: str,
    ) -> dict[str, object]:
        metadata: dict[str, object] = dict(request.metadata or {})
        metadata.setdefault('workflow_lifecycle_result_supplied', request.workflow_lifecycle_result is not None)
        metadata.setdefault('service_component', 'TechLeadAcceptanceDecisionService')
        metadata.setdefault('execution_mode', execution_mode)
        metadata.setdefault('merge_ready', self._resolve_merge_ready(request))
        return metadata

    def _default_clock(self) -> str:
        return datetime.now(timezone.utc).isoformat()


__all__ = ['DefaultTechLeadAcceptanceDecisionService']

"""Default implementation for the TechLead lineage decision service."""

from __future__ import annotations

from datetime import datetime, timezone

from paa_core.services.implementation_plan_derivation.contracts import StructuredLogger

from .models import (
    TechLeadLineageDecisionRequest,
    TechLeadLineageDecisionResult,
    TechLeadLineageDecisionSummary,
)


class _NullStructuredLogger:
    def info(self, event: str, **fields: object) -> None:
        return None

    def warning(self, event: str, **fields: object) -> None:
        return None


class DefaultTechLeadLineageDecisionService:
    """Derive supported superseded-lineage decisions from resolved runtime context."""

    _SUPPORTED_STAGES = frozenset({'qa_pending', 'techlead_qa_review_pending'})
    _SUPPORTED_LINEAGE_STATES = frozenset({'superseded'})
    _SUPPORTED_ESCALATION_TYPES = frozenset({'qa_escalation_superseded'})

    def __init__(
        self,
        *,
        logger: StructuredLogger | None = None,
        clock: callable | None = None,
    ) -> None:
        self._logger = logger if logger is not None else _NullStructuredLogger()
        self._clock = clock if clock is not None else self._default_clock

    @property
    def logger(self) -> StructuredLogger:
        return self._logger

    def derive_lineage_decision(
        self,
        request: TechLeadLineageDecisionRequest,
    ) -> TechLeadLineageDecisionResult:
        normalized_stage = request.workflow_stage.strip()
        normalized_lineage_state = request.lineage_state.strip()
        normalized_escalation_type = (request.superseded_escalation_type or '').strip()

        self._logger.info(
            'techlead_lineage_decision.derive_lineage_decision.start',
            project_slug=request.project_slug,
            issue_number=request.issue_number,
            workflow_stage=normalized_stage,
            lineage_state=normalized_lineage_state,
            superseded_escalation_type=normalized_escalation_type,
        )

        if request.issue_number <= 0:
            return self._build_rejected_result(
                request,
                reason='missing_issue_number',
                details='The lineage decision request must include a positive issue number.',
                blocking_reasons=('missing_issue_number',),
                notes=('issue-number-required',),
            )

        if not normalized_stage:
            return self._build_rejected_result(
                request,
                reason='missing_workflow_stage',
                details='The lineage decision request must include a workflow stage.',
                blocking_reasons=('missing_workflow_stage',),
                notes=('workflow-stage-required',),
            )

        if not normalized_lineage_state and not normalized_escalation_type:
            return self._build_rejected_result(
                request,
                reason='missing_lineage_signal',
                details='The lineage decision request must include a lineage state or superseded escalation type.',
                blocking_reasons=('missing_lineage_signal',),
                notes=('lineage-signal-required',),
            )

        if not self.supports_lineage_decision(
            normalized_stage,
            normalized_lineage_state or None,
            normalized_escalation_type or None,
        ):
            return self._build_rejected_result(
                request,
                reason='unsupported_lineage_decision',
                details=(
                    f'Current workflow stage {normalized_stage!r}, lineage state {normalized_lineage_state!r}, '
                    f'and superseded escalation type {normalized_escalation_type!r} are not supported in this slice.'
                ),
                blocking_reasons=('unsupported_lineage_decision',),
                notes=('fail-closed',),
            )

        summary_text = request.superseded_escalation_summary or (
            f'The prior branch lineage for issue #{request.issue_number} has been superseded by a newer QA or rework lineage.'
        )
        summary = TechLeadLineageDecisionSummary(
            decision_supported=True,
            recommended_next_decision='supersede_branch_lineage',
            recommended_target_role='TechLead',
            supersede_allowed=True,
            lineage_decision_summary=summary_text,
            blocking_reasons=(),
            notes=('superseded-lineage',),
        )
        result = self._build_supported_result(request, summary=summary)
        self._logger.info(
            'techlead_lineage_decision.derive_lineage_decision.supported',
            issue_number=request.issue_number,
            workflow_stage=normalized_stage,
            lineage_state=normalized_lineage_state,
            superseded_escalation_type=normalized_escalation_type,
        )
        return result

    def supports_lineage_decision(
        self,
        workflow_stage: str,
        lineage_state: str | None = None,
        superseded_escalation_type: str | None = None,
    ) -> bool:
        normalized_stage = workflow_stage.strip()
        normalized_lineage_state = (lineage_state or '').strip()
        normalized_escalation_type = (superseded_escalation_type or '').strip()
        if normalized_lineage_state in self._SUPPORTED_LINEAGE_STATES:
            return True
        if normalized_escalation_type in self._SUPPORTED_ESCALATION_TYPES:
            return True
        if normalized_stage in self._SUPPORTED_STAGES and normalized_escalation_type in self._SUPPORTED_ESCALATION_TYPES:
            return True
        return False

    def _build_supported_result(
        self,
        request: TechLeadLineageDecisionRequest,
        *,
        summary: TechLeadLineageDecisionSummary,
    ) -> TechLeadLineageDecisionResult:
        return TechLeadLineageDecisionResult(
            project_slug=request.project_slug,
            issue_number=request.issue_number,
            issue_url=request.issue_url,
            pr_number=request.pr_number,
            pr_url=request.pr_url,
            workflow_stage=request.workflow_stage,
            lineage_state=request.lineage_state,
            superseded_escalation_type=request.superseded_escalation_type,
            source_packet_schema_type=request.source_packet_schema_type,
            source_packet_message_id=request.source_packet_message_id,
            source_packet_path=request.source_packet_path,
            branch_name=request.branch_name,
            superseded_branch=request.superseded_branch,
            summary=summary,
            ok=True,
            reason=None,
            details=None,
            recommended_actions=(summary.recommended_next_decision,) if summary.recommended_next_decision else None,
            unattended_safe=False,
            metadata=self._base_metadata(request),
        )

    def _build_rejected_result(
        self,
        request: TechLeadLineageDecisionRequest,
        *,
        reason: str,
        details: str,
        blocking_reasons: tuple[str, ...],
        notes: tuple[str, ...],
    ) -> TechLeadLineageDecisionResult:
        self._logger.warning(
            'techlead_lineage_decision.derive_lineage_decision.rejected',
            issue_number=request.issue_number,
            workflow_stage=request.workflow_stage,
            lineage_state=request.lineage_state,
            superseded_escalation_type=request.superseded_escalation_type,
            reason=reason,
        )
        summary = TechLeadLineageDecisionSummary(
            decision_supported=False,
            recommended_next_decision=None,
            recommended_target_role=None,
            supersede_allowed=False,
            lineage_decision_summary='No supported lineage decision is available for this slice.',
            blocking_reasons=blocking_reasons,
            notes=notes,
        )
        metadata = self._base_metadata(request)
        metadata['rejected_at'] = self._clock()
        return TechLeadLineageDecisionResult(
            project_slug=request.project_slug,
            issue_number=request.issue_number,
            issue_url=request.issue_url,
            pr_number=request.pr_number,
            pr_url=request.pr_url,
            workflow_stage=request.workflow_stage,
            lineage_state=request.lineage_state,
            superseded_escalation_type=request.superseded_escalation_type,
            source_packet_schema_type=request.source_packet_schema_type,
            source_packet_message_id=request.source_packet_message_id,
            source_packet_path=request.source_packet_path,
            branch_name=request.branch_name,
            superseded_branch=request.superseded_branch,
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
        request: TechLeadLineageDecisionRequest,
    ) -> dict[str, object]:
        metadata: dict[str, object] = dict(request.metadata or {})
        metadata.setdefault('service_component', 'TechLeadLineageDecisionService')
        metadata.setdefault('source_packet_present', request.source_packet_schema_type is not None)
        metadata.setdefault('superseded_branch_present', request.superseded_branch is not None)
        metadata.setdefault('superseded_escalation_details_supplied', request.superseded_escalation_details is not None)
        return metadata

    def _default_clock(self) -> str:
        return datetime.now(timezone.utc).isoformat()


__all__ = ['DefaultTechLeadLineageDecisionService']

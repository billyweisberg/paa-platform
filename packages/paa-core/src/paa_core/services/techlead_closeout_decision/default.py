"""Default implementation for the TechLead closeout decision service."""

from __future__ import annotations

from datetime import datetime, timezone

from paa_core.services.implementation_plan_derivation.contracts import StructuredLogger

from .models import (
    TechLeadCloseoutDecisionRequest,
    TechLeadCloseoutDecisionResult,
    TechLeadCloseoutDecisionSummary,
)


class _NullStructuredLogger:
    def info(self, event: str, **fields: object) -> None:
        return None

    def warning(self, event: str, **fields: object) -> None:
        return None


class DefaultTechLeadCloseoutDecisionService:
    """Derive supported proof-only closeout decisions from terminal QA-pass context."""

    _SUPPORTED_STAGES = frozenset({'proof_only_closed'})
    _SUPPORTED_DECISION_TYPES = frozenset({'proof_only_closed'})
    _SUPPORTED_SOURCE_SCHEMAS = frozenset({'qa_verification_packet'})

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

    def derive_closeout_decision(
        self,
        request: TechLeadCloseoutDecisionRequest,
    ) -> TechLeadCloseoutDecisionResult:
        normalized_stage = request.workflow_stage.strip()
        normalized_decision_type = request.decision_type.strip()
        source_schema = (request.source_packet_schema_type or '').strip() or None

        self._logger.info(
            'techlead_closeout_decision.derive_closeout_decision.start',
            project_slug=request.project_slug,
            issue_number=request.issue_number,
            workflow_stage=normalized_stage,
            decision_type=normalized_decision_type,
            proof_only_mode=request.proof_only_mode,
            source_packet_schema_type=source_schema,
        )

        if request.issue_number <= 0:
            return self._build_rejected_result(
                request,
                reason='missing_issue_number',
                details='The closeout decision request must include a positive issue number.',
                blocking_reasons=('missing_issue_number',),
                notes=('issue-number-required',),
            )

        if not normalized_stage:
            return self._build_rejected_result(
                request,
                reason='missing_workflow_stage',
                details='The closeout decision request must include a workflow stage.',
                blocking_reasons=('missing_workflow_stage',),
                notes=('workflow-stage-required',),
            )

        if not normalized_decision_type:
            return self._build_rejected_result(
                request,
                reason='missing_decision_type',
                details='The closeout decision request must include a decision type.',
                blocking_reasons=('missing_decision_type',),
                notes=('decision-type-required',),
            )

        if source_schema is not None and source_schema not in self._SUPPORTED_SOURCE_SCHEMAS:
            return self._build_rejected_result(
                request,
                reason='unsupported_source_packet_schema',
                details=(
                    f'Source packet schema {request.source_packet_schema_type!r} is not supported '
                    'by the current TechLeadCloseoutDecisionService slice.'
                ),
                blocking_reasons=('unsupported_source_packet_schema',),
                notes=('fail-closed',),
            )

        if not request.proof_only_mode:
            return self._build_rejected_result(
                request,
                reason='proof_only_mode_required',
                details='The current closeout decision slice only supports proof-only execution mode.',
                blocking_reasons=('proof_only_mode_required',),
                notes=('proof-only-required',),
            )

        if source_schema is None or request.source_packet_path is None:
            return self._build_rejected_result(
                request,
                reason='missing_source_packet',
                details='Proof-only closeout requires a resolved QA source packet reference.',
                blocking_reasons=('missing_source_packet',),
                notes=('source-packet-required',),
            )

        if not self.supports_closeout_decision(normalized_stage, normalized_decision_type, request.proof_only_mode):
            return self._build_rejected_result(
                request,
                reason='unsupported_closeout_decision',
                details=(
                    f'Current workflow stage {normalized_stage!r}, decision type '
                    f'{normalized_decision_type!r}, and proof-only mode {request.proof_only_mode!r} '
                    'are not supported in this slice.'
                ),
                blocking_reasons=('unsupported_closeout_decision',),
                notes=('fail-closed',),
            )

        summary = TechLeadCloseoutDecisionSummary(
            decision_supported=True,
            recommended_next_decision='proof_only_close_slice',
            recommended_target_role='TechLead',
            closeout_allowed=True,
            closeout_decision_summary=(
                f'TechLead may record proof-only closeout for issue #{request.issue_number} '
                'without requiring merge or issue-close side effects.'
            ),
            blocking_reasons=(),
            notes=('proof-only-closeout', 'qa-pass'),
        )
        result = self._build_supported_result(request, summary=summary)
        self._logger.info(
            'techlead_closeout_decision.derive_closeout_decision.proof_only_close_slice',
            issue_number=request.issue_number,
            workflow_stage=request.workflow_stage,
            decision_type=request.decision_type,
        )
        return result

    def supports_closeout_decision(
        self,
        workflow_stage: str,
        decision_type: str | None = None,
        proof_only_mode: bool | None = None,
    ) -> bool:
        normalized_stage = workflow_stage.strip()
        if normalized_stage not in self._SUPPORTED_STAGES:
            return False
        if proof_only_mode is not True:
            return False
        if decision_type is None:
            return True
        return decision_type.strip() in self._SUPPORTED_DECISION_TYPES

    def _build_supported_result(
        self,
        request: TechLeadCloseoutDecisionRequest,
        *,
        summary: TechLeadCloseoutDecisionSummary,
    ) -> TechLeadCloseoutDecisionResult:
        return TechLeadCloseoutDecisionResult(
            project_slug=request.project_slug,
            issue_number=request.issue_number,
            issue_url=request.issue_url,
            pr_number=request.pr_number,
            pr_url=request.pr_url,
            workflow_stage=request.workflow_stage,
            decision_type=request.decision_type,
            source_packet_schema_type=request.source_packet_schema_type,
            source_packet_message_id=request.source_packet_message_id,
            source_packet_path=request.source_packet_path,
            branch_name=request.branch_name,
            canonical_branch=request.canonical_branch,
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
        request: TechLeadCloseoutDecisionRequest,
        *,
        reason: str,
        details: str,
        blocking_reasons: tuple[str, ...],
        notes: tuple[str, ...],
    ) -> TechLeadCloseoutDecisionResult:
        self._logger.warning(
            'techlead_closeout_decision.derive_closeout_decision.rejected',
            issue_number=request.issue_number,
            workflow_stage=request.workflow_stage,
            decision_type=request.decision_type,
            proof_only_mode=request.proof_only_mode,
            reason=reason,
        )
        summary = TechLeadCloseoutDecisionSummary(
            decision_supported=False,
            recommended_next_decision=None,
            recommended_target_role=None,
            closeout_allowed=False,
            closeout_decision_summary='No supported closeout decision is available for this slice.',
            blocking_reasons=blocking_reasons,
            notes=notes,
        )
        metadata = self._base_metadata(request)
        metadata['rejected_at'] = self._clock()
        return TechLeadCloseoutDecisionResult(
            project_slug=request.project_slug,
            issue_number=request.issue_number,
            issue_url=request.issue_url,
            pr_number=request.pr_number,
            pr_url=request.pr_url,
            workflow_stage=request.workflow_stage,
            decision_type=request.decision_type,
            source_packet_schema_type=request.source_packet_schema_type,
            source_packet_message_id=request.source_packet_message_id,
            source_packet_path=request.source_packet_path,
            branch_name=request.branch_name,
            canonical_branch=request.canonical_branch,
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
        request: TechLeadCloseoutDecisionRequest,
    ) -> dict[str, object]:
        metadata: dict[str, object] = dict(request.metadata or {})
        metadata.setdefault('service_component', 'TechLeadCloseoutDecisionService')
        metadata.setdefault('source_packet_present', request.source_packet_schema_type is not None)
        metadata.setdefault('proof_only_mode', request.proof_only_mode)
        metadata.setdefault('canonical_branch_supplied', request.canonical_branch is not None)
        return metadata

    def _default_clock(self) -> str:
        return datetime.now(timezone.utc).isoformat()


__all__ = ['DefaultTechLeadCloseoutDecisionService']

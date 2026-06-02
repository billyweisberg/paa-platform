"""Default implementation for the TechLead assignment decision service."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from paa_core.services.implementation_plan_derivation.contracts import StructuredLogger
from paa_core.services.workflow_lifecycle import WorkflowLifecycleService

from .models import (
    TechLeadAssignmentDecisionRequest,
    TechLeadAssignmentDecisionResult,
    TechLeadAssignmentDecisionSummary,
)


class _NullStructuredLogger:
    def info(self, event: str, **fields: object) -> None:
        return None

    def warning(self, event: str, **fields: object) -> None:
        return None


class DefaultTechLeadAssignmentDecisionService:
    """Derive supported next-assignment decisions from resolved runtime context."""

    _EXPLICIT_TEAM_ROLE_MAP: dict[str, tuple[str, str]] = {
        'dev': ('Dev', 'dev'),
        'python': ('Python Dev', 'python'),
        'python-dev': ('Python Dev', 'python'),
        'python-team': ('Python Dev', 'python'),
    }

    _QA_READY_STAGES = frozenset({'techlead_dev_review_pending', 'techlead_worker_review_pending'})
    _QA_READY_SOURCE_SCHEMAS = frozenset({'slice_result_packet', 'worker_result_packet'})

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

    def derive_assignment_decision(
        self,
        request: TechLeadAssignmentDecisionRequest,
    ) -> TechLeadAssignmentDecisionResult:
        normalized_stage = request.workflow_stage.strip()
        explicit_target_role = self._normalize_target_role(request.explicit_target_role)

        self._logger.info(
            'techlead_assignment_decision.derive_assignment_decision.start',
            project_slug=request.project_slug,
            issue_number=request.issue_number,
            workflow_stage=normalized_stage,
            explicit_target_role=explicit_target_role,
            source_packet_schema_type=request.source_packet_schema_type,
        )

        if request.issue_number <= 0:
            return self._build_rejected_result(
                request,
                reason='missing_issue_number',
                details='The assignment decision request must include a positive issue number.',
                blocking_reasons=('missing_issue_number',),
                notes=('issue-number-required',),
            )

        if not normalized_stage:
            return self._build_rejected_result(
                request,
                reason='missing_workflow_stage',
                details='The assignment decision request must include a workflow stage.',
                blocking_reasons=('missing_workflow_stage',),
                notes=('workflow-stage-required',),
            )

        if explicit_target_role is not None:
            return self._derive_explicit_team_worker_assignment(request, explicit_target_role)

        if self._supports_qa_review_assignment(
            workflow_stage=normalized_stage,
            source_packet_schema_type=request.source_packet_schema_type,
        ):
            return self._derive_worker_review_ready_assignment(request)

        return self._build_rejected_result(
            request,
            reason='no_supported_emission_available',
            details=(
                f'Current workflow stage {normalized_stage!r} does not support next-assignment '
                'derivation in this slice. Supported paths are explicit Team Worker Role emission '
                'and techlead_dev_review_pending/techlead_worker_review_pending to QA.'
            ),
            blocking_reasons=('unsupported_workflow_stage',),
            notes=('fail-closed',),
        )

    def supports_assignment_for_stage(
        self,
        workflow_stage: str,
        source_packet_schema_type: str | None = None,
    ) -> bool:
        normalized_stage = workflow_stage.strip()
        return self._supports_qa_review_assignment(
            workflow_stage=normalized_stage,
            source_packet_schema_type=source_packet_schema_type,
        )

    def _derive_explicit_team_worker_assignment(
        self,
        request: TechLeadAssignmentDecisionRequest,
        explicit_target_role: str,
    ) -> TechLeadAssignmentDecisionResult:
        team_worker = self._EXPLICIT_TEAM_ROLE_MAP.get(explicit_target_role)
        if team_worker is None:
            return self._build_rejected_result(
                request,
                reason='explicit_target_role_not_supported',
                details=(
                    f'Explicit target role {request.explicit_target_role!r} is not supported by '
                    'the current TechLeadAssignmentDecisionService slice.'
                ),
                blocking_reasons=('unsupported_explicit_target_role',),
                notes=('supported-explicit-targets:dev,python,python-dev,python-team',),
            )

        target_role, target_role_cli = team_worker
        summary = TechLeadAssignmentDecisionSummary(
            decision_supported=True,
            target_role=target_role,
            target_role_cli=target_role_cli,
            assignment_type='implement_authorized_slice',
            allowed_result_types=('implemented_ready_for_qa', 'blocked', 'needs_clarification'),
            assignment_summary=(
                f'TechLead is explicitly issuing a {target_role} implementation assignment '
                f'for issue #{request.issue_number}.'
            ),
            decision_reason='supported_explicit_team_worker_emission',
            blocking_reasons=(),
            notes=('explicit-target-role',),
        )
        result = self._build_supported_result(
            request,
            summary=summary,
        )
        self._logger.info(
            'techlead_assignment_decision.derive_assignment_decision.explicit_team_worker',
            issue_number=request.issue_number,
            target_role=target_role,
            target_role_cli=target_role_cli,
        )
        return result

    def _derive_worker_review_ready_assignment(
        self,
        request: TechLeadAssignmentDecisionRequest,
    ) -> TechLeadAssignmentDecisionResult:
        summary = TechLeadAssignmentDecisionSummary(
            decision_supported=True,
            target_role='QA',
            target_role_cli='qa',
            assignment_type='verify_authorized_slice',
            allowed_result_types=('pass', 'fail_fixable', 'needs_human_review'),
            assignment_summary=(
                f'TechLead is routing the returned implementation slice for issue '
                f'#{request.issue_number} to QA.'
            ),
            decision_reason='supported_worker_review_ready_to_qa_assignment',
            blocking_reasons=(),
            notes=('source-packet-carry-forward',),
        )
        result = self._build_supported_result(
            request,
            summary=summary,
        )
        self._logger.info(
            'techlead_assignment_decision.derive_assignment_decision.worker_review_ready',
            issue_number=request.issue_number,
            workflow_stage=request.workflow_stage,
            source_packet_schema_type=request.source_packet_schema_type,
        )
        return result

    def _build_supported_result(
        self,
        request: TechLeadAssignmentDecisionRequest,
        *,
        summary: TechLeadAssignmentDecisionSummary,
    ) -> TechLeadAssignmentDecisionResult:
        return TechLeadAssignmentDecisionResult(
            project_slug=request.project_slug,
            issue_number=request.issue_number,
            issue_url=request.issue_url,
            pr_number=request.pr_number,
            pr_url=request.pr_url,
            branch_name=request.branch_name,
            workflow_stage=request.workflow_stage,
            source_packet_schema_type=request.source_packet_schema_type,
            source_packet_message_id=request.source_packet_message_id,
            source_packet_queue_name=request.source_packet_queue_name,
            source_packet_path=request.source_packet_path,
            summary=summary,
            ok=True,
            reason=None,
            details=None,
            recommended_actions=request.recommended_actions,
            unattended_safe=True,
            metadata=self._base_metadata(request),
        )

    def _build_rejected_result(
        self,
        request: TechLeadAssignmentDecisionRequest,
        *,
        reason: str,
        details: str,
        blocking_reasons: tuple[str, ...],
        notes: tuple[str, ...],
    ) -> TechLeadAssignmentDecisionResult:
        self._logger.warning(
            'techlead_assignment_decision.derive_assignment_decision.rejected',
            issue_number=request.issue_number,
            workflow_stage=request.workflow_stage,
            reason=reason,
            source_packet_schema_type=request.source_packet_schema_type,
        )
        summary = TechLeadAssignmentDecisionSummary(
            decision_supported=False,
            target_role=None,
            target_role_cli=None,
            assignment_type=None,
            allowed_result_types=(),
            assignment_summary='No supported next-assignment decision is available for this slice.',
            decision_reason=reason,
            blocking_reasons=blocking_reasons,
            notes=notes,
        )
        metadata = self._base_metadata(request)
        metadata['rejected_at'] = self._clock()
        return TechLeadAssignmentDecisionResult(
            project_slug=request.project_slug,
            issue_number=request.issue_number,
            issue_url=request.issue_url,
            pr_number=request.pr_number,
            pr_url=request.pr_url,
            branch_name=request.branch_name,
            workflow_stage=request.workflow_stage,
            source_packet_schema_type=request.source_packet_schema_type,
            source_packet_message_id=request.source_packet_message_id,
            source_packet_queue_name=request.source_packet_queue_name,
            source_packet_path=request.source_packet_path,
            summary=summary,
            ok=False,
            reason=reason,
            details=details,
            recommended_actions=request.recommended_actions,
            unattended_safe=False,
            metadata=metadata,
        )

    def _supports_qa_review_assignment(
        self,
        *,
        workflow_stage: str,
        source_packet_schema_type: str | None,
    ) -> bool:
        if workflow_stage not in self._QA_READY_STAGES:
            return False
        return source_packet_schema_type in self._QA_READY_SOURCE_SCHEMAS

    def _normalize_target_role(self, target_role: str | None) -> str | None:
        if target_role is None:
            return None
        normalized = target_role.strip().lower()
        return normalized or None

    def _base_metadata(
        self,
        request: TechLeadAssignmentDecisionRequest,
    ) -> dict[str, object]:
        metadata: dict[str, object] = dict(request.metadata or {})
        metadata.setdefault('workflow_lifecycle_result_supplied', request.workflow_lifecycle_result is not None)
        metadata.setdefault('service_component', 'TechLeadAssignmentDecisionService')
        return metadata

    def _default_clock(self) -> str:
        return datetime.now(timezone.utc).isoformat()


__all__ = ['DefaultTechLeadAssignmentDecisionService']

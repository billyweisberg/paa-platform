"""Default implementation shell for the workflow lifecycle service."""

from __future__ import annotations

from datetime import datetime, timezone

from paa_core.policies.reset_recovery import (
    ResetRecoveryDecision,
    ResetRecoveryEvaluationContext,
    ResetRecoveryRequest,
)
from paa_core.policies.workflow_transition import (
    WorkflowTransitionDecision,
    WorkflowTransitionEvaluationContext,
    WorkflowTransitionRequest,
)
from paa_core.policies.acceptance import AcceptancePolicy
from paa_core.policies.reset_recovery import ResetRecoveryPolicy
from paa_core.policies.workflow_transition import WorkflowTransitionPolicy
from paa_core.repositories.runtime_event import QueueMessageRecord, RuntimeEventRepository, TransitionInputRecord
from paa_core.repositories.workflow_state import (
    QueueClaimRecord,
    WorkflowStateRecord,
    WorkflowStateRepository,
    WorkflowStateUpsertSpec,
    WorkflowTransitionAppendSpec,
)
from paa_core.services.execution_package_resolution import ExecutionPackageResolutionService
from paa_core.services.execution_package_resolution.models import ExecutionPackageResolutionRequest
from paa_core.services.implementation_plan_derivation.contracts import StructuredLogger

from .models import (
    WorkflowLifecycleDecisionSummary,
    WorkflowLifecycleRequest,
    WorkflowLifecycleResult,
    WorkflowLifecycleStateView,
)


class _NullStructuredLogger:
    def info(self, event: str, **fields: object) -> None:
        return None

    def warning(self, event: str, **fields: object) -> None:
        return None


class DefaultWorkflowLifecycleService:
    """Default shell for workflow lifecycle coordination."""

    _WORKER_RESULT_TRANSITION = 'worker_result_returned'
    _WORKER_RESULT_FROM_STAGE = 'worker_execution_in_progress'
    _WORKER_RESULT_TO_STAGE = 'techlead_worker_review_pending'
    _WORKER_RESULT_PACKET_SCHEMA = 'worker_result_packet'
    _QA_RESULT_TRANSITION = 'qa_result_returned'
    _QA_RESULT_FROM_STAGE = 'qa_execution_in_progress'
    _QA_RESULT_TO_STAGE = 'techlead_qa_review_pending'
    _QA_RESULT_PACKET_SCHEMA = 'qa_verification_packet'

    def __init__(
        self,
        *,
        workflow_state_repository: WorkflowStateRepository,
        runtime_event_repository: RuntimeEventRepository,
        execution_package_resolution_service: ExecutionPackageResolutionService,
        workflow_transition_policy: WorkflowTransitionPolicy,
        acceptance_policy: AcceptancePolicy,
        reset_recovery_policy: ResetRecoveryPolicy,
        logger: StructuredLogger | None = None,
    ) -> None:
        self._workflow_state_repository = workflow_state_repository
        self._runtime_event_repository = runtime_event_repository
        self._execution_package_resolution_service = execution_package_resolution_service
        self._workflow_transition_policy = workflow_transition_policy
        self._acceptance_policy = acceptance_policy
        self._reset_recovery_policy = reset_recovery_policy
        self._logger = logger if logger is not None else _NullStructuredLogger()

    @property
    def workflow_state_repository(self) -> WorkflowStateRepository:
        return self._workflow_state_repository

    @property
    def runtime_event_repository(self) -> RuntimeEventRepository:
        return self._runtime_event_repository

    @property
    def execution_package_resolution_service(self) -> ExecutionPackageResolutionService:
        return self._execution_package_resolution_service

    @property
    def workflow_transition_policy(self) -> WorkflowTransitionPolicy:
        return self._workflow_transition_policy

    @property
    def acceptance_policy(self) -> AcceptancePolicy:
        return self._acceptance_policy

    @property
    def reset_recovery_policy(self) -> ResetRecoveryPolicy:
        return self._reset_recovery_policy

    @property
    def logger(self) -> StructuredLogger:
        return self._logger

    def get_current_workflow_state(self, work_item_id: str) -> WorkflowLifecycleStateView:
        state = self._workflow_state_repository.get_workflow_state_for_work_item(work_item_id)
        if state is None:
            raise LookupError(f'No workflow state found for work item {work_item_id!r}')
        self._logger.info(
            'workflow_lifecycle.get_current_workflow_state',
            work_item_id=work_item_id,
            workflow_state_id=state.workflow_state_id,
            workflow_stage=state.workflow_stage,
        )
        return self._state_view_from_record(state)

    def evaluate_workflow_transition(
        self,
        request: WorkflowLifecycleRequest,
    ) -> WorkflowLifecycleResult:
        evaluation = self._evaluate_supported_transition(request)
        self._logger.info(
            'workflow_lifecycle.evaluate_workflow_transition',
            work_item_id=request.work_item_id,
            requested_transition_type=request.requested_transition_type,
            transition_allowed=evaluation.decision_summary.transition_allowed,
            resolved_execution_surface_key=evaluation.resolved_execution_surface_key,
        )
        return evaluation

    def apply_workflow_transition(
        self,
        request: WorkflowLifecycleRequest,
    ) -> WorkflowLifecycleResult:
        evaluation = self._evaluate_supported_transition(request)
        if not evaluation.decision_summary.transition_allowed:
            self._logger.warning(
                'workflow_lifecycle.apply_workflow_transition.rejected',
                work_item_id=request.work_item_id,
                requested_transition_type=request.requested_transition_type,
                blocking_reasons=evaluation.decision_summary.blocking_reasons,
            )
            return evaluation

        current_state = self._require_current_state(request)
        transition_applied_at = self._now_iso()
        transition_type = request.requested_transition_type or self._WORKER_RESULT_TRANSITION
        next_owner_role_id = current_state.active_result_role_id or current_state.current_owner_role_id
        next_lineage_state = self._derive_next_lineage_state(transition_type, current_state)
        target_stage = self._target_stage_for_transition(transition_type)
        packet_schema = self._packet_schema_for_transition(transition_type)
        next_metadata = dict(current_state.metadata or {})
        next_metadata.update(
            {
                'last_applied_transition_type': transition_type,
                'lineage_state_strategy': self._lineage_strategy_for_transition(transition_type),
            }
        )

        self._workflow_state_repository.upsert_workflow_state(
            WorkflowStateUpsertSpec(
                project_id=current_state.project_id,
                work_item_id=current_state.work_item_id,
                workflow_stage=target_stage,
                lineage_state=next_lineage_state,
                current_owner_role_id=next_owner_role_id,
                authority_version_id=current_state.authority_version_id,
                design_package_id=current_state.design_package_id,
                coder_run_brief_id=current_state.coder_run_brief_id,
                blocking_reason_code=None,
                blocking_reason_text=None,
                terminal_decision=current_state.terminal_decision,
                state_consistency=current_state.state_consistency,
                current_issue_number=current_state.current_issue_number,
                current_pr_number=current_state.current_pr_number,
                canonical_branch=current_state.canonical_branch,
                active_role_branch=current_state.active_role_branch,
                active_handoff_id=current_state.active_handoff_id,
                active_queue_message_id=request.source_queue_message_id or current_state.active_queue_message_id,
                active_message_id_external=request.source_message_id_external
                or current_state.active_message_id_external,
                active_assignment_role_id=current_state.active_assignment_role_id,
                active_result_role_id=current_state.active_result_role_id,
                active_queue_claim_id=current_state.active_queue_claim_id,
                state_entered_at=transition_applied_at,
                last_transition_at=transition_applied_at,
                closed_at=current_state.closed_at,
                metadata=next_metadata,
            )
        )
        self._workflow_state_repository.append_workflow_transition(
            WorkflowTransitionAppendSpec(
                workflow_state_id=current_state.workflow_state_id,
                project_id=current_state.project_id,
                work_item_id=current_state.work_item_id,
                transition_type=transition_type,
                transition_status='applied',
                from_workflow_stage=current_state.workflow_stage,
                to_workflow_stage=target_stage,
                from_owner_role_id=current_state.current_owner_role_id,
                to_owner_role_id=next_owner_role_id,
                source_handoff_id=current_state.active_handoff_id,
                source_queue_message_id=request.source_queue_message_id or current_state.active_queue_message_id,
                source_queue_claim_id=current_state.active_queue_claim_id,
                source_message_id_external=request.source_message_id_external
                or current_state.active_message_id_external,
                source_packet_schema_type=packet_schema,
                result_role_id=next_owner_role_id,
                automation_run_id=request.automation_run_id,
                transition_requested_at=transition_applied_at,
                transition_applied_at=transition_applied_at,
                metadata={
                    'lineage_state': next_lineage_state,
                    'requested_transition_type': request.requested_transition_type,
                },
            )
        )
        updated_state = self._require_current_state(request)
        result = WorkflowLifecycleResult(
            project_id=request.project_id,
            work_item_id=request.work_item_id,
            requested_transition_type=request.requested_transition_type,
            applied=True,
            state_view=self._state_view_from_record(updated_state),
            decision_summary=evaluation.decision_summary,
            resolved_execution_surface_key=evaluation.resolved_execution_surface_key,
            recommended_next_action=self._post_apply_review_action(transition_type),
            metadata={
                **dict(evaluation.metadata),
                'applied_transition_type': transition_type,
                'transition_applied_at': transition_applied_at,
            },
        )
        self._logger.info(
            'workflow_lifecycle.apply_workflow_transition.applied',
            work_item_id=request.work_item_id,
            requested_transition_type=request.requested_transition_type,
            workflow_state_id=updated_state.workflow_state_id,
            workflow_stage=updated_state.workflow_stage,
        )
        return result

    def detect_workflow_blocks(
        self,
        request: WorkflowLifecycleRequest,
    ) -> WorkflowLifecycleResult:
        evaluation = self._evaluate_supported_transition(request)
        self._logger.info(
            'workflow_lifecycle.detect_workflow_blocks',
            work_item_id=request.work_item_id,
            requested_transition_type=request.requested_transition_type,
            blocking_reasons=evaluation.decision_summary.blocking_reasons,
        )
        return evaluation

    def _evaluate_supported_transition(
        self,
        request: WorkflowLifecycleRequest,
    ) -> WorkflowLifecycleResult:
        transition_type = request.requested_transition_type
        if transition_type not in {self._WORKER_RESULT_TRANSITION, self._QA_RESULT_TRANSITION}:
            return self._rejected_result(
                request,
                state=None,
                blocking_reasons=(
                    f"Unsupported transition type {request.requested_transition_type!r}; only {self._WORKER_RESULT_TRANSITION!r} and {self._QA_RESULT_TRANSITION!r} are implemented in this slice.",
                ),
                notes=(
                    'This workflow lifecycle slice currently supports only worker-result and qa-result return paths.',
                ),
                resolved_execution_surface_key=None,
                metadata={
                    'supported_transition_types': (
                        self._WORKER_RESULT_TRANSITION,
                        self._QA_RESULT_TRANSITION,
                    )
                },
                recommended_next_action='Use the worker-result or qa-result transition family, or extend the workflow lifecycle slice.',
            )

        current_state = self._require_current_state(request)
        queue_message, transition_input = self._resolve_transition_evidence(request)
        source_schema_type = self._resolve_source_schema_type(request, queue_message, transition_input)
        blocking: list[str] = []
        notes: list[str] = []
        target_stage = self._target_stage_for_transition(transition_type)
        packet_schema = self._packet_schema_for_transition(transition_type)
        from_stage = self._from_stage_for_transition(transition_type)

        if request.requested_to_stage and request.requested_to_stage != target_stage:
            blocking.append(
                f"Requested to-stage {request.requested_to_stage!r} does not match the supported target stage {target_stage!r}."
            )
        if source_schema_type != packet_schema:
            blocking.append(
                f"{transition_type!r} requires source schema {packet_schema!r}, received {source_schema_type!r}."
            )
        if queue_message is None and transition_input is None and request.source_packet_schema_type is None:
            blocking.append(f'No runtime evidence was provided for transition {transition_type!r}.')

        transition_decision = self._workflow_transition_policy.evaluate_transition(
            WorkflowTransitionRequest(
                work_item_id=request.work_item_id,
                transition_type=transition_type,
                requested_from_stage=request.requested_from_stage or from_stage,
                requested_to_stage=target_stage,
                source_schema_type=source_schema_type,
                metadata=dict(request.metadata or {}),
            ),
            WorkflowTransitionEvaluationContext(
                current_workflow_stage=current_state.workflow_stage,
                current_owner_role=current_state.current_owner_role_id,
                lineage_state=current_state.lineage_state,
                state_consistency=current_state.state_consistency,
                execution_surface_type=None,
                execution_surface_key=request.execution_surface_key,
                metadata={'workflow_state_id': current_state.workflow_state_id},
            ),
        )
        claim = self._resolve_active_claim(current_state, queue_message)
        reset_decision = self._reset_recovery_policy.evaluate_reset_recovery(
            ResetRecoveryRequest(
                work_item_id=request.work_item_id,
                workflow_stage=current_state.workflow_stage,
                transition_status='proposed',
                retry_requested=False,
                metadata=dict(request.metadata or {}),
            ),
            ResetRecoveryEvaluationContext(
                state_consistency=current_state.state_consistency,
                blocking_reason_code=current_state.blocking_reason_code,
                active_claim_status=claim.claim_status if claim is not None else None,
                execution_surface_key=request.execution_surface_key,
                metadata={'workflow_state_id': current_state.workflow_state_id},
            ),
        )

        blocking.extend(transition_decision.blocking_reasons)
        blocking.extend(reset_decision.blocking_reasons)
        notes.extend(transition_decision.notes)
        notes.extend(reset_decision.notes)

        resolved_execution_surface_key = self._resolve_execution_surface_key(request)
        if resolved_execution_surface_key is not None:
            notes.append(f"Execution context resolved for surface {resolved_execution_surface_key!r}.")

        transition_allowed = not blocking and transition_decision.allowed
        recommended_next_action = (
            self._recommended_apply_action(transition_type)
            if transition_allowed
            else self._recommended_next_action(transition_type, reset_decision, blocking)
        )

        return WorkflowLifecycleResult(
            project_id=request.project_id,
            work_item_id=request.work_item_id,
            requested_transition_type=request.requested_transition_type,
            applied=False,
            state_view=self._state_view_from_record(current_state),
            decision_summary=WorkflowLifecycleDecisionSummary(
                transition_allowed=transition_allowed,
                acceptance_allowed=False,
                requires_manual_repair=reset_decision.requires_manual_repair,
                should_reset=reset_decision.should_reset,
                should_retry=reset_decision.should_retry,
                blocking_reasons=tuple(blocking),
                notes=tuple(notes),
                metadata={
                    'resolved_to_stage': transition_decision.resolved_to_stage,
                    'rejection_code': transition_decision.rejection_code,
                    'source_schema_type': source_schema_type,
                    'transition_type': transition_type,
                },
            ),
            resolved_execution_surface_key=resolved_execution_surface_key,
            recommended_next_action=recommended_next_action,
            metadata={
                'current_workflow_stage': current_state.workflow_stage,
                'target_workflow_stage': target_stage,
                'source_queue_message_id': request.source_queue_message_id,
                'source_message_id_external': request.source_message_id_external,
                'source_transition_input_id': transition_input.transition_input_id if transition_input else None,
            },
        )

    def _state_view_from_record(self, state: WorkflowStateRecord) -> WorkflowLifecycleStateView:
        return WorkflowLifecycleStateView(
            workflow_state_id=state.workflow_state_id,
            project_id=state.project_id,
            work_item_id=state.work_item_id,
            workflow_stage=state.workflow_stage,
            current_owner_role_id=state.current_owner_role_id,
            lineage_state=state.lineage_state,
            terminal_decision=state.terminal_decision,
            state_consistency=state.state_consistency,
            blocking_reason_code=state.blocking_reason_code,
            blocking_reason_text=state.blocking_reason_text,
            current_issue_number=state.current_issue_number,
            current_pr_number=state.current_pr_number,
            canonical_branch=state.canonical_branch,
            active_role_branch=state.active_role_branch,
            active_handoff_id=state.active_handoff_id,
            active_queue_message_id=state.active_queue_message_id,
            active_message_id_external=state.active_message_id_external,
            active_queue_claim_id=state.active_queue_claim_id,
            closed_at=state.closed_at,
            metadata=dict(state.metadata or {}),
        )

    @staticmethod
    def _not_implemented_result(
        request: WorkflowLifecycleRequest,
        *,
        note: str,
    ) -> WorkflowLifecycleResult:
        return WorkflowLifecycleResult(
            project_id=request.project_id,
            work_item_id=request.work_item_id,
            requested_transition_type=request.requested_transition_type,
            applied=False,
            state_view=None,
            decision_summary=WorkflowLifecycleDecisionSummary(
                transition_allowed=False,
                acceptance_allowed=False,
                requires_manual_repair=False,
                should_reset=False,
                should_retry=False,
                blocking_reasons=(note,),
                notes=(note,),
                metadata={'phase': 'phase1_phase2_shell'},
            ),
            resolved_execution_surface_key=None,
            recommended_next_action='Implement the first behavioral workflow lifecycle slice before using this path.',
            metadata={'phase': 'phase1_phase2_shell'},
        )

    def _require_current_state(self, request: WorkflowLifecycleRequest) -> WorkflowStateRecord:
        if request.workflow_state_id:
            state = self._workflow_state_repository.get_workflow_state(request.workflow_state_id)
            if state is not None:
                return state
        state = self._workflow_state_repository.get_workflow_state_for_work_item(request.work_item_id)
        if state is None:
            raise LookupError(f'No workflow state found for work item {request.work_item_id!r}')
        return state

    def _resolve_transition_evidence(
        self,
        request: WorkflowLifecycleRequest,
    ) -> tuple[QueueMessageRecord | None, TransitionInputRecord | None]:
        queue_message = None
        if request.source_queue_message_id:
            queue_message = self._runtime_event_repository.get_queue_message(request.source_queue_message_id)
        elif request.source_message_id_external:
            queue_message = self._runtime_event_repository.get_queue_message_by_external(
                request.source_message_id_external
            )

        transition_input = None
        if queue_message is None and request.source_packet_schema_type is None:
            expected_schema = self._packet_schema_for_transition(
                request.requested_transition_type or self._WORKER_RESULT_TRANSITION
            )
            for candidate in self._runtime_event_repository.list_transition_inputs_for_work_item(
                request.work_item_id
            ):
                if candidate.input_schema_type == expected_schema:
                    transition_input = candidate
                    break
        return queue_message, transition_input

    def _resolve_source_schema_type(
        self,
        request: WorkflowLifecycleRequest,
        queue_message: QueueMessageRecord | None,
        transition_input: TransitionInputRecord | None,
    ) -> str | None:
        if queue_message is not None:
            return queue_message.schema_type
        if request.source_packet_schema_type is not None:
            return request.source_packet_schema_type
        if transition_input is not None:
            return transition_input.input_schema_type
        return None

    def _resolve_active_claim(
        self,
        current_state: WorkflowStateRecord,
        queue_message: QueueMessageRecord | None,
    ) -> QueueClaimRecord | None:
        message_id = None
        if queue_message is not None:
            message_id = queue_message.queue_message_id
        elif current_state.active_queue_message_id is not None:
            message_id = current_state.active_queue_message_id
        if message_id is None:
            return None
        return self._workflow_state_repository.get_active_queue_claim_for_message(message_id)

    def _resolve_execution_surface_key(self, request: WorkflowLifecycleRequest) -> str | None:
        if not request.execution_surface_key and not request.repo_root_path and not request.runtime_root_path:
            return None
        resolution_request = ExecutionPackageResolutionRequest(
            execution_surface_key=request.execution_surface_key,
            repo_root_path=request.repo_root_path,
            runtime_root_path=request.runtime_root_path,
            work_item_id=request.work_item_id,
            metadata=dict(request.metadata or {}),
        )
        resolution = self._execution_package_resolution_service.resolve_execution_context(
            resolution_request
        )
        return resolution.execution_surface_key

    def _rejected_result(
        self,
        request: WorkflowLifecycleRequest,
        *,
        state: WorkflowStateRecord | None,
        blocking_reasons: tuple[str, ...],
        notes: tuple[str, ...],
        resolved_execution_surface_key: str | None,
        metadata: dict[str, object],
        recommended_next_action: str | None,
    ) -> WorkflowLifecycleResult:
        return WorkflowLifecycleResult(
            project_id=request.project_id,
            work_item_id=request.work_item_id,
            requested_transition_type=request.requested_transition_type,
            applied=False,
            state_view=self._state_view_from_record(state) if state is not None else None,
            decision_summary=WorkflowLifecycleDecisionSummary(
                transition_allowed=False,
                acceptance_allowed=False,
                requires_manual_repair=False,
                should_reset=False,
                should_retry=False,
                blocking_reasons=blocking_reasons,
                notes=notes,
                metadata=metadata,
            ),
            resolved_execution_surface_key=resolved_execution_surface_key,
            recommended_next_action=recommended_next_action,
            metadata=metadata,
        )

    def _derive_next_lineage_state(
        self,
        transition_type: str,
        current_state: WorkflowStateRecord,
    ) -> str:
        if transition_type == self._QA_RESULT_TRANSITION:
            return 'awaiting_acceptance'
        return current_state.lineage_state or 'awaiting_result'

    def _target_stage_for_transition(self, transition_type: str) -> str:
        if transition_type == self._QA_RESULT_TRANSITION:
            return self._QA_RESULT_TO_STAGE
        return self._WORKER_RESULT_TO_STAGE

    def _from_stage_for_transition(self, transition_type: str) -> str:
        if transition_type == self._QA_RESULT_TRANSITION:
            return self._QA_RESULT_FROM_STAGE
        return self._WORKER_RESULT_FROM_STAGE

    def _packet_schema_for_transition(self, transition_type: str) -> str:
        if transition_type == self._QA_RESULT_TRANSITION:
            return self._QA_RESULT_PACKET_SCHEMA
        return self._WORKER_RESULT_PACKET_SCHEMA

    def _lineage_strategy_for_transition(self, transition_type: str) -> str:
        if transition_type == self._QA_RESULT_TRANSITION:
            return 'advance_to_awaiting_acceptance'
        return 'preserve_current_lineage_state'

    def _recommended_apply_action(self, transition_type: str) -> str:
        if transition_type == self._QA_RESULT_TRANSITION:
            return 'Apply the QA-result transition to move the slice into TechLead QA review.'
        return 'Apply the worker-result transition to move the slice into TechLead worker review.'

    def _post_apply_review_action(self, transition_type: str) -> str:
        if transition_type == self._QA_RESULT_TRANSITION:
            return 'TechLead should review the returned QA verification result.'
        return 'TechLead should review the returned worker result.'

    def _recommended_next_action(
        self,
        transition_type: str,
        reset_decision: ResetRecoveryDecision,
        blocking_reasons: list[str],
    ) -> str:
        transition_label = 'QA-result' if transition_type == self._QA_RESULT_TRANSITION else 'worker-result'
        if reset_decision.requires_manual_repair:
            return f'Repair workflow consistency before applying the {transition_label} transition.'
        if reset_decision.should_reset:
            return f'Reset or reassign the active claim before accepting the {transition_label} transition.'
        if blocking_reasons:
            return f'Correct the {transition_label} transition request and evidence before retrying.'
        return self._recommended_apply_action(transition_type)

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()


__all__ = ['DefaultWorkflowLifecycleService']

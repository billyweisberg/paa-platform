from __future__ import annotations

from typing import Any

from paa_core.application.dto.methodology_execution import (
    ApplyMethodologyExecutionTransitionRequest,
    EvaluateMethodologyExecutionPreflightRequest,
    ExplainMethodologyExecutionRequest,
    GetMethodologyExecutionNextActionRequest,
    GetMethodologyExecutionStatusRequest,
    MethodologyExecutionBindingEntryInput,
    MethodologyExecutionOperationResult,
)
from paa_core.repositories.methodology_execution import (
    MethodologyExecutionBindingEntrySpec,
    MethodologyExecutionRecord,
    MethodologyExecutionRepository,
    PostgresMethodologyExecutionRepository,
)
from paa_core.runtime.workflow.methodology_execution_preflight import (
    DefaultMethodologyExecutionPreflightService,
    MethodologyExecutionPreflightOutcome,
    MethodologyExecutionPreflightRequest,
    MethodologyExecutionPreflightResult,
)
from paa_core.runtime.workflow.methodology_execution_projection import (
    DefaultMethodologyExecutionProjectionService,
    MethodologyExecutionExplainProjection,
    MethodologyExecutionNextActionProjection,
    MethodologyExecutionStatusProjection,
)
from paa_core.runtime.workflow.methodology_execution_state import (
    DefaultMethodologyExecutionStateService,
    MethodologyExecutionStateRequest,
    MethodologyExecutionStateResult,
    MethodologyExecutionStateSummary,
    MethodologyExecutionTransitionSummary,
)
from paa_core.services.implementation_plan_derivation.contracts import StructuredLogger


class _NullStructuredLogger:
    def info(self, event: str, **fields: object) -> None:
        del event, fields

    def warning(self, event: str, **fields: object) -> None:
        del event, fields


class DefaultMethodologyExecutionApplicationService:
    def __init__(
        self,
        *,
        methodology_execution_repository: MethodologyExecutionRepository | None = None,
        methodology_execution_projection_service: DefaultMethodologyExecutionProjectionService | None = None,
        methodology_execution_state_service: DefaultMethodologyExecutionStateService | None = None,
        methodology_execution_preflight_service: DefaultMethodologyExecutionPreflightService | None = None,
        logger: StructuredLogger | None = None,
    ) -> None:
        self._logger = logger if logger is not None else _NullStructuredLogger()
        self._repository = methodology_execution_repository or PostgresMethodologyExecutionRepository()
        self._projection_service = methodology_execution_projection_service or DefaultMethodologyExecutionProjectionService(
            methodology_execution_repository=self._repository,
            logger=self._logger,
        )
        self._state_service = methodology_execution_state_service or DefaultMethodologyExecutionStateService(
            methodology_execution_repository=self._repository,
            logger=self._logger,
        )
        self._preflight_service = methodology_execution_preflight_service or DefaultMethodologyExecutionPreflightService(
            methodology_execution_repository=self._repository,
            methodology_execution_state_service=self._state_service,
            methodology_execution_projection_service=self._projection_service,
            logger=self._logger,
        )

    def get_status(self, request: GetMethodologyExecutionStatusRequest) -> MethodologyExecutionOperationResult:
        if request.methodology_execution_id is not None:
            try:
                projection = self._projection_service.get_status_projection(request.methodology_execution_id)
            except LookupError:
                return self._not_found_result(
                    methodology_execution_id=request.methodology_execution_id,
                    project_id=request.project_id,
                    work_item_id=request.work_item_id,
                    component_id=request.component_id,
                )
            return MethodologyExecutionOperationResult(
                payload={'ok': True, 'item': self._serialize_status_projection(projection)}
            )
        if request.project_id and request.work_item_id:
            projection = self._projection_service.find_status_projection(
                request.project_id,
                request.work_item_id,
                request.component_id,
            )
            if projection is None:
                return self._not_found_result(
                    methodology_execution_id=request.methodology_execution_id,
                    project_id=request.project_id,
                    work_item_id=request.work_item_id,
                    component_id=request.component_id,
                )
            return MethodologyExecutionOperationResult(
                payload={'ok': True, 'item': self._serialize_status_projection(projection)}
            )
        return self._missing_identity_result()

    def get_next_action(
        self, request: GetMethodologyExecutionNextActionRequest
    ) -> MethodologyExecutionOperationResult:
        methodology_execution_id = request.methodology_execution_id
        if methodology_execution_id is None:
            if not (request.project_id and request.work_item_id):
                return self._missing_identity_result()
            resolved = self._resolve_record_from_anchors(
                project_id=request.project_id,
                work_item_id=request.work_item_id,
                component_id=request.component_id,
            )
            if resolved is None:
                return self._not_found_result(
                    methodology_execution_id=request.methodology_execution_id,
                    project_id=request.project_id,
                    work_item_id=request.work_item_id,
                    component_id=request.component_id,
                )
            methodology_execution_id = resolved.methodology_execution_id
        try:
            projection = self._projection_service.get_next_action_projection(methodology_execution_id)
        except LookupError:
            return self._not_found_result(
                methodology_execution_id=request.methodology_execution_id,
                project_id=request.project_id,
                work_item_id=request.work_item_id,
                component_id=request.component_id,
            )
        return MethodologyExecutionOperationResult(
            payload={'ok': True, 'item': self._serialize_next_action_projection(projection)}
        )

    def explain(self, request: ExplainMethodologyExecutionRequest) -> MethodologyExecutionOperationResult:
        methodology_execution_id = request.methodology_execution_id
        if methodology_execution_id is None:
            if not (request.project_id and request.work_item_id):
                return self._missing_identity_result()
            resolved = self._resolve_record_from_anchors(
                project_id=request.project_id,
                work_item_id=request.work_item_id,
                component_id=request.component_id,
            )
            if resolved is None:
                return self._not_found_result(
                    methodology_execution_id=request.methodology_execution_id,
                    project_id=request.project_id,
                    work_item_id=request.work_item_id,
                    component_id=request.component_id,
                )
            methodology_execution_id = resolved.methodology_execution_id
        try:
            projection = self._projection_service.explain_current_methodology_execution(methodology_execution_id)
        except LookupError:
            return self._not_found_result(
                methodology_execution_id=request.methodology_execution_id,
                project_id=request.project_id,
                work_item_id=request.work_item_id,
                component_id=request.component_id,
            )
        return MethodologyExecutionOperationResult(
            payload={'ok': True, 'item': self._serialize_explain_projection(projection)}
        )

    def apply_transition(
        self, request: ApplyMethodologyExecutionTransitionRequest
    ) -> MethodologyExecutionOperationResult:
        methodology_execution_id = request.methodology_execution_id
        if methodology_execution_id is None and not (request.project_id and request.work_item_id):
            return self._missing_identity_result()
        if methodology_execution_id is None:
            resolved = self._resolve_record_from_anchors(
                project_id=request.project_id,
                work_item_id=request.work_item_id,
                component_id=request.component_id,
            )
            if resolved is None:
                return self._not_found_result(
                    methodology_execution_id=request.methodology_execution_id,
                    project_id=request.project_id,
                    work_item_id=request.work_item_id,
                    component_id=request.component_id,
                )
            methodology_execution_id = resolved.methodology_execution_id
        result = self._state_service.apply_transition(
            MethodologyExecutionStateRequest(
                methodology_execution_id=methodology_execution_id,
                project_id=request.project_id,
                work_item_id=request.work_item_id,
                component_id=request.component_id,
                transition_key=request.transition_key,
                actor_role_id=request.actor_role_id,
                actor_name=request.actor_name,
                notes=request.notes,
                evidence=dict(request.evidence or {}),
                binding_entries=tuple(
                    self._binding_entry_spec_from_input(entry) for entry in request.binding_entries
                ),
                metadata=dict(request.metadata or {}),
            )
        )
        if not result.ok:
            payload: dict[str, Any] = {
                'ok': False,
                'code': result.reason,
                'details': result.details,
            }
            if result.current_state is not None:
                payload['current_state'] = self._serialize_state_summary(result.current_state)
            if result.methodology_execution_id is not None:
                payload['methodology_execution_id'] = result.methodology_execution_id
            return MethodologyExecutionOperationResult(payload=payload, exit_code=1)
        return MethodologyExecutionOperationResult(
            payload={
                'ok': True,
                'methodology_execution_id': result.methodology_execution_id,
                'current_state': self._serialize_state_summary(result.current_state),
                'transition': self._serialize_transition_summary(result.transition),
                'binding_update_applied': result.binding_update_applied,
            }
        )

    def evaluate_preflight(
        self, request: EvaluateMethodologyExecutionPreflightRequest
    ) -> MethodologyExecutionOperationResult:
        if request.methodology_execution_id is None and not (request.project_id and request.work_item_id):
            return self._missing_identity_result()
        result = self._preflight_service.evaluate_command(
            MethodologyExecutionPreflightRequest(
                methodology_execution_id=request.methodology_execution_id,
                project_id=request.project_id,
                work_item_id=request.work_item_id,
                component_id=request.component_id,
                command_family=request.command_family,
                command_name=request.command_name,
                command_arguments=dict(request.command_arguments or {}),
                actor_role_id=request.actor_role_id,
                actor_name=request.actor_name,
                metadata=dict(request.metadata or {}),
            )
        )
        return MethodologyExecutionOperationResult(
            payload=self._serialize_preflight_result(result),
            exit_code=0 if result.ok else 1,
        )

    def _resolve_record_from_anchors(
        self,
        *,
        project_id: str | None,
        work_item_id: str | None,
        component_id: str | None,
    ) -> MethodologyExecutionRecord | None:
        if not (project_id and work_item_id):
            return None
        return self._repository.find_methodology_execution_by_primary_ref(project_id, work_item_id, component_id)

    @staticmethod
    def _binding_entry_spec_from_input(
        entry: MethodologyExecutionBindingEntryInput,
    ) -> MethodologyExecutionBindingEntrySpec:
        return MethodologyExecutionBindingEntrySpec(
            binding_kind=entry.binding_kind,
            bound_record_id=entry.bound_record_id,
            bound_record_key=entry.bound_record_key,
            bound_record_ref=entry.bound_record_ref,
            is_primary=entry.is_primary,
            notes=entry.notes,
            metadata=entry.metadata,
        )

    @staticmethod
    def _serialize_status_projection(projection: MethodologyExecutionStatusProjection) -> dict[str, Any]:
        return {
            'methodology_execution_id': projection.methodology_execution_id,
            'lane': projection.lane,
            'stage': projection.stage,
            'step': projection.step,
            'status': projection.status,
            'current_owner_role': projection.current_owner_role,
            'next_action_key': projection.next_action_key,
            'blocked_reason': projection.blocked_reason,
            'component_id': projection.component_id,
            'design_package_id': projection.design_package_id,
            'implementation_plan_id': projection.implementation_plan_id,
            'coder_run_brief_id': projection.coder_run_brief_id,
            'packet_id': projection.packet_id,
            'workflow_state_id': projection.workflow_state_id,
            'active_authority_ref': projection.active_authority_ref,
            'active_artifact_ref': projection.active_artifact_ref,
            'binding_refs': projection.binding_refs,
            'summary_text': projection.summary_text,
            'metadata': projection.metadata or {},
        }

    @staticmethod
    def _serialize_next_action_projection(
        projection: MethodologyExecutionNextActionProjection,
    ) -> dict[str, Any]:
        return {
            'methodology_execution_id': projection.methodology_execution_id,
            'recommended_next_action_key': projection.recommended_next_action_key,
            'recommended_owner_role': projection.recommended_owner_role,
            'lane': projection.lane,
            'stage': projection.stage,
            'step': projection.step,
            'prerequisite_summary': projection.prerequisite_summary,
            'blocked_reason': projection.blocked_reason,
            'component_id': projection.component_id,
            'implementation_plan_id': projection.implementation_plan_id,
            'packet_id': projection.packet_id,
            'metadata': projection.metadata or {},
        }

    @staticmethod
    def _serialize_explain_projection(projection: MethodologyExecutionExplainProjection) -> dict[str, Any]:
        return {
            'methodology_execution_id': projection.methodology_execution_id,
            'lane': projection.lane,
            'stage': projection.stage,
            'step': projection.step,
            'status': projection.status,
            'current_owner_role': projection.current_owner_role,
            'explanation_summary': projection.explanation_summary,
            'transition_context': projection.transition_context,
            'binding_refs': projection.binding_refs,
            'blocked_reason': projection.blocked_reason,
            'metadata': projection.metadata or {},
        }

    @staticmethod
    def _serialize_state_summary(summary: MethodologyExecutionStateSummary | None) -> dict[str, Any] | None:
        if summary is None:
            return None
        return {
            'methodology_execution_id': summary.methodology_execution_id,
            'lane': summary.lane,
            'stage': summary.stage,
            'step': summary.step,
            'status': summary.status,
            'current_owner_role': summary.current_owner_role,
            'next_action_key': summary.next_action_key,
            'blocked_reason': summary.blocked_reason,
            'component_id': summary.component_id,
            'design_package_id': summary.design_package_id,
            'implementation_plan_id': summary.implementation_plan_id,
            'coder_run_brief_id': summary.coder_run_brief_id,
            'packet_id': summary.packet_id,
            'workflow_state_id': summary.workflow_state_id,
            'active_authority_ref': summary.active_authority_ref,
            'active_artifact_ref': summary.active_artifact_ref,
            'binding_refs': summary.binding_refs,
            'notes': summary.notes,
            'metadata': summary.metadata or {},
        }

    @staticmethod
    def _serialize_transition_summary(
        transition: MethodologyExecutionTransitionSummary | None,
    ) -> dict[str, Any] | None:
        if transition is None:
            return None
        return {
            'transition_key': transition.transition_key,
            'transition_kind': transition.transition_kind,
            'from_lane': transition.from_lane,
            'to_lane': transition.to_lane,
            'from_stage': transition.from_stage,
            'to_stage': transition.to_stage,
            'from_step': transition.from_step,
            'to_step': transition.to_step,
            'from_status': transition.from_status,
            'to_status': transition.to_status,
            'current_owner_role': transition.current_owner_role,
            'next_owner_role': transition.next_owner_role,
            'prerequisites_satisfied': transition.prerequisites_satisfied,
            'blocking_reasons': transition.blocking_reasons,
            'recommended_next_action': transition.recommended_next_action,
        }

    def _serialize_preflight_result(
        self, result: MethodologyExecutionPreflightResult
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            'ok': result.ok,
            'methodology_execution_id': result.methodology_execution_id,
            'outcome': self._serialize_preflight_outcome(result.outcome),
            'reason': result.reason,
            'details': result.details,
        }
        if result.status_projection is not None:
            payload['status_projection'] = self._serialize_status_projection(result.status_projection)
        return payload

    @staticmethod
    def _serialize_preflight_outcome(
        outcome: MethodologyExecutionPreflightOutcome,
    ) -> dict[str, Any]:
        return {
            'methodology_execution_id': outcome.methodology_execution_id,
            'outcome_kind': outcome.outcome_kind,
            'rule_key': outcome.rule_key,
            'lane': outcome.lane,
            'stage': outcome.stage,
            'step': outcome.step,
            'status': outcome.status,
            'current_owner_role': outcome.current_owner_role,
            'redirect_target': outcome.redirect_target,
            'recommended_next_action_key': outcome.recommended_next_action_key,
            'reason': outcome.reason,
            'details': outcome.details,
            'metadata': outcome.metadata or {},
        }

    @staticmethod
    def _missing_identity_result() -> MethodologyExecutionOperationResult:
        return MethodologyExecutionOperationResult(
            payload={'ok': False, 'code': 'missing_methodology_identity'},
            exit_code=1,
        )

    @staticmethod
    def _not_found_result(
        *,
        methodology_execution_id: str | None,
        project_id: str | None,
        work_item_id: str | None,
        component_id: str | None,
    ) -> MethodologyExecutionOperationResult:
        payload: dict[str, Any] = {'ok': False, 'code': 'methodology_execution_not_found'}
        if methodology_execution_id is not None:
            payload['methodology_execution_id'] = methodology_execution_id
        if project_id is not None:
            payload['project_id'] = project_id
        if work_item_id is not None:
            payload['work_item_id'] = work_item_id
        if component_id is not None:
            payload['component_id'] = component_id
        return MethodologyExecutionOperationResult(payload=payload, exit_code=1)


def build_default_methodology_execution_application_service() -> DefaultMethodologyExecutionApplicationService:
    return DefaultMethodologyExecutionApplicationService()

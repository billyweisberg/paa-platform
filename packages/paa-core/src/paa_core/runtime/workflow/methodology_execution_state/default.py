"""Default implementation for the methodology execution state service."""

from __future__ import annotations

from paa_core.repositories.methodology_execution import (
    MethodologyExecutionBindingReplaceSpec,
    MethodologyExecutionEventAppendSpec,
    MethodologyExecutionRecord,
    MethodologyExecutionRepository,
    MethodologyExecutionUpsertSpec,
)
from paa_core.services.implementation_plan_derivation.contracts import StructuredLogger

from .models import (
    MethodologyExecutionStateRequest,
    MethodologyExecutionStateResult,
    MethodologyExecutionStateSummary,
    MethodologyExecutionTransitionSummary,
)


class _NullStructuredLogger:
    def info(self, event: str, **fields: object) -> None:
        return None

    def warning(self, event: str, **fields: object) -> None:
        return None


class DefaultMethodologyExecutionStateService:
    """Default service for current methodology execution reads and one supported transition slice."""

    _SUPPORTED_TRANSITION_KEY = 'component-progress-reconciled'
    _SUPPORTED_FROM = (
        'component_realization',
        'slice_execution',
        'reconcile_component_plan_progress',
        'active',
    )
    _SUPPORTED_TO = (
        'component_realization',
        'slice_execution',
        'derive_next_activity_bundle',
        'ready',
    )
    _NEXT_OWNER_ROLE = 'System'
    _RECOMMENDED_NEXT_ACTION = 'derive-next-activity-bundle'

    def __init__(
        self,
        *,
        methodology_execution_repository: MethodologyExecutionRepository,
        logger: StructuredLogger | None = None,
    ) -> None:
        self._methodology_execution_repository = methodology_execution_repository
        self._logger = logger if logger is not None else _NullStructuredLogger()

    @property
    def methodology_execution_repository(self) -> MethodologyExecutionRepository:
        return self._methodology_execution_repository

    @property
    def logger(self) -> StructuredLogger:
        return self._logger

    def get_current_methodology_execution(self, methodology_execution_id: str) -> MethodologyExecutionStateSummary:
        record = self.methodology_execution_repository.get_methodology_execution(methodology_execution_id)
        if record is None:
            raise LookupError(f'No methodology execution found for {methodology_execution_id!r}')
        summary = self._summary_from_record(record)
        self.logger.info(
            'methodology_execution_state.get_current',
            methodology_execution_id=methodology_execution_id,
            lane=summary.lane,
            stage=summary.stage,
            step=summary.step,
            status=summary.status,
        )
        return summary

    def find_current_methodology_execution(
        self,
        project_id: str,
        work_item_id: str,
        component_id: str | None = None,
    ) -> MethodologyExecutionStateSummary | None:
        record = self.methodology_execution_repository.find_methodology_execution_by_primary_ref(
            project_id=project_id,
            work_item_id=work_item_id,
            component_id=component_id,
        )
        if record is None:
            return None
        summary = self._summary_from_record(record)
        self.logger.info(
            'methodology_execution_state.find_current',
            methodology_execution_id=summary.methodology_execution_id,
            project_id=project_id,
            work_item_id=work_item_id,
            component_id=component_id,
        )
        return summary

    def apply_transition(
        self,
        request: MethodologyExecutionStateRequest,
    ) -> MethodologyExecutionStateResult:
        record = self._resolve_record(request)
        if record is None:
            return self._blocked_result(
                request,
                reason='missing_methodology_execution',
                details='No current methodology execution record could be resolved for the supplied identity.',
            )

        current_summary = self._summary_from_record(record)
        if request.transition_key != self._SUPPORTED_TRANSITION_KEY:
            return self._blocked_result(
                request,
                current_state=current_summary,
                reason='unsupported_transition_key',
                details=(
                    f"Transition {request.transition_key!r} is not supported by the current "
                    'MethodologyExecutionStateService slice.'
                ),
            )

        current_tuple = (record.lane, record.stage, record.step, record.status)
        if current_tuple != self._SUPPORTED_FROM:
            return self._blocked_result(
                request,
                current_state=current_summary,
                reason='unsupported_current_state',
                details=(
                    'Current methodology execution state does not match the supported transition source: '
                    f'{current_tuple!r}'
                ),
            )

        transition = MethodologyExecutionTransitionSummary(
            transition_key=self._SUPPORTED_TRANSITION_KEY,
            transition_kind='automated_progression',
            from_lane=record.lane,
            to_lane=self._SUPPORTED_TO[0],
            from_stage=record.stage,
            to_stage=self._SUPPORTED_TO[1],
            from_step=record.step,
            to_step=self._SUPPORTED_TO[2],
            from_status=record.status,
            to_status=self._SUPPORTED_TO[3],
            current_owner_role=record.current_owner_role,
            next_owner_role=self._NEXT_OWNER_ROLE,
            prerequisites_satisfied=True,
            blocking_reasons=(),
            recommended_next_action=self._RECOMMENDED_NEXT_ACTION,
        )

        self.methodology_execution_repository.upsert_methodology_execution(
            MethodologyExecutionUpsertSpec(
                methodology_execution_id=record.methodology_execution_id,
                project_id=record.project_id,
                work_item_id=record.work_item_id,
                lane=transition.to_lane,
                stage=transition.to_stage,
                step=transition.to_step,
                status=transition.to_status,
                current_owner_role=self._NEXT_OWNER_ROLE,
                next_action_key=self._RECOMMENDED_NEXT_ACTION,
                blocked_reason=None,
                component_id=record.component_id,
                design_package_id=record.design_package_id,
                implementation_plan_id=record.implementation_plan_id,
                coder_run_brief_id=record.coder_run_brief_id,
                packet_id=record.packet_id,
                workflow_state_id=record.workflow_state_id,
                active_authority_ref=record.active_authority_ref,
                active_artifact_ref=record.active_artifact_ref,
                metadata=dict(record.metadata or {}),
            )
        )
        self.methodology_execution_repository.append_methodology_execution_event(
            MethodologyExecutionEventAppendSpec(
                methodology_execution_id=record.methodology_execution_id,
                from_lane=record.lane,
                to_lane=transition.to_lane,
                from_stage=record.stage,
                to_stage=transition.to_stage,
                from_step=record.step,
                to_step=transition.to_step,
                from_status=record.status,
                to_status=transition.to_status,
                transition_kind=transition.transition_kind,
                actor_role_id=request.actor_role_id,
                actor_name=request.actor_name,
                notes=request.notes,
                evidence=dict(request.evidence or {}),
            )
        )

        binding_update_applied = False
        if request.binding_entries:
            self.methodology_execution_repository.replace_methodology_execution_bindings(
                MethodologyExecutionBindingReplaceSpec(
                    methodology_execution_id=record.methodology_execution_id,
                    bindings=request.binding_entries,
                    replace_scope='replace_kind',
                )
            )
            binding_update_applied = True

        updated_record = self.methodology_execution_repository.get_methodology_execution(
            record.methodology_execution_id
        )
        if updated_record is None:
            raise LookupError(
                'Methodology execution disappeared after transition application: '
                f'{record.methodology_execution_id}'
            )
        updated_summary = self._summary_from_record(updated_record)
        self.logger.info(
            'methodology_execution_state.apply_transition.applied',
            methodology_execution_id=record.methodology_execution_id,
            transition_key=transition.transition_key,
            to_lane=transition.to_lane,
            to_stage=transition.to_stage,
            to_step=transition.to_step,
            to_status=transition.to_status,
        )
        return MethodologyExecutionStateResult(
            methodology_execution_id=record.methodology_execution_id,
            request=request,
            current_state=updated_summary,
            transition=transition,
            ok=True,
            binding_update_applied=binding_update_applied,
            metadata={'recommended_next_action': self._RECOMMENDED_NEXT_ACTION},
        )

    def supports_transition(self, transition_key: str) -> bool:
        return transition_key == self._SUPPORTED_TRANSITION_KEY

    def _resolve_record(
        self,
        request: MethodologyExecutionStateRequest,
    ) -> MethodologyExecutionRecord | None:
        if request.methodology_execution_id:
            return self.methodology_execution_repository.get_methodology_execution(
                request.methodology_execution_id
            )
        if request.project_id and request.work_item_id:
            return self.methodology_execution_repository.find_methodology_execution_by_primary_ref(
                project_id=request.project_id,
                work_item_id=request.work_item_id,
                component_id=request.component_id,
            )
        return None

    def _summary_from_record(self, record: MethodologyExecutionRecord) -> MethodologyExecutionStateSummary:
        bindings = self.methodology_execution_repository.list_methodology_execution_bindings(
            record.methodology_execution_id
        )
        binding_refs = tuple(
            binding.bound_record_ref
            for binding in bindings
            if binding.bound_record_ref
        )
        notes: list[str] = []
        if record.blocked_reason:
            notes.append(f'blocked:{record.blocked_reason}')
        if record.next_action_key:
            notes.append(f'next:{record.next_action_key}')
        return MethodologyExecutionStateSummary(
            methodology_execution_id=record.methodology_execution_id,
            lane=record.lane,
            stage=record.stage,
            step=record.step,
            status=record.status,
            current_owner_role=record.current_owner_role,
            next_action_key=record.next_action_key,
            blocked_reason=record.blocked_reason,
            component_id=record.component_id,
            design_package_id=record.design_package_id,
            implementation_plan_id=record.implementation_plan_id,
            coder_run_brief_id=record.coder_run_brief_id,
            packet_id=record.packet_id,
            workflow_state_id=record.workflow_state_id,
            active_authority_ref=record.active_authority_ref,
            active_artifact_ref=record.active_artifact_ref,
            binding_refs=binding_refs,
            notes=tuple(notes),
            metadata=dict(record.metadata or {}),
        )

    def _blocked_result(
        self,
        request: MethodologyExecutionStateRequest,
        *,
        reason: str,
        details: str,
        current_state: MethodologyExecutionStateSummary | None = None,
    ) -> MethodologyExecutionStateResult:
        self.logger.warning(
            'methodology_execution_state.apply_transition.blocked',
            methodology_execution_id=request.methodology_execution_id,
            transition_key=request.transition_key,
            reason=reason,
        )
        return MethodologyExecutionStateResult(
            methodology_execution_id=current_state.methodology_execution_id if current_state else request.methodology_execution_id,
            request=request,
            current_state=current_state,
            transition=None,
            ok=False,
            reason=reason,
            details=details,
            binding_update_applied=False,
            metadata={'blocking_reason': reason},
        )


__all__ = ['DefaultMethodologyExecutionStateService']

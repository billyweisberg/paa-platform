"""Default implementation for the methodology execution projection service."""

from __future__ import annotations

from paa_core.repositories.methodology_execution import (
    MethodologyExecutionProjectionInputRecord,
    MethodologyExecutionRecord,
    MethodologyExecutionRepository,
)
from paa_core.services.implementation_plan_derivation.contracts import StructuredLogger

from .models import (
    MethodologyExecutionExplainProjection,
    MethodologyExecutionNextActionProjection,
    MethodologyExecutionProjectionRequest,
    MethodologyExecutionProjectionResult,
    MethodologyExecutionStatusProjection,
)


class _NullStructuredLogger:
    def info(self, event: str, **fields: object) -> None:
        return None

    def warning(self, event: str, **fields: object) -> None:
        return None


class DefaultMethodologyExecutionProjectionService:
    """Default service for methodology execution status, next-action, and explain projection."""

    _SUPPORTED_PROJECTION_MODES = {'status', 'next', 'explain'}

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

    def get_status_projection(self, methodology_execution_id: str) -> MethodologyExecutionStatusProjection:
        projection_input = self.methodology_execution_repository.load_methodology_execution_projection_inputs(
            methodology_execution_id
        )
        projection = self._status_projection_from_input(projection_input)
        self.logger.info(
            'methodology_execution_projection.get_status',
            methodology_execution_id=methodology_execution_id,
            lane=projection.lane,
            stage=projection.stage,
            step=projection.step,
            status=projection.status,
        )
        return projection

    def find_status_projection(
        self,
        project_id: str,
        work_item_id: str,
        component_id: str | None = None,
    ) -> MethodologyExecutionStatusProjection | None:
        record = self.methodology_execution_repository.find_methodology_execution_by_primary_ref(
            project_id=project_id,
            work_item_id=work_item_id,
            component_id=component_id,
        )
        if record is None:
            return None
        projection = self.get_status_projection(record.methodology_execution_id)
        self.logger.info(
            'methodology_execution_projection.find_status',
            methodology_execution_id=projection.methodology_execution_id,
            project_id=project_id,
            work_item_id=work_item_id,
            component_id=component_id,
        )
        return projection

    def get_next_action_projection(self, methodology_execution_id: str) -> MethodologyExecutionNextActionProjection:
        projection_input = self.methodology_execution_repository.load_methodology_execution_projection_inputs(
            methodology_execution_id
        )
        projection = self._next_action_projection_from_input(projection_input)
        self.logger.info(
            'methodology_execution_projection.get_next',
            methodology_execution_id=methodology_execution_id,
            recommended_next_action_key=projection.recommended_next_action_key,
        )
        return projection

    def explain_current_methodology_execution(
        self,
        methodology_execution_id: str,
    ) -> MethodologyExecutionExplainProjection:
        projection_input = self.methodology_execution_repository.load_methodology_execution_projection_inputs(
            methodology_execution_id
        )
        projection = self._explain_projection_from_input(projection_input)
        self.logger.info(
            'methodology_execution_projection.explain',
            methodology_execution_id=methodology_execution_id,
            lane=projection.lane,
            stage=projection.stage,
            step=projection.step,
        )
        return projection

    def get_projection(
        self,
        request: MethodologyExecutionProjectionRequest,
    ) -> MethodologyExecutionProjectionResult:
        if request.projection_mode not in self._SUPPORTED_PROJECTION_MODES:
            return self._blocked_result(
                request,
                reason='unsupported_projection_mode',
                details=(
                    f"Projection mode {request.projection_mode!r} is not supported by the current "
                    'MethodologyExecutionProjectionService slice.'
                ),
            )

        projection_input = self._resolve_projection_input(request)
        if projection_input is None:
            return self._blocked_result(
                request,
                reason='missing_methodology_execution',
                details='No current methodology execution record could be resolved for the supplied identity.',
            )

        status_projection = self._status_projection_from_input(projection_input)
        next_action_projection = self._next_action_projection_from_input(projection_input)
        explain_projection = self._explain_projection_from_input(projection_input)
        result = MethodologyExecutionProjectionResult(
            methodology_execution_id=projection_input.execution.methodology_execution_id,
            request=request,
            status_projection=status_projection if request.projection_mode == 'status' else None,
            next_action_projection=next_action_projection if request.projection_mode == 'next' else None,
            explain_projection=explain_projection if request.projection_mode == 'explain' else None,
            ok=True,
            metadata={'projection_mode': request.projection_mode},
        )
        self.logger.info(
            'methodology_execution_projection.get_projection',
            methodology_execution_id=projection_input.execution.methodology_execution_id,
            projection_mode=request.projection_mode,
        )
        return result

    def _resolve_projection_input(
        self,
        request: MethodologyExecutionProjectionRequest,
    ) -> MethodologyExecutionProjectionInputRecord | None:
        methodology_execution_id = request.methodology_execution_id
        if methodology_execution_id is None and request.project_id and request.work_item_id:
            record = self.methodology_execution_repository.find_methodology_execution_by_primary_ref(
                project_id=request.project_id,
                work_item_id=request.work_item_id,
                component_id=request.component_id,
            )
            if record is None:
                return None
            methodology_execution_id = record.methodology_execution_id
        if methodology_execution_id is None:
            return None
        try:
            return self.methodology_execution_repository.load_methodology_execution_projection_inputs(
                methodology_execution_id
            )
        except LookupError:
            return None

    def _status_projection_from_input(
        self,
        projection_input: MethodologyExecutionProjectionInputRecord,
    ) -> MethodologyExecutionStatusProjection:
        record = projection_input.execution
        binding_refs = self._binding_refs(projection_input)
        return MethodologyExecutionStatusProjection(
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
            summary_text=self._status_summary_text(record),
            metadata=dict(record.metadata or {}),
        )

    def _next_action_projection_from_input(
        self,
        projection_input: MethodologyExecutionProjectionInputRecord,
    ) -> MethodologyExecutionNextActionProjection:
        record = projection_input.execution
        return MethodologyExecutionNextActionProjection(
            methodology_execution_id=record.methodology_execution_id,
            recommended_next_action_key=record.next_action_key,
            recommended_owner_role=record.current_owner_role,
            lane=record.lane,
            stage=record.stage,
            step=record.step,
            prerequisite_summary=self._prerequisite_summary(record),
            blocked_reason=record.blocked_reason,
            component_id=record.component_id,
            implementation_plan_id=record.implementation_plan_id,
            packet_id=record.packet_id,
            metadata=dict(record.metadata or {}),
        )

    def _explain_projection_from_input(
        self,
        projection_input: MethodologyExecutionProjectionInputRecord,
    ) -> MethodologyExecutionExplainProjection:
        record = projection_input.execution
        transition_context = None
        if projection_input.events:
            latest_event = projection_input.events[-1]
            transition_context = latest_event.transition_kind
        return MethodologyExecutionExplainProjection(
            methodology_execution_id=record.methodology_execution_id,
            lane=record.lane,
            stage=record.stage,
            step=record.step,
            status=record.status,
            current_owner_role=record.current_owner_role,
            explanation_summary=self._explanation_summary(record),
            transition_context=transition_context,
            binding_refs=self._binding_refs(projection_input),
            blocked_reason=record.blocked_reason,
            metadata=dict(record.metadata or {}),
        )

    def _binding_refs(self, projection_input: MethodologyExecutionProjectionInputRecord) -> tuple[str, ...]:
        return tuple(
            binding.bound_record_ref
            for binding in projection_input.bindings
            if binding.bound_record_ref
        )

    def _status_summary_text(self, record: MethodologyExecutionRecord) -> str:
        if record.blocked_reason:
            return (
                f'Methodology execution is blocked in {record.lane}/{record.stage}/{record.step}: '
                f'{record.blocked_reason}.'
            )
        if record.next_action_key:
            return (
                f'Methodology execution is {record.status} in {record.lane}/{record.stage}/{record.step} '
                f'and is ready for {record.next_action_key}.'
            )
        return f'Methodology execution is {record.status} in {record.lane}/{record.stage}/{record.step}.'

    def _prerequisite_summary(self, record: MethodologyExecutionRecord) -> tuple[str, ...]:
        summary: list[str] = [f'current-step:{record.step}', f'current-status:{record.status}']
        if record.implementation_plan_id:
            summary.append(f'implementation-plan:{record.implementation_plan_id}')
        if record.blocked_reason:
            summary.append(f'blocked:{record.blocked_reason}')
        return tuple(summary)

    def _explanation_summary(self, record: MethodologyExecutionRecord) -> str:
        if record.blocked_reason:
            return (
                f'The current methodology pointer is blocked during {record.step} because '
                f'{record.blocked_reason}.'
            )
        if record.next_action_key:
            return (
                f'The current methodology pointer is in {record.lane}/{record.stage}/{record.step} '
                f'with status {record.status}, so the next recommended action is {record.next_action_key}.'
            )
        return (
            f'The current methodology pointer is in {record.lane}/{record.stage}/{record.step} '
            f'with status {record.status}.'
        )

    def _blocked_result(
        self,
        request: MethodologyExecutionProjectionRequest,
        *,
        reason: str,
        details: str,
    ) -> MethodologyExecutionProjectionResult:
        self.logger.warning(
            'methodology_execution_projection.get_projection.blocked',
            methodology_execution_id=request.methodology_execution_id,
            projection_mode=request.projection_mode,
            reason=reason,
        )
        return MethodologyExecutionProjectionResult(
            methodology_execution_id=request.methodology_execution_id,
            request=request,
            status_projection=None,
            next_action_projection=None,
            explain_projection=None,
            ok=False,
            reason=reason,
            details=details,
            metadata={'blocking_reason': reason},
        )


__all__ = ['DefaultMethodologyExecutionProjectionService']

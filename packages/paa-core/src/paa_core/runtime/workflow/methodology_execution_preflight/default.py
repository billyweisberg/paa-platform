"""Default implementation for the methodology execution preflight service."""

from __future__ import annotations

from paa_core.repositories.methodology_execution import MethodologyExecutionRepository
from paa_core.services.implementation_plan_derivation.contracts import StructuredLogger
from paa_core.runtime.workflow.methodology_execution_projection import (
    MethodologyExecutionProjectionService,
    MethodologyExecutionStatusProjection,
)
from paa_core.runtime.workflow.methodology_execution_state import MethodologyExecutionStateService

from .models import (
    MethodologyExecutionPreflightOutcome,
    MethodologyExecutionPreflightRequest,
    MethodologyExecutionPreflightResult,
)


class _NullStructuredLogger:
    def info(self, event: str, **fields: object) -> None:
        return None

    def warning(self, event: str, **fields: object) -> None:
        return None


class DefaultMethodologyExecutionPreflightService:
    """Default service for methodology-aware command preflight classification."""

    _SUPPORTED_COMMANDS: dict[str, set[str]] = {
        'component': {'materialize', 'progress', 'reconcile', 'next'},
        'plan': {'progress', 'inspect'},
    }
    _WRONG_LANE_REDIRECTS = {'component': 'status', 'plan': 'status'}
    _NON_TERMINAL_WRONG_LANES = {'authority_derivation', 'runtime_execution', 'acceptance_closeout'}
    _MUTATING_COMPONENT_COMMANDS = {'materialize', 'reconcile', 'next'}

    def __init__(
        self,
        *,
        methodology_execution_repository: MethodologyExecutionRepository,
        methodology_execution_state_service: MethodologyExecutionStateService,
        methodology_execution_projection_service: MethodologyExecutionProjectionService,
        logger: StructuredLogger | None = None,
    ) -> None:
        self._methodology_execution_repository = methodology_execution_repository
        self._methodology_execution_state_service = methodology_execution_state_service
        self._methodology_execution_projection_service = methodology_execution_projection_service
        self._logger = logger if logger is not None else _NullStructuredLogger()

    @property
    def methodology_execution_repository(self) -> MethodologyExecutionRepository:
        return self._methodology_execution_repository

    @property
    def methodology_execution_state_service(self) -> MethodologyExecutionStateService:
        return self._methodology_execution_state_service

    @property
    def methodology_execution_projection_service(self) -> MethodologyExecutionProjectionService:
        return self._methodology_execution_projection_service

    @property
    def logger(self) -> StructuredLogger:
        return self._logger

    def evaluate_command(
        self,
        request: MethodologyExecutionPreflightRequest,
    ) -> MethodologyExecutionPreflightResult:
        if not self.supports_command_family(request.command_family or ''):
            outcome = self.blocked_outcome(
                request,
                reason='unsupported_command_family',
                details=f'Command family {request.command_family!r} is not supported by the current preflight slice.',
            )
            return self._result(request, None, outcome, ok=False, reason=outcome.reason, details=outcome.details)

        if not self.supports_command(request.command_family or '', request.command_name or ''):
            outcome = self.blocked_outcome(
                request,
                reason='unsupported_command',
                details=(
                    f'Command {request.command_family!r}/{request.command_name!r} is not supported '
                    'by the current preflight slice.'
                ),
            )
            return self._result(request, None, outcome, ok=False, reason=outcome.reason, details=outcome.details)

        projection = self._resolve_status_projection(request)
        if projection is None:
            outcome = self.blocked_outcome(
                request,
                reason='missing_methodology_execution',
                details='No current methodology execution record could be resolved for the supplied identity.',
            )
            return self._result(request, None, outcome, ok=False, reason=outcome.reason, details=outcome.details)

        if projection.lane in self._NON_TERMINAL_WRONG_LANES:
            outcome = MethodologyExecutionPreflightOutcome(
                methodology_execution_id=projection.methodology_execution_id,
                outcome_kind='redirect',
                rule_key=f'wrong-lane-{request.command_family}-command',
                lane=projection.lane,
                stage=projection.stage,
                step=projection.step,
                status=projection.status,
                current_owner_role=projection.current_owner_role,
                redirect_target=self._WRONG_LANE_REDIRECTS[request.command_family or ''],
                recommended_next_action_key=projection.next_action_key,
                reason=f'{request.command_family} commands are not valid while the active lane is {projection.lane}.',
                details='Use a lane-native command family or inspect the current methodology status first.',
            )
            return self._result(request, projection, outcome, ok=True)

        if projection.status == 'blocked' and self._is_mutating_command(request):
            outcome = self.blocked_outcome(
                request,
                methodology_execution_id=projection.methodology_execution_id,
                lane=projection.lane,
                stage=projection.stage,
                step=projection.step,
                status=projection.status,
                current_owner_role=projection.current_owner_role,
                redirect_target='explain',
                recommended_next_action_key=projection.next_action_key,
                reason='blocked_state',
                details='The current methodology execution is blocked; inspect the blocking reason before mutating commands.',
            )
            return self._result(request, projection, outcome, ok=False, reason=outcome.reason, details=outcome.details)

        outcome = self._classify_supported_command(request, projection)
        ok = outcome.outcome_kind in {'allowed', 'warn', 'redirect'}
        result = self._result(
            request,
            projection,
            outcome,
            ok=ok,
            reason=None if ok else outcome.reason,
            details=outcome.details if outcome.outcome_kind == 'blocked' else None,
        )
        event = 'methodology_execution_preflight.evaluate_command' if ok else 'methodology_execution_preflight.evaluate_command.blocked'
        log = self.logger.info if ok else self.logger.warning
        log(
            event,
            methodology_execution_id=projection.methodology_execution_id,
            command_family=request.command_family,
            command_name=request.command_name,
            outcome_kind=outcome.outcome_kind,
            rule_key=outcome.rule_key,
        )
        return result

    def supports_command_family(self, command_family: str) -> bool:
        return command_family in self._SUPPORTED_COMMANDS

    def supports_command(self, command_family: str, command_name: str) -> bool:
        return command_name in self._SUPPORTED_COMMANDS.get(command_family, set())

    def blocked_outcome(
        self,
        request: MethodologyExecutionPreflightRequest,
        *,
        reason: str,
        details: str,
        methodology_execution_id: str | None = None,
        lane: str | None = None,
        stage: str | None = None,
        step: str | None = None,
        status: str | None = None,
        current_owner_role: str | None = None,
        redirect_target: str | None = None,
        recommended_next_action_key: str | None = None,
    ) -> MethodologyExecutionPreflightOutcome:
        return MethodologyExecutionPreflightOutcome(
            methodology_execution_id=methodology_execution_id or request.methodology_execution_id,
            outcome_kind='blocked',
            rule_key=None,
            lane=lane,
            stage=stage,
            step=step,
            status=status,
            current_owner_role=current_owner_role,
            redirect_target=redirect_target,
            recommended_next_action_key=recommended_next_action_key,
            reason=reason,
            details=details,
            metadata={'blocking_reason': reason},
        )

    def _resolve_status_projection(
        self,
        request: MethodologyExecutionPreflightRequest,
    ) -> MethodologyExecutionStatusProjection | None:
        if request.methodology_execution_id:
            try:
                return self.methodology_execution_projection_service.get_status_projection(
                    request.methodology_execution_id
                )
            except LookupError:
                return None
        if request.project_id and request.work_item_id:
            return self.methodology_execution_projection_service.find_status_projection(
                request.project_id,
                request.work_item_id,
                request.component_id,
            )
        return None

    def _classify_supported_command(
        self,
        request: MethodologyExecutionPreflightRequest,
        projection: MethodologyExecutionStatusProjection,
    ) -> MethodologyExecutionPreflightOutcome:
        family = request.command_family or ''
        name = request.command_name or ''

        if family == 'component' and name == 'materialize':
            if (
                projection.lane == 'component_realization'
                and projection.stage == 'slice_execution'
                and projection.step == 'execute_component_activity'
                and projection.status in {'active', 'waiting'}
                and projection.implementation_plan_id is not None
            ):
                return MethodologyExecutionPreflightOutcome(
                    methodology_execution_id=projection.methodology_execution_id,
                    outcome_kind='warn',
                    rule_key='component-materialize-warn-active-slice',
                    lane=projection.lane,
                    stage=projection.stage,
                    step=projection.step,
                    status=projection.status,
                    current_owner_role=projection.current_owner_role,
                    redirect_target='component progress',
                    recommended_next_action_key=projection.next_action_key,
                    reason='An active slice already exists; rematerializing now may disrupt the current loop.',
                    details='Inspect component progress before re-materializing this component.',
                )
            if (
                projection.lane == 'component_realization'
                and projection.stage == 'component_materialization'
                and projection.step == 'materialize_component_spec'
                and projection.status in {'ready', 'active'}
            ):
                return self._allowed_outcome(
                    projection,
                    'component-materialize-allowed',
                    'Component materialization is allowed for the active component-materialization state.',
                )
            return self.blocked_outcome(
                request,
                methodology_execution_id=projection.methodology_execution_id,
                lane=projection.lane,
                stage=projection.stage,
                step=projection.step,
                status=projection.status,
                current_owner_role=projection.current_owner_role,
                recommended_next_action_key=projection.next_action_key,
                reason='component_materialize_not_allowed',
                details='Component materialization is not allowed for the current methodology state.',
            )

        if family == 'component' and name == 'progress':
            if self._has_component_plan_context(projection) and projection.stage in {'component_materialization', 'slice_execution'}:
                return self._allowed_outcome(
                    projection,
                    'component-progress-allowed',
                    'Component progress is allowed for the active component-realization lane.',
                )
            return self._missing_binding_outcome(request, projection, 'implementation_plan')

        if family == 'component' and name == 'reconcile':
            if not self._has_component_plan_context(projection):
                return self._missing_binding_outcome(request, projection, 'implementation_plan')
            if (
                projection.lane == 'component_realization'
                and projection.stage == 'slice_execution'
                and projection.step in {'reconcile_component_plan_progress', 'execute_component_activity'}
                and projection.status in {'ready', 'active', 'waiting'}
            ):
                return self._allowed_outcome(
                    projection,
                    'component-reconcile-allowed',
                    'Component reconcile is allowed for the active slice-execution state.',
                    redirect_target='component progress',
                )
            return self.blocked_outcome(
                request,
                methodology_execution_id=projection.methodology_execution_id,
                lane=projection.lane,
                stage=projection.stage,
                step=projection.step,
                status=projection.status,
                current_owner_role=projection.current_owner_role,
                recommended_next_action_key=projection.next_action_key,
                reason='component_reconcile_not_allowed',
                details='Component reconcile is not allowed for the current methodology state.',
            )

        if family == 'component' and name == 'next':
            if not self._has_component_plan_context(projection):
                return self._missing_binding_outcome(request, projection, 'implementation_plan')
            if (
                projection.lane == 'component_realization'
                and projection.stage == 'slice_execution'
                and projection.step == 'derive_next_activity_bundle'
                and projection.status == 'completed'
            ):
                return MethodologyExecutionPreflightOutcome(
                    methodology_execution_id=projection.methodology_execution_id,
                    outcome_kind='redirect',
                    rule_key='component-next-redirect-terminal',
                    lane=projection.lane,
                    stage=projection.stage,
                    step=projection.step,
                    status=projection.status,
                    current_owner_role=projection.current_owner_role,
                    redirect_target='status',
                    recommended_next_action_key=projection.next_action_key,
                    reason='No further component activities remain; inspect current methodology status instead.',
                    details='The component-realization lane is already completed for this plan.',
                )
            if (
                projection.lane == 'component_realization'
                and projection.stage == 'slice_execution'
                and projection.step in {'derive_next_activity_bundle', 'reconcile_component_plan_progress'}
                and projection.status in {'ready', 'active', 'waiting'}
            ):
                return self._allowed_outcome(
                    projection,
                    'component-next-allowed',
                    'Next activity derivation is allowed for the active slice-execution state.',
                )
            return self.blocked_outcome(
                request,
                methodology_execution_id=projection.methodology_execution_id,
                lane=projection.lane,
                stage=projection.stage,
                step=projection.step,
                status=projection.status,
                current_owner_role=projection.current_owner_role,
                recommended_next_action_key=projection.next_action_key,
                reason='component_next_not_allowed',
                details='Component next is not allowed for the current methodology state.',
            )

        if family == 'plan' and name in {'progress', 'inspect'}:
            if not self._has_component_plan_context(projection):
                return self._missing_binding_outcome(request, projection, 'implementation_plan')
            if (
                projection.lane == 'component_realization'
                and projection.stage in {'component_materialization', 'slice_execution'}
                and projection.status in {'ready', 'active', 'waiting', 'blocked', 'completed'}
            ):
                return self._allowed_outcome(
                    projection,
                    'plan-progress-allowed' if name == 'progress' else 'plan-inspect-allowed',
                    f'Plan {name} is allowed for the active component-realization lane.',
                )
            return self.blocked_outcome(
                request,
                methodology_execution_id=projection.methodology_execution_id,
                lane=projection.lane,
                stage=projection.stage,
                step=projection.step,
                status=projection.status,
                current_owner_role=projection.current_owner_role,
                recommended_next_action_key=projection.next_action_key,
                reason='plan_command_not_allowed',
                details=f'Plan {name} is not allowed for the current methodology state.',
            )

        return self.blocked_outcome(
            request,
            methodology_execution_id=projection.methodology_execution_id,
            lane=projection.lane,
            stage=projection.stage,
            step=projection.step,
            status=projection.status,
            current_owner_role=projection.current_owner_role,
            recommended_next_action_key=projection.next_action_key,
            reason='unsupported_command',
            details='Command is not supported by the current preflight slice.',
        )

    def _allowed_outcome(
        self,
        projection: MethodologyExecutionStatusProjection,
        rule_key: str,
        reason: str,
        *,
        redirect_target: str | None = None,
    ) -> MethodologyExecutionPreflightOutcome:
        return MethodologyExecutionPreflightOutcome(
            methodology_execution_id=projection.methodology_execution_id,
            outcome_kind='allowed',
            rule_key=rule_key,
            lane=projection.lane,
            stage=projection.stage,
            step=projection.step,
            status=projection.status,
            current_owner_role=projection.current_owner_role,
            redirect_target=redirect_target,
            recommended_next_action_key=projection.next_action_key,
            reason=reason,
        )

    def _missing_binding_outcome(
        self,
        request: MethodologyExecutionPreflightRequest,
        projection: MethodologyExecutionStatusProjection,
        binding_name: str,
    ) -> MethodologyExecutionPreflightOutcome:
        return self.blocked_outcome(
            request,
            methodology_execution_id=projection.methodology_execution_id,
            lane=projection.lane,
            stage=projection.stage,
            step=projection.step,
            status=projection.status,
            current_owner_role=projection.current_owner_role,
            recommended_next_action_key=projection.next_action_key,
            reason='missing_required_binding',
            details=f'The current methodology execution does not expose the required {binding_name} binding.',
        )

    def _has_component_plan_context(self, projection: MethodologyExecutionStatusProjection) -> bool:
        return projection.implementation_plan_id is not None or any(
            binding_ref.startswith('implementation_plan:')
            for binding_ref in projection.binding_refs
        )

    def _is_mutating_command(self, request: MethodologyExecutionPreflightRequest) -> bool:
        return (request.command_family == 'component' and request.command_name in self._MUTATING_COMPONENT_COMMANDS)

    def _result(
        self,
        request: MethodologyExecutionPreflightRequest,
        projection: MethodologyExecutionStatusProjection | None,
        outcome: MethodologyExecutionPreflightOutcome,
        *,
        ok: bool,
        reason: str | None = None,
        details: str | None = None,
    ) -> MethodologyExecutionPreflightResult:
        return MethodologyExecutionPreflightResult(
            methodology_execution_id=(
                projection.methodology_execution_id if projection is not None else request.methodology_execution_id
            ),
            request=request,
            status_projection=projection,
            outcome=outcome,
            ok=ok,
            reason=reason,
            details=details,
            metadata={'outcome_kind': outcome.outcome_kind, 'rule_key': outcome.rule_key},
        )


__all__ = ['DefaultMethodologyExecutionPreflightService']

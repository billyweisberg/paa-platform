"""Lane-aware command-family adapters for the PAA operator CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from paa_producer.component_spec_materializer import (
    DEFAULT_ANCHOR_CONSUMER_CONTEXT_KEY,
    DEFAULT_ANCHOR_DESIGN_PACKAGE_EXTERNAL,
    DEFAULT_PROJECT_SLUG,
    materialize_component_spec,
)
from paa_producer.implementation_plan_activity_state import (
    set_implementation_plan_activity_state,
)
from paa_producer.implementation_plan_progress import (
    derive_next_activity_bundle,
    implementation_plan_progress,
    reconcile_implementation_plan_progress,
)

from .models import (
    OperatorCommandRequest,
    OperatorCommandResult,
    OperatorFailure,
    OperatorOutputMessage,
    OperatorOutputSection,
    OperatorOutputTable,
)


def _missing_argument_result(request: OperatorCommandRequest, argument_name: str) -> OperatorCommandResult:
    return OperatorCommandResult(
        command=request.command,
        supported=True,
        success=False,
        exit_code=2,
        failure=OperatorFailure(
            code='missing_argument',
            summary=f'Missing required argument: {argument_name}',
            details=(f'command={request.command.command_family}:{request.command.command_name}',),
        ),
    )


def _unsupported_command_result(request: OperatorCommandRequest) -> OperatorCommandResult:
    return OperatorCommandResult(
        command=request.command,
        supported=False,
        success=False,
        exit_code=2,
        failure=OperatorFailure(
            code='unsupported_command',
            summary='Unsupported command for this command family.',
            details=(request.command.command_name,),
        ),
    )


def _summary_table(title: str, payload: dict[str, Any]) -> OperatorOutputTable:
    rows = tuple((str(key), str(value)) for key, value in payload.items())
    return OperatorOutputTable(title=title, columns=('field', 'value'), rows=rows)


class ComponentCommandAdapter:
    """Handle component-realization lane commands for governed components."""

    def run(self, request: OperatorCommandRequest) -> OperatorCommandResult:
        command_name = request.command.command_name
        if command_name == 'materialize':
            return self._materialize(request)
        if command_name == 'progress':
            return self._progress(request)
        if command_name == 'reconcile':
            return self._reconcile(request)
        if command_name == 'next':
            return self._next(request)
        if command_name == 'complete':
            return self._complete(request)
        return _unsupported_command_result(request)

    def _materialize(self, request: OperatorCommandRequest) -> OperatorCommandResult:
        spec = request.arguments.get('spec')
        if not spec:
            return _missing_argument_result(request, 'spec')
        result = materialize_component_spec(
            spec_path=Path(spec).resolve(),
            project_slug=str(request.arguments.get('project_slug', DEFAULT_PROJECT_SLUG)),
            anchor_design_package_external=str(
                request.arguments.get('anchor_design_package_external', DEFAULT_ANCHOR_DESIGN_PACKAGE_EXTERNAL)
            ),
            anchor_consumer_context_key=str(
                request.arguments.get('anchor_consumer_context_key', DEFAULT_ANCHOR_CONSUMER_CONTEXT_KEY)
            ),
        )
        payload = {
            'implementation_plan_id': result.implementation_plan_id,
            'plan_id_external': result.plan_id_external,
            'component_id': result.component_id,
            'component_element_count': len(result.component_element_keys),
            'activity_count': len(result.activity_keys),
        }
        return OperatorCommandResult(
            command=request.command,
            supported=True,
            success=True,
            exit_code=0,
            sections=(
                OperatorOutputSection(
                    title='Component Materialization',
                    messages=(
                        OperatorOutputMessage(
                            level='info',
                            text=f'Materialized {result.source_path}',
                        ),
                    ),
                    tables=(_summary_table('Materialization Summary', payload),),
                    data=payload,
                ),
            ),
            metadata={
                'implementation_plan_id': result.implementation_plan_id,
                'plan_id_external': result.plan_id_external,
            },
        )

    def _progress(self, request: OperatorCommandRequest) -> OperatorCommandResult:
        plan_id = request.arguments.get('plan_id')
        if not plan_id:
            return _missing_argument_result(request, 'plan_id')
        payload = implementation_plan_progress(plan_id=str(plan_id))
        return self._result_from_payload(request, 'Component Progress', payload)

    def _reconcile(self, request: OperatorCommandRequest) -> OperatorCommandResult:
        plan_id = request.arguments.get('plan_id')
        if not plan_id:
            return _missing_argument_result(request, 'plan_id')
        payload = reconcile_implementation_plan_progress(plan_id=str(plan_id))
        return self._result_from_payload(request, 'Component Reconcile', payload)

    def _next(self, request: OperatorCommandRequest) -> OperatorCommandResult:
        plan_id = request.arguments.get('plan_id')
        if not plan_id:
            return _missing_argument_result(request, 'plan_id')
        payload = derive_next_activity_bundle(plan_id=str(plan_id))
        success = bool(payload.get('ok', False))
        return self._result_from_payload(
            request,
            'Component Next Activity',
            payload,
            success=success,
            exit_code=0 if success else 2,
        )

    def _complete(self, request: OperatorCommandRequest) -> OperatorCommandResult:
        plan_id = request.arguments.get('plan_id')
        if not plan_id:
            return _missing_argument_result(request, 'plan_id')
        activity_key = request.arguments.get('activity_key')
        if not activity_key:
            return _missing_argument_result(request, 'activity_key')

        transition_payload = set_implementation_plan_activity_state(
            plan_id=str(plan_id),
            activity_key=str(activity_key),
            activity_state='completed',
            completed_at=_optional_string(request.arguments.get('completed_at')),
            metadata_json=_optional_string(request.arguments.get('metadata_json')),
        )

        if bool(request.arguments.get('no_reconcile', False)):
            payload = {
                **transition_payload,
                'reconcile_performed': False,
                'next_activity_derived': False,
            }
            return self._result_from_payload(request, 'Component Complete', payload)

        reconcile_payload = reconcile_implementation_plan_progress(plan_id=str(plan_id))
        payload: dict[str, Any] = {
            **transition_payload,
            'reconcile_performed': True,
            'reconcile_summary': reconcile_payload,
        }

        if bool(request.arguments.get('no_next', False)):
            payload['next_activity_derived'] = False
            return self._result_from_payload(request, 'Component Complete', payload)

        next_payload = derive_next_activity_bundle(plan_id=str(plan_id))
        payload['next_activity_derived'] = True
        payload['next_activity_bundle'] = next_payload
        success = bool(next_payload.get('ok', False) or next_payload.get('bundle_kind') == 'none')
        failure = None
        exit_code = 0 if success else 2
        if not success:
            failure = OperatorFailure(
                code='complete_followthrough_failed',
                summary='Activity completion persisted, but next-activity derivation did not produce an executable result.',
                details=tuple(str(item) for item in next_payload.get('blocking_reasons', ())),
                blocking=True,
                metadata=dict(next_payload),
            )
        return OperatorCommandResult(
            command=request.command,
            supported=True,
            success=success,
            exit_code=exit_code,
            sections=(
                OperatorOutputSection(
                    title='Component Complete',
                    messages=(OperatorOutputMessage(level='info', text='Activity completion command applied.'),),
                    tables=(_summary_table('Component Complete Summary', payload),),
                    data=payload,
                ),
            ),
            failure=failure,
            metadata=dict(payload),
        )

    @staticmethod
    def _result_from_payload(
        request: OperatorCommandRequest,
        title: str,
        payload: dict[str, Any],
        *,
        success: bool = True,
        exit_code: int = 0,
    ) -> OperatorCommandResult:
        return OperatorCommandResult(
            command=request.command,
            supported=True,
            success=success,
            exit_code=exit_code,
            sections=(
                OperatorOutputSection(
                    title=title,
                    messages=(OperatorOutputMessage(level='info', text='Command completed.'),),
                    tables=(_summary_table(title, payload),),
                    data=payload,
                ),
            ),
            failure=None if success else OperatorFailure(
                code='no_next_activity',
                summary='No executable next activity bundle is available.',
                details=tuple(str(item) for item in payload.get('blocking_reasons', ())),
                blocking=True,
                metadata=dict(payload),
            ),
            metadata=dict(payload),
        )


class PlanCommandAdapter:
    """Handle implementation-plan inspection commands."""

    def run(self, request: OperatorCommandRequest) -> OperatorCommandResult:
        command_name = request.command.command_name
        if command_name in {'progress', 'inspect'}:
            return self._progress(request)
        return _unsupported_command_result(request)

    def _progress(self, request: OperatorCommandRequest) -> OperatorCommandResult:
        plan_id = request.arguments.get('plan_id')
        if not plan_id:
            return _missing_argument_result(request, 'plan_id')
        payload = implementation_plan_progress(plan_id=str(plan_id))
        return OperatorCommandResult(
            command=request.command,
            supported=True,
            success=True,
            exit_code=0,
            sections=(
                OperatorOutputSection(
                    title='Implementation Plan Progress',
                    messages=(OperatorOutputMessage(level='info', text='Plan summary loaded.'),),
                    tables=(_summary_table('Plan Progress Summary', payload),),
                    data=payload,
                ),
            ),
            metadata=dict(payload),
        )


class StatusCommandAdapter:
    """Handle pointer-facing methodology status reads."""

    def __init__(self, *, methodology_execution_projection_service: object) -> None:
        self._projection_service = methodology_execution_projection_service

    def run(self, request: OperatorCommandRequest) -> OperatorCommandResult:
        if request.command.command_name == 'inspect':
            return self._inspect(request)
        if request.command.command_name == 'next':
            return self._next(request)
        return _unsupported_command_result(request)

    def _inspect(self, request: OperatorCommandRequest) -> OperatorCommandResult:
        methodology_execution_id = request.arguments.get('methodology_execution_id')
        project_id = request.arguments.get('project_id')
        work_item_id = request.arguments.get('work_item_id')
        component_id = request.arguments.get('component_id')
        if methodology_execution_id:
            projection = self._projection_service.get_status_projection(str(methodology_execution_id))
        elif project_id and work_item_id:
            projection = self._projection_service.find_status_projection(
                str(project_id),
                str(work_item_id),
                _optional_string(component_id),
            )
            if projection is None:
                return OperatorCommandResult(
                    command=request.command,
                    supported=True,
                    success=False,
                    exit_code=2,
                    failure=OperatorFailure(
                        code='missing_methodology_execution',
                        summary='No methodology execution could be resolved for the supplied anchors.',
                    ),
                )
        else:
            return _missing_argument_result(request, 'methodology_execution_id or project_id/work_item_id')
        payload = {
            'methodology_execution_id': projection.methodology_execution_id,
            'lane': projection.lane,
            'stage': projection.stage,
            'step': projection.step,
            'status': projection.status,
            'current_owner_role': projection.current_owner_role,
            'next_action_key': projection.next_action_key,
            'blocked_reason': projection.blocked_reason,
            'component_id': projection.component_id,
            'implementation_plan_id': projection.implementation_plan_id,
            'summary_text': projection.summary_text,
        }
        return OperatorCommandResult(
            command=request.command,
            supported=True,
            success=True,
            exit_code=0,
            sections=(
                OperatorOutputSection(
                    title='Methodology Status',
                    messages=(OperatorOutputMessage(level='info', text=projection.summary_text),),
                    tables=(_summary_table('Methodology Status Summary', payload),),
                    data=payload,
                ),
            ),
            metadata=dict(payload),
        )

    def _next(self, request: OperatorCommandRequest) -> OperatorCommandResult:
        methodology_execution_id = request.arguments.get('methodology_execution_id')
        if not methodology_execution_id:
            return _missing_argument_result(request, 'methodology_execution_id')
        projection = self._projection_service.get_next_action_projection(str(methodology_execution_id))
        payload = {
            'methodology_execution_id': projection.methodology_execution_id,
            'recommended_next_action_key': projection.recommended_next_action_key,
            'recommended_owner_role': projection.recommended_owner_role,
            'lane': projection.lane,
            'stage': projection.stage,
            'step': projection.step,
            'blocked_reason': projection.blocked_reason,
            'implementation_plan_id': projection.implementation_plan_id,
            'packet_id': projection.packet_id,
        }
        return OperatorCommandResult(
            command=request.command,
            supported=True,
            success=True,
            exit_code=0,
            sections=(
                OperatorOutputSection(
                    title='Methodology Next Action',
                    messages=(
                        OperatorOutputMessage(
                            level='info',
                            text=f"Next recommended action: {projection.recommended_next_action_key or 'none'}",
                        ),
                    ),
                    tables=(_summary_table('Methodology Next Summary', payload),),
                    data=payload,
                ),
            ),
            metadata=dict(payload),
        )


class ReportCommandAdapter:
    """Handle pointer-facing next/explain reads."""

    def __init__(self, *, methodology_execution_projection_service: object) -> None:
        self._projection_service = methodology_execution_projection_service

    def run(self, request: OperatorCommandRequest) -> OperatorCommandResult:
        if request.command.command_name == 'next':
            return self._next(request)
        if request.command.command_name == 'explain':
            return self._explain(request)
        return _unsupported_command_result(request)

    def _next(self, request: OperatorCommandRequest) -> OperatorCommandResult:
        methodology_execution_id = request.arguments.get('methodology_execution_id')
        if not methodology_execution_id:
            return _missing_argument_result(request, 'methodology_execution_id')
        projection = self._projection_service.get_next_action_projection(str(methodology_execution_id))
        payload = {
            'methodology_execution_id': projection.methodology_execution_id,
            'recommended_next_action_key': projection.recommended_next_action_key,
            'recommended_owner_role': projection.recommended_owner_role,
            'lane': projection.lane,
            'stage': projection.stage,
            'step': projection.step,
            'blocked_reason': projection.blocked_reason,
            'implementation_plan_id': projection.implementation_plan_id,
            'packet_id': projection.packet_id,
        }
        return OperatorCommandResult(
            command=request.command,
            supported=True,
            success=True,
            exit_code=0,
            sections=(
                OperatorOutputSection(
                    title='Methodology Next Action',
                    messages=(
                        OperatorOutputMessage(
                            level='info',
                            text=f"Next recommended action: {projection.recommended_next_action_key or 'none'}",
                        ),
                    ),
                    tables=(_summary_table('Methodology Next Summary', payload),),
                    data=payload,
                ),
            ),
            metadata=dict(payload),
        )

    def _explain(self, request: OperatorCommandRequest) -> OperatorCommandResult:
        methodology_execution_id = request.arguments.get('methodology_execution_id')
        if not methodology_execution_id:
            return _missing_argument_result(request, 'methodology_execution_id')
        projection = self._projection_service.explain_current_methodology_execution(str(methodology_execution_id))
        payload = {
            'methodology_execution_id': projection.methodology_execution_id,
            'lane': projection.lane,
            'stage': projection.stage,
            'step': projection.step,
            'status': projection.status,
            'current_owner_role': projection.current_owner_role,
            'transition_context': projection.transition_context,
            'blocked_reason': projection.blocked_reason,
            'explanation_summary': projection.explanation_summary,
        }
        return OperatorCommandResult(
            command=request.command,
            supported=True,
            success=True,
            exit_code=0,
            sections=(
                OperatorOutputSection(
                    title='Methodology Explain',
                    messages=(
                        OperatorOutputMessage(level='info', text=projection.explanation_summary),
                    ),
                    tables=(_summary_table('Methodology Explain Summary', payload),),
                    data=payload,
                ),
            ),
            metadata=dict(payload),
        )


def _optional_string(value: object | None) -> str | None:
    if value is None:
        return None
    return str(value)


__all__ = ['ComponentCommandAdapter', 'PlanCommandAdapter', 'ReportCommandAdapter', 'StatusCommandAdapter']

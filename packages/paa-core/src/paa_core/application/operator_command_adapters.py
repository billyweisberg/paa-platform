# pyright: reportMissingTypeStubs=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownParameterType=false, reportAttributeAccessIssue=false, reportGeneralTypeIssues=false, reportArgumentType=false
"""Application-layer operator command adapters for the PAA platform."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from paa_core.runtime.support.runtime_paths import resolved_repo_runtime_queue_topology
from paa_core.producer.component_spec_materializer import (
    DEFAULT_ANCHOR_CONSUMER_CONTEXT_KEY,
    DEFAULT_ANCHOR_DESIGN_PACKAGE_EXTERNAL,
    DEFAULT_PROJECT_SLUG,
    materialize_component_spec,
)
from paa_core.producer.implementation_plan_activity_state import (
    set_implementation_plan_activity_state,
)
from paa_core.producer.implementation_plan_progress import (
    derive_next_activity_bundle,
    implementation_plan_progress,
    reconcile_implementation_plan_progress,
)

from paa_core.runtime.orchestration.queue_claim_runtime import DefaultQueueClaimRuntimeService, QueueClaimRuntimeRequest
from paa_core.runtime.packets.reference_resolution import (
    PacketReferenceResolutionRequest,
)

from paa_core.application.dto.operator import (
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


def _invalid_argument_result(request: OperatorCommandRequest, argument_name: str, details: str) -> OperatorCommandResult:
    return OperatorCommandResult(
        command=request.command,
        supported=True,
        success=False,
        exit_code=2,
        failure=OperatorFailure(
            code='invalid_argument',
            summary=f'Invalid argument: {argument_name}',
            details=(details,),
        ),
    )


def _optional_json_object(value: object | None) -> dict[str, Any] | None:
    if value is None:
        return None
    parsed = json.loads(str(value))
    if not isinstance(parsed, dict):
        raise ValueError('JSON value must decode to an object.')
    return parsed


def _summary_table(title: str, payload: dict[str, Any]) -> OperatorOutputTable:
    rows = tuple((str(key), str(value)) for key, value in payload.items())
    return OperatorOutputTable(title=title, columns=('field', 'value'), rows=rows)


class _RequestBoundQueueTransportAdapter:
    def __init__(
        self,
        *,
        packet_message_id: str | None,
        packet_payload: dict[str, Any] | None,
        packet_path: str | None,
        queue_name: str,
        packet_schema_type: str,
        queue_packet_reader: object | None,
        runtime_event_repository: object | None = None,
    ) -> None:
        self._packet_message_id = packet_message_id
        self._packet_payload = packet_payload
        self._packet_path = packet_path
        self._queue_name = queue_name
        self._packet_schema_type = packet_schema_type
        self._queue_packet_reader = queue_packet_reader
        self._runtime_event_repository = runtime_event_repository

    def preview_queue(self, queue_name: str, *, limit: int = 1) -> object:
        del limit
        if queue_name != self._queue_name:
            return None
        return self._resolve_packet()

    def claim_next_packet(self, queue_name: str, *, claimant_name: str | None = None) -> object:
        del claimant_name
        if queue_name != self._queue_name:
            return None
        return self._resolve_packet()

    def _resolve_packet(self) -> object:
        if self._packet_message_id and self._runtime_event_repository is not None:
            queue_message = self._runtime_event_repository.get_queue_message_by_external(self._packet_message_id)
            if queue_message is None or queue_message.queue_name != self._queue_name:
                return None
            return {
                'packet_message_id': queue_message.message_id_external or queue_message.queue_message_id,
                'packet_schema_type': queue_message.schema_type,
                'packet_reference': queue_message.message_id_external or queue_message.queue_message_id,
            }
        if self._packet_payload is not None:
            return {
                'packet_message_id': None,
                'packet_schema_type': self._packet_schema_type,
                'packet_reference': 'debug:inline-packet-payload',
                'packet_payload': self._packet_payload,
            }
        if self._packet_path:
            return {
                'packet_message_id': None,
                'packet_schema_type': self._packet_schema_type,
                'packet_path': self._packet_path,
                'packet_reference': self._packet_path,
            }
        return None


class _PassthroughPacketEnvelopeValidator:
    def validate_packet_envelope(self, packet: object) -> object:
        return {'ok': packet is not None}


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


class RoleCommandAdapter:
    """Handle generic runtime role identity commands."""

    _ALLOWED_CATEGORIES = frozenset({'architecture', 'engineering', 'verification', 'operations', 'coordination'})

    def __init__(self, *, runtime_identity_repository: object) -> None:
        self._runtime_identity_repository = runtime_identity_repository

    def run(self, request: OperatorCommandRequest) -> OperatorCommandResult:
        if request.command.command_name == 'add':
            return self._add(request)
        return _unsupported_command_result(request)

    def _add(self, request: OperatorCommandRequest) -> OperatorCommandResult:
        project_slug = request.arguments.get('project_slug')
        if not project_slug:
            return _missing_argument_result(request, 'project_slug')
        name = request.arguments.get('name')
        if not name:
            return _missing_argument_result(request, 'name')
        category = str(request.arguments.get('category') or '').strip()
        if not category:
            return _missing_argument_result(request, 'category')
        if category not in self._ALLOWED_CATEGORIES:
            return _invalid_argument_result(
                request,
                'category',
                'Allowed values: architecture, engineering, verification, operations, coordination.',
            )

        from paa_core.repositories.runtime_identity import RoleUpsertSpec

        try:
            record = self._runtime_identity_repository.upsert_role(
                RoleUpsertSpec(
                    project_slug=str(project_slug),
                    name=str(name),
                    category=category,
                    description=_optional_string(request.arguments.get('description')),
                    is_human_capable=bool(request.arguments.get('is_human_capable', True)),
                    is_automation_capable=bool(request.arguments.get('is_automation_capable', True)),
                    sort_order=int(request.arguments.get('sort_order', 100)),
                    active=bool(request.arguments.get('active', True)),
                )
            )
        except LookupError as exc:
            return _invalid_argument_result(request, 'project_slug', str(exc))

        payload = {
            'project_slug': str(project_slug),
            'role_id': record.role_id,
            'name': record.name,
            'category': record.category,
            'is_human_capable': record.is_human_capable,
            'is_automation_capable': record.is_automation_capable,
            'sort_order': record.sort_order,
            'active': record.active,
        }
        return OperatorCommandResult(
            command=request.command,
            supported=True,
            success=True,
            exit_code=0,
            sections=(
                OperatorOutputSection(
                    title='Role Add',
                    messages=(OperatorOutputMessage(level='info', text='Runtime role upsert completed.'),),
                    tables=(_summary_table('Role Add Summary', payload),),
                    data=payload,
                ),
            ),
            metadata=dict(payload),
        )


class AgentCommandAdapter:
    """Handle generic runtime agent identity commands."""

    _ALLOWED_AGENT_TYPES = frozenset({'human', 'automation', 'service'})

    def __init__(self, *, runtime_identity_repository: object) -> None:
        self._runtime_identity_repository = runtime_identity_repository

    def run(self, request: OperatorCommandRequest) -> OperatorCommandResult:
        if request.command.command_name == 'add':
            return self._add(request)
        return _unsupported_command_result(request)

    def _add(self, request: OperatorCommandRequest) -> OperatorCommandResult:
        project_slug = request.arguments.get('project_slug')
        if not project_slug:
            return _missing_argument_result(request, 'project_slug')
        name = request.arguments.get('name')
        if not name:
            return _missing_argument_result(request, 'name')
        agent_type = str(request.arguments.get('agent_type') or '').strip()
        if not agent_type:
            return _missing_argument_result(request, 'agent_type')
        if agent_type not in self._ALLOWED_AGENT_TYPES:
            return _invalid_argument_result(
                request,
                'agent_type',
                'Allowed values: human, automation, service.',
            )
        metadata: dict[str, Any] | None = None
        if request.arguments.get('metadata_json') is not None:
            try:
                metadata = _optional_json_object(request.arguments.get('metadata_json'))
            except ValueError as exc:
                return _invalid_argument_result(request, 'metadata_json', str(exc))

        from paa_core.repositories.runtime_identity import AgentUpsertSpec

        try:
            record = self._runtime_identity_repository.upsert_agent(
                AgentUpsertSpec(
                    project_slug=str(project_slug),
                    name=str(name),
                    role_name=_optional_string(request.arguments.get('role_name')),
                    agent_type=agent_type,
                    runtime_kind=_optional_string(request.arguments.get('runtime_kind')),
                    active=bool(request.arguments.get('active', True)),
                    metadata=metadata,
                )
            )
        except LookupError as exc:
            return _invalid_argument_result(request, 'role_name', str(exc))

        payload = {
            'project_slug': str(project_slug),
            'agent_id': record.agent_id,
            'name': record.name,
            'role_id': record.role_id,
            'agent_type': record.agent_type,
            'runtime_kind': record.runtime_kind,
            'active': record.active,
        }
        return OperatorCommandResult(
            command=request.command,
            supported=True,
            success=True,
            exit_code=0,
            sections=(
                OperatorOutputSection(
                    title='Agent Add',
                    messages=(OperatorOutputMessage(level='info', text='Runtime agent upsert completed.'),),
                    tables=(_summary_table('Agent Add Summary', payload),),
                    data=payload,
                ),
            ),
            metadata=dict(payload),
        )


__all__ = ['AgentCommandAdapter', 'ComponentCommandAdapter', 'PlanCommandAdapter', 'QueueCommandAdapter', 'ReportCommandAdapter', 'RoleCommandAdapter', 'StatusCommandAdapter', 'WorkerCommandAdapter']


class QueueCommandAdapter:
    """Handle queue-facing preview commands over the runtime controller."""

    def __init__(
        self,
        *,
        queue_packet_runtime_controller: object,
        queue_packet_reader: object | None = None,
        packet_envelope_validator: object | None = None,
        queue_claim_state_adapter: object | None = None,
        runtime_event_repository: object | None = None,
    ) -> None:
        self._runtime_controller = queue_packet_runtime_controller
        self._queue_packet_reader = queue_packet_reader
        self._packet_envelope_validator = packet_envelope_validator
        self._queue_claim_state_adapter = queue_claim_state_adapter
        self._runtime_event_repository = runtime_event_repository

    def run(self, request: OperatorCommandRequest) -> OperatorCommandResult:
        if request.command.command_name == 'preview':
            return self._preview(request)
        return _unsupported_command_result(request)

    def _preview(self, request: OperatorCommandRequest) -> OperatorCommandResult:
        queue_name = request.arguments.get('queue_name')
        if not queue_name:
            return _missing_argument_result(request, 'queue_name')
        packet_schema_type = request.arguments.get('packet_schema_type')
        if not packet_schema_type:
            return _missing_argument_result(request, 'packet_schema_type')
        result = self._assemble_queue_preview(
            request,
            queue_name=str(queue_name),
            packet_schema_type=str(packet_schema_type),
        )
        if isinstance(result, OperatorCommandResult):
            return result
        payload = {
            'queue_name': result.request.queue_name,
            'packet_schema_type': result.preview_summary.packet_schema_type if result.preview_summary else None,
            'packet_message_id': result.preview_summary.packet_message_id if result.preview_summary else None,
            'packet_reference': result.preview_summary.packet_reference if result.preview_summary else None,
            'preview_supported': result.preview_summary.preview_supported if result.preview_summary else False,
            'claim_supported': result.preview_summary.claim_supported if result.preview_summary else False,
            'reason': result.reason,
            'normalized_packet_envelope': result.normalized_packet_envelope,
            'normalized_packet_payload': result.normalized_packet_payload,
        }
        return OperatorCommandResult(
            command=request.command,
            supported=True,
            success=result.ok,
            exit_code=0 if result.ok else 2,
            sections=(
                OperatorOutputSection(
                    title='Queue Preview',
                    messages=(OperatorOutputMessage(level='info', text='Queue packet preview completed.'),),
                    tables=(_summary_table('Queue Preview Summary', payload),),
                    data=payload,
                ),
            ),
            failure=None if result.ok else OperatorFailure(
                code=result.reason or 'queue_preview_failed',
                summary=result.details or 'Queue packet preview failed.',
                details=tuple(result.preview_summary.blocking_reasons) if result.preview_summary else (),
            ),
            metadata=dict(payload),
        )

    def _assemble_queue_preview(
        self,
        request: OperatorCommandRequest,
        *,
        queue_name: str,
        packet_schema_type: str,
    ) -> object:
        try:
            packet_payload = _optional_json_object(request.arguments.get('packet_payload_json'))
        except ValueError as exc:
            return _invalid_argument_result(request, 'packet_payload_json', str(exc))
        supported_queue_names = (queue_name,)
        repo_root_value = _optional_string(request.invocation_context.repo_root)
        if repo_root_value:
            topology = resolved_repo_runtime_queue_topology(Path(repo_root_value).resolve())
            supported_queue_names = tuple(topology.queue_names.values())
        service = DefaultQueueClaimRuntimeService(
            queue_transport_adapter=_RequestBoundQueueTransportAdapter(
                packet_message_id=_optional_string(request.arguments.get('packet_message_id')),
                packet_payload=packet_payload,
                packet_path=_optional_string(request.arguments.get('packet_path')),
                queue_name=queue_name,
                packet_schema_type=packet_schema_type,
                queue_packet_reader=self._queue_packet_reader,
                runtime_event_repository=self._runtime_event_repository,
            ),
            packet_envelope_validator=self._packet_envelope_validator or _PassthroughPacketEnvelopeValidator(),
            queue_claim_state_adapter=self._queue_claim_state_adapter,
            supported_queue_names=supported_queue_names,
        )
        return service.assemble_queue_intake(
            QueueClaimRuntimeRequest(
                queue_name=queue_name,
                intake_mode='preview',
                packet_message_id=_optional_string(request.arguments.get('packet_message_id')),
                packet_schema_type=packet_schema_type,
                claimant_name=_optional_string(request.arguments.get('actor_name')),
                host_name=_optional_string(request.arguments.get('host_name')),
                metadata={'repo_root': request.invocation_context.repo_root},
            ),
        )


class WorkerCommandAdapter:
    """Handle worker-facing dispatch commands over the runtime controller."""

    def __init__(
        self,
        *,
        queue_packet_runtime_controller: object,
        packet_reference_resolution_service: object,
        queue_packet_reader: object | None = None,
        packet_envelope_validator: object | None = None,
        queue_claim_state_adapter: object | None = None,
        runtime_event_repository: object | None = None,
    ) -> None:
        self._runtime_controller = queue_packet_runtime_controller
        self._packet_reference_resolution_service = packet_reference_resolution_service
        self._queue_adapter = QueueCommandAdapter(
            queue_packet_runtime_controller=queue_packet_runtime_controller,
            queue_packet_reader=queue_packet_reader,
            packet_envelope_validator=packet_envelope_validator,
            queue_claim_state_adapter=queue_claim_state_adapter,
            runtime_event_repository=runtime_event_repository,
        )

    def run(self, request: OperatorCommandRequest) -> OperatorCommandResult:
        if request.command.command_name == 'dispatch':
            return self._dispatch(request)
        return _unsupported_command_result(request)

    def _dispatch(self, request: OperatorCommandRequest) -> OperatorCommandResult:
        queue_name = request.arguments.get('queue_name')
        if not queue_name:
            return _missing_argument_result(request, 'queue_name')
        packet_schema_type = request.arguments.get('packet_schema_type')
        if not packet_schema_type:
            return _missing_argument_result(request, 'packet_schema_type')
        queue_claim_result = self._queue_adapter._assemble_queue_preview(
            request,
            queue_name=str(queue_name),
            packet_schema_type=str(packet_schema_type),
        )
        if isinstance(queue_claim_result, OperatorCommandResult):
            return queue_claim_result
        resolution_result = self._packet_reference_resolution_service.resolve_packet_reference(
            PacketReferenceResolutionRequest(
                packet_message_id=(
                    queue_claim_result.preview_summary.packet_message_id
                    if queue_claim_result.preview_summary
                    else _optional_string(request.arguments.get('packet_message_id'))
                ),
                packet_path=_optional_string(request.arguments.get('packet_path')),
                packet_reference=(
                    queue_claim_result.preview_summary.packet_reference
                    if queue_claim_result.preview_summary
                    else None
                ),
                queue_name=str(queue_name),
                packet_schema_type=str(packet_schema_type),
                actor_name=_optional_string(request.arguments.get('actor_name')),
                host_name=_optional_string(request.arguments.get('host_name')),
                metadata={'repo_root': request.invocation_context.repo_root},
            )
        )
        if not resolution_result.ok and queue_claim_result.normalized_packet_payload is None:
            return OperatorCommandResult(
                command=request.command,
                supported=True,
                success=False,
                exit_code=2,
                sections=(
                    OperatorOutputSection(
                        title='Worker Dispatch',
                        messages=(OperatorOutputMessage(level='warning', text='Worker dispatch could not resolve the packet reference.'),),
                        tables=(
                            _summary_table(
                                'Worker Dispatch Summary',
                                {
                                    'queue_name': str(queue_name),
                                    'packet_schema_type': str(packet_schema_type),
                                    'packet_message_id': (
                                        resolution_result.resolution_summary.packet_message_id
                                        or _optional_string(request.arguments.get('packet_message_id'))
                                    ),
                                    'packet_path': resolution_result.resolution_summary.resolved_packet_path,
                                    'target_worker_host': 'TechLeadWorkerService',
                                    'dispatch_supported': False,
                                    'reason': resolution_result.reason,
                                    'normalized_queue_side_effect_summary': None,
                                },
                            ),
                        ),
                        data={
                            'queue_name': str(queue_name),
                            'packet_schema_type': str(packet_schema_type),
                            'packet_message_id': (
                                resolution_result.resolution_summary.packet_message_id
                                or _optional_string(request.arguments.get('packet_message_id'))
                            ),
                            'packet_path': resolution_result.resolution_summary.resolved_packet_path,
                            'target_worker_host': 'TechLeadWorkerService',
                            'dispatch_supported': False,
                            'reason': resolution_result.reason,
                            'normalized_queue_side_effect_summary': None,
                        },
                    ),
                ),
                failure=OperatorFailure(
                    code=resolution_result.reason or 'packet_reference_resolution_failed',
                    summary=resolution_result.details or 'Worker dispatch could not resolve the packet reference.',
                    details=resolution_result.resolution_summary.blocking_reasons,
                ),
            )
        from paa_core.runtime.orchestration.queue_packet_runtime_controller import QueuePacketRuntimeRequest

        result = self._runtime_controller.handle_packet(
            QueuePacketRuntimeRequest(
                queue_name=str(queue_name),
                packet_schema_type=str(packet_schema_type),
                packet_message_id=(
                    resolution_result.resolution_summary.packet_message_id
                    or (
                        queue_claim_result.preview_summary.packet_message_id
                        if queue_claim_result.preview_summary
                        else _optional_string(request.arguments.get('packet_message_id'))
                    )
                ),
                packet_path=resolution_result.resolution_summary.resolved_packet_path,
                packet_payload=resolution_result.normalized_packet_payload or queue_claim_result.normalized_packet_payload,
                runtime_mode='dry_run' if bool(request.invocation_context.dry_run) else 'live',
                actor_name=_optional_string(request.arguments.get('actor_name')),
                host_name=_optional_string(request.arguments.get('host_name')),
                metadata={'repo_root': request.invocation_context.repo_root},
            )
        )
        payload = {
            'queue_name': result.request.queue_name,
            'packet_schema_type': result.request.packet_schema_type,
            'packet_message_id': result.request.packet_message_id,
            'packet_path': result.request.packet_path,
            'target_worker_host': result.dispatch_summary.target_worker_host,
            'dispatch_supported': result.dispatch_summary.dispatch_supported,
            'reason': result.reason,
            'normalized_queue_side_effect_summary': result.normalized_queue_side_effect_summary,
        }
        return OperatorCommandResult(
            command=request.command,
            supported=True,
            success=result.ok,
            exit_code=0 if result.ok else 2,
            sections=(
                OperatorOutputSection(
                    title='Worker Dispatch',
                    messages=(OperatorOutputMessage(level='info', text='Worker dispatch preview completed.'),),
                    tables=(_summary_table('Worker Dispatch Summary', payload),),
                    data=payload,
                ),
            ),
            failure=None if result.ok else OperatorFailure(
                code=result.reason or 'worker_dispatch_failed',
                summary=result.details or 'Worker dispatch failed.',
                details=tuple(result.dispatch_summary.blocking_reasons),
            ),
            metadata=dict(payload),
        )

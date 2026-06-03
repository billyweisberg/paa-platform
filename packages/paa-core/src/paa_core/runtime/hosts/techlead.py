"""TechLead runtime host bootstrap and loop for the PAA consumer runtime."""

from __future__ import annotations

from dataclasses import dataclass
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol, cast

from paa_core.runtime.transport.claim_ledger import FileQueueClaimLedgerRepository, utc_now
from paa_core.config import DEFAULT_RUNTIME_QUEUE_EXCHANGE, load_unified_runtime_project_config
from paa_core.policies.deployment_capability import DefaultDeploymentCapabilityPolicy
from paa_core.runtime.transport.rabbitmq import RabbitMQManagementClient, build_default_management_client
from paa_core.repositories.execution_package import PostgresExecutionPackageRepository
from paa_core.policies.acceptance import DefaultAcceptancePolicy
from paa_core.policies.reset_recovery import DefaultResetRecoveryPolicy
from paa_core.policies.workflow_transition import DefaultWorkflowTransitionPolicy
from paa_core.repositories.methodology_execution import PostgresMethodologyExecutionRepository
from paa_core.repositories.runtime_identity import PostgresRuntimeIdentityRepository
from paa_core.repositories.runtime_event import PostgresRuntimeEventRepository
from paa_core.repositories.workflow_state import (
    PostgresWorkflowStateRepository,
    WorkflowStateUpsertSpec,
    WorkflowTransitionAppendSpec,
)
from paa_core.runtime_paths import repo_project_config_path, resolved_repo_runtime_queue_topology
from paa_core.services.dev_worker import DevWorkerService
from paa_core.runtime.packets.execution_package_resolution import (
    DefaultExecutionPackageResolutionService,
    ExecutionPackageResolutionService,
)
from paa_core.runtime.packets.execution_package_resolution.models import (
    ExecutionPackageCapabilitySummary,
    ExecutionPackageGap,
    ExecutionPackageResolutionRequest,
    ExecutionPackageResolutionView,
)
from paa_core.services.implementation_plan_derivation.contracts import StructuredLogger
from paa_core.services.methodology_execution_preflight import DefaultMethodologyExecutionPreflightService
from paa_core.services.methodology_execution_projection import DefaultMethodologyExecutionProjectionService
from paa_core.services.methodology_execution_state import DefaultMethodologyExecutionStateService
from paa_core.runtime.packets.reference_resolution import (
    DefaultPacketReferenceResolutionService,
    PacketReferenceResolutionRequest,
    PacketReferenceResolutionService,
)
from paa_core.services.qa_worker import QAWorkerService
from paa_core.services.queue_claim_runtime import (
    DefaultQueueClaimRuntimeService,
    QueueClaimRuntimeRequest,
    QueueClaimRuntimeResult,
    QueueClaimRuntimeService,
)
from paa_core.services.queue_packet_runtime_controller import (
    DefaultQueuePacketRuntimeController,
    QueuePacketRuntimeRequest,
    QueuePacketRuntimeController,
)
from paa_core.services.techlead_acceptance_decision import DefaultTechLeadAcceptanceDecisionService
from paa_core.services.techlead_assignment_decision import DefaultTechLeadAssignmentDecisionService
from paa_core.services.techlead_closeout_decision import DefaultTechLeadCloseoutDecisionService
from paa_core.services.techlead_delivery_review_decision import DefaultTechLeadDeliveryReviewDecisionService
from paa_core.services.techlead_lineage_decision import DefaultTechLeadLineageDecisionService
from paa_core.services.techlead_reset_recovery_decision import DefaultTechLeadResetRecoveryDecisionService
from paa_core.services.techlead_worker import (
    DefaultTechLeadWorkerService,
    TechLeadWorkerResult,
)
from paa_core.services.techlead_worker_review_routing import DefaultTechLeadWorkerReviewRoutingService
from paa_core.services.workflow_lifecycle import DefaultWorkflowLifecycleService, WorkflowLifecycleRequest

from paa_core.runtime.transport.packet_dispatch import dispatch_packet

JsonDict = dict[str, Any]


class _QueueClaimLifecycleAdapterProtocol(Protocol):
    def acknowledge_claim(self, claim_id: str) -> dict[str, object]:
        ...

    def requeue_claim(self, claim_id: str) -> dict[str, object]:
        ...


class _TechLeadAssignmentPublisherProtocol(Protocol):
    def publish_next_assignment(
        self,
        *,
        worker_result: TechLeadWorkerResult,
        source_packet_message_id: str | None,
        source_packet_path: str | None,
    ) -> dict[str, Any] | None:
        ...


class _WorkflowTransitionAdapterProtocol(Protocol):
    def apply_return_transition(
        self,
        *,
        packet_path: str | None,
        packet_message_id: str | None,
        packet_schema_type: str | None,
    ) -> dict[str, Any]:
        ...

    def record_assignment_emitted(
        self,
        *,
        source_packet_message_id: str | None,
        source_packet_schema_type: str | None,
        source_claim_id: str | None,
        emitted_assignment: dict[str, Any],
    ) -> dict[str, Any]:
        ...


class _NullStructuredLogger:
    def info(self, event: str, **fields: object) -> None:
        return None

    def warning(self, event: str, **fields: object) -> None:
        return None


class _JsonFilePacketArtifactReader:
    def read_packet_payload(self, packet_path: str) -> dict[str, object]:
        path = Path(packet_path).expanduser().resolve()
        payload: object = json.loads(path.read_text())
        if isinstance(payload, dict):
            inner_payload = payload.get('payload')
            if isinstance(inner_payload, dict):
                return cast(dict[str, object], inner_payload)
            return cast(dict[str, object], payload)
        return {'packet_payload': payload}

    def read_packet(self, packet_reference: object) -> dict[str, object]:
        if isinstance(packet_reference, str):
            return self.read_packet_payload(packet_reference)
        return {'packet_payload': packet_reference}


class _QueueTransportAdapter:
    def __init__(self, *, client: RabbitMQManagementClient) -> None:
        self._client = client

    def preview_queue(self, queue_name: str, *, limit: int = 1) -> JsonDict | None:
        _, messages = self._client.get_messages(queue_name, count=limit, ackmode='ack_requeue_true')
        if not messages:
            return None
        return self._normalize_broker_message(messages[0])

    def claim_next_packet(self, queue_name: str, *, claimant_name: str | None = None) -> JsonDict | None:
        del claimant_name
        _, messages = self._client.get_messages(queue_name, count=1, ackmode='ack_requeue_false')
        if not messages:
            return None
        return self._normalize_broker_message(messages[0])

    @staticmethod
    def _normalize_broker_message(message: dict[str, Any]) -> dict[str, Any] | None:
        payload = message.get('payload')
        parsed = json.loads(payload) if isinstance(payload, str) else payload
        if not isinstance(parsed, dict):
            return None
        return {
            'packet_message_id': parsed.get('message_id'),
            'packet_schema_type': parsed.get('schema_type'),
            'packet_reference': parsed.get('message_id'),
            'packet_payload': parsed.get('payload') if isinstance(parsed.get('payload'), dict) else None,
            'message_id': parsed.get('message_id'),
            'schema_type': parsed.get('schema_type'),
            'original_envelope': parsed,
        }


class _QueueClaimStateAdapter:
    def __init__(self, *, claim_ledger_repository: FileQueueClaimLedgerRepository, runtime_event_repository: PostgresRuntimeEventRepository) -> None:
        self._claim_ledger_repository = claim_ledger_repository
        self._runtime_event_repository = runtime_event_repository

    def record_claim(self, claim_record: object) -> dict[str, object]:
        if not isinstance(claim_record, dict):
            return {'claim_id': None}
        record = self._claim_ledger_repository.record_claim({
            'queue': claim_record.get('queue_name'),
            'claimed_at': utc_now(),
            'claimed_by': claim_record.get('claimant_name'),
            'status': 'claimed',
            'packet_message_id': claim_record.get('packet_message_id'),
            'packet_schema_type': claim_record.get('packet_schema_type'),
            'packet_reference': claim_record.get('packet_reference'),
        })
        packet_message_id = claim_record.get('packet_message_id')
        if isinstance(packet_message_id, str) and packet_message_id:
            self._runtime_event_repository.update_queue_message_status_by_external(
                message_id_external=packet_message_id,
                queue_status='claimed',
                handoff_status='claimed',
                timestamp_field='claimed_at',
            )
        return {'claim_id': record['claim_id']}


class _QueueClaimLifecycleAdapter:
    def __init__(
        self,
        *,
        claim_ledger_repository: FileQueueClaimLedgerRepository,
        runtime_event_repository: PostgresRuntimeEventRepository,
        client: RabbitMQManagementClient,
        exchange: str,
    ) -> None:
        self._claim_ledger_repository = claim_ledger_repository
        self._runtime_event_repository = runtime_event_repository
        self._client = client
        self._exchange = exchange

    def acknowledge_claim(self, claim_id: str) -> dict[str, object]:
        path, claim = self._claim_ledger_repository.load_claim(claim_id)
        claim['status'] = 'done'
        claim['acked_at'] = utc_now()
        self._claim_ledger_repository.update_claim(path, claim)
        message_id = (claim.get('original_envelope') or {}).get('message_id')
        if isinstance(message_id, str) and message_id:
            self._runtime_event_repository.update_queue_message_status_by_external(
                message_id_external=message_id,
                queue_status='acknowledged',
                handoff_status='completed',
                timestamp_field='acknowledged_at',
            )
        return {'ok': True, 'claim_id': claim_id, 'status': claim['status']}

    def requeue_claim(self, claim_id: str) -> dict[str, object]:
        path, claim = self._claim_ledger_repository.load_claim(claim_id)
        envelope = claim.get('original_envelope')
        if not isinstance(envelope, dict):
            return {'ok': False, 'claim_id': claim_id, 'status': 'invalid', 'reason': 'missing_original_envelope'}
        _, result = self._client.publish(self._exchange, claim['queue'], envelope)
        claim['status'] = 'requeued'
        claim['requeued_at'] = utc_now()
        claim['requeue_result'] = result if isinstance(result, dict) else {}
        self._claim_ledger_repository.update_claim(path, claim)
        message_id = envelope.get('message_id')
        if isinstance(message_id, str) and message_id:
            self._runtime_event_repository.update_queue_message_status_by_external(
                message_id_external=message_id,
                queue_status='requeued',
                handoff_status='requeued',
                timestamp_field='updated_at',
            )
        routed = result.get('routed') if isinstance(result, dict) else False
        return {'ok': bool(routed), 'claim_id': claim_id, 'status': claim['status']}


class _NullExecutionPackageResolutionService:
    @property
    def repository(self) -> PostgresExecutionPackageRepository:
        return self._repository

    @property
    def capability_policy(self) -> DefaultDeploymentCapabilityPolicy:
        return self._capability_policy

    @property
    def logger(self) -> StructuredLogger:
        return self._logger

    def __init__(self) -> None:
        self._repository = PostgresExecutionPackageRepository()
        self._capability_policy = DefaultDeploymentCapabilityPolicy()
        self._logger: StructuredLogger = _NullStructuredLogger()

    def resolve_execution_context(
        self,
        request: ExecutionPackageResolutionRequest,
    ) -> ExecutionPackageResolutionView:
        return ExecutionPackageResolutionView(
            execution_surface_key=request.execution_surface_key or 'techlead-runtime',
            execution_surface_type=request.execution_surface_type or 'consumer_repo_runtime',
            execution_package_install_id=None,
            package_name=None,
            repo_root_path=request.repo_root_path,
            runtime_root_path=request.runtime_root_path,
            package_version=None,
            authority_version_id=None,
            active_overlay_keys=(),
            manifest_path=None,
            package_metadata_path=None,
            docs_root_path=None,
            artifacts_root_path=None,
            capability_summary=ExecutionPackageCapabilitySummary(
                allowed=True,
                missing_capabilities=(),
                blocking_reasons=(),
                satisfied_capabilities=(),
                notes=('not-used-in-techlead-runtime-transition-proof',),
                metadata={},
            ),
            warnings=(),
            gaps=(),
            metadata={},
        )

    def resolve_execution_context_for_surface(
        self,
        execution_surface_key: str,
        request: ExecutionPackageResolutionRequest | None = None,
    ) -> ExecutionPackageResolutionView:
        merged_request = request or ExecutionPackageResolutionRequest()
        return self.resolve_execution_context(
            ExecutionPackageResolutionRequest(
                execution_surface_key=execution_surface_key,
                execution_surface_type=merged_request.execution_surface_type,
                repo_root_path=merged_request.repo_root_path,
                runtime_root_path=merged_request.runtime_root_path,
                work_item_id=merged_request.work_item_id,
                coder_run_brief_id=merged_request.coder_run_brief_id,
                consumer_context_key=merged_request.consumer_context_key,
                required_surface_types=merged_request.required_surface_types,
                required_artifact_refs=merged_request.required_artifact_refs,
                required_overlay_keys=merged_request.required_overlay_keys,
                metadata=dict(merged_request.metadata or {}) if merged_request.metadata else None,
            )
        )

    def resolve_execution_context_for_repo_root(
        self,
        repo_root_path: str,
        request: ExecutionPackageResolutionRequest | None = None,
    ) -> ExecutionPackageResolutionView:
        merged_request = request or ExecutionPackageResolutionRequest()
        return self.resolve_execution_context(
            ExecutionPackageResolutionRequest(
                execution_surface_key=merged_request.execution_surface_key,
                execution_surface_type=merged_request.execution_surface_type,
                repo_root_path=repo_root_path,
                runtime_root_path=merged_request.runtime_root_path,
                work_item_id=merged_request.work_item_id,
                coder_run_brief_id=merged_request.coder_run_brief_id,
                consumer_context_key=merged_request.consumer_context_key,
                required_surface_types=merged_request.required_surface_types,
                required_artifact_refs=merged_request.required_artifact_refs,
                required_overlay_keys=merged_request.required_overlay_keys,
                metadata=dict(merged_request.metadata or {}) if merged_request.metadata else None,
            )
        )

    def resolve_execution_context_for_runtime_root(
        self,
        runtime_root_path: str,
        request: ExecutionPackageResolutionRequest | None = None,
    ) -> ExecutionPackageResolutionView:
        merged_request = request or ExecutionPackageResolutionRequest()
        return self.resolve_execution_context(
            ExecutionPackageResolutionRequest(
                execution_surface_key=merged_request.execution_surface_key,
                execution_surface_type=merged_request.execution_surface_type,
                repo_root_path=merged_request.repo_root_path,
                runtime_root_path=runtime_root_path,
                work_item_id=merged_request.work_item_id,
                coder_run_brief_id=merged_request.coder_run_brief_id,
                consumer_context_key=merged_request.consumer_context_key,
                required_surface_types=merged_request.required_surface_types,
                required_artifact_refs=merged_request.required_artifact_refs,
                required_overlay_keys=merged_request.required_overlay_keys,
                metadata=dict(merged_request.metadata or {}) if merged_request.metadata else None,
            )
        )

    def detect_execution_package_gaps(
        self,
        request: ExecutionPackageResolutionRequest,
    ) -> tuple[ExecutionPackageGap, ...]:
        del request
        return ()


class _TechLeadWorkflowTransitionAdapter:
    def __init__(
        self,
        *,
        workflow_state_repository: PostgresWorkflowStateRepository,
        runtime_event_repository: PostgresRuntimeEventRepository,
        runtime_identity_repository: PostgresRuntimeIdentityRepository,
        logger: StructuredLogger | None = None,
    ) -> None:
        self._workflow_state_repository = workflow_state_repository
        self._runtime_event_repository = runtime_event_repository
        self._runtime_identity_repository = runtime_identity_repository
        self._logger = logger if logger is not None else _NullStructuredLogger()
        self._workflow_lifecycle_service = DefaultWorkflowLifecycleService(
            workflow_state_repository=workflow_state_repository,
            runtime_event_repository=runtime_event_repository,
            execution_package_resolution_service=_NullExecutionPackageResolutionService(),
            workflow_transition_policy=DefaultWorkflowTransitionPolicy(),
            acceptance_policy=DefaultAcceptancePolicy(),
            reset_recovery_policy=DefaultResetRecoveryPolicy(),
            logger=self._logger,
        )

    def record_assignment_emitted(
        self,
        *,
        source_packet_message_id: str | None,
        source_packet_schema_type: str | None,
        source_claim_id: str | None,
        emitted_assignment: dict[str, Any],
    ) -> dict[str, Any]:
        dispatch = emitted_assignment.get('dispatch') or {}
        message_file = emitted_assignment.get('message_file')
        if not isinstance(message_file, str) or not message_file:
            return {'ok': False, 'reason': 'missing_assignment_message_file'}
        packet = self._load_packet(message_file)
        project_slug = self._project_slug_from_packet(packet)
        work_item_id = self._runtime_event_repository.resolve_work_item_id_for_message(packet)
        project_id = self._runtime_identity_repository.resolve_project_id(project_slug)
        if not work_item_id or not project_id:
            return {'ok': False, 'reason': 'missing_work_item_or_project'}
        current_state = self._workflow_state_repository.get_workflow_state_for_work_item(work_item_id)
        if current_state is None:
            return {'ok': False, 'reason': 'missing_workflow_state'}
        target_role = str((packet.get('payload') or {}).get('target_role') or '')
        target_role_id = self._runtime_identity_repository.resolve_role_id(project_slug, target_role)
        techlead_role_id = self._runtime_identity_repository.resolve_role_id(project_slug, 'TechLead')
        emitted_queue_message = self._runtime_event_repository.get_queue_message_by_external(
            str(emitted_assignment.get('message_id') or '')
        )
        target_stage = 'worker_execution_in_progress' if target_role == 'Dev' else 'qa_execution_in_progress'
        self._workflow_state_repository.upsert_workflow_state(
            WorkflowStateUpsertSpec(
                project_id=current_state.project_id,
                work_item_id=current_state.work_item_id,
                workflow_stage=target_stage,
                lineage_state='awaiting_result',
                current_owner_role_id=target_role_id,
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
                active_handoff_id=emitted_queue_message.handoff_id if emitted_queue_message is not None else current_state.active_handoff_id,
                active_queue_message_id=emitted_queue_message.queue_message_id if emitted_queue_message is not None else current_state.active_queue_message_id,
                active_message_id_external=str(emitted_assignment.get('message_id') or current_state.active_message_id_external),
                active_assignment_role_id=target_role_id,
                active_result_role_id=techlead_role_id,
                active_queue_claim_id=None,
                metadata={
                    **dict(current_state.metadata or {}),
                    'last_assignment_message_id': emitted_assignment.get('message_id'),
                    'last_assignment_target_role': target_role,
                },
            )
        )
        self._workflow_state_repository.append_workflow_transition(
            WorkflowTransitionAppendSpec(
                workflow_state_id=current_state.workflow_state_id,
                project_id=current_state.project_id,
                work_item_id=current_state.work_item_id,
                transition_type='assignment_emitted',
                transition_status='applied',
                from_workflow_stage=current_state.workflow_stage,
                to_workflow_stage=target_stage,
                from_owner_role_id=current_state.current_owner_role_id,
                to_owner_role_id=target_role_id,
                source_queue_message_id=current_state.active_queue_message_id,
                source_queue_claim_id=None,
                source_message_id_external=source_packet_message_id,
                source_packet_schema_type=source_packet_schema_type,
                result_queue_message_id=emitted_queue_message.queue_message_id if emitted_queue_message is not None else None,
                result_message_id_external=str(emitted_assignment.get('message_id') or ''),
                result_packet_schema_type='techlead_assignment_packet',
                result_role_id=target_role_id,
                performed_by_role_id=techlead_role_id,
                metadata={'assignment_target_role': target_role},
            )
        )
        return {'ok': True, 'work_item_id': work_item_id, 'workflow_stage': target_stage}

    def apply_return_transition(
        self,
        *,
        packet_path: str | None,
        packet_message_id: str | None,
        packet_schema_type: str | None,
    ) -> dict[str, Any]:
        packet = self._load_packet(packet_path) if packet_path else None
        if packet is None:
            return {'ok': False, 'reason': 'missing_source_packet'}
        project_slug = self._project_slug_from_packet(packet)
        work_item_id = self._runtime_event_repository.resolve_work_item_id_for_message(packet)
        project_id = self._runtime_identity_repository.resolve_project_id(project_slug)
        if not work_item_id or not project_id:
            return {'ok': False, 'reason': 'missing_work_item_or_project'}
        transition_type = (
            'qa_result_returned' if packet_schema_type == 'qa_verification_packet' else 'worker_result_returned'
        )
        result = self._workflow_lifecycle_service.apply_workflow_transition(
            WorkflowLifecycleRequest(
                project_id=project_id,
                work_item_id=work_item_id,
                requested_transition_type=transition_type,
                source_message_id_external=packet_message_id,
                source_packet_schema_type=packet_schema_type,
            )
        )
        return {
            'ok': result.applied,
            'work_item_id': work_item_id,
            'workflow_stage': result.state_view.workflow_stage if result.state_view is not None else None,
            'blocking_reasons': result.decision_summary.blocking_reasons,
        }

    @staticmethod
    def _load_packet(packet_path: str) -> dict[str, Any]:
        path = Path(packet_path).expanduser().resolve()
        payload = json.loads(path.read_text())
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def _project_slug_from_packet(packet: dict[str, Any]) -> str:
        project = packet.get('project')
        if isinstance(project, str) and project:
            return project
        payload = packet.get('payload')
        if isinstance(payload, dict):
            project_slug = payload.get('project_slug')
            if isinstance(project_slug, str) and project_slug:
                return project_slug
        return 'paa-platform'


class _PassthroughPacketEnvelopeValidator:
    def validate_packet_envelope(self, packet: object) -> dict[str, bool]:
        return {'ok': packet is not None}


class _UnsupportedWorkerHost:
    def __init__(self, name: str) -> None:
        self._name = name

    def handle_packet(self, request: object) -> object:
        raise RuntimeError(f'{self._name} is not composed for this runtime slice.')

    def supports_packet_schema_type(self, packet_schema_type: str) -> bool:
        del packet_schema_type
        return False


class _TechLeadAssignmentPublisher:
    def __init__(self, *, repo_root: Path, project_slug: str, github_repo: str) -> None:
        self._repo_root = repo_root
        self._project_slug = project_slug
        self._github_repo = github_repo

    def publish_next_assignment(
        self,
        *,
        worker_result: TechLeadWorkerResult,
        source_packet_message_id: str | None,
        source_packet_path: str | None,
    ) -> dict[str, Any] | None:
        assignment_result = worker_result.assignment_decision_result
        routing_result = worker_result.worker_review_routing_result
        dispatch_summary = worker_result.dispatch_summary
        request = worker_result.request
        payload = request.packet_payload or {}
        source_packet = self._read_source_packet(source_packet_path)
        if not worker_result.ok:
            return None

        target_role = dispatch_summary.recommended_target_role
        assignment_type = None
        assignment_summary = None
        allowed_result_types: tuple[str, ...] = ()
        if assignment_result is not None:
            assignment_type = assignment_result.summary.assignment_type
            assignment_summary = assignment_result.summary.assignment_summary
            allowed_result_types = assignment_result.summary.allowed_result_types
        elif routing_result is not None and dispatch_summary.recommended_next_action == 'assign_qa' and target_role == 'QA':
            assignment_type = 'verify_authorized_slice'
            assignment_summary = routing_result.summary.review_summary
            allowed_result_types = tuple(routing_result.recommended_actions or ('pass', 'fail_fixable', 'needs_human_review'))
        if not target_role or not assignment_type or not assignment_summary:
            return None

        issue_number = payload.get('issue_number')
        if not isinstance(issue_number, int) or issue_number <= 0:
            issue = payload.get('issue')
            if isinstance(issue, dict):
                nested_issue_number = issue.get('number')
                if isinstance(nested_issue_number, int):
                    issue_number = nested_issue_number
        if not isinstance(issue_number, int) or issue_number <= 0:
            return {
                'ok': False,
                'reason': 'missing_issue_number',
                'details': 'TechLead assignment emission requires a positive issue_number in the source packet payload.',
            }

        pr_number = payload.get('pr_number')
        if not isinstance(pr_number, int):
            pr_number = None

        github_links = self._normalize_github_links(payload, source_packet)
        branch_name = self._resolve_branch_name(payload, source_packet)
        target_role_value = target_role.strip()
        target_role_key = target_role_value.lower()
        assignment_slug = assignment_type.replace('_', '-')
        packet = {
            'message_id': self._build_message_id(issue_number=issue_number, assignment_type=assignment_type),
            'schema_type': 'techlead_assignment_packet',
            'schema_version': '1.0.0',
            'project': self._project_slug,
            'from_role': 'techlead',
            'to_role': target_role_value,
            'created_at': self._utc_now(),
            'correlation_id': f'issue-{issue_number}',
            'github_context': {
                'repo': self._github_repo,
                'issue_number': issue_number,
                'pr_number': pr_number,
                'branch': branch_name,
                'links': github_links,
            },
            'payload': {
                'issue': {
                    'number': issue_number,
                    'url': payload.get('issue_url'),
                },
                'pr': {
                    'number': pr_number,
                    'url': payload.get('pr_url'),
                    'ready_for_review': True,
                },
                'target_role': target_role,
                'assignment_type': assignment_type,
                'source_context_ref': {
                    'source_packet_path': source_packet_path,
                    'source_packet_message_id': source_packet_message_id,
                    'package_id_external': self._nested_value(payload, 'coder_brief_resolution', 'package_id_external'),
                    'brief_id_external': self._nested_value(payload, 'coder_brief_resolution', 'brief_id_external'),
                },
                'canonical_branch': branch_name,
                'role_branch': None,
                'branch_owner_role': 'TechLead',
                'lineage_state': 'active',
                'lineage_action': 'created',
                'source_branch': branch_name,
                'superseded_branch': None,
                'worktree_hint': f'issue-{issue_number}-{target_role_key}',
                'reset_reason': None,
                'allowed_result_types': list(allowed_result_types),
                'assignment_summary': assignment_summary,
                'coder_run_brief_ref': payload.get('coder_run_brief_ref'),
                'coder_run_brief': payload.get('coder_run_brief'),
                'coder_brief_resolution': payload.get('coder_brief_resolution'),
                'methodology_execution_id': payload.get('methodology_execution_id'),
                'project_slug': payload.get('project_slug'),
                'issue_number': issue_number,
                'pr_number': pr_number,
                'workflow_stage': payload.get('workflow_stage'),
                'worker_result_type': payload.get('worker_result_type'),
                'next_assignment_type': assignment_type,
            },
            'authority_context': self._authority_context(source_packet),
        }

        output_path = self._assignment_output_path(
            issue_number=issue_number,
            target_role_slug=target_role_key,
            assignment_slug=assignment_slug,
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(packet, indent=2) + '\n')
        dispatch_result = dispatch_packet(self._repo_root, output_path)
        return {
            'ok': bool(dispatch_result.get('ok')),
            'message_id': packet['message_id'],
            'message_file': str(output_path),
            'resolved_queue': dispatch_result.get('resolved_queue'),
            'dispatch': dispatch_result,
        }

    def _assignment_output_path(self, *, issue_number: int, target_role_slug: str, assignment_slug: str) -> Path:
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        return (
            self._repo_root
            / '.codex-work'
            / 'techlead-runtime'
            / f'issue-{issue_number}-{target_role_slug}-{assignment_slug}-{stamp}.json'
        )

    def _authority_context(self, source_packet: dict[str, Any] | None) -> dict[str, Any]:
        source = source_packet.get('authority_context') if isinstance(source_packet, dict) else None
        if not isinstance(source, dict):
            source = {}
        return {
            'manifest_path': source.get('manifest_path') or str(self._repo_root / 'docs/2_Design/2026-05-17-paa-proof-slice-authority-manifest.json'),
            'authority_version': source.get('authority_version') or '2026-05-16.1',
            'milestone_id': source.get('milestone_id') or 'm0-paa-runtime-proof',
            'phase_id': source.get('phase_id') or 'p0-techlead-runtime-host',
            'task_id': source.get('task_id') or 'paa-techlead-runtime-host',
        }

    def _normalize_github_links(self, payload: dict[str, Any], source_packet: dict[str, Any] | None) -> list[str]:
        links = []
        issue_url = payload.get('issue_url')
        pr_url = payload.get('pr_url')
        if isinstance(issue_url, str) and issue_url:
            links.append(issue_url)
        if isinstance(pr_url, str) and pr_url:
            links.append(pr_url)
        if not links and isinstance(source_packet, dict):
            github_context = source_packet.get('github_context')
            if isinstance(github_context, dict):
                source_links = github_context.get('links')
                if isinstance(source_links, list):
                    links.extend(str(link) for link in source_links if isinstance(link, str) and link)
        return links

    def _resolve_branch_name(self, payload: dict[str, Any], source_packet: dict[str, Any] | None) -> str | None:
        branch = payload.get('branch')
        if isinstance(branch, dict):
            name = branch.get('name')
            if isinstance(name, str) and name:
                return name
        if isinstance(branch, str) and branch:
            return branch
        if isinstance(source_packet, dict):
            github_context = source_packet.get('github_context')
            if isinstance(github_context, dict):
                branch_name = github_context.get('branch')
                if isinstance(branch_name, str) and branch_name:
                    return branch_name
        return None

    @staticmethod
    def _read_source_packet(source_packet_path: str | None) -> dict[str, Any] | None:
        if not source_packet_path:
            return None
        path = Path(source_packet_path).expanduser().resolve()
        if not path.exists():
            return None
        payload = json.loads(path.read_text())
        return payload if isinstance(payload, dict) else None

    @staticmethod
    def _nested_value(payload: dict[str, Any], container_key: str, field_key: str) -> str | None:
        container = payload.get(container_key)
        if not isinstance(container, dict):
            return None
        value = container.get(field_key)
        return value if isinstance(value, str) and value else None

    @staticmethod
    def _build_message_id(*, issue_number: int, assignment_type: str) -> str:
        slug = assignment_type.replace('_', '-')
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        run_suffix = uuid.uuid4().hex[:8]
        return f'paa-techlead-{stamp}-issue{issue_number}-{slug}-{run_suffix}'

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


@dataclass(frozen=True)
class TechLeadRuntimeLoopResult:
    queue_name: str
    intake_mode: str
    ok: bool
    skipped: bool
    packet_message_id: str | None = None
    claim_id: str | None = None
    packet_reference: str | None = None
    packet_path: str | None = None
    target_worker_host: str | None = None
    emitted_assignment: dict[str, Any] | None = None
    reason: str | None = None
    details: str | None = None
    metadata: dict[str, Any] | None = None


class TechLeadRuntimeHost:
    def __init__(
        self,
        *,
        queue_name: str,
        queue_claim_runtime_service: QueueClaimRuntimeService,
        queue_claim_lifecycle_adapter: _QueueClaimLifecycleAdapterProtocol | None,
        packet_reference_resolution_service: PacketReferenceResolutionService,
        queue_packet_runtime_controller: QueuePacketRuntimeController,
        assignment_publisher: _TechLeadAssignmentPublisherProtocol | None,
        workflow_transition_adapter: _WorkflowTransitionAdapterProtocol | None,
        actor_name: str,
        host_name: str,
        logger: StructuredLogger | None = None,
    ) -> None:
        self._queue_name = queue_name
        self._queue_claim_runtime_service = queue_claim_runtime_service
        self._queue_claim_lifecycle_adapter = queue_claim_lifecycle_adapter
        self._packet_reference_resolution_service = packet_reference_resolution_service
        self._queue_packet_runtime_controller = queue_packet_runtime_controller
        self._assignment_publisher = assignment_publisher
        self._workflow_transition_adapter = workflow_transition_adapter
        self._actor_name = actor_name
        self._host_name = host_name
        self._logger = logger if logger is not None else _NullStructuredLogger()

    def run_once(self, *, intake_mode: str = 'preview', emit_next_assignment: bool = False) -> TechLeadRuntimeLoopResult:
        claim_result = self._claim_with_retry(intake_mode=intake_mode)
        if not claim_result.ok:
            return TechLeadRuntimeLoopResult(
                queue_name=self._queue_name,
                intake_mode=intake_mode,
                ok=False,
                skipped=claim_result.reason == 'missing_queue_packet',
                packet_message_id=(claim_result.preview_summary.packet_message_id if claim_result.preview_summary else None),
                claim_id=(claim_result.claim_summary.claim_id if claim_result.claim_summary else None),
                reason=claim_result.reason,
                details=claim_result.details,
                metadata=claim_result.metadata,
            )

        packet_message_id = self._resolved_packet_message_id(claim_result)
        packet_reference = self._resolved_packet_reference(claim_result)
        packet_schema_type = self._resolved_packet_schema_type(claim_result) or 'worker_result_packet'
        resolution_result = self._packet_reference_resolution_service.resolve_packet_reference(
            PacketReferenceResolutionRequest(
                packet_message_id=packet_message_id,
                packet_reference=packet_reference,
                queue_name=self._queue_name,
                packet_schema_type=packet_schema_type,
                actor_name=self._actor_name,
                host_name=self._host_name,
                metadata={'claim_id': claim_result.claim_summary.claim_id if claim_result.claim_summary else None},
            )
        )
        if not resolution_result.ok:
            lifecycle_result = self._finalize_claim(
                intake_mode=intake_mode,
                claim_id=(claim_result.claim_summary.claim_id if claim_result.claim_summary else None),
                success=False,
            )
            return TechLeadRuntimeLoopResult(
                queue_name=self._queue_name,
                intake_mode=intake_mode,
                ok=False,
                skipped=False,
                packet_message_id=resolution_result.resolution_summary.packet_message_id,
                claim_id=(claim_result.claim_summary.claim_id if claim_result.claim_summary else None),
                packet_reference=resolution_result.resolution_summary.packet_reference,
                packet_path=resolution_result.resolution_summary.resolved_packet_path,
                reason=resolution_result.reason,
                details=resolution_result.details,
                metadata={
                    'resolution': resolution_result.metadata,
                    'claim_lifecycle': lifecycle_result,
                },
            )

        runtime_result = self._queue_packet_runtime_controller.handle_packet(
            QueuePacketRuntimeRequest(
                queue_name=self._queue_name,
                packet_schema_type=resolution_result.resolution_summary.packet_schema_type or 'worker_result_packet',
                packet_message_id=resolution_result.resolution_summary.packet_message_id,
                packet_path=resolution_result.resolution_summary.resolved_packet_path,
                packet_payload=resolution_result.normalized_packet_payload,
                runtime_mode='dry_run',
                actor_name=self._actor_name,
                host_name=self._host_name,
                metadata={
                    'claim_id': claim_result.claim_summary.claim_id if claim_result.claim_summary else None,
                    'intake_mode': intake_mode,
                },
            )
        )
        workflow_transition_result = None
        if (
            runtime_result.ok
            and self._workflow_transition_adapter is not None
            and packet_schema_type in ('worker_result_packet', 'qa_verification_packet')
        ):
            workflow_transition_result = self._workflow_transition_adapter.apply_return_transition(
                packet_path=resolution_result.resolution_summary.resolved_packet_path,
                packet_message_id=resolution_result.resolution_summary.packet_message_id,
                packet_schema_type=packet_schema_type,
            )
        emitted_assignment = None
        if (
            emit_next_assignment
            and intake_mode == 'claim_next'
            and runtime_result.ok
            and (workflow_transition_result is None or bool(workflow_transition_result.get('ok')))
        ):
            selected_worker_result = runtime_result.selected_worker_result
            if (
                isinstance(selected_worker_result, TechLeadWorkerResult)
                and self._assignment_publisher is not None
            ):
                emitted_assignment = self._assignment_publisher.publish_next_assignment(
                    worker_result=selected_worker_result,
                    source_packet_message_id=resolution_result.resolution_summary.packet_message_id,
                    source_packet_path=resolution_result.resolution_summary.resolved_packet_path,
                )
        assignment_transition_result = None
        if (
            emitted_assignment is not None
            and bool(emitted_assignment.get('ok'))
            and self._workflow_transition_adapter is not None
        ):
            assignment_transition_result = self._workflow_transition_adapter.record_assignment_emitted(
                source_packet_message_id=resolution_result.resolution_summary.packet_message_id,
                source_packet_schema_type=packet_schema_type,
                source_claim_id=(claim_result.claim_summary.claim_id if claim_result.claim_summary else None),
                emitted_assignment=emitted_assignment,
            )
        workflow_success = workflow_transition_result is None or bool(workflow_transition_result.get('ok'))
        assignment_transition_success = assignment_transition_result is None or bool(assignment_transition_result.get('ok'))
        emitted_assignment_success = emitted_assignment is None or bool(emitted_assignment.get('ok'))
        lifecycle_success = runtime_result.ok and workflow_success and emitted_assignment_success and assignment_transition_success
        final_ok = runtime_result.ok and workflow_success and assignment_transition_success
        final_reason = runtime_result.reason
        final_details = runtime_result.details
        if not workflow_success:
            assert workflow_transition_result is not None
            final_reason = str(workflow_transition_result.get('reason') or 'workflow_transition_failed')
            final_details = ', '.join(str(item) for item in workflow_transition_result.get('blocking_reasons') or ()) or runtime_result.details
        elif not assignment_transition_success:
            assert assignment_transition_result is not None
            final_reason = str(assignment_transition_result.get('reason') or 'assignment_transition_failed')
            final_details = ', '.join(str(item) for item in assignment_transition_result.get('blocking_reasons') or ()) or runtime_result.details
        lifecycle_result = self._finalize_claim(
            intake_mode=intake_mode,
            claim_id=(claim_result.claim_summary.claim_id if claim_result.claim_summary else None),
            success=lifecycle_success,
        )
        return TechLeadRuntimeLoopResult(
            queue_name=self._queue_name,
            intake_mode=intake_mode,
            ok=final_ok,
            skipped=False,
            packet_message_id=runtime_result.request.packet_message_id,
            claim_id=(claim_result.claim_summary.claim_id if claim_result.claim_summary else None),
            packet_reference=resolution_result.resolution_summary.packet_reference,
            packet_path=resolution_result.resolution_summary.resolved_packet_path,
            target_worker_host=runtime_result.dispatch_summary.target_worker_host,
            emitted_assignment=emitted_assignment,
            reason=final_reason,
            details=final_details,
            metadata={
                'claim': claim_result.metadata,
                'resolution': resolution_result.metadata,
                'dispatch': runtime_result.metadata,
                'workflow_transition': workflow_transition_result,
                'assignment_transition': assignment_transition_result,
                'claim_lifecycle': lifecycle_result,
            },
        )

    def _finalize_claim(
        self,
        *,
        intake_mode: str,
        claim_id: str | None,
        success: bool,
    ) -> dict[str, object] | None:
        if intake_mode != 'claim_next' or not claim_id or self._queue_claim_lifecycle_adapter is None:
            return None
        if success:
            return self._queue_claim_lifecycle_adapter.acknowledge_claim(claim_id)
        return self._queue_claim_lifecycle_adapter.requeue_claim(claim_id)

    def _claim_with_retry(self, *, intake_mode: str) -> QueueClaimRuntimeResult:
        attempts = 3 if intake_mode == 'claim_next' else 1
        retry_delay_seconds = 0.75
        last_result = None
        for attempt in range(1, attempts + 1):
            last_result = self._queue_claim_runtime_service.assemble_queue_intake(
                QueueClaimRuntimeRequest(
                    queue_name=self._queue_name,
                    intake_mode=intake_mode,
                    packet_schema_type=None,
                    claimant_name=self._actor_name,
                    host_name=self._host_name,
                    metadata={
                        'host_name': self._host_name,
                        'claim_attempt': attempt,
                        'max_claim_attempts': attempts,
                    },
                )
            )
            if getattr(last_result, 'ok', False):
                return last_result
            if getattr(last_result, 'reason', None) != 'missing_queue_packet' or attempt >= attempts:
                return last_result
            time.sleep(retry_delay_seconds)
        return cast(QueueClaimRuntimeResult, last_result)

    @staticmethod
    def _resolved_packet_message_id(claim_result: QueueClaimRuntimeResult) -> str | None:
        envelope = getattr(claim_result, 'normalized_packet_envelope', None) or {}
        if isinstance(envelope, dict):
            value = envelope.get('packet_message_id')
            if isinstance(value, str) and value:
                return value
        claim_summary = getattr(claim_result, 'claim_summary', None)
        if claim_summary is not None:
            value = getattr(claim_summary, 'packet_message_id', None)
            if isinstance(value, str) and value:
                return value
        preview_summary = getattr(claim_result, 'preview_summary', None)
        if preview_summary is not None:
            value = getattr(preview_summary, 'packet_message_id', None)
            if isinstance(value, str) and value:
                return value
        return None

    @staticmethod
    def _resolved_packet_reference(claim_result: QueueClaimRuntimeResult) -> str | None:
        envelope = getattr(claim_result, 'normalized_packet_envelope', None) or {}
        if isinstance(envelope, dict):
            value = envelope.get('packet_reference')
            if isinstance(value, str) and value:
                return value
        claim_summary = getattr(claim_result, 'claim_summary', None)
        if claim_summary is not None:
            value = getattr(claim_summary, 'packet_reference', None)
            if isinstance(value, str) and value:
                return value
        preview_summary = getattr(claim_result, 'preview_summary', None)
        if preview_summary is not None:
            value = getattr(preview_summary, 'packet_reference', None)
            if isinstance(value, str) and value:
                return value
        return None

    @staticmethod
    def _resolved_packet_schema_type(claim_result: QueueClaimRuntimeResult) -> str | None:
        envelope = getattr(claim_result, 'normalized_packet_envelope', None) or {}
        if isinstance(envelope, dict):
            value = envelope.get('packet_schema_type')
            if isinstance(value, str) and value:
                return value
        claim_summary = getattr(claim_result, 'claim_summary', None)
        if claim_summary is not None:
            value = getattr(claim_summary, 'packet_schema_type', None)
            if isinstance(value, str) and value:
                return value
        preview_summary = getattr(claim_result, 'preview_summary', None)
        if preview_summary is not None:
            value = getattr(preview_summary, 'packet_schema_type', None)
            if isinstance(value, str) and value:
                return value
        return None

    def run_loop(
        self,
        *,
        intake_mode: str = 'preview',
        emit_next_assignment: bool = False,
        max_iterations: int = 1,
        poll_interval_seconds: float = 5.0,
    ) -> dict[str, Any]:
        iterations: list[dict[str, Any]] = []
        last_preview_message_id: str | None = None
        count = 0
        while True:
            if max_iterations > 0 and count >= max_iterations:
                break
            result = self.run_once(intake_mode=intake_mode, emit_next_assignment=emit_next_assignment)
            result_payload = {
                'queue_name': result.queue_name,
                'intake_mode': result.intake_mode,
                'ok': result.ok,
                'skipped': result.skipped,
                'packet_message_id': result.packet_message_id,
                'claim_id': result.claim_id,
                'packet_reference': result.packet_reference,
                'packet_path': result.packet_path,
                'target_worker_host': result.target_worker_host,
                'emitted_assignment': result.emitted_assignment,
                'reason': result.reason,
                'details': result.details,
                'metadata': result.metadata,
            }
            if intake_mode == 'preview' and result.packet_message_id and result.packet_message_id == last_preview_message_id:
                result_payload['skipped'] = True
                result_payload['reason'] = 'duplicate_preview_head'
                result_payload['details'] = 'Preview loop saw the same head packet again and did not redispatch it.'
            else:
                last_preview_message_id = result.packet_message_id or last_preview_message_id
            iterations.append(result_payload)
            count += 1
            if max_iterations > 0 and count >= max_iterations:
                break
            if intake_mode == 'preview' and result_payload['reason'] == 'duplicate_preview_head':
                time.sleep(poll_interval_seconds)
                continue
            time.sleep(poll_interval_seconds)
        return {
            'host_name': self._host_name,
            'actor_name': self._actor_name,
            'queue_name': self._queue_name,
            'intake_mode': intake_mode,
            'iterations': iterations,
            'iteration_count': len(iterations),
        }


def build_techlead_runtime_host(
    repo_root: Path,
    *,
    actor_name: str = 'TechLead Agent',
    host_name: str = 'techlead-runtime-host',
    logger: StructuredLogger | None = None,
) -> TechLeadRuntimeHost:
    resolved_repo_root = repo_root.expanduser().resolve()
    runtime_logger = logger if logger is not None else _NullStructuredLogger()
    topology = resolved_repo_runtime_queue_topology(resolved_repo_root)
    project_config = load_unified_runtime_project_config(repo_project_config_path(resolved_repo_root))
    methodology_execution_repository = PostgresMethodologyExecutionRepository()
    runtime_event_repository = PostgresRuntimeEventRepository()
    runtime_identity_repository = PostgresRuntimeIdentityRepository()
    workflow_state_repository = PostgresWorkflowStateRepository()
    methodology_execution_state_service = DefaultMethodologyExecutionStateService(
        methodology_execution_repository=methodology_execution_repository,
        logger=runtime_logger,
    )
    methodology_execution_projection_service = DefaultMethodologyExecutionProjectionService(
        methodology_execution_repository=methodology_execution_repository,
        logger=runtime_logger,
    )
    methodology_execution_preflight_service = DefaultMethodologyExecutionPreflightService(
        methodology_execution_repository=methodology_execution_repository,
        methodology_execution_state_service=methodology_execution_state_service,
        methodology_execution_projection_service=methodology_execution_projection_service,
        logger=runtime_logger,
    )
    techlead_worker_service = DefaultTechLeadWorkerService(
        methodology_execution_repository=methodology_execution_repository,
        methodology_execution_state_service=methodology_execution_state_service,
        methodology_execution_projection_service=methodology_execution_projection_service,
        methodology_execution_preflight_service=methodology_execution_preflight_service,
        techlead_assignment_decision_service=DefaultTechLeadAssignmentDecisionService(logger=runtime_logger),
        techlead_worker_review_routing_service=DefaultTechLeadWorkerReviewRoutingService(logger=runtime_logger),
        techlead_acceptance_decision_service=DefaultTechLeadAcceptanceDecisionService(logger=runtime_logger),
        techlead_delivery_review_decision_service=DefaultTechLeadDeliveryReviewDecisionService(logger=runtime_logger),
        techlead_reset_recovery_decision_service=DefaultTechLeadResetRecoveryDecisionService(logger=runtime_logger),
        techlead_lineage_decision_service=DefaultTechLeadLineageDecisionService(logger=runtime_logger),
        techlead_closeout_decision_service=DefaultTechLeadCloseoutDecisionService(logger=runtime_logger),
        logger=runtime_logger,
    )
    packet_reader = _JsonFilePacketArtifactReader()
    queue_packet_runtime_controller = DefaultQueuePacketRuntimeController(
        techlead_worker_service=techlead_worker_service,
        dev_worker_service=cast(DevWorkerService, _UnsupportedWorkerHost('DevWorkerService')),
        qa_worker_service=cast(QAWorkerService, _UnsupportedWorkerHost('QAWorkerService')),
        queue_packet_reader=packet_reader,
        queue_packet_delivery_adapter=None,
        logger=runtime_logger,
    )
    packet_reference_resolution_service = DefaultPacketReferenceResolutionService(
        runtime_event_repository=runtime_event_repository,
        packet_artifact_reader=packet_reader,
        runtime_path_adapter=None,
        logger=runtime_logger,
    )
    client = build_default_management_client()
    claim_ledger_repository = FileQueueClaimLedgerRepository()
    queue_claim_runtime_service = DefaultQueueClaimRuntimeService(
        queue_transport_adapter=_QueueTransportAdapter(client=client),
        packet_envelope_validator=_PassthroughPacketEnvelopeValidator(),
        queue_claim_state_adapter=_QueueClaimStateAdapter(
            claim_ledger_repository=claim_ledger_repository,
            runtime_event_repository=runtime_event_repository,
        ),
        supported_queue_names=tuple(topology.queue_names.values()),
        logger=runtime_logger,
    )
    return TechLeadRuntimeHost(
        queue_name=topology.queue_names['techlead'],
        queue_claim_runtime_service=queue_claim_runtime_service,
        queue_claim_lifecycle_adapter=_QueueClaimLifecycleAdapter(
            claim_ledger_repository=claim_ledger_repository,
            runtime_event_repository=runtime_event_repository,
            client=client,
            exchange=DEFAULT_RUNTIME_QUEUE_EXCHANGE,
        ),
        packet_reference_resolution_service=packet_reference_resolution_service,
        queue_packet_runtime_controller=queue_packet_runtime_controller,
        assignment_publisher=_TechLeadAssignmentPublisher(
            repo_root=resolved_repo_root,
            project_slug=project_config.project_id,
            github_repo=project_config.github_repo,
        ),
        workflow_transition_adapter=_TechLeadWorkflowTransitionAdapter(
            workflow_state_repository=workflow_state_repository,
            runtime_event_repository=runtime_event_repository,
            runtime_identity_repository=runtime_identity_repository,
            logger=runtime_logger,
        ),
        actor_name=actor_name,
        host_name=host_name,
        logger=runtime_logger,
    )


__all__ = [
    'TechLeadRuntimeHost',
    'TechLeadRuntimeLoopResult',
    'build_techlead_runtime_host',
]

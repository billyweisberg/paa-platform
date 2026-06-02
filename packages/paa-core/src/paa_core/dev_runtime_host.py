"""Dev runtime host bootstrap and loop for the PAA consumer runtime."""

from __future__ import annotations

from dataclasses import dataclass
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol, cast

from paa_core.claim_ledger import FileQueueClaimLedgerRepository, utc_now
from paa_core.config import load_unified_runtime_project_config
from paa_core.policies.deployment_capability import DeploymentCapabilityPolicy, DefaultDeploymentCapabilityPolicy
from paa_core.queue_transport import DEFAULT_EXCHANGE, RabbitMQManagementClient, build_default_management_client
from paa_core.repositories.execution_package import ExecutionPackageRepository, PostgresExecutionPackageRepository
from paa_core.repositories.methodology_execution import PostgresMethodologyExecutionRepository
from paa_core.repositories.runtime_event import PostgresRuntimeEventRepository
from paa_core.runtime_paths import repo_project_config_path, resolved_repo_runtime_queue_topology
from paa_core.services.dev_worker import DefaultDevWorkerService, DevWorkerRequest, DevWorkerResult, DevWorkerService
from paa_core.services.execution_package_resolution import (
    DefaultExecutionPackageResolutionService,
    ExecutionPackageGap,
    ExecutionPackageResolutionRequest,
    ExecutionPackageResolutionService,
    ExecutionPackageResolutionView,
)
from paa_core.services.implementation_plan_derivation.contracts import StructuredLogger
from paa_core.services.methodology_execution_projection import DefaultMethodologyExecutionProjectionService
from paa_core.services.methodology_execution_state import DefaultMethodologyExecutionStateService
from paa_core.services.packet_context_assembly import DefaultPacketContextAssemblyService, PacketContextAssemblyService
from paa_core.services.packet_reference_resolution import (
    DefaultPacketReferenceResolutionService,
    PacketReferenceResolutionRequest,
    PacketReferenceResolutionResult,
    PacketReferenceResolutionService,
)
from paa_core.services.queue_claim_runtime import (
    DefaultQueueClaimRuntimeService,
    QueueClaimRuntimeRequest,
    QueueClaimRuntimeResult,
    QueueClaimRuntimeService,
)

from paa_core.runtime_packet_dispatch import dispatch_packet

JsonDict = dict[str, Any]


class _QueueClaimLifecycleAdapterProtocol(Protocol):
    def acknowledge_claim(self, claim_id: str) -> dict[str, object]:
        ...

    def requeue_claim(self, claim_id: str) -> dict[str, object]:
        ...


class _WorkerResultPublisherProtocol(Protocol):
    def publish_worker_result(
        self,
        *,
        worker_result: DevWorkerResult,
        source_packet_message_id: str | None,
        source_packet_path: str | None,
    ) -> dict[str, Any] | None:
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
    def _normalize_broker_message(message: dict[str, Any]) -> JsonDict | None:
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
        envelope = claim.get('original_envelope')
        message_id = envelope.get('message_id') if isinstance(envelope, dict) else None
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


class _PassthroughPacketEnvelopeValidator:
    def validate_packet_envelope(self, packet: object) -> dict[str, bool]:
        return {'ok': packet is not None}


class _DefaultDevExecutionRunner:
    def run_dev_execution(self, context: object) -> JsonDict:
        packet_payload = getattr(context, 'packet_payload', None)
        if not isinstance(packet_payload, dict):
            packet_payload = {}
        issue_number = packet_payload.get('issue_number')
        return cast(JsonDict, {
            'worker_result_type': 'implemented_ready_for_qa',
            'execution_scope': {
                'issue_number': issue_number,
                'scope': 'implement_authorized_slice',
            },
            'changed_files': (
                'packages/paa-core/src/paa_core/services/dev_worker/default.py',
            ),
            'validation_summary': {
                'checks': (
                    {'name': 'dev-runtime-host-dry-run', 'status': 'pass'},
                )
            },
            'implementation_summary': {
                'summary': 'Authorized slice implemented in dry-run runtime proof.'
            },
            'workflow_compliance': {
                'status': 'pass',
                'notes': ('runtime-proof',),
            },
            'merge_status': {
                'ready': False,
                'reason': 'Runtime proof only',
            },
            'techlead_action_recommended': {
                'action': 'assign_qa',
                'reason': 'Implementation completed and ready for QA.',
            },
        })


class _DefaultWorkerResultPacketAssembler:
    def assemble_worker_result_packet(self, execution_result: object) -> object:
        return execution_result


class _RepoExecutionPackageResolutionAdapter:
    def __init__(self, *, service: DefaultExecutionPackageResolutionService, repo_root: str) -> None:
        self._service = service
        self._repo_root = repo_root

    @property
    def repository(self) -> ExecutionPackageRepository:
        return self._service.repository

    @property
    def capability_policy(self) -> DeploymentCapabilityPolicy:
        return self._service.capability_policy

    @property
    def logger(self) -> StructuredLogger:
        return self._service.logger

    def resolve_execution_context(
        self,
        request: ExecutionPackageResolutionRequest,
    ) -> ExecutionPackageResolutionView:
        merged_request = request
        if request.repo_root_path is None:
            merged_request = ExecutionPackageResolutionRequest(
                execution_surface_key=request.execution_surface_key,
                execution_surface_type=request.execution_surface_type,
                repo_root_path=self._repo_root,
                runtime_root_path=request.runtime_root_path,
                work_item_id=request.work_item_id,
                coder_run_brief_id=request.coder_run_brief_id,
                consumer_context_key=request.consumer_context_key,
                required_surface_types=request.required_surface_types,
                required_artifact_refs=request.required_artifact_refs,
                required_overlay_keys=request.required_overlay_keys,
                metadata=dict(request.metadata or {}) if request.metadata else None,
            )
        return self._service.resolve_execution_context(merged_request)

    def resolve_execution_context_for_surface(
        self,
        execution_surface_key: str,
        request: ExecutionPackageResolutionRequest | None = None,
    ) -> ExecutionPackageResolutionView:
        del execution_surface_key
        merged_request: ExecutionPackageResolutionRequest | None = None
        if request is not None:
            merged_request = ExecutionPackageResolutionRequest(
                execution_surface_key=None,
                execution_surface_type=request.execution_surface_type,
                repo_root_path=self._repo_root,
                runtime_root_path=request.runtime_root_path,
                work_item_id=request.work_item_id,
                coder_run_brief_id=request.coder_run_brief_id,
                consumer_context_key=request.consumer_context_key,
                required_surface_types=request.required_surface_types,
                required_artifact_refs=request.required_artifact_refs,
                required_overlay_keys=request.required_overlay_keys,
                metadata=dict(request.metadata or {}) if request.metadata else None,
            )
        return self._service.resolve_execution_context_for_repo_root(self._repo_root, merged_request)

    def resolve_execution_context_for_repo_root(
        self,
        repo_root_path: str,
        request: ExecutionPackageResolutionRequest | None = None,
    ) -> ExecutionPackageResolutionView:
        return self._service.resolve_execution_context_for_repo_root(repo_root_path, request)

    def resolve_execution_context_for_runtime_root(
        self,
        runtime_root_path: str,
        request: ExecutionPackageResolutionRequest | None = None,
    ) -> ExecutionPackageResolutionView:
        return self._service.resolve_execution_context_for_runtime_root(runtime_root_path, request)

    def detect_execution_package_gaps(
        self,
        request: ExecutionPackageResolutionRequest,
    ) -> tuple[ExecutionPackageGap, ...]:
        return self._service.detect_execution_package_gaps(request)


class _WorkerResultPublisher:
    def __init__(self, *, repo_root: Path, project_slug: str, github_repo: str) -> None:
        self._repo_root = repo_root
        self._project_slug = project_slug
        self._github_repo = github_repo

    def publish_worker_result(
        self,
        *,
        worker_result: DevWorkerResult,
        source_packet_message_id: str | None,
        source_packet_path: str | None,
    ) -> dict[str, Any] | None:
        if not getattr(worker_result, 'ok', False):
            return None

        request = worker_result.request
        payload = request.packet_payload or {}
        execution_result = worker_result.execution_result if isinstance(worker_result.execution_result, dict) else {}
        source_packet = self._read_source_packet(source_packet_path)

        issue_number = payload.get('issue_number')
        if not isinstance(issue_number, int) or issue_number <= 0:
            return {
                'ok': False,
                'reason': 'missing_issue_number',
                'details': 'Dev worker-result emission requires a positive issue_number in the source assignment payload.',
            }
        pr_number = payload.get('pr_number')
        if not isinstance(pr_number, int):
            pr_number = None

        packet = {
            'message_id': self._build_message_id(issue_number=issue_number, worker_result_type=str(execution_result.get('worker_result_type') or 'implemented_ready_for_qa')),
            'schema_type': 'worker_result_packet',
            'schema_version': '1.0.0',
            'project': self._project_slug,
            'from_role': 'Dev',
            'to_role': 'TechLead',
            'created_at': self._utc_now(),
            'correlation_id': f'issue-{issue_number}',
            'github_context': {
                'repo': self._github_repo,
                'issue_number': issue_number,
                'pr_number': pr_number,
                'branch': self._resolve_branch_name(payload, source_packet),
                'links': self._normalize_github_links(payload, source_packet),
            },
            'payload': {
                'issue': {'number': issue_number, 'url': payload.get('issue', {}).get('url') if isinstance(payload.get('issue'), dict) else None},
                'branch': {'name': self._resolve_branch_name(payload, source_packet)},
                'pr': {'number': pr_number, 'url': payload.get('pr', {}).get('url') if isinstance(payload.get('pr'), dict) else None, 'ready_for_review': False},
                'worker_role': 'Dev',
                'worker_family': 'implementation',
                'result_type': execution_result.get('worker_result_type', 'implemented_ready_for_qa'),
                'workflow_compliance': execution_result.get('workflow_compliance', {'status': 'pass'}),
                'implementation_summary': execution_result.get('implementation_summary', {}),
                'validation_summary': execution_result.get('validation_summary', {}),
                'artifacts': {'changed_files': list(execution_result.get('changed_files', ()))},
                'merge_status': execution_result.get('merge_status', {'ready': False, 'reason': 'Runtime proof only'}),
                'techlead_action_recommended': execution_result.get('techlead_action_recommended', {'action': 'assign_qa'}),
                'source_assignment_ref': {
                    'message_id': source_packet_message_id,
                    'assignment_type': payload.get('assignment_type'),
                    'target_role': payload.get('target_role'),
                    'path': source_packet_path,
                },
                'coder_run_brief_ref': payload.get('coder_run_brief_ref'),
                'coder_run_brief': payload.get('coder_run_brief'),
                'coder_brief_resolution': payload.get('coder_brief_resolution'),
                'methodology_execution_id': payload.get('methodology_execution_id'),
                'project_slug': payload.get('project_slug'),
                'issue_number': issue_number,
                'pr_number': pr_number,
                'workflow_stage': 'techlead_worker_review_pending',
                'worker_result_type': execution_result.get('worker_result_type', 'implemented_ready_for_qa'),
            },
            'authority_context': self._authority_context(source_packet),
        }
        output_path = self._worker_result_output_path(issue_number=issue_number)
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

    def _worker_result_output_path(self, *, issue_number: int) -> Path:
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        return self._repo_root / '.codex-work' / 'dev-runtime' / f'issue-{issue_number}-worker-result-{stamp}.json'

    def _authority_context(self, source_packet: dict[str, Any] | None) -> dict[str, Any]:
        source = source_packet.get('authority_context') if isinstance(source_packet, dict) else None
        if not isinstance(source, dict):
            source = {}
        return {
            'manifest_path': source.get('manifest_path') or str(self._repo_root / 'docs/2_Design/2026-05-17-paa-proof-slice-authority-manifest.json'),
            'authority_version': source.get('authority_version') or '2026-05-16.1',
            'milestone_id': source.get('milestone_id') or 'm0-paa-runtime-proof',
            'phase_id': source.get('phase_id') or 'p0-dev-runtime-host',
            'task_id': source.get('task_id') or 'paa-dev-runtime-host',
        }

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
    def _normalize_github_links(payload: dict[str, Any], source_packet: dict[str, Any] | None) -> list[str]:
        links = []
        issue = payload.get('issue')
        pr = payload.get('pr')
        if isinstance(issue, dict):
            issue_url = issue.get('url')
            if isinstance(issue_url, str) and issue_url:
                links.append(issue_url)
        if isinstance(pr, dict):
            pr_url = pr.get('url')
            if isinstance(pr_url, str) and pr_url:
                links.append(pr_url)
        if not links and isinstance(source_packet, dict):
            github_context = source_packet.get('github_context')
            if isinstance(github_context, dict):
                source_links = github_context.get('links')
                if isinstance(source_links, list):
                    links.extend(str(link) for link in source_links if isinstance(link, str) and link)
        return links

    @staticmethod
    def _resolve_branch_name(payload: dict[str, Any], source_packet: dict[str, Any] | None) -> str | None:
        branch = payload.get('canonical_branch') or payload.get('source_branch')
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
    def _build_message_id(*, issue_number: int, worker_result_type: str) -> str:
        slug = worker_result_type.replace('_', '-')
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        run_suffix = uuid.uuid4().hex[:8]
        return f'paa-dev-{stamp}-issue{issue_number}-{slug}-{run_suffix}'

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


@dataclass(frozen=True)
class DevRuntimeLoopResult:
    queue_name: str
    intake_mode: str
    ok: bool
    skipped: bool
    packet_message_id: str | None = None
    claim_id: str | None = None
    packet_reference: str | None = None
    packet_path: str | None = None
    emitted_worker_result: dict[str, Any] | None = None
    reason: str | None = None
    details: str | None = None
    metadata: dict[str, Any] | None = None


class DevRuntimeHost:
    def __init__(
        self,
        *,
        queue_name: str,
        queue_claim_runtime_service: QueueClaimRuntimeService,
        queue_claim_lifecycle_adapter: _QueueClaimLifecycleAdapterProtocol | None,
        packet_reference_resolution_service: PacketReferenceResolutionService,
        dev_worker_service: DevWorkerService,
        worker_result_publisher: _WorkerResultPublisherProtocol | None,
        actor_name: str,
        host_name: str,
        logger: StructuredLogger | None = None,
    ) -> None:
        self._queue_name = queue_name
        self._queue_claim_runtime_service = queue_claim_runtime_service
        self._queue_claim_lifecycle_adapter = queue_claim_lifecycle_adapter
        self._packet_reference_resolution_service = packet_reference_resolution_service
        self._dev_worker_service = dev_worker_service
        self._worker_result_publisher = worker_result_publisher
        self._actor_name = actor_name
        self._host_name = host_name
        self._logger = logger if logger is not None else _NullStructuredLogger()

    def run_once(self, *, intake_mode: str = 'preview', emit_worker_result: bool = False) -> DevRuntimeLoopResult:
        claim_result = self._claim_with_retry(intake_mode=intake_mode)
        if not claim_result.ok:
            return DevRuntimeLoopResult(
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
        packet_schema_type = self._resolved_packet_schema_type(claim_result) or 'techlead_assignment_packet'
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
            return DevRuntimeLoopResult(
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

        payload = resolution_result.normalized_packet_payload or claim_result.normalized_packet_payload or {}
        dev_result = self._dev_worker_service.handle_packet(
            DevWorkerRequest(
                packet_schema_type=resolution_result.resolution_summary.packet_schema_type or 'techlead_assignment_packet',
                packet_message_id=resolution_result.resolution_summary.packet_message_id,
                packet_path=resolution_result.resolution_summary.resolved_packet_path,
                packet_payload=payload,
                methodology_execution_id=payload.get('methodology_execution_id') if isinstance(payload, dict) else None,
                runtime_mode='dry_run',
                actor_name=self._actor_name,
                host_name=self._host_name,
                metadata={
                    'claim_id': claim_result.claim_summary.claim_id if claim_result.claim_summary else None,
                    'intake_mode': intake_mode,
                },
            )
        )
        emitted_worker_result = None
        if emit_worker_result and intake_mode == 'claim_next' and self._worker_result_publisher is not None:
            emitted_worker_result = self._worker_result_publisher.publish_worker_result(
                worker_result=dev_result,
                source_packet_message_id=resolution_result.resolution_summary.packet_message_id,
                source_packet_path=resolution_result.resolution_summary.resolved_packet_path,
            )
        lifecycle_success = dev_result.ok and (emitted_worker_result is None or bool(emitted_worker_result.get('ok')))
        lifecycle_result = self._finalize_claim(
            intake_mode=intake_mode,
            claim_id=(claim_result.claim_summary.claim_id if claim_result.claim_summary else None),
            success=lifecycle_success,
        )
        return DevRuntimeLoopResult(
            queue_name=self._queue_name,
            intake_mode=intake_mode,
            ok=dev_result.ok,
            skipped=False,
            packet_message_id=resolution_result.resolution_summary.packet_message_id,
            claim_id=(claim_result.claim_summary.claim_id if claim_result.claim_summary else None),
            packet_reference=resolution_result.resolution_summary.packet_reference,
            packet_path=resolution_result.resolution_summary.resolved_packet_path,
            emitted_worker_result=emitted_worker_result,
            reason=dev_result.reason,
            details=dev_result.details,
            metadata={
                'claim': claim_result.metadata,
                'resolution': resolution_result.metadata,
                'execution': dev_result.metadata,
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
                    packet_schema_type='techlead_assignment_packet',
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
        emit_worker_result: bool = False,
        max_iterations: int = 1,
        poll_interval_seconds: float = 5.0,
    ) -> dict[str, Any]:
        iterations: list[dict[str, Any]] = []
        last_preview_message_id: str | None = None
        count = 0
        while True:
            if max_iterations > 0 and count >= max_iterations:
                break
            result = self.run_once(intake_mode=intake_mode, emit_worker_result=emit_worker_result)
            result_payload = {
                'queue_name': result.queue_name,
                'intake_mode': result.intake_mode,
                'ok': result.ok,
                'skipped': result.skipped,
                'packet_message_id': result.packet_message_id,
                'claim_id': result.claim_id,
                'packet_reference': result.packet_reference,
                'packet_path': result.packet_path,
                'emitted_worker_result': result.emitted_worker_result,
                'reason': result.reason,
                'details': result.details,
                'metadata': result.metadata,
            }
            if intake_mode == 'preview' and result.packet_message_id and result.packet_message_id == last_preview_message_id:
                result_payload['skipped'] = True
                result_payload['reason'] = 'duplicate_preview_head'
                result_payload['details'] = 'Preview loop saw the same head packet again and did not re-execute it.'
            else:
                last_preview_message_id = result.packet_message_id or last_preview_message_id
            iterations.append(result_payload)
            count += 1
            if max_iterations > 0 and count >= max_iterations:
                break
            time.sleep(poll_interval_seconds)
        return {
            'host_name': self._host_name,
            'actor_name': self._actor_name,
            'queue_name': self._queue_name,
            'intake_mode': intake_mode,
            'iterations': iterations,
            'iteration_count': len(iterations),
        }


def build_dev_runtime_host(
    repo_root: Path,
    *,
    actor_name: str = 'Dev Agent',
    host_name: str = 'dev-runtime-host',
    logger: StructuredLogger | None = None,
) -> DevRuntimeHost:
    resolved_repo_root = repo_root.expanduser().resolve()
    runtime_logger = logger if logger is not None else _NullStructuredLogger()
    topology = resolved_repo_runtime_queue_topology(resolved_repo_root)
    project_config = load_unified_runtime_project_config(repo_project_config_path(resolved_repo_root))
    methodology_execution_repository = PostgresMethodologyExecutionRepository()
    runtime_event_repository = PostgresRuntimeEventRepository()
    execution_package_repository = PostgresExecutionPackageRepository()
    methodology_execution_state_service = DefaultMethodologyExecutionStateService(
        methodology_execution_repository=methodology_execution_repository,
        logger=runtime_logger,
    )
    methodology_execution_projection_service = DefaultMethodologyExecutionProjectionService(
        methodology_execution_repository=methodology_execution_repository,
        logger=runtime_logger,
    )
    execution_package_resolution_service = DefaultExecutionPackageResolutionService(
        repository=execution_package_repository,
        capability_policy=DefaultDeploymentCapabilityPolicy(),
        logger=runtime_logger,
    )
    packet_reader = _JsonFilePacketArtifactReader()
    packet_context_assembly_service = DefaultPacketContextAssemblyService(
        methodology_execution_repository=methodology_execution_repository,
        methodology_execution_projection_service=methodology_execution_projection_service,
        execution_package_resolution_service=_RepoExecutionPackageResolutionAdapter(
            service=execution_package_resolution_service,
            repo_root=str(resolved_repo_root),
        ),
        packet_payload_reader=packet_reader,
        logger=runtime_logger,
    )
    dev_worker_service = DefaultDevWorkerService(
        packet_context_assembly_service=packet_context_assembly_service,
        methodology_execution_state_service=methodology_execution_state_service,
        methodology_execution_projection_service=methodology_execution_projection_service,
        execution_runner=_DefaultDevExecutionRunner(),
        worker_result_packet_assembler=_DefaultWorkerResultPacketAssembler(),
        logger=runtime_logger,
    )
    queue_client = build_default_management_client()
    claim_ledger_repository = FileQueueClaimLedgerRepository()
    queue_claim_runtime_service = DefaultQueueClaimRuntimeService(
        queue_transport_adapter=_QueueTransportAdapter(client=queue_client),
        packet_envelope_validator=_PassthroughPacketEnvelopeValidator(),
        queue_claim_state_adapter=_QueueClaimStateAdapter(
            claim_ledger_repository=claim_ledger_repository,
            runtime_event_repository=runtime_event_repository,
        ),
        supported_queue_names=tuple(name for name in topology.queue_names.values() if name),
        logger=runtime_logger,
    )
    packet_reference_resolution_service = DefaultPacketReferenceResolutionService(
        runtime_event_repository=runtime_event_repository,
        packet_artifact_reader=packet_reader,
        logger=runtime_logger,
    )
    github_repo = project_config.github_repo or f'billyweisberg/{resolved_repo_root.name}'
    return DevRuntimeHost(
        queue_name=topology.queue_names['dev'],
        queue_claim_runtime_service=queue_claim_runtime_service,
        queue_claim_lifecycle_adapter=_QueueClaimLifecycleAdapter(
            claim_ledger_repository=claim_ledger_repository,
            runtime_event_repository=runtime_event_repository,
            client=queue_client,
            exchange=DEFAULT_EXCHANGE,
        ),
        packet_reference_resolution_service=packet_reference_resolution_service,
        dev_worker_service=dev_worker_service,
        worker_result_publisher=_WorkerResultPublisher(
            repo_root=resolved_repo_root,
            project_slug=project_config.project_id,
            github_repo=github_repo,
        ),
        actor_name=actor_name,
        host_name=host_name,
        logger=runtime_logger,
    )


__all__ = ['DevRuntimeHost', 'DevRuntimeLoopResult', 'build_dev_runtime_host']

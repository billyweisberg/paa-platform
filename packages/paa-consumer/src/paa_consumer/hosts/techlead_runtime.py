"""TechLead runtime host bootstrap and loop for the PAA consumer runtime."""

from __future__ import annotations

from dataclasses import dataclass
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from paa_core import handoff_runtime
from paa_core.config import DEFAULT_RUNTIME_QUEUE_EXCHANGE, load_producer_consumer_project_config
from paa_core.repositories.methodology_execution import PostgresMethodologyExecutionRepository
from paa_core.repositories.runtime_event import PostgresRuntimeEventRepository
from paa_core.runtime_paths import repo_project_config_path, resolved_repo_runtime_queue_topology
from paa_core.services.methodology_execution_preflight import DefaultMethodologyExecutionPreflightService
from paa_core.services.methodology_execution_projection import DefaultMethodologyExecutionProjectionService
from paa_core.services.methodology_execution_state import DefaultMethodologyExecutionStateService
from paa_core.services.packet_reference_resolution import (
    DefaultPacketReferenceResolutionService,
    PacketReferenceResolutionRequest,
)
from paa_core.services.queue_claim_runtime import DefaultQueueClaimRuntimeService, QueueClaimRuntimeRequest
from paa_core.services.queue_packet_runtime_controller import (
    DefaultQueuePacketRuntimeController,
    QueuePacketRuntimeRequest,
)
from paa_core.services.techlead_acceptance_decision import DefaultTechLeadAcceptanceDecisionService
from paa_core.services.techlead_assignment_decision import DefaultTechLeadAssignmentDecisionService
from paa_core.services.techlead_closeout_decision import DefaultTechLeadCloseoutDecisionService
from paa_core.services.techlead_delivery_review_decision import DefaultTechLeadDeliveryReviewDecisionService
from paa_core.services.techlead_lineage_decision import DefaultTechLeadLineageDecisionService
from paa_core.services.techlead_reset_recovery_decision import DefaultTechLeadResetRecoveryDecisionService
from paa_core.services.techlead_worker import DefaultTechLeadWorkerService
from paa_core.services.techlead_worker_review_routing import DefaultTechLeadWorkerReviewRoutingService

from paa_consumer.inbox import dispatch_packet


class _NullStructuredLogger:
    def info(self, event: str, **fields: object) -> None:
        return None

    def warning(self, event: str, **fields: object) -> None:
        return None


class _JsonFilePacketArtifactReader:
    def read_packet_payload(self, packet_path: str) -> dict[str, object]:
        path = Path(packet_path).expanduser().resolve()
        payload = json.loads(path.read_text())
        if isinstance(payload, dict):
            inner_payload = payload.get('payload')
            if isinstance(inner_payload, dict):
                return inner_payload
            return payload
        return {'packet_payload': payload}


class _QueueTransportAdapter:
    def __init__(self, *, client: handoff_runtime.RabbitMQManagementClient) -> None:
        self._client = client

    def preview_queue(self, queue_name: str, *, limit: int = 1) -> object:
        _, messages = self._client.get_messages(queue_name, count=limit, ackmode='ack_requeue_true')
        if not messages:
            return None
        return self._normalize_broker_message(messages[0])

    def claim_next_packet(self, queue_name: str, *, claimant_name: str | None = None) -> object:
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
            'message_id': parsed.get('message_id'),
            'schema_type': parsed.get('schema_type'),
            'original_envelope': parsed,
        }


class _QueueClaimStateAdapter:
    def __init__(self) -> None:
        self._root, self._source, _ = handoff_runtime.ensure_state_dirs()

    def record_claim(self, claim_record: object) -> object:
        if not isinstance(claim_record, dict):
            return {'claim_id': None}
        claim_id = str(uuid.uuid4())
        record = {
            'claim_id': claim_id,
            'queue': claim_record.get('queue_name'),
            'claimed_at': handoff_runtime.utc_now(),
            'claimed_by': claim_record.get('claimant_name'),
            'status': 'claimed',
            'state_dir': str(self._root),
            'state_dir_source': self._source,
            'packet_message_id': claim_record.get('packet_message_id'),
            'packet_schema_type': claim_record.get('packet_schema_type'),
            'packet_reference': claim_record.get('packet_reference'),
        }
        handoff_runtime.save_json(handoff_runtime.claim_path(claim_id, self._root), record)
        handoff_runtime.update_queue_message_status(
            claim_record.get('packet_message_id'),
            'claimed',
            'claimed',
            'claimed_at',
        )
        return {'claim_id': claim_id}


class _PassthroughPacketEnvelopeValidator:
    def validate_packet_envelope(self, packet: object) -> object:
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
        routing_result = worker_result.worker_review_routing_result
        dispatch_summary = worker_result.dispatch_summary
        request = worker_result.request
        payload = request.packet_payload or {}
        source_packet = self._read_source_packet(source_packet_path)
        if (
            routing_result is None
            or not worker_result.ok
            or dispatch_summary.recommended_next_action != 'assign_qa'
            or dispatch_summary.recommended_target_role != 'QA'
        ):
            return None

        issue_number = payload.get('issue_number')
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
        packet = {
            'message_id': self._build_message_id(issue_number=issue_number, assignment_type='verify_authorized_slice'),
            'schema_type': 'techlead_assignment_packet',
            'schema_version': '1.0.0',
            'project': self._project_slug,
            'from_role': 'techlead',
            'to_role': 'qa',
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
                'target_role': 'QA',
                'assignment_type': 'verify_authorized_slice',
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
                'worktree_hint': f'issue-{issue_number}-qa',
                'reset_reason': None,
                'allowed_result_types': list(routing_result.recommended_actions or ('pass', 'fail_fixable', 'needs_human_review')),
                'assignment_summary': routing_result.summary.review_summary,
                'coder_run_brief_ref': payload.get('coder_run_brief_ref'),
                'coder_run_brief': payload.get('coder_run_brief'),
                'coder_brief_resolution': payload.get('coder_brief_resolution'),
                'methodology_execution_id': payload.get('methodology_execution_id'),
                'project_slug': payload.get('project_slug'),
                'issue_number': issue_number,
                'pr_number': pr_number,
                'workflow_stage': payload.get('workflow_stage'),
                'worker_result_type': payload.get('worker_result_type'),
            },
            'authority_context': self._authority_context(source_packet),
        }

        output_path = self._assignment_output_path(issue_number=issue_number)
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

    def _assignment_output_path(self, *, issue_number: int) -> Path:
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        return self._repo_root / '.codex-work' / 'techlead-runtime' / f'issue-{issue_number}-qa-assignment-{stamp}.json'

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
        queue_claim_runtime_service: object,
        packet_reference_resolution_service: object,
        queue_packet_runtime_controller: object,
        assignment_publisher: object | None,
        actor_name: str,
        host_name: str,
        logger: object | None = None,
    ) -> None:
        self._queue_name = queue_name
        self._queue_claim_runtime_service = queue_claim_runtime_service
        self._packet_reference_resolution_service = packet_reference_resolution_service
        self._queue_packet_runtime_controller = queue_packet_runtime_controller
        self._assignment_publisher = assignment_publisher
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

        envelope = claim_result.normalized_packet_envelope or {}
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
                metadata=resolution_result.metadata,
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
        emitted_assignment = None
        if emit_next_assignment and intake_mode == 'claim_next':
            selected_worker_result = runtime_result.selected_worker_result
            if selected_worker_result is not None and self._assignment_publisher is not None:
                emitted_assignment = self._assignment_publisher.publish_next_assignment(
                    worker_result=selected_worker_result,
                    source_packet_message_id=resolution_result.resolution_summary.packet_message_id,
                    source_packet_path=resolution_result.resolution_summary.resolved_packet_path,
                )
        return TechLeadRuntimeLoopResult(
            queue_name=self._queue_name,
            intake_mode=intake_mode,
            ok=runtime_result.ok,
            skipped=False,
            packet_message_id=runtime_result.request.packet_message_id,
            claim_id=(claim_result.claim_summary.claim_id if claim_result.claim_summary else None),
            packet_reference=resolution_result.resolution_summary.packet_reference,
            packet_path=resolution_result.resolution_summary.resolved_packet_path,
            target_worker_host=runtime_result.dispatch_summary.target_worker_host,
            emitted_assignment=emitted_assignment,
            reason=runtime_result.reason,
            details=runtime_result.details,
            metadata={
                'claim': claim_result.metadata,
                'resolution': resolution_result.metadata,
                'dispatch': runtime_result.metadata,
            },
        )

    def _claim_with_retry(self, *, intake_mode: str) -> object:
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
        return last_result

    @staticmethod
    def _resolved_packet_message_id(claim_result: object) -> str | None:
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
    def _resolved_packet_reference(claim_result: object) -> str | None:
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
    def _resolved_packet_schema_type(claim_result: object) -> str | None:
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
    logger: object | None = None,
) -> TechLeadRuntimeHost:
    resolved_repo_root = repo_root.expanduser().resolve()
    runtime_logger = logger if logger is not None else _NullStructuredLogger()
    topology = resolved_repo_runtime_queue_topology(resolved_repo_root)
    project_config = load_producer_consumer_project_config(repo_project_config_path(resolved_repo_root))
    methodology_execution_repository = PostgresMethodologyExecutionRepository()
    runtime_event_repository = PostgresRuntimeEventRepository()
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
        dev_worker_service=_UnsupportedWorkerHost('DevWorkerService'),
        qa_worker_service=_UnsupportedWorkerHost('QAWorkerService'),
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
    client = handoff_runtime.RabbitMQManagementClient(
        user=handoff_runtime.DEFAULT_USER,
        password=handoff_runtime.DEFAULT_PASSWORD,
        host=handoff_runtime.DEFAULT_HOST,
        port=handoff_runtime.DEFAULT_MANAGEMENT_PORT,
        vhost=handoff_runtime.DEFAULT_VHOST,
    )
    queue_claim_runtime_service = DefaultQueueClaimRuntimeService(
        queue_transport_adapter=_QueueTransportAdapter(client=client),
        packet_envelope_validator=_PassthroughPacketEnvelopeValidator(),
        queue_claim_state_adapter=_QueueClaimStateAdapter(),
        supported_queue_names=tuple(topology.queue_names.values()),
        logger=runtime_logger,
    )
    return TechLeadRuntimeHost(
        queue_name=topology.queue_names['techlead'],
        queue_claim_runtime_service=queue_claim_runtime_service,
        packet_reference_resolution_service=packet_reference_resolution_service,
        queue_packet_runtime_controller=queue_packet_runtime_controller,
        assignment_publisher=_TechLeadAssignmentPublisher(
            repo_root=resolved_repo_root,
            project_slug=project_config.project_id,
            github_repo=project_config.github_repo,
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

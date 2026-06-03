"""Typed queue admin and packet transport service for the unified PAA runtime."""

from __future__ import annotations

import json
import uuid
from copy import deepcopy
from pathlib import Path
from typing import Any

from paa_core.runtime.transport.claim_ledger import FileQueueClaimLedgerRepository, load_json, utc_now
from paa_core.runtime.support.config import (
    DEFAULT_RUNTIME_QUEUE_EXCHANGE,
    runtime_queue_name_for_role,
    runtime_queue_name_for_schema,
)
from paa_core.runtime.transport.packet_envelope import normalize_role_name, validate_envelope
from paa_core.runtime.transport.rabbitmq import RabbitMQManagementClient, build_default_management_client
from paa_core.repositories.runtime_event import PostgresRuntimeEventRepository, RuntimeEventRepository
from paa_core.runtime.support.runtime_evidence import persist_qa_verification, persist_slice_result
from paa_core.runtime.support.runtime_paths import repo_queue_state_root, resolved_repo_runtime_queue_topology
from paa_core.team_worker_roles import team_worker_queue_name_by_display_name

JsonDict = dict[str, Any]


class DefaultRuntimeQueueAdminService:
    """Owns queue admin, claim lifecycle, and packet transport for the `paa` CLI."""

    def __init__(
        self,
        *,
        management_client: RabbitMQManagementClient | None = None,
        runtime_event_repository: RuntimeEventRepository | None = None,
    ) -> None:
        self._management_client = management_client
        self._runtime_event_repository = runtime_event_repository or PostgresRuntimeEventRepository()

    def state_info(self, *, repo_root: Path) -> dict[str, object]:
        root = repo_queue_state_root(repo_root)
        claim_repo = self._claim_repo(root)
        return {
            'active_state_dir': str(root),
            'active_state_source': 'repo-runtime',
            'claim_dir': str(claim_repo.root / 'claims'),
            'candidates': ({'path': str(root), 'source': 'repo-runtime', 'writable': True},),
        }

    def ensure_topology(self, *, repo_root: Path) -> dict[str, object]:
        client = self._client()
        status, overview = client.overview()
        exchange = self._resolved_runtime_exchange(repo_root)
        queues = self._resolved_runtime_queues(repo_root)
        client.declare_exchange(exchange)
        for queue in queues:
            client.declare_queue(queue)
            client.bind_queue(exchange, queue, queue)
        state_info = self.state_info(repo_root=repo_root)
        return {
            'ok': True,
            'management_status': status,
            'rabbitmq_version': overview.get('rabbitmq_version') if isinstance(overview, dict) else None,
            'exchange': exchange,
            'queues': queues,
            'state_dir': state_info['active_state_dir'],
            'state_dir_source': state_info['active_state_source'],
            'state_dir_candidates': state_info['candidates'],
        }

    def check(self, *, repo_root: Path, queue: str, preview: int = 0) -> dict[str, object]:
        client = self._client()
        _, queue_data = client.queue(queue)
        preview_rows: list[dict[str, object]] = []
        preview_probe_ran = preview > 0
        if preview > 0:
            _, messages = client.get_messages(queue, count=preview, ackmode='ack_requeue_true')
            for msg in messages or []:
                payload = msg.get('payload') if isinstance(msg, dict) else None
                try:
                    parsed = json.loads(payload) if isinstance(payload, str) else payload
                except Exception:
                    parsed = {'raw_payload': payload}
                preview_rows.append({
                    'message_count': msg.get('message_count') if isinstance(msg, dict) else None,
                    'redelivered': msg.get('redelivered') if isinstance(msg, dict) else None,
                    'payload_preview': {
                        'message_id': parsed.get('message_id') if isinstance(parsed, dict) else None,
                        'schema_type': parsed.get('schema_type') if isinstance(parsed, dict) else None,
                        'created_at': parsed.get('created_at') if isinstance(parsed, dict) else None,
                        'correlation_id': parsed.get('correlation_id') if isinstance(parsed, dict) else None,
                        'from_role': parsed.get('from_role') if isinstance(parsed, dict) else None,
                        'to_role': parsed.get('to_role') if isinstance(parsed, dict) else None,
                        'github_context': parsed.get('github_context') if isinstance(parsed, dict) else None,
                        'payload': parsed.get('payload') if isinstance(parsed, dict) else None,
                    },
                })
        messages_ready, reconciliation = self._reconcile_ready_count(
            queue_data.get('messages_ready') if isinstance(queue_data, dict) else None,
            preview_rows,
            preview_probe_ran,
        )
        state_info = self.state_info(repo_root=repo_root)
        result: dict[str, object] = {
            'queue': queue,
            'messages_ready': messages_ready,
            'messages_ready_raw': queue_data.get('messages_ready') if isinstance(queue_data, dict) else None,
            'messages_unacknowledged': queue_data.get('messages_unacknowledged') if isinstance(queue_data, dict) else None,
            'consumers': queue_data.get('consumers') if isinstance(queue_data, dict) else None,
            'active_state_dir': state_info['active_state_dir'],
            'active_state_source': state_info['active_state_source'],
            'preview': preview_rows,
        }
        if reconciliation is not None:
            result['reconciliation'] = reconciliation
        return result

    def purge(self, *, repo_root: Path, queue: str | None = None) -> dict[str, object]:
        client = self._client()
        queues = [queue] if queue else self._resolved_runtime_queues(repo_root)
        purged: list[str] = []
        for queue_name in queues:
            client.purge_queue(queue_name)
            purged.append(queue_name)
        return {'ok': True, 'purged_queues': purged, 'queue_count': len(purged)}

    def validate(self, *, message_file: Path) -> dict[str, object]:
        message = load_json(message_file)
        errors = validate_envelope(message, require_authority=True)
        if errors:
            return {'ok': False, 'errors': errors}
        return {'ok': True, 'schema_type': message['schema_type'], 'message_id': message['message_id']}

    def send(self, *, repo_root: Path, queue: str, message_file: Path) -> dict[str, object]:
        message = load_json(message_file)
        validated = self.validate(message_file=message_file)
        if not validated.get('ok'):
            return validated
        exchange = self._resolved_runtime_exchange(repo_root)
        packet_compilation_run = self._runtime_event_repository.create_packet_compilation_run_for_message(
            message=message,
            message_file=str(message_file),
            agent_name=self._packet_compiler_agent_name_for_message(message),
        )
        _, publish_result = self._client().publish(exchange, queue, message)
        routed = publish_result.get('routed') if isinstance(publish_result, dict) else False
        if routed and isinstance(publish_result, dict):
            self._runtime_event_repository.record_queue_send_for_message(
                message=message,
                queue_name=queue,
                exchange=exchange,
                publish_result=publish_result,
                packet_compilation_run=packet_compilation_run,
            )
            persist_slice_result(message)
            persist_qa_verification(message)
        return {
            'ok': bool(routed),
            'queue': queue,
            'message_id': message['message_id'],
            'schema_type': message['schema_type'],
        }

    def claim_next(self, *, repo_root: Path, queue: str, claimed_by: str = 'paa') -> tuple[dict[str, object], int]:
        root = repo_queue_state_root(repo_root)
        claim_repo = self._claim_repo(root)
        _, messages = self._client().get_messages(queue, count=1, ackmode='ack_requeue_false')
        if not messages:
            return ({'ok': True, 'queue': queue, 'claimed': False}, 0)
        msg = messages[0]
        payload = msg.get('payload') if isinstance(msg, dict) else None
        parsed = json.loads(payload) if isinstance(payload, str) else payload
        if not isinstance(parsed, dict):
            parsed = {}
            errors = ['queue message payload must decode to an object envelope']
        else:
            errors = validate_envelope(parsed, require_authority=False)
        if errors:
            record = claim_repo.record_claim({
                'queue': queue,
                'claimed_at': utc_now(),
                'claimed_by': claimed_by,
                'status': 'invalid',
                'validation_errors': errors,
                'original_envelope': parsed,
            })
            return ({
                'ok': False,
                'claimed': True,
                'claim_id': record['claim_id'],
                'errors': errors,
                'state_dir': str(root),
            }, 1)
        record = claim_repo.record_claim({
            'queue': queue,
            'claimed_at': utc_now(),
            'claimed_by': claimed_by,
            'status': 'claimed',
            'original_envelope': parsed,
        })
        message_id = parsed.get('message_id')
        if message_id:
            self._runtime_event_repository.update_queue_message_status_by_external(
                message_id_external=str(message_id),
                queue_status='claimed',
                handoff_status='claimed',
                timestamp_field='claimed_at',
            )
        return ({
            'ok': True,
            'claimed': True,
            'claim_id': record['claim_id'],
            'queue': queue,
            'message_id': parsed.get('message_id'),
            'schema_type': parsed.get('schema_type'),
            'correlation_id': parsed.get('correlation_id'),
            'state_dir': str(root),
            'state_dir_source': 'repo-runtime',
        }, 0)

    def list_claims(self, *, repo_root: Path, queue: str | None = None, status: str | None = None) -> dict[str, object]:
        claim_repo = self._claim_repo(repo_queue_state_root(repo_root))
        claims = claim_repo.list_claims(queue=queue, status=status)
        summary = []
        for claim in claims:
            env = claim.get('original_envelope', {})
            summary.append({
                'claim_id': claim.get('claim_id'),
                'queue': claim.get('queue'),
                'status': claim.get('status'),
                'claimed_at': claim.get('claimed_at'),
                'claimed_by': claim.get('claimed_by'),
                'state_dir': claim.get('state_dir'),
                'message_id': env.get('message_id') if isinstance(env, dict) else None,
                'schema_type': env.get('schema_type') if isinstance(env, dict) else None,
                'correlation_id': env.get('correlation_id') if isinstance(env, dict) else None,
            })
        return {'claims': summary}

    def ack(self, *, repo_root: Path, claim_id: str) -> dict[str, object]:
        claim_repo = self._claim_repo(repo_queue_state_root(repo_root))
        path, claim = claim_repo.load_claim(claim_id)
        claim['status'] = 'done'
        claim['acked_at'] = utc_now()
        claim_repo.update_claim(path, claim)
        message = claim.get('original_envelope') or {}
        message_id = message.get('message_id') if isinstance(message, dict) else None
        if message_id:
            self._runtime_event_repository.update_queue_message_status_by_external(
                message_id_external=str(message_id),
                queue_status='acknowledged',
                handoff_status='completed',
                timestamp_field='acknowledged_at',
            )
        return {'ok': True, 'claim_id': claim_id, 'status': claim['status'], 'state_dir': claim.get('state_dir')}

    def requeue(self, *, repo_root: Path, claim_id: str) -> tuple[dict[str, object], int]:
        claim_repo = self._claim_repo(repo_queue_state_root(repo_root))
        path, claim = claim_repo.load_claim(claim_id)
        env = claim.get('original_envelope')
        queue = str(claim.get('queue') or '')
        exchange = self._resolved_runtime_exchange(repo_root)
        if not isinstance(env, dict):
            return ({
                'ok': False,
                'claim_id': claim_id,
                'status': 'invalid',
                'queue': claim.get('queue'),
                'state_dir': claim.get('state_dir'),
                'reason': 'missing_original_envelope',
            }, 1)
        _, result = self._client().publish(exchange, queue, env)
        claim['status'] = 'requeued'
        claim['requeued_at'] = utc_now()
        claim['requeue_result'] = deepcopy(result)
        claim_repo.update_claim(path, claim)
        message_id = env.get('message_id') if isinstance(env, dict) else None
        if message_id:
            self._runtime_event_repository.update_queue_message_status_by_external(
                message_id_external=str(message_id),
                queue_status='requeued',
                handoff_status='requeued',
                timestamp_field='updated_at',
            )
        payload = {
            'ok': bool(result.get('routed')) if isinstance(result, dict) else False,
            'claim_id': claim_id,
            'status': claim['status'],
            'queue': claim.get('queue'),
            'state_dir': claim.get('state_dir'),
        }
        return payload, 0 if payload['ok'] else 1

    def validate_packet(self, *, repo_root: Path, message_file: Path) -> tuple[dict[str, object], int]:
        message = load_json(message_file)
        errors = validate_envelope(message, require_authority=True)
        if errors:
            return ({
                'ok': False,
                'message_file': str(message_file),
                'resolved_queue': None,
                'errors': errors,
            }, 1)
        resolved_queue = self.resolve_packet_queue(message=message, repo_root=repo_root)
        return ({
            'ok': True,
            'message_file': str(message_file),
            'message_id': message.get('message_id'),
            'schema_type': message.get('schema_type'),
            'resolved_queue': resolved_queue,
            'from_role': message.get('from_role'),
            'to_role': message.get('to_role'),
        }, 0)

    def send_packet(self, *, repo_root: Path, message_file: Path) -> tuple[dict[str, object], int]:
        message = load_json(message_file)
        errors = validate_envelope(message, require_authority=True)
        if errors:
            return ({'ok': False, 'message_file': str(message_file), 'errors': errors}, 1)
        queue_name = self.resolve_packet_queue(message=message, repo_root=repo_root)
        exchange = self._resolved_runtime_exchange(repo_root)
        packet_compilation_run = self._runtime_event_repository.create_packet_compilation_run_for_message(
            message=message,
            message_file=str(message_file),
            agent_name=self._packet_compiler_agent_name_for_message(message),
        )
        _, publish_result = self._client().publish(exchange, queue_name, message)
        routed = publish_result.get('routed') if isinstance(publish_result, dict) else False
        if routed and isinstance(publish_result, dict):
            self._runtime_event_repository.record_queue_send_for_message(
                message=message,
                queue_name=queue_name,
                exchange=exchange,
                publish_result=publish_result,
                packet_compilation_run=packet_compilation_run,
            )
            persist_slice_result(message)
            persist_qa_verification(message)
        result = {
            'ok': bool(routed),
            'message_file': str(message_file),
            'message_id': message.get('message_id'),
            'schema_type': message.get('schema_type'),
            'resolved_queue': queue_name,
            'from_role': message.get('from_role'),
            'to_role': message.get('to_role'),
        }
        return result, 0 if result['ok'] else 1

    def resolve_packet_queue(self, *, message: dict[str, Any], repo_root: Path) -> str:
        schema_type = message.get('schema_type')
        topology = resolved_repo_runtime_queue_topology(repo_root)
        queue_name = runtime_queue_name_for_schema(schema_type, topology=topology)
        if queue_name:
            return queue_name
        if schema_type in {'techlead_assignment_packet', 'techlead_decision_packet'}:
            return self._resolve_techlead_packet_queue(message=message, repo_root=repo_root)
        raise RuntimeError(f'No queue mapping is defined for schema type {schema_type!r}')

    def _resolve_techlead_packet_queue(self, *, message: dict[str, Any], repo_root: Path) -> str:
        schema_type = message.get('schema_type')
        raw_payload = message.get('payload')
        payload: JsonDict = raw_payload if isinstance(raw_payload, dict) else {}
        if schema_type == 'techlead_assignment_packet':
            role = normalize_role_name(payload.get('target_role') if isinstance(payload, dict) else None) or normalize_role_name(message.get('to_role'))
        elif schema_type == 'techlead_decision_packet':
            role = normalize_role_name(message.get('to_role'))
        else:
            raise RuntimeError(
                'techlead packet dispatch only supports techlead_assignment_packet and '
                f'techlead_decision_packet, got {schema_type!r}'
            )
        topology = resolved_repo_runtime_queue_topology(repo_root)
        queue_name = runtime_queue_name_for_role(role, topology=topology)
        if not queue_name and role:
            queue_name = team_worker_queue_name_by_display_name(role, repo_root=repo_root)
        if not queue_name:
            raise RuntimeError(f'No queue mapping is defined for TechLead packet role {role!r}')
        return queue_name

    def _claim_repo(self, root: Path) -> FileQueueClaimLedgerRepository:
        return FileQueueClaimLedgerRepository(root=root)

    def _client(self) -> RabbitMQManagementClient:
        return self._management_client or build_default_management_client()

    def _resolved_runtime_exchange(self, repo_root: Path) -> str:
        topology = resolved_repo_runtime_queue_topology(repo_root)
        return topology.queue_exchange or DEFAULT_RUNTIME_QUEUE_EXCHANGE

    def _resolved_runtime_queues(self, repo_root: Path) -> list[str]:
        topology = resolved_repo_runtime_queue_topology(repo_root)
        return list(topology.queue_names.values())

    @staticmethod
    def _packet_compiler_agent_name_for_message(message: dict[str, Any]) -> str:
        normalized_from_role = normalize_role_name(message.get('from_role'))
        if normalized_from_role in {'Python Dev', 'Frontend Dev', 'Backend Dev', 'Infra Dev', 'Docs Dev', 'Dev'}:
            return 'Dev Agent'
        if normalized_from_role == 'QA':
            return 'QA Agent'
        if normalized_from_role == 'TechLead':
            return 'TechLead Agent'
        if normalized_from_role in {'Architect', 'Authority Architect', 'Delivery Architect'}:
            return 'Architect Agent'
        return 'TechLead Agent'

    @staticmethod
    def _reconcile_ready_count(
        raw_ready: int | None,
        preview: list[dict[str, object]],
        preview_probe_ran: bool,
    ) -> tuple[int, dict[str, object] | None]:
        raw_value = 0 if raw_ready is None else int(raw_ready)
        observed_minimum = len(preview)
        if not preview_probe_ran:
            return raw_value, None
        if observed_minimum == 0 and raw_value != 0:
            return 0, {
                'raw_messages_ready': raw_value,
                'observed_preview_count': observed_minimum,
                'reason': 'preview_empty_but_broker_ready_nonzero',
            }
        if observed_minimum > raw_value:
            return observed_minimum, {
                'raw_messages_ready': raw_value,
                'observed_preview_count': observed_minimum,
                'reason': 'preview_count_exceeded_broker_ready',
            }
        return raw_value, None


__all__ = ['DefaultRuntimeQueueAdminService']

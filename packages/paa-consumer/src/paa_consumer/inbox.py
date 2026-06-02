"""Consumer-facing queue wrappers over the shared handoff runtime."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from paa_core import handoff_runtime
from paa_core.config import (
    DEFAULT_RUNTIME_QUEUE_EXCHANGE,
    runtime_queue_name_for_role,
    runtime_queue_name_for_schema,
)
from paa_core.repositories.runtime_event import PostgresRuntimeEventRepository
from paa_core.runtime_paths import repo_queue_state_root, resolved_repo_runtime_queue_topology
from paa_core.team_worker_roles import team_worker_queue_name_by_display_name


def run_queue_command(repo_root: Path, argv: list[str]) -> int:
    os.environ.setdefault('FRACTAL_CORE_HANDOFF_STATE_DIR', str(repo_queue_state_root(repo_root)))
    return handoff_runtime.main(['--repo-root', str(repo_root), *argv])


def _normalize_role(role: Any) -> str | None:
    return handoff_runtime.normalize_role_name(role)


def resolve_techlead_packet_queue(message: dict[str, Any], repo_root: Path | None = None) -> str:
    resolved_repo_root = repo_root.resolve() if repo_root is not None else None
    schema_type = message.get('schema_type')
    payload = message.get('payload') or {}
    if schema_type == 'techlead_assignment_packet':
        role = _normalize_role(payload.get('target_role') or message.get('to_role'))
    elif schema_type == 'techlead_decision_packet':
        role = _normalize_role(message.get('to_role'))
    else:
        raise RuntimeError(
            f"techlead packet dispatch only supports techlead_assignment_packet and "
            f"techlead_decision_packet, got {schema_type!r}"
        )
    topology = None if resolved_repo_root is None else resolved_repo_runtime_queue_topology(resolved_repo_root)
    queue_name = runtime_queue_name_for_role(role, topology=topology)
    if not queue_name and role:
        queue_name = team_worker_queue_name_by_display_name(role, repo_root=resolved_repo_root)
    if not queue_name:
        raise RuntimeError(f'No queue mapping is defined for TechLead packet role {role!r}')
    return queue_name


def resolve_packet_queue(message: dict[str, Any], repo_root: Path | None = None) -> str:
    resolved_repo_root = repo_root.resolve() if repo_root is not None else None
    schema_type = message.get('schema_type')
    topology = None if resolved_repo_root is None else resolved_repo_runtime_queue_topology(resolved_repo_root)
    queue_name = runtime_queue_name_for_schema(schema_type, topology=topology)
    if queue_name:
        return queue_name
    if schema_type in {'techlead_assignment_packet', 'techlead_decision_packet'}:
        return resolve_techlead_packet_queue(message, repo_root=resolved_repo_root)
    raise RuntimeError(f'No queue mapping is defined for schema type {schema_type!r}')


def dispatch_packet(repo_root: Path, message_file: Path) -> dict[str, Any]:
    os.environ.setdefault('FRACTAL_CORE_HANDOFF_STATE_DIR', str(repo_queue_state_root(repo_root)))
    message = handoff_runtime.load_json(message_file)
    schema_type = message.get('schema_type')
    errors = handoff_runtime.validate_envelope(message, require_authority=True)
    if errors:
        return {
            'ok': False,
            'message_file': str(message_file),
            'errors': errors,
        }
    queue_name = (
        resolve_techlead_packet_queue(message, repo_root=repo_root)
        if schema_type in {'techlead_assignment_packet', 'techlead_decision_packet'}
        else resolve_packet_queue(message, repo_root=repo_root)
    )
    topology = resolved_repo_runtime_queue_topology(repo_root)
    exchange = topology.queue_exchange or DEFAULT_RUNTIME_QUEUE_EXCHANGE
    runtime_event_repository = PostgresRuntimeEventRepository()
    packet_compilation_run = runtime_event_repository.create_packet_compilation_run_for_message(
        message=message,
        message_file=str(message_file),
        agent_name=handoff_runtime.packet_compiler_agent_name_for_message(message),
    )
    client = handoff_runtime.RabbitMQManagementClient(
        user=handoff_runtime.DEFAULT_USER,
        password=handoff_runtime.DEFAULT_PASSWORD,
        host=handoff_runtime.DEFAULT_HOST,
        port=handoff_runtime.DEFAULT_MANAGEMENT_PORT,
        vhost=handoff_runtime.DEFAULT_VHOST,
    )
    _, result = client.publish(exchange, queue_name, message)
    if result.get('routed'):
        runtime_event_repository.record_queue_send_for_message(
            message=message,
            queue_name=queue_name,
            exchange=exchange,
            publish_result=result,
            packet_compilation_run=packet_compilation_run,
        )
        handoff_runtime.persist_slice_result(message)
        handoff_runtime.persist_qa_verification(message)
    return {
        'ok': bool(result.get('routed')),
        'message_file': str(message_file),
        'message_id': message.get('message_id'),
        'schema_type': message.get('schema_type'),
        'resolved_queue': queue_name,
        'from_role': message.get('from_role'),
        'to_role': message.get('to_role'),
    }


def dispatch_techlead_packet(repo_root: Path, message_file: Path) -> dict[str, Any]:
    message = handoff_runtime.load_json(message_file)
    schema_type = message.get('schema_type')
    if schema_type not in {'techlead_assignment_packet', 'techlead_decision_packet'}:
        return {
            'ok': False,
            'message_file': str(message_file),
            'errors': [f'techlead dispatch only supports techlead packet families, got {schema_type!r}'],
        }
    return dispatch_packet(repo_root, message_file)

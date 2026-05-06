"""Consumer-facing queue wrappers over the shared handoff runtime."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from paa_core import handoff_runtime
from paa_core.runtime_paths import repo_queue_state_root


TECHLEAD_QUEUE_BY_ROLE = {
    'Python Dev': 'fractal-core-python',
    'QA': 'fractal-core-qa',
    'Delivery Architect': 'fractal-core-architecture',
    'Authority Architect': 'fractal-core-architecture',
    'Architect': 'fractal-core-architecture',
    # There is no dedicated TechLead queue yet; Phase B keeps control traffic on the
    # architecture queue until we decide whether TechLead gets a first-class queue.
    'TechLead': 'fractal-core-architecture',
}

TRANSITIONAL_RESULT_QUEUE_BY_SCHEMA = {
    # Phase A keeps physical queue names stable while semantic routing changes to TechLead.
    'architect_cycle_packet': 'fractal-core-python',
    'slice_result_packet': 'fractal-core-qa',
    'worker_result_packet': 'fractal-core-architecture',
    'qa_verification_packet': 'fractal-core-architecture',
    'delivery_review_packet': 'fractal-core-architecture',
}


def run_queue_command(repo_root: Path, argv: list[str]) -> int:
    os.environ.setdefault('FRACTAL_CORE_HANDOFF_STATE_DIR', str(repo_queue_state_root(repo_root)))
    return handoff_runtime.main(argv)


def _normalize_role(role: Any) -> str | None:
    return handoff_runtime.normalize_role_name(role)


def resolve_techlead_packet_queue(message: dict[str, Any]) -> str:
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
    queue_name = TECHLEAD_QUEUE_BY_ROLE.get(role or '')
    if not queue_name:
        raise RuntimeError(f'No queue mapping is defined for TechLead packet role {role!r}')
    return queue_name


def resolve_packet_queue(message: dict[str, Any]) -> str:
    schema_type = message.get('schema_type')
    if schema_type in TRANSITIONAL_RESULT_QUEUE_BY_SCHEMA:
        return TRANSITIONAL_RESULT_QUEUE_BY_SCHEMA[schema_type]
    if schema_type in {'techlead_assignment_packet', 'techlead_decision_packet'}:
        return resolve_techlead_packet_queue(message)
    raise RuntimeError(f'No queue mapping is defined for schema type {schema_type!r}')


def dispatch_packet(repo_root: Path, message_file: Path) -> dict[str, Any]:
    os.environ.setdefault('FRACTAL_CORE_HANDOFF_STATE_DIR', str(repo_queue_state_root(repo_root)))
    message = handoff_runtime.load_json(message_file)
    errors = handoff_runtime.validate_envelope(message, require_authority=True)
    if errors:
        return {
            'ok': False,
            'message_file': str(message_file),
            'errors': errors,
        }
    queue_name = resolve_packet_queue(message)
    client = handoff_runtime.RabbitMQManagementClient(
        user=handoff_runtime.DEFAULT_USER,
        password=handoff_runtime.DEFAULT_PASSWORD,
        host=handoff_runtime.DEFAULT_HOST,
        port=handoff_runtime.DEFAULT_MANAGEMENT_PORT,
        vhost=handoff_runtime.DEFAULT_VHOST,
    )
    _, result = client.publish(handoff_runtime.DEFAULT_EXCHANGE, queue_name, message)
    if result.get('routed'):
        handoff_runtime.persist_send_event(message, queue_name, publish_result=result)
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

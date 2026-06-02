"""Unified packet dispatch helpers for runtime hosts and CLI flows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from paa_core.claim_ledger import load_json
from paa_core.packet_envelope import validate_envelope
from paa_core.services.runtime_queue_admin import DefaultRuntimeQueueAdminService


def resolve_techlead_packet_queue(message: dict[str, Any], repo_root: Path | None = None) -> str:
    if repo_root is None:
        raise RuntimeError('repo_root is required to resolve TechLead packet queues.')
    return DefaultRuntimeQueueAdminService()._resolve_techlead_packet_queue(  # noqa: SLF001
        message=message,
        repo_root=repo_root.resolve(),
    )


def resolve_packet_queue(message: dict[str, Any], repo_root: Path | None = None) -> str:
    if repo_root is None:
        raise RuntimeError('repo_root is required to resolve packet queues.')
    return DefaultRuntimeQueueAdminService().resolve_packet_queue(
        message=message,
        repo_root=repo_root.resolve(),
    )


def dispatch_packet(repo_root: Path, message_file: Path) -> dict[str, Any]:
    message = load_json(message_file)
    errors = validate_envelope(message, require_authority=True)
    if errors:
        return {
            'ok': False,
            'message_file': str(message_file),
            'errors': errors,
        }
    result, _ = DefaultRuntimeQueueAdminService().send_packet(
        repo_root=repo_root.resolve(),
        message_file=message_file.resolve(),
    )
    return result


def dispatch_techlead_packet(repo_root: Path, message_file: Path) -> dict[str, Any]:
    message = load_json(message_file)
    schema_type = message.get('schema_type')
    if schema_type not in {'techlead_assignment_packet', 'techlead_decision_packet'}:
        return {
            'ok': False,
            'message_file': str(message_file),
            'errors': [f'techlead dispatch only supports techlead packet families, got {schema_type!r}'],
        }
    return dispatch_packet(repo_root, message_file)


__all__ = [
    'dispatch_packet',
    'dispatch_techlead_packet',
    'resolve_packet_queue',
    'resolve_techlead_packet_queue',
]

"""Queue-driven automation preflight service for the unified PAA runtime."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from paa_core.services.runtime_queue_admin import DefaultRuntimeQueueAdminService
from paa_core.team_worker_roles import active_team_worker_roles, team_worker_role_by_key
from paa_core.runtime.support.runtime_paths import resolved_repo_runtime_queue_topology
from paa_core.runtime.transport.claim_ledger import FileQueueClaimLedgerRepository
from paa_core.runtime.transport.packet_envelope import normalize_role_name

QUEUE_PREVIEW_DEPTH = 10
TECHLEAD_GATE_SCHEMA_TYPES = {
    'slice_result_packet',
    'worker_result_packet',
    'qa_verification_packet',
    'delivery_review_packet',
    'techlead_decision_packet',
}


@dataclass(frozen=True)
class AutomationPreflightRoleGate:
    queue_name: str
    to_role: str
    schema_types: set[str]
    role_label: str


class DefaultAutomationPreflightService:
    def __init__(
        self,
        *,
        runtime_queue_admin_service: DefaultRuntimeQueueAdminService | None = None,
    ) -> None:
        self._runtime_queue_admin_service = runtime_queue_admin_service or DefaultRuntimeQueueAdminService()

    def evaluate(
        self,
        *,
        repo_root: Path,
        target_role: str,
        project_slug: str = 'paa-platform',
    ) -> dict[str, object]:
        resolved_repo_root = repo_root.expanduser().resolve()
        queues = self._queue_state(resolved_repo_root)
        queue_snapshot = {
            queue_name: {
                'messages_ready': queue_data.get('messages_ready'),
                'messages_unacknowledged': queue_data.get('messages_unacknowledged'),
            }
            for queue_name, queue_data in queues.items()
        }
        active_claims = self._active_claims(resolved_repo_root)

        if target_role == 'techlead':
            queue_candidates = self._queue_gate_candidates(
                queues,
                to_role='TechLead',
                schema_types=TECHLEAD_GATE_SCHEMA_TYPES,
            )
            claim_match = any(
                claim.get('queue') == self._queue_name_by_key(resolved_repo_root, 'techlead')
                and normalize_role_name(_role_string(claim.get('to_role'))) == 'TechLead'
                for claim in active_claims
            )
            should_invoke_model = bool(queue_candidates or claim_match)
            if queue_candidates:
                gate_reason = 'queue_packet_for_techlead'
                workflow_stage = self._workflow_stage_for_candidate(queue_candidates[0])
                current_owner_role = 'TechLead'
            elif claim_match:
                gate_reason = 'active_techlead_work_in_progress'
                workflow_stage = 'techlead_work_in_progress'
                current_owner_role = 'TechLead'
            else:
                gate_reason = 'no_techlead_work_detected'
                workflow_stage = 'idle'
                current_owner_role = 'Unknown'
            role_label = 'TechLead'
        else:
            gate = self._role_queue_gate(resolved_repo_root)[target_role]
            queue_candidates = self._queue_gate_candidates(
                queues,
                queue_name=gate.queue_name,
                to_role=gate.to_role,
                schema_types=gate.schema_types,
            )
            claim_match = any(
                claim.get('queue') == gate.queue_name
                and normalize_role_name(_role_string(claim.get('to_role')))
                == normalize_role_name(gate.to_role)
                for claim in active_claims
            )
            should_invoke_model = bool(queue_candidates or claim_match)
            if queue_candidates:
                gate_reason = 'claimable_assignment_packet_available'
                workflow_stage = self._workflow_stage_for_candidate(queue_candidates[0])
                current_owner_role = gate.role_label
            elif claim_match:
                gate_reason = 'active_role_work_in_progress'
                workflow_stage = f"{target_role.replace('-', '_')}_work_in_progress"
                current_owner_role = gate.role_label
            else:
                gate_reason = 'no_role_work_detected'
                workflow_stage = 'idle'
                current_owner_role = 'Unknown'
            role_label = gate.role_label

        active_issue_number = None
        if queue_candidates:
            active_issue_number = queue_candidates[0].get('issue_number')
        elif active_claims:
            active_issue_number = active_claims[0].get('issue_number')

        return {
            'ok': True,
            'repo_root': str(resolved_repo_root),
            'project_slug': project_slug,
            'target_role': target_role,
            'role_label': role_label,
            'should_invoke_model': should_invoke_model,
            'skip_model_invocation': not should_invoke_model,
            'gate_reason': gate_reason,
            'workflow_stage': workflow_stage,
            'current_owner_role': current_owner_role,
            'active_issue_number': active_issue_number,
            'queue_candidates': [
                {
                    'message_id': candidate.get('message_id'),
                    'schema_type': candidate.get('schema_type'),
                    'queue_name': candidate.get('queue_name'),
                    'issue_number': candidate.get('issue_number'),
                    'from_role': candidate.get('from_role'),
                    'to_role': candidate.get('to_role'),
                    'created_at': candidate.get('created_at'),
                }
                for candidate in queue_candidates
            ],
            'queue_snapshot': queue_snapshot,
            'next_step_hint': (
                'invoke_model_for_role_run' if should_invoke_model else 'exit_without_model_invocation'
            ),
        }

    def _queue_state(self, repo_root: Path) -> dict[str, dict[str, object]]:
        return {
            queue_name: self._runtime_queue_admin_service.check(
                repo_root=repo_root,
                queue=queue_name,
                preview=QUEUE_PREVIEW_DEPTH,
            )
            for queue_name in resolved_repo_runtime_queue_topology(repo_root).queue_names.values()
        }

    def _active_claims(self, repo_root: Path) -> list[dict[str, object]]:
        claim_repo = FileQueueClaimLedgerRepository(root=repo_root / '.project/data/paa/queue-state/fractal-core-handoff')
        claims = claim_repo.list_claims(status='claimed')
        normalized: list[dict[str, object]] = []
        for claim in claims:
            envelope = claim.get('original_envelope') or {}
            if not isinstance(envelope, dict):
                continue
            normalized.append({
                'claim_id': claim.get('claim_id'),
                'queue': claim.get('queue'),
                'message_id': envelope.get('message_id'),
                'schema_type': envelope.get('schema_type'),
                'from_role': envelope.get('from_role'),
                'to_role': envelope.get('to_role'),
                'created_at': envelope.get('created_at'),
                'issue_number': self._issue_number_from_packet_preview(envelope),
            })
        normalized.sort(
            key=lambda claim: self._parse_created_at(claim.get('created_at')) or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        return normalized

    def _role_queue_gate(self, repo_root: Path) -> dict[str, AutomationPreflightRoleGate]:
        dev_queue_name = self._queue_name_by_key(repo_root, 'dev')
        qa_queue_name = self._queue_name_by_key(repo_root, 'qa')
        techlead_queue_name = self._queue_name_by_key(repo_root, 'techlead')
        gate = {
            'delivery-architect': AutomationPreflightRoleGate(
                queue_name=techlead_queue_name,
                to_role='Delivery Architect',
                schema_types={'techlead_assignment_packet'},
                role_label='Delivery Architect',
            ),
            'qa': AutomationPreflightRoleGate(
                queue_name=qa_queue_name,
                to_role='QA',
                schema_types={'techlead_assignment_packet'},
                role_label='QA',
            ),
        }
        for worker_role in active_team_worker_roles(repo_root=repo_root):
            gate[worker_role.key] = AutomationPreflightRoleGate(
                queue_name=dev_queue_name,
                to_role='Dev' if worker_role.display_name == 'Python Dev' else worker_role.display_name,
                schema_types={'techlead_assignment_packet', 'architect_cycle_packet'},
                role_label='Dev' if worker_role.display_name == 'Python Dev' else worker_role.display_name,
            )
        return gate

    def _queue_gate_candidates(
        self,
        queues: dict[str, dict[str, object]],
        *,
        queue_name: str | None = None,
        to_role: str | None = None,
        schema_types: set[str] | None = None,
    ) -> list[dict[str, object]]:
        candidates: list[dict[str, object]] = []
        normalized_to_role = normalize_role_name(to_role) if to_role else None
        for current_queue_name, queue_data in queues.items():
            if queue_name and current_queue_name != queue_name:
                continue
            preview_value = queue_data.get('preview')
            preview = preview_value if isinstance(preview_value, list) else []
            for item in preview:
                if not isinstance(item, dict):
                    continue
                payload = item.get('payload_preview') or {}
                if not isinstance(payload, dict):
                    continue
                payload_to_role = normalize_role_name(_role_string(payload.get('to_role')))
                if normalized_to_role and payload_to_role != normalized_to_role:
                    continue
                if schema_types and payload.get('schema_type') not in schema_types:
                    continue
                candidate = dict(payload)
                candidate['queue_name'] = current_queue_name
                candidate['issue_number'] = self._issue_number_from_packet_preview(payload)
                candidates.append(candidate)
        candidates.sort(
            key=lambda candidate: self._parse_created_at(candidate.get('created_at')) or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        return candidates

    @staticmethod
    def _queue_name_by_key(repo_root: Path, key: str) -> str:
        topology = resolved_repo_runtime_queue_topology(repo_root)
        queue_name = topology.queue_names.get(key)
        if not queue_name:
            raise RuntimeError(f'Queue topology does not define queue key {key!r}.')
        return queue_name

    @staticmethod
    def _issue_number_from_packet_preview(payload: dict[str, object]) -> int | None:
        github_context = payload.get('github_context') or {}
        if isinstance(github_context, dict):
            issue_number = github_context.get('issue_number')
            try:
                return int(issue_number) if issue_number is not None else None
            except Exception:
                return None
        return None

    @staticmethod
    def _parse_created_at(value: object) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        except Exception:
            return None

    @staticmethod
    def _workflow_stage_for_candidate(candidate: dict[str, object]) -> str:
        schema_type = candidate.get('schema_type')
        if schema_type == 'worker_result_packet':
            return 'techlead_worker_review_pending'
        if schema_type == 'qa_verification_packet':
            return 'techlead_qa_review_pending'
        if schema_type == 'delivery_review_packet':
            return 'techlead_delivery_review_pending'
        if schema_type == 'techlead_assignment_packet':
            return 'assignment_ready'
        if schema_type == 'architect_cycle_packet':
            return 'assignment_ready'
        if schema_type == 'techlead_decision_packet':
            return 'techlead_decision_pending'
        if schema_type == 'slice_result_packet':
            return 'techlead_worker_review_pending'
        return 'queue_work_detected'


def _role_string(value: object) -> str | None:
    return value if isinstance(value, str) else None


__all__ = ['AutomationPreflightRoleGate', 'DefaultAutomationPreflightService']

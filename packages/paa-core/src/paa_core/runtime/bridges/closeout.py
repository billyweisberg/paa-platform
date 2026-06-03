"""Core QA closeout helpers extracted from the legacy TechLead shell."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


@dataclass(frozen=True)
class RuntimeQaCloseoutRequest:
    repo_root: Path
    issue_number: int
    execution_mode: str
    qa_packet: dict[str, Any] | None
    issue_full: dict[str, Any]
    pr_full: dict[str, Any] | None
    package_id_external: str
    brief_id_external: str
    project_slug: str
    architecture_queue: str
    send_decision: bool = False
    ack_qa_packet: bool = False
    claimed_by: str = 'techlead-closeout-qa-pass'
    canonical_branch: str | None = None
    role_branch: str | None = None
    worktree_hint: str | None = None
    output_path: Path | None = None
    review_output_path: Path | None = None


class DefaultRuntimeCloseoutService:
    def __init__(
        self,
        *,
        queue_admin_service,
        acceptance_event_persister: Callable[..., Any],
        decision_emitter: Callable[[dict[str, Any]], dict[str, Any]],
    ) -> None:
        self._queue_admin_service = queue_admin_service
        self._acceptance_event_persister = acceptance_event_persister
        self._decision_emitter = decision_emitter

    def closeout_qa_pass(self, request: RuntimeQaCloseoutRequest) -> dict[str, Any]:
        qa_packet = request.qa_packet
        if qa_packet is None:
            return {
                'ok': False,
                'reason': 'qa_packet_not_found',
                'details': f'No repo-local QA verification packet was found for issue #{request.issue_number}.',
            }
        if qa_packet.get('verification_status') != 'pass':
            return {
                'ok': False,
                'reason': 'qa_packet_not_pass',
                'details': f"QA packet {qa_packet.get('message_id')!r} is not a passing packet.",
                'qa_packet': qa_packet,
            }

        proof_only = request.execution_mode == 'proof_only'
        pr_merged = bool(request.pr_full and request.pr_full.get('mergedAt'))
        issue_closed = (request.issue_full.get('state') or '').upper() == 'CLOSED'
        if not pr_merged and not issue_closed and not proof_only:
            return {
                'ok': False,
                'reason': 'slice_not_merged_or_closed',
                'details': 'QA pass closeout requires a merged PR or a closed issue before TechLead records closed lineage.',
                'qa_packet': qa_packet,
                'github_state': {
                    'issue_state': request.issue_full.get('state'),
                    'pr_state': request.pr_full.get('state') if request.pr_full else None,
                    'pr_merged_at': request.pr_full.get('mergedAt') if request.pr_full else None,
                },
            }

        self._acceptance_event_persister(
            request.project_slug,
            request.issue_number,
            qa_packet,
            request.pr_full or {},
            decision='proof_only_closed' if proof_only else 'accepted',
            decision_notes=(
                f"TechLead recorded proof-only closeout for issue #{request.issue_number} after QA pass from packet "
                f"{qa_packet.get('message_id')} without requiring live merge or issue closure."
                if proof_only
                else None
            ),
            metadata_extra={
                'closeout_mode': 'proof_only' if proof_only else 'live_delivery',
                'proof_only_closeout': proof_only,
                'issue_closed_at_closeout': issue_closed,
                'pr_merged_at_closeout': pr_merged,
            },
        )

        decision_result = self._decision_emitter({
            'repo_root': request.repo_root,
            'package_id_external': request.package_id_external,
            'brief_id_external': request.brief_id_external,
            'project_slug': request.project_slug,
            'decision_type': 'proof_only_closed' if proof_only else 'closed',
            'send': request.send_decision,
            'source_packet_path': Path(qa_packet['path']),
            'canonical_branch': request.canonical_branch,
            'role_branch': request.role_branch,
            'superseded_branch': None,
            'worktree_hint': request.worktree_hint,
            'reset_reason': None,
            'output': request.output_path,
            'review_output': request.review_output_path,
        })
        if not decision_result.get('ok'):
            return {
                'ok': False,
                'reason': 'decision_emission_failed',
                'details': 'TechLead could not record the closed decision for the passing QA packet.',
                'qa_packet': qa_packet,
                'decision': decision_result,
            }

        qa_ack = None
        if request.ack_qa_packet:
            qa_ack_result = self._ack_if_queue_head(
                repo_root=request.repo_root,
                queue_name=request.architecture_queue,
                expected_message_id=str(qa_packet.get('message_id')),
                claimed_by=request.claimed_by,
                not_head_reason='qa_packet_not_queue_head',
                not_head_details='The passing QA packet is not the next claimable architecture-queue message; refusing to acknowledge the wrong packet.',
                wrong_claim_reason='claimed_wrong_packet',
                wrong_claim_details='Architecture queue claim did not return the expected passing QA packet.',
            )
            if not qa_ack_result.get('ok'):
                qa_ack_result['qa_packet'] = qa_packet
                qa_ack_result['decision'] = decision_result
                return qa_ack_result
            qa_ack = qa_ack_result['ack']

        decision_ack = None
        if request.send_decision and decision_result.get('sent'):
            decision_ack_result = self._ack_if_queue_head(
                repo_root=request.repo_root,
                queue_name=request.architecture_queue,
                expected_message_id=str(decision_result.get('message_id')),
                claimed_by=f"{request.claimed_by}-decision",
                not_head_reason='decision_packet_not_queue_head',
                not_head_details='The emitted decision packet is not the next claimable architecture-queue message.',
                wrong_claim_reason='claimed_wrong_decision_packet',
                wrong_claim_details='Architecture queue claim did not return the expected decision packet.',
            )
            decision_ack = decision_ack_result['ack'] if decision_ack_result.get('ok') else decision_ack_result

        return {
            'ok': True,
            'issue_number': request.issue_number,
            'execution_mode': request.execution_mode,
            'closeout_mode': 'proof_only' if proof_only else 'live_delivery',
            'qa_packet': qa_packet,
            'github_state': {
                'issue_state': request.issue_full.get('state'),
                'issue_closed_at': request.issue_full.get('closedAt'),
                'pr_number': request.pr_full.get('number') if request.pr_full else None,
                'pr_state': request.pr_full.get('state') if request.pr_full else None,
                'pr_merged_at': request.pr_full.get('mergedAt') if request.pr_full else None,
            },
            'decision': decision_result,
            'qa_ack': qa_ack,
            'decision_ack': decision_ack,
            'next_step_hint': 'run_closed_cleanup_if_registered_role_worktrees_should_be_pruned',
        }

    def _ack_if_queue_head(
        self,
        *,
        repo_root: Path,
        queue_name: str,
        expected_message_id: str,
        claimed_by: str,
        not_head_reason: str,
        not_head_details: str,
        wrong_claim_reason: str,
        wrong_claim_details: str,
    ) -> dict[str, Any]:
        queue_state = self._queue_admin_service.check(repo_root=repo_root, queue=queue_name, preview=1)
        preview = queue_state.get('preview') or []
        head_payload = (preview[0] or {}).get('payload_preview') if preview else None
        if not head_payload or head_payload.get('message_id') != expected_message_id:
            return {
                'ok': False,
                'reason': not_head_reason,
                'details': not_head_details,
                'architecture_queue_head': head_payload,
            }
        claim_result, claim_code = self._queue_admin_service.claim_next(
            repo_root=repo_root,
            queue=queue_name,
            claimed_by=claimed_by,
        )
        if claim_code != 0 or claim_result.get('message_id') != expected_message_id:
            return {
                'ok': False,
                'reason': wrong_claim_reason,
                'details': wrong_claim_details,
                'expected_message_id': expected_message_id,
                'claim': claim_result,
            }
        ack_result = self._queue_admin_service.ack(repo_root=repo_root, claim_id=str(claim_result['claim_id']))
        return {'ok': True, 'ack': ack_result}


__all__ = [
    'DefaultRuntimeCloseoutService',
    'RuntimeQaCloseoutRequest',
]

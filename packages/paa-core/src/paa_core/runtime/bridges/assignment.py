"""Core next-assignment compile/validate/send bridge extracted from the legacy TechLead shell."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
from typing import Any, Callable, cast

from paa_core.runtime.transport.packet_dispatch import resolve_packet_queue
from paa_core.runtime_paths import repo_authority_manifest_path, repo_producer_bin
from paa_core.services.runtime_queue_admin import DefaultRuntimeQueueAdminService


@dataclass(frozen=True)
class RuntimeAssignmentBridgeRequest:
    repo_root: Path
    project_slug: str
    package_id_external: str
    brief_id_external: str
    github_repo: str
    issue_number: int
    issue_url: str
    pr_number: int
    pr_url: str
    branch: str
    workflow_stage: str
    target_role: str
    target_role_cli: str
    assignment_type: str
    assignment_summary: str
    allowed_result_types: tuple[str, ...]
    source_packet_message_id: str | None = None
    source_packet_path: str | None = None
    source_packet_queue: str | None = None
    source_packet_schema_type: str | None = None
    output_path: Path | None = None
    review_output_path: Path | None = None
    send: bool = False


class DefaultRuntimeAssignmentBridgeService:
    def __init__(
        self,
        *,
        queue_admin_service: DefaultRuntimeQueueAdminService | None = None,
        authority_manifest_resolver: Callable[[Path], Path] | None = None,
        producer_bin_resolver: Callable[[Path], Path] | None = None,
    ) -> None:
        self._queue_admin_service = queue_admin_service or DefaultRuntimeQueueAdminService()
        self._authority_manifest_resolver = authority_manifest_resolver or repo_authority_manifest_path
        self._producer_bin_resolver = producer_bin_resolver or repo_producer_bin

    def emit_next_assignment(self, request: RuntimeAssignmentBridgeRequest) -> dict[str, Any]:
        repo_root = request.repo_root.resolve()
        output_path, review_output_path = self._resolve_output_paths(
            repo_root=repo_root,
            issue_number=request.issue_number,
            target_role=request.target_role,
            output_path=request.output_path,
            review_output_path=request.review_output_path,
        )

        compile_cmd = [
            str(self._producer_bin_resolver(repo_root)),
            'authority',
            'materialize-techlead-assignment-packet',
            '--manifest', str(self._authority_manifest_resolver(repo_root)),
            '--project-slug', request.project_slug,
            '--package-id-external', request.package_id_external,
            '--brief-id-external', request.brief_id_external,
            '--repo', request.github_repo,
            '--issue-number', str(request.issue_number),
            '--issue-url', str(request.issue_url),
            '--pr-number', str(request.pr_number),
            '--pr-url', str(request.pr_url),
            '--branch', str(request.branch),
            '--target-role', request.target_role_cli,
            '--assignment-type', request.assignment_type,
            '--assignment-summary', request.assignment_summary,
            '--output', str(output_path),
            '--review-output', str(review_output_path),
            '--persist-db',
        ]
        if request.source_packet_path:
            compile_cmd.extend(['--source-packet-path', str(request.source_packet_path)])
        if request.source_packet_message_id:
            compile_cmd.extend(['--source-packet-message-id', str(request.source_packet_message_id)])
        for allowed_result_type in request.allowed_result_types:
            compile_cmd.extend(['--allowed-result-type', allowed_result_type])

        compile_result = self.run_json(compile_cmd)
        validate_result, validate_code = self._queue_admin_service.validate_packet(
            repo_root=repo_root,
            message_file=output_path,
        )
        result = {
            'ok': validate_code == 0,
            'workflow_stage': request.workflow_stage,
            'derived_decision': {
                'target_role': request.target_role,
                'assignment_type': request.assignment_type,
                'allowed_result_types': list(request.allowed_result_types),
            },
            'package_id_external': request.package_id_external,
            'brief_id_external': request.brief_id_external,
            'output_path': str(output_path),
            'review_output_path': str(review_output_path),
            'message_id': compile_result.get('message_id'),
            'automation_run_id': compile_result.get('automation_run_id'),
            'resolved_queue': validate_result.get('resolved_queue') if validate_result else None,
            'sent': False,
            'compile': compile_result,
            'validate': validate_result,
            'source_packet_ref': {
                'message_id': request.source_packet_message_id,
                'path': request.source_packet_path,
            },
        }
        if validate_code != 0:
            result['error'] = validate_result
            return result

        if request.send:
            send_result, send_code = self._queue_admin_service.send_packet(
                repo_root=repo_root,
                message_file=output_path,
            )
            result['send'] = send_result
            result['sent'] = send_code == 0 and bool(send_result and send_result.get('ok'))
            if send_code != 0:
                result['ok'] = False
                result['error'] = send_result
                return result

            source_packet_ack = self._maybe_ack_source_assignment(request=request, repo_root=repo_root)
            if source_packet_ack is not None:
                result['source_packet_ack'] = source_packet_ack
                if not source_packet_ack.get('ok'):
                    result['ok'] = False
                    result['error'] = 'sent_next_assignment_but_failed_to_close_source_packet'
                    return result

        return result

    def _maybe_ack_source_assignment(
        self,
        *,
        request: RuntimeAssignmentBridgeRequest,
        repo_root: Path,
    ) -> dict[str, Any] | None:
        if not request.source_packet_message_id or not (request.source_packet_path or request.source_packet_queue):
            return None
        source_queue = request.source_packet_queue
        if request.source_packet_path:
            source_packet = json.loads(Path(request.source_packet_path).resolve().read_text())
            if isinstance(source_packet, dict):
                source_queue = resolve_packet_queue(source_packet, repo_root=repo_root)
        if not source_queue:
            return None
        return self.acknowledge_source_assignment(
            repo_root=repo_root,
            message_id=str(request.source_packet_message_id),
            queue_name=str(source_queue),
            claimed_by='techlead-emit-next-assignment',
        )

    def acknowledge_source_assignment(self, *, repo_root: Path, message_id: str, queue_name: str, claimed_by: str) -> dict[str, Any]:
        claims_result = self._queue_admin_service.list_claims(repo_root=repo_root, queue=queue_name, status='claimed')
        raw_claims = claims_result.get('claims', [])
        claims = cast(list[dict[str, Any]], raw_claims if isinstance(raw_claims, list) else [])
        matching_claims = [claim for claim in claims if claim.get('message_id') == message_id]
        if len(matching_claims) > 1:
            return {
                'ok': False,
                'reason': 'multiple_open_claims_for_source_assignment',
                'details': f'More than one active claim exists for source assignment {message_id!r}.',
                'message_id': message_id,
                'queue_name': queue_name,
                'matching_claim_ids': [claim.get('claim_id') for claim in matching_claims],
            }
        if len(matching_claims) == 1:
            ack_result = self._queue_admin_service.ack(repo_root=repo_root, claim_id=str(matching_claims[0]['claim_id']))
            ack_result['ack_mode'] = 'existing_claim'
            ack_result['queue_name'] = queue_name
            return ack_result

        claim_result, claim_exit = self._queue_admin_service.claim_next(repo_root=repo_root, queue=queue_name, claimed_by=claimed_by)
        if claim_exit != 0 or claim_result is None:
            return {
                'ok': False,
                'reason': 'source_assignment_claim_failed',
                'details': 'Queue claim failed while closing the source assignment.',
                'message_id': message_id,
                'queue_name': queue_name,
                'claim_result': claim_result,
            }
        if not claim_result.get('claimed'):
            return {
                'ok': False,
                'reason': 'source_assignment_not_claimable',
                'details': f'No claimable queue message was available while trying to close source assignment {message_id!r}.',
                'message_id': message_id,
                'queue_name': queue_name,
                'claim_result': claim_result,
            }
        if claim_result.get('message_id') != message_id:
            requeue_result, requeue_exit = self._queue_admin_service.requeue(repo_root=repo_root, claim_id=str(claim_result['claim_id']))
            return {
                'ok': False,
                'reason': 'unexpected_queue_head_when_closing_source_assignment',
                'details': 'The next claimable queue message was not the expected source assignment; refusing to acknowledge the wrong packet.',
                'message_id': message_id,
                'queue_name': queue_name,
                'claim_result': claim_result,
                'requeue': requeue_result if requeue_exit == 0 else {
                    'ok': False,
                    'claim_id': claim_result['claim_id'],
                    'requeue_result': requeue_result,
                },
            }

        ack_result = self._queue_admin_service.ack(repo_root=repo_root, claim_id=str(claim_result['claim_id']))
        ack_result['ack_mode'] = 'claim_then_ack'
        ack_result['queue_name'] = queue_name
        return ack_result

    @staticmethod
    def _resolve_output_paths(
        *,
        repo_root: Path,
        issue_number: int,
        target_role: str,
        output_path: Path | None,
        review_output_path: Path | None,
    ) -> tuple[Path, Path]:
        if output_path is not None and review_output_path is not None:
            resolved_output = output_path.resolve()
            resolved_review = review_output_path.resolve()
        else:
            slug = target_role.replace(' ', '-').lower()
            reports_dir = repo_root / '.project' / 'data' / 'paa' / 'reports'
            resolved_output = (output_path or (reports_dir / f'techlead-assignment.issue{issue_number}.{slug}.json')).resolve()
            resolved_review = (review_output_path or (reports_dir / f'techlead-assignment.issue{issue_number}.{slug}.md')).resolve()
        resolved_output.parent.mkdir(parents=True, exist_ok=True)
        resolved_review.parent.mkdir(parents=True, exist_ok=True)
        return resolved_output, resolved_review

    @staticmethod
    def run_json(cmd: list[str]) -> dict[str, Any]:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f'command failed: {cmd}')
        return json.loads(result.stdout)


__all__ = [
    'DefaultRuntimeAssignmentBridgeService',
    'RuntimeAssignmentBridgeRequest',
]

"""Core manual role-entry/result bridge helpers extracted from the legacy TechLead shell."""

from __future__ import annotations

from dataclasses import dataclass
import json
import subprocess
from pathlib import Path
from typing import Any

from paa_core.runtime.transport.claim_ledger import load_json
from paa_core.runtime.transport.packet_envelope import validate_envelope
from paa_core.runtime.transport.packet_dispatch import dispatch_packet, resolve_packet_queue
from paa_core.runtime.support.runtime_paths import repo_producer_bin
from paa_core.services.runtime_queue_admin import DefaultRuntimeQueueAdminService
from paa_core.runtime.bridges.worktree import (
    DefaultRuntimeWorktreeService,
    RuntimeWorktreeInspectRequest,
)
from paa_core.team_worker_roles import team_worker_role_by_display_name


@dataclass(frozen=True)
class RuntimeRoleEntryRequest:
    repo_root: Path
    package_id_external: str
    brief_id_external: str
    project_slug: str
    target_role: str
    lineage_view: dict[str, Any]
    role_branch: str | None = None
    worktree_path: Path | None = None
    assignment_path: Path | None = None
    review_output_path: Path | None = None


@dataclass(frozen=True)
class RuntimeRoleResultAssistRequest:
    repo_root: Path
    package_id_external: str
    brief_id_external: str
    project_slug: str
    target_role: str
    lineage_view: dict[str, Any]
    role_branch: str | None = None
    worktree_path: Path | None = None
    assignment_path: Path | None = None
    review_output_path: Path | None = None
    result_input_path: Path | None = None


@dataclass(frozen=True)
class RuntimeRoleReturnBridgeRequest:
    repo_root: Path
    package_id_external: str
    brief_id_external: str
    project_slug: str
    target_role: str
    lineage_view: dict[str, Any]
    role_branch: str | None = None
    worktree_path: Path | None = None
    assignment_path: Path | None = None
    assignment_review_output_path: Path | None = None
    result_input_path: Path | None = None
    output_path: Path | None = None
    review_output_path: Path | None = None
    send: bool = False


class DefaultRuntimeRoleBridgeService:
    def __init__(
        self,
        *,
        worktree_service: DefaultRuntimeWorktreeService | None = None,
        queue_admin_service: DefaultRuntimeQueueAdminService | None = None,
    ) -> None:
        self._worktree_service = worktree_service or DefaultRuntimeWorktreeService()
        self._queue_admin_service = queue_admin_service or DefaultRuntimeQueueAdminService()

    def role_entry_helper(self, request: RuntimeRoleEntryRequest) -> dict[str, Any]:
        inspection = self._worktree_service.inspect_role_worktree(
            RuntimeWorktreeInspectRequest(
                repo_root=request.repo_root.resolve(),
                target_role=request.target_role,
                lineage_view=request.lineage_view,
                role_branch=request.role_branch,
                worktree_path=request.worktree_path,
                assignment_path=request.assignment_path,
                review_output_path=request.review_output_path,
            )
        )
        if not inspection.get('ok'):
            return {
                'ok': False,
                'reason': 'inspection_failed',
                'details': 'Role entry helper requires a successful role-worktree inspection result.',
                'inspection': inspection,
            }

        repo_root = request.repo_root.resolve()
        worktree_path = Path(inspection['worktree_path']).resolve()
        current_branch = inspection['current_branch']
        role_branch = inspection['role_branch']
        artifact = inspection['assignment_artifact']
        role_label = inspection['target_role']
        branch_alignment = {
            'ok': current_branch == role_branch,
            'current_branch': current_branch,
            'expected_role_branch': role_branch,
            'assignment_role_branch': artifact.get('role_branch'),
            'assignment_canonical_branch': artifact.get('canonical_branch'),
        }
        if artifact.get('role_branch') and artifact.get('role_branch') != role_branch:
            return {
                'ok': False,
                'reason': 'assignment_role_branch_mismatch',
                'details': 'The assignment artifact names a different role branch than the prepared worktree context.',
                'inspection': inspection,
                'branch_alignment': branch_alignment,
            }
        if current_branch != role_branch:
            return {
                'ok': False,
                'reason': 'worktree_branch_not_aligned',
                'details': 'The prepared worktree is no longer on the expected role branch.',
                'inspection': inspection,
                'branch_alignment': branch_alignment,
            }

        producer_wrapper = repo_producer_bin(repo_root)
        issue_number = inspection['lineage_view']['issue_number']
        issue_url = inspection['lineage_view']['issue_url']
        pr_number = inspection['lineage_view']['pr_number']
        pr_url = inspection['lineage_view']['pr_url']
        team_worker = team_worker_role_by_display_name(role_label, repo_root=repo_root)
        if role_label == 'Delivery Architect':
            result_command = [
                str(producer_wrapper),
                'authority',
                'materialize-delivery-review-packet',
                '--project-slug', request.project_slug,
                '--package-id-external', request.package_id_external,
                '--brief-id-external', request.brief_id_external,
                '--repo', str(worktree_path),
                '--issue-number', str(issue_number),
                '--issue-url', str(issue_url),
                '--pr-number', str(pr_number),
                '--pr-url', str(pr_url),
                '--branch', current_branch,
                '--result-type', '<delivery_result_type>',
                '--delivery-input-file', '<delivery_input_json>',
                '--source-assignment-path', artifact['path'],
                '--source-assignment-type', artifact['assignment_type'],
                '--persist-db',
            ]
        elif team_worker:
            result_command = [
                str(producer_wrapper),
                'authority',
                'materialize-worker-result-packet',
                '--project-slug', request.project_slug,
                '--package-id-external', request.package_id_external,
                '--brief-id-external', request.brief_id_external,
                '--worker-role', team_worker.key,
                '--worker-family', team_worker.family,
                '--result-type', '<worker_result_type>',
                '--repo', str(worktree_path),
                '--issue-number', str(issue_number),
                '--issue-url', str(issue_url),
                '--pr-number', str(pr_number),
                '--pr-url', str(pr_url),
                '--branch', current_branch,
                '--worker-input-file', '<worker_input_json>',
                '--source-assignment-path', artifact['path'],
                '--source-assignment-type', artifact['assignment_type'],
                '--persist-db',
            ]
        else:
            result_command = [
                str(producer_wrapper),
                'authority',
                'materialize-qa-verification-packet',
                '--project-slug', request.project_slug,
                '--package-id-external', request.package_id_external,
                '--brief-id-external', request.brief_id_external,
                '--repo', str(worktree_path),
                '--issue-number', str(issue_number),
                '--issue-url', str(issue_url),
                '--pr-number', str(pr_number),
                '--pr-url', str(pr_url),
                '--branch', current_branch,
                '--qa-input-file', '<qa_input_json>',
                '--persist-db',
            ]

        return {
            'ok': True,
            'repo_root': str(repo_root),
            'target_role': role_label,
            'worktree_path': str(worktree_path),
            'assignment_artifact': artifact,
            'branch_alignment': branch_alignment,
            'manual_execution_surfaces': {
                'enter_worktree_command': f'cd {worktree_path}',
                'assignment_json_command': f'cat {artifact["path"]}',
                'assignment_review_command': f'cat {artifact["review_output_path"]}',
                'result_compile_command': ' '.join(result_command),
                'producer_wrapper_path': str(producer_wrapper),
            },
            'inspection': inspection,
            'next_step_hint': 'review_assignment_and_begin_role_work_manually',
        }

    def role_result_assist(self, request: RuntimeRoleResultAssistRequest) -> dict[str, Any]:
        entry = self.role_entry_helper(
            RuntimeRoleEntryRequest(
                repo_root=request.repo_root,
                package_id_external=request.package_id_external,
                brief_id_external=request.brief_id_external,
                project_slug=request.project_slug,
                target_role=request.target_role,
                lineage_view=request.lineage_view,
                role_branch=request.role_branch,
                worktree_path=request.worktree_path,
                assignment_path=request.assignment_path,
                review_output_path=request.review_output_path,
            )
        )
        if not entry.get('ok'):
            return {
                'ok': False,
                'reason': 'role_entry_failed',
                'details': 'Role result assist requires a successful role-entry context.',
                'role_entry': entry,
            }

        inspection = entry['inspection']
        lineage_view = inspection['lineage_view']
        role_label = entry['target_role']
        worktree_path = Path(entry['worktree_path']).resolve()
        branch_alignment = entry['branch_alignment']
        artifact = entry['assignment_artifact']
        repo_root = request.repo_root.resolve()
        issue_number = lineage_view.get('issue_number')
        issue_url = lineage_view.get('issue_url')
        pr_number = lineage_view.get('pr_number')
        pr_url = lineage_view.get('pr_url')
        current_branch = branch_alignment.get('current_branch')
        required_context = {
            'issue_number': issue_number,
            'issue_url': issue_url,
            'pr_number': pr_number,
            'pr_url': pr_url,
            'branch': current_branch,
            'package_id_external': request.package_id_external,
            'brief_id_external': request.brief_id_external,
            'assignment_artifact_path': artifact.get('path'),
            'allowed_result_types': artifact.get('allowed_result_types') or [],
        }
        missing_fields = [
            field_name for field_name, field_value in required_context.items()
            if field_value in (None, '', [])
        ]
        if not branch_alignment.get('ok'):
            missing_fields.append('aligned_role_branch')
        if artifact.get('assignment_type') is None:
            missing_fields.append('assignment_type')

        result_input_path = (
            request.result_input_path.resolve()
            if request.result_input_path is not None
            else self.default_result_input_path(repo_root, issue_number, role_label)
        )

        team_worker = team_worker_role_by_display_name(role_label, repo_root=repo_root)
        if role_label == 'Delivery Architect':
            result_family = 'delivery_review_packet'
            expected_assignment_type = 'delivery_architecture_review'
            input_contract = {
                'required_top_level_keys': [
                    'result_type',
                    'scope_recommendation',
                    'authority_impact',
                    'branch_recommendation',
                    'techlead_action_recommended',
                    'review_summary',
                    'findings',
                ],
                'recommended_result_types': [
                    'ready_for_dev',
                    'narrow_scope',
                    'reject_scope',
                ],
            }
        elif team_worker:
            result_family = 'worker_result_packet'
            expected_assignment_type = 'implement_authorized_slice'
            input_contract = {
                'required_top_level_keys': [
                    'result_type',
                    'implementation_summary',
                    'validation_summary',
                    'artifacts',
                    'merge_status',
                ],
                'recommended_result_types': [
                    'implemented_ready_for_qa',
                    'blocked',
                    'needs_clarification',
                ],
            }
        else:
            result_family = 'qa_verification_packet'
            expected_assignment_type = 'verify_authorized_slice'
            input_contract = {
                'required_top_level_keys': [
                    'verification_status',
                    'mechanical_checks',
                    'technical_scope_checks',
                    'protected_path_checks',
                    'artifact_checks',
                    'findings',
                ],
                'recommended_result_types': [
                    'pass',
                    'fail_fixable',
                    'needs_human_review',
                ],
            }

        if artifact.get('assignment_type') != expected_assignment_type:
            return {
                'ok': False,
                'reason': 'assignment_type_not_supported_for_role_result',
                'details': f'Assignment type {artifact.get("assignment_type")!r} is not supported for role {role_label!r} in the current Phase E bridge.',
                'role_entry': entry,
                'expected_assignment_type': expected_assignment_type,
            }

        producer_wrapper = repo_producer_bin(repo_root)
        if role_label == 'Delivery Architect':
            result_compile_command = [
                str(producer_wrapper),
                'authority',
                'materialize-delivery-review-packet',
                '--project-slug', request.project_slug,
                '--package-id-external', request.package_id_external,
                '--brief-id-external', request.brief_id_external,
                '--repo', str(worktree_path),
                '--issue-number', str(issue_number),
                '--issue-url', str(issue_url),
                '--pr-number', str(pr_number),
                '--pr-url', str(pr_url),
                '--branch', str(current_branch),
                '--result-type', '<delivery_result_type>',
                '--delivery-input-file', str(result_input_path),
                '--source-assignment-path', str(artifact.get('path')),
                '--source-assignment-type', str(artifact.get('assignment_type')),
                '--persist-db',
            ]
        elif team_worker:
            result_compile_command = [
                str(producer_wrapper),
                'authority',
                'materialize-worker-result-packet',
                '--project-slug', request.project_slug,
                '--package-id-external', request.package_id_external,
                '--brief-id-external', request.brief_id_external,
                '--worker-role', team_worker.key,
                '--worker-family', team_worker.family,
                '--result-type', '<worker_result_type>',
                '--repo', str(worktree_path),
                '--issue-number', str(issue_number),
                '--issue-url', str(issue_url),
                '--pr-number', str(pr_number),
                '--pr-url', str(pr_url),
                '--branch', str(current_branch),
                '--worker-input-file', str(result_input_path),
                '--source-assignment-path', str(artifact.get('path')),
                '--source-assignment-type', str(artifact.get('assignment_type')),
                '--persist-db',
            ]
        else:
            result_compile_command = [
                str(producer_wrapper),
                'authority',
                'materialize-qa-verification-packet',
                '--project-slug', request.project_slug,
                '--package-id-external', request.package_id_external,
                '--brief-id-external', request.brief_id_external,
                '--repo', str(worktree_path),
                '--issue-number', str(issue_number),
                '--issue-url', str(issue_url),
                '--pr-number', str(pr_number),
                '--pr-url', str(pr_url),
                '--branch', str(current_branch),
                '--qa-input-file', str(result_input_path),
                '--persist-db',
            ]

        return {
            'ok': len(missing_fields) == 0,
            'repo_root': str(repo_root),
            'target_role': role_label,
            'result_family': result_family,
            'worktree_path': str(worktree_path),
            'branch_alignment': branch_alignment,
            'assignment_artifact': artifact,
            'required_context': required_context,
            'missing_fields': missing_fields,
            'result_input_contract': input_contract,
            'manual_result_surfaces': {
                'enter_worktree_command': entry['manual_execution_surfaces']['enter_worktree_command'],
                'assignment_json_command': entry['manual_execution_surfaces']['assignment_json_command'],
                'assignment_review_command': entry['manual_execution_surfaces']['assignment_review_command'],
                'result_input_template_path': str(result_input_path),
                'result_compile_command': ' '.join(result_compile_command),
                'producer_wrapper_path': str(producer_wrapper),
            },
            'role_entry': entry,
            'next_step_hint': 'prepare_role_result_input_and_compile_manually' if len(missing_fields) == 0 else 'resolve_missing_role_result_context',
        }

    def role_return_bridge(self, request: RuntimeRoleReturnBridgeRequest) -> dict[str, Any]:
        assist = self.role_result_assist(
            RuntimeRoleResultAssistRequest(
                repo_root=request.repo_root,
                package_id_external=request.package_id_external,
                brief_id_external=request.brief_id_external,
                project_slug=request.project_slug,
                target_role=request.target_role,
                lineage_view=request.lineage_view,
                role_branch=request.role_branch,
                worktree_path=request.worktree_path,
                assignment_path=request.assignment_path,
                review_output_path=request.assignment_review_output_path,
                result_input_path=request.result_input_path,
            )
        )
        if not assist.get('ok'):
            return {
                'ok': False,
                'reason': 'role_result_assist_failed',
                'details': 'Role return bridge requires a successful role-result assist context.',
                'assist': assist,
            }

        result_input_path = Path(assist['manual_result_surfaces']['result_input_template_path']).resolve()
        if not result_input_path.exists():
            return {
                'ok': False,
                'reason': 'result_input_missing',
                'details': f'No role result input file was found at {str(result_input_path)!r}.',
                'assist': assist,
                'result_input_path': str(result_input_path),
            }

        repo_root = request.repo_root.resolve()
        issue_number = assist['required_context']['issue_number']
        role_label = assist['target_role']
        default_output_path, default_review_output_path = self.default_result_packet_paths(repo_root, issue_number, role_label)
        output_path = request.output_path.resolve() if request.output_path else default_output_path.resolve()
        review_output_path = request.review_output_path.resolve() if request.review_output_path else default_review_output_path.resolve()

        compile_command = assist['manual_result_surfaces']['result_compile_command'].split()
        if role_label == 'Delivery Architect' or team_worker_role_by_display_name(role_label, repo_root=repo_root):
            result_input = load_json(result_input_path)
            result_type = result_input.get('result_type')
            if not result_type:
                return {
                    'ok': False,
                    'reason': 'result_type_missing',
                    'details': f'{role_label} return bridge requires result_input_file to include a top-level result_type.',
                    'assist': assist,
                    'result_input_path': str(result_input_path),
                }
            compile_command = [
                result_type if token in {'<delivery_result_type>', '<worker_result_type>'} else token
                for token in compile_command
            ]
        compile_command.extend(['--output', str(output_path), '--review-output', str(review_output_path)])
        code, compile_result, compile_error = self.run_json_with_errors(compile_command)
        if code != 0 or compile_result is None:
            return {
                'ok': False,
                'reason': 'result_compile_failed',
                'details': compile_error,
                'assist': assist,
                'compile_command': compile_command,
            }

        packet_path = Path(compile_result['output_path']).resolve()
        packet = load_json(packet_path)
        errors = validate_envelope(packet, require_authority=True)
        resolved_queue = resolve_packet_queue(packet, repo_root=repo_root)
        validate_result = {
            'ok': not errors,
            'message_file': str(packet_path),
            'message_id': packet.get('message_id'),
            'schema_type': packet.get('schema_type'),
            'resolved_queue': resolved_queue,
            'from_role': packet.get('from_role'),
            'to_role': packet.get('to_role'),
            'errors': errors,
        }
        if errors:
            return {
                'ok': False,
                'reason': 'result_packet_validation_failed',
                'details': 'Compiled role result packet failed envelope validation.',
                'assist': assist,
                'compile': compile_result,
                'validate': validate_result,
            }

        send_result = None
        source_assignment_ack = None
        if request.send:
            send_result = dispatch_packet(repo_root, packet_path)
            if not send_result.get('ok'):
                return {
                    'ok': False,
                    'reason': 'result_packet_send_failed',
                    'details': 'Compiled role result packet could not be sent through the queue runtime.',
                    'assist': assist,
                    'compile': compile_result,
                    'validate': validate_result,
                    'send': send_result,
                }
            assignment_artifact = assist.get('assignment_artifact') or {}
            source_assignment_message_id = assignment_artifact.get('message_id')
            source_assignment_path = assignment_artifact.get('path')
            source_assignment_queue = None
            if source_assignment_path:
                source_assignment_packet = load_json(Path(source_assignment_path).resolve())
                source_assignment_queue = resolve_packet_queue(source_assignment_packet, repo_root=repo_root)
            if source_assignment_message_id and source_assignment_queue:
                source_assignment_ack = self.acknowledge_source_assignment(
                    repo_root=repo_root,
                    message_id=str(source_assignment_message_id),
                    queue_name=str(source_assignment_queue),
                    claimed_by=f"{request.target_role}-role-return",
                )
                if not source_assignment_ack.get('ok'):
                    return {
                        'ok': False,
                        'reason': 'source_assignment_ack_failed',
                        'details': 'Role result packet was sent, but the source assignment packet could not be closed cleanly.',
                        'assist': assist,
                        'compile': compile_result,
                        'validate': validate_result,
                        'send': send_result,
                        'source_assignment_ack': source_assignment_ack,
                    }

        return {
            'ok': True,
            'repo_root': str(repo_root),
            'target_role': role_label,
            'result_family': assist['result_family'],
            'result_input_path': str(result_input_path),
            'output_path': str(packet_path),
            'review_output_path': str(review_output_path),
            'compile': compile_result,
            'validate': validate_result,
            'send': send_result,
            'source_assignment_ack': source_assignment_ack,
            'sent': bool(send_result and send_result.get('ok')),
            'resolved_queue': resolved_queue,
            'assist': assist,
            'next_step_hint': 'techlead_should_review_returned_result' if request.send else 'review_compiled_role_result_packet',
        }

    def acknowledge_source_assignment(self, *, repo_root: Path, message_id: str, queue_name: str, claimed_by: str) -> dict[str, Any]:
        claims_result = self._queue_admin_service.list_claims(repo_root=repo_root, queue=queue_name, status='claimed')
        claims_value = claims_result.get('claims', [])
        claims = [claim for claim in claims_value if isinstance(claim, dict)] if isinstance(claims_value, list) else []
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
    def default_result_input_path(repo_root: Path, issue_number: int, target_role: str) -> Path:
        slug = target_role.replace(' ', '-').lower()
        reports_dir = repo_root / '.project' / 'data' / 'paa' / 'reports'
        return reports_dir / f'role-result-input.issue{issue_number}.{slug}.json'

    @staticmethod
    def default_result_packet_paths(repo_root: Path, issue_number: int, target_role: str) -> tuple[Path, Path]:
        slug = target_role.replace(' ', '-').lower()
        reports_dir = repo_root / '.project' / 'data' / 'paa' / 'reports'
        if target_role == 'Delivery Architect':
            stem = f'delivery-review.issue{issue_number}.{slug}'
        elif team_worker_role_by_display_name(target_role, repo_root=repo_root):
            stem = f'worker-result.issue{issue_number}.{slug}'
        else:
            stem = f'qa-verification.issue{issue_number}.{slug}'
        return reports_dir / f'{stem}.json', reports_dir / f'{stem}.md'

    @staticmethod
    def run_json_with_errors(cmd: list[str]) -> tuple[int, dict[str, Any] | None, str | None]:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return result.returncode, None, result.stderr.strip() or result.stdout.strip() or f'command failed: {cmd}'
        return 0, json.loads(result.stdout), None


__all__ = [
    'DefaultRuntimeRoleBridgeService',
    'RuntimeRoleEntryRequest',
    'RuntimeRoleResultAssistRequest',
    'RuntimeRoleReturnBridgeRequest',
]

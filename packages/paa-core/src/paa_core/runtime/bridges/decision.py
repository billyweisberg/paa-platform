"""Core decision packet compile/validate/send bridge extracted from the legacy TechLead shell."""

from __future__ import annotations

from dataclasses import dataclass
import json
import subprocess
from pathlib import Path
from typing import Any

from paa_core.runtime.support.runtime_paths import repo_authority_manifest_path, repo_producer_bin
from paa_core.services.runtime_queue_admin import DefaultRuntimeQueueAdminService


@dataclass(frozen=True)
class RuntimeDecisionBridgeRequest:
    repo_root: Path
    project_slug: str
    package_id_external: str
    brief_id_external: str
    issue_number: int
    issue_url: str
    pr_number: int | None
    pr_url: str | None
    branch: str
    canonical_branch: str
    to_role: str
    decision_type: str
    decision_rationale: str
    work_item_status_update_intent: str
    source_packet_path: str
    branch_owner_role: str
    lineage_state: str
    lineage_action: str
    workflow_stage: str | None = None
    target_role_cli: str | None = None
    next_assignment_type: str | None = None
    role_branch: str | None = None
    superseded_branch: str | None = None
    worktree_hint: str | None = None
    reset_reason: str | None = None
    output_path: Path | None = None
    review_output_path: Path | None = None
    send: bool = False


class DefaultRuntimeDecisionBridgeService:
    def __init__(
        self,
        *,
        queue_admin_service: DefaultRuntimeQueueAdminService | None = None,
        authority_manifest_resolver=None,
        producer_bin_resolver=None,
    ) -> None:
        self._queue_admin_service = queue_admin_service or DefaultRuntimeQueueAdminService()
        self._authority_manifest_resolver = authority_manifest_resolver or repo_authority_manifest_path
        self._producer_bin_resolver = producer_bin_resolver or repo_producer_bin

    def emit_decision(self, request: RuntimeDecisionBridgeRequest) -> dict[str, Any]:
        if request.pr_number is None or request.pr_url is None:
            return {
                'ok': False,
                'workflow_stage': request.workflow_stage,
                'reason': 'decision_missing_pr_context',
                'details': 'TechLead decision emission requires PR context in this slice.',
            }

        repo_root = request.repo_root.resolve()
        output_stem = request.decision_type.replace('_', '-')
        reports_dir = repo_root / '.project' / 'data' / 'paa' / 'reports'
        output_path = (request.output_path or (reports_dir / f'techlead-decision.issue{request.issue_number}.{output_stem}.json')).resolve()
        review_output_path = (request.review_output_path or (reports_dir / f'techlead-decision.issue{request.issue_number}.{output_stem}.md')).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        review_output_path.parent.mkdir(parents=True, exist_ok=True)

        auth_script = self._producer_bin_resolver(repo_root)
        auth_current = self._authority_manifest_resolver(repo_root)
        compile_cmd = [
            str(auth_script),
            'authority',
            'materialize-techlead-decision-packet',
            '--manifest', str(auth_current),
            '--project-slug', request.project_slug,
            '--package-id-external', request.package_id_external,
            '--brief-id-external', request.brief_id_external,
            '--repo', self.github_repo_for_root(repo_root),
            '--issue-number', str(request.issue_number),
            '--issue-url', str(request.issue_url),
            '--pr-number', str(request.pr_number),
            '--pr-url', str(request.pr_url),
            '--branch', str(request.branch),
            '--canonical-branch', str(request.canonical_branch),
            '--to-role', request.to_role,
            '--decision-type', request.decision_type,
            '--decision-rationale', request.decision_rationale,
            '--work-item-status-update-intent', request.work_item_status_update_intent,
            '--source-packet-path', str(request.source_packet_path),
            '--branch-owner-role', request.branch_owner_role,
            '--lineage-state', request.lineage_state,
            '--lineage-action', request.lineage_action,
            '--source-branch', request.branch,
            '--output', str(output_path),
            '--review-output', str(review_output_path),
            '--persist-db',
        ]
        if request.target_role_cli:
            compile_cmd.extend(['--target-role', request.target_role_cli])
        if request.next_assignment_type:
            compile_cmd.extend(['--next-assignment-type', request.next_assignment_type])
        if request.role_branch:
            compile_cmd.extend(['--role-branch', str(request.role_branch)])
        if request.superseded_branch:
            compile_cmd.extend(['--superseded-branch', str(request.superseded_branch)])
        if request.worktree_hint:
            compile_cmd.extend(['--worktree-hint', str(request.worktree_hint)])
        if request.reset_reason:
            compile_cmd.extend(['--reset-reason', request.reset_reason])

        compile_result = self.run_json(compile_cmd)
        validate_result, validate_code = self._queue_admin_service.validate_packet(repo_root=repo_root, message_file=output_path)
        result = {
            'ok': validate_code == 0,
            'workflow_stage': request.workflow_stage,
            'derived_decision': {
                'decision_type': request.decision_type,
                'lineage_state': request.lineage_state,
                'lineage_action': request.lineage_action,
                'target_role': request.target_role_cli,
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
            'source_packet_path': request.source_packet_path,
        }
        if validate_code != 0:
            result['error'] = (validate_result or {}).get('errors')
            return result
        if request.send:
            send_result, send_code = self._queue_admin_service.send_packet(repo_root=repo_root, message_file=output_path)
            result['send'] = send_result
            result['sent'] = send_code == 0 and bool(send_result and send_result.get('ok'))
            if send_code != 0:
                result['ok'] = False
                result['error'] = send_result
        return result

    @staticmethod
    def run_json(cmd: list[str]) -> dict[str, Any]:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f'command failed: {cmd}')
        return json.loads(result.stdout)

    @staticmethod
    def github_repo_for_root(repo_root: Path) -> str:
        try:
            url = subprocess.check_output(['git', 'remote', 'get-url', 'origin'], cwd=repo_root, text=True).strip()
        except subprocess.CalledProcessError as exc:
            raise RuntimeError('Could not determine GitHub repo for decision emission.') from exc
        if url.startswith('git@github.com:'):
            repo = url.split(':', 1)[1]
        elif 'github.com/' in url:
            repo = url.split('github.com/', 1)[1]
        else:
            raise RuntimeError(f'Unsupported git remote format: {url!r}')
        if repo.endswith('.git'):
            repo = repo[:-4]
        return repo


__all__ = [
    'DefaultRuntimeDecisionBridgeService',
    'RuntimeDecisionBridgeRequest',
]

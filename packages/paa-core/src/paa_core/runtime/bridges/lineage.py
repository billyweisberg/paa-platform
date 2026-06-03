"""Core lineage view helpers extracted from the legacy TechLead shell."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, cast


@dataclass(frozen=True)
class RuntimeLineageRequest:
    repo_root: Path
    project_slug: str
    package_id_external: str
    brief_id_external: str


class DefaultRuntimeLineageService:
    def __init__(
        self,
        *,
        load_authority: Callable[[Path], tuple[dict[str, Any], dict[str, Any]]],
        load_design_package: Callable[[str, str], dict[str, Any]],
        resolve_issue_number_from_package: Callable[[dict[str, Any], str, str | None], int],
        resolve_task_summary: Callable[[dict[str, Any], dict[str, Any], int], dict[str, Any]],
        queue_state_loader: Callable[[Path], dict[str, Any]],
        local_decision_loader: Callable[[int, Path], dict[str, Any] | None],
        qa_packet_loader: Callable[[int, Path], dict[str, Any] | None],
        reports_dir_resolver: Callable[[Path], Path],
        packet_preview_loader: Callable[..., dict[str, Any] | None],
        github_state_loader: Callable[..., tuple[dict[str, Any], dict[str, Any] | None]],
        github_repo_resolver: Callable[[Path], str],
        workflow_deriver: Callable[[dict[str, Any] | None, dict[str, Any], dict[str, Any] | None, dict[str, Any] | None, dict[str, Any]], tuple[str, str, list[dict[str, Any]], list[dict[str, Any]], bool]],
        newest_packet: Callable[..., dict[str, Any] | None],
        target_role_for_branch: Callable[[str | None], str | None],
        default_role_worktree_path: Callable[[Path, str], Path],
        git_worktree_for_path: Callable[[Path, Path], dict[str, Any] | None],
        worktree_ownership_record: Callable[..., dict[str, Any] | None],
        worktree_staleness_assessment: Callable[[str | None, dict[str, Any] | None], dict[str, Any] | None],
    ) -> None:
        self._load_authority = load_authority
        self._load_design_package = load_design_package
        self._resolve_issue_number_from_package = resolve_issue_number_from_package
        self._resolve_task_summary = resolve_task_summary
        self._queue_state_loader = queue_state_loader
        self._local_decision_loader = local_decision_loader
        self._qa_packet_loader = qa_packet_loader
        self._reports_dir_resolver = reports_dir_resolver
        self._packet_preview_loader = packet_preview_loader
        self._github_state_loader = github_state_loader
        self._github_repo_resolver = github_repo_resolver
        self._workflow_deriver = workflow_deriver
        self._newest_packet = newest_packet
        self._target_role_for_branch = target_role_for_branch
        self._default_role_worktree_path = default_role_worktree_path
        self._git_worktree_for_path = git_worktree_for_path
        self._worktree_ownership_record = worktree_ownership_record
        self._worktree_staleness_assessment = worktree_staleness_assessment

    @staticmethod
    def _packet_payload(packet: dict[str, Any] | None) -> dict[str, Any]:
        payload = (packet or {}).get('payload')
        return cast(dict[str, Any], payload) if isinstance(payload, dict) else {}

    def build_lineage_view(self, request: RuntimeLineageRequest) -> dict[str, Any]:
        repo_root = request.repo_root.resolve()
        _current, manifest = self._load_authority(repo_root)
        package = self._load_design_package(request.project_slug, request.package_id_external)
        issue_number = self._resolve_issue_number_from_package(package, request.package_id_external, request.project_slug)
        current_task = self._resolve_task_summary(manifest, package, issue_number)
        queues = self._queue_state_loader(repo_root)
        reports_dir = self._reports_dir_resolver(repo_root)
        local_decision_packet = self._local_decision_loader(issue_number, reports_dir)
        qa_packet = self._qa_packet_loader(issue_number, reports_dir)
        fallback_packet = self._packet_preview_loader(queues, issue_number)
        issue, pr = self._github_state_loader(
            issue_number,
            self._github_repo_resolver(repo_root),
            fallback_pr_number=qa_packet.get('pr_number') if qa_packet else None,
            fallback_task=current_task,
            fallback_packet=fallback_packet,
        )
        workflow_stage, owner_role, escalations, recommended, unattended_safe = self._workflow_deriver(
            current_task, issue, pr, qa_packet, queues
        )
        lineage = self.derive_lineage_section(
            repo_root=repo_root,
            current_task=current_task,
            pr=pr,
            queues=queues,
            escalations=escalations,
            reports_dir=reports_dir,
        )
        workflow_stage, owner_role, recommended, unattended_safe = self.apply_terminal_lineage_override(
            local_decision_packet=local_decision_packet,
            queues=queues,
            issue=issue,
            pr=pr,
            workflow_stage=workflow_stage,
            owner_role=owner_role,
            recommended=recommended,
            unattended_safe=unattended_safe,
        )
        ambiguity_reasons: list[str] = []
        if lineage['current_packet_type'] is None and lineage['canonical_branch'] is None and not pr:
            ambiguity_reasons.append('no_lineage_packet_or_pr_context')
        return {
            'ok': len(ambiguity_reasons) == 0,
            'project_slug': request.project_slug,
            'package_id_external': request.package_id_external,
            'brief_id_external': request.brief_id_external,
            'issue_number': issue_number,
            'issue_url': issue.get('url'),
            'pr_number': pr.get('number') if pr else None,
            'pr_url': pr.get('url') if pr else None,
            'workflow_stage': workflow_stage,
            'current_owner_role': owner_role,
            'lineage': lineage,
            'source_packet_path': qa_packet.get('path') if qa_packet else None,
            'recommended_actions': recommended,
            'unattended_safe': unattended_safe,
            'ambiguity_reasons': ambiguity_reasons,
        }

    def derive_lineage_section(
        self,
        *,
        repo_root: Path,
        current_task: dict[str, Any] | None,
        pr: dict[str, Any] | None,
        queues: dict[str, Any],
        escalations: list[dict[str, Any]],
        reports_dir: Path,
    ) -> dict[str, Any]:
        issue_number = current_task['issue_number'] if current_task else None
        assignment_packet = self._packet_preview_loader(
            queues,
            issue_number,
            schema_type='techlead_assignment_packet',
        ) if issue_number else None
        decision_packet = self._packet_preview_loader(
            queues,
            issue_number,
            schema_type='techlead_decision_packet',
        ) if issue_number else None
        local_decision_packet = self._local_decision_loader(issue_number, reports_dir) if issue_number else None
        lineage_packet = self._newest_packet(decision_packet, assignment_packet, local_decision_packet)
        payload = self._packet_payload(lineage_packet)
        canonical_branch = cast(str | None, payload.get('canonical_branch')) or (cast(str | None, pr.get('headRefName')) if pr else None)
        role_branch = cast(str | None, payload.get('role_branch'))
        reset_required = any(e.get('event_type') in {'reset_branch_required', 'reset_branch_recommended'} for e in escalations)
        lineage_state = cast(str | None, payload.get('lineage_state'))
        if lineage_state is None:
            if reset_required:
                lineage_state = 'reset_required'
            elif canonical_branch:
                lineage_state = 'active'
            else:
                lineage_state = 'unknown'
        worktree_target_role = self._target_role_for_branch(role_branch)
        worktree_ownership = None
        if worktree_target_role and role_branch:
            worktree_path = self._default_role_worktree_path(repo_root, role_branch)
            worktree_entry = self._git_worktree_for_path(repo_root, worktree_path)
            worktree_ownership = self._worktree_ownership_record(
                repo_root,
                worktree_target_role,
                role_branch,
                worktree_path,
                worktree_entry=worktree_entry,
            )
        worktree_staleness = self._worktree_staleness_assessment(lineage_state, worktree_ownership)
        return {
            'canonical_branch': canonical_branch,
            'active_role_branch': role_branch,
            'branch_owner_role': cast(str | None, payload.get('branch_owner_role')) or ('TechLead' if lineage_packet else None),
            'lineage_state': lineage_state,
            'latest_lineage_action': cast(str | None, payload.get('lineage_action')),
            'source_branch': cast(str | None, payload.get('source_branch')),
            'superseded_branch': cast(str | None, payload.get('superseded_branch')),
            'worktree_hint': cast(str | None, payload.get('worktree_hint')),
            'reset_reason': cast(str | None, payload.get('reset_reason')),
            'current_packet_type': lineage_packet.get('schema_type') if lineage_packet else None,
            'current_packet_message_id': lineage_packet.get('message_id') if lineage_packet else None,
            'current_packet_queue': lineage_packet.get('queue_name') if lineage_packet else None,
            'worktree_ownership': worktree_ownership,
            'worktree_staleness': worktree_staleness,
        }

    @staticmethod
    def apply_terminal_lineage_override(
        *,
        local_decision_packet: dict[str, Any] | None,
        queues: dict[str, Any],
        issue: dict[str, Any] | None,
        pr: dict[str, Any] | None,
        workflow_stage: str,
        owner_role: str,
        recommended: list[dict[str, Any]],
        unattended_safe: bool,
    ) -> tuple[str, str, list[dict[str, Any]], bool]:
        if not local_decision_packet:
            return workflow_stage, owner_role, recommended, unattended_safe
        payload = DefaultRuntimeLineageService._packet_payload(local_decision_packet)
        if payload.get('lineage_state') != 'closed':
            return workflow_stage, owner_role, recommended, unattended_safe
        if any((queue_data.get('preview') or []) for queue_data in queues.values()):
            return workflow_stage, owner_role, recommended, unattended_safe
        latest_lineage_action = cast(str | None, payload.get('lineage_action'))
        if latest_lineage_action == 'proof_only_closed':
            return 'proof_only_closed', 'TechLead', [], True
        if pr and pr.get('mergedAt') and (issue and (issue.get('state') or '').upper() == 'CLOSED'):
            return 'techlead_decision_recorded', 'TechLead', [], True
        return workflow_stage, owner_role, recommended, unattended_safe


__all__ = [
    'DefaultRuntimeLineageService',
    'RuntimeLineageRequest',
]

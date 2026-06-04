"""Core next-assignment context derivation extracted from the legacy TechLead shell."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from paa_core.services.techlead_assignment_decision import (
    TechLeadAssignmentDecisionRequest,
    TechLeadAssignmentDecisionResult,
)
from paa_core.services.techlead_delivery_review_decision import (
    TechLeadDeliveryReviewDecisionRequest,
    TechLeadDeliveryReviewDecisionResult,
)
from paa_core.runtime.support.team_worker_roles import TeamWorkerRole


@dataclass(frozen=True)
class RuntimeAssignmentContextRequest:
    repo_root: Path
    project_slug: str
    package_id_external: str
    target_role: str | None = None


class DefaultRuntimeAssignmentContextService:
    def __init__(
        self,
        *,
        load_authority: Callable[[Path], tuple[dict[str, Any], dict[str, Any]]],
        github_repo_resolver: Callable[[Path], str],
        load_design_package: Callable[[str, str], dict[str, Any]],
        resolve_issue_number_from_package: Callable[[dict[str, Any], str, str], int],
        resolve_task_summary: Callable[[dict[str, Any], dict[str, Any], int], dict[str, Any]],
        queue_state_loader: Callable[[Path], dict[str, Any]],
        qa_packet_loader: Callable[[int, Path], dict[str, Any] | None],
        reports_dir_resolver: Callable[[Path], Path],
        packet_preview_loader: Callable[..., dict[str, Any] | None],
        github_state_loader: Callable[..., tuple[dict[str, Any], dict[str, Any] | None]],
        workflow_deriver: Callable[[dict[str, Any] | None, dict[str, Any], dict[str, Any] | None, dict[str, Any] | None, dict[str, Any]], tuple[str, str, list[dict[str, Any]], list[dict[str, Any]], bool]],
        team_worker_role_for_cli: Callable[[str | None, Path | None], TeamWorkerRole | None],
        team_worker_role_for_label: Callable[[str | None, Path | None], TeamWorkerRole | None],
        normalize_role_name: Callable[[str | None], str | None],
        assignment_decision_service,
        delivery_review_decision_service,
    ) -> None:
        self._load_authority = load_authority
        self._github_repo_resolver = github_repo_resolver
        self._load_design_package = load_design_package
        self._resolve_issue_number_from_package = resolve_issue_number_from_package
        self._resolve_task_summary = resolve_task_summary
        self._queue_state_loader = queue_state_loader
        self._qa_packet_loader = qa_packet_loader
        self._reports_dir_resolver = reports_dir_resolver
        self._packet_preview_loader = packet_preview_loader
        self._github_state_loader = github_state_loader
        self._workflow_deriver = workflow_deriver
        self._team_worker_role_for_cli = team_worker_role_for_cli
        self._team_worker_role_for_label = team_worker_role_for_label
        self._normalize_role_name = normalize_role_name
        self._assignment_decision_service = assignment_decision_service
        self._delivery_review_decision_service = delivery_review_decision_service

    def derive_next_assignment_context(self, request: RuntimeAssignmentContextRequest) -> dict[str, Any]:
        repo_root = request.repo_root.resolve()
        _current, manifest = self._load_authority(repo_root)
        github_repo = self._github_repo_resolver(repo_root)
        package = self._load_design_package(request.project_slug, request.package_id_external)
        issue_number = self._resolve_issue_number_from_package(package, request.package_id_external, request.project_slug)
        current_task = self._resolve_task_summary(manifest, package, issue_number)
        queues = self._queue_state_loader(repo_root)
        qa_packet = self._qa_packet_loader(issue_number, self._reports_dir_resolver(repo_root))
        fallback_packet = self._packet_preview_loader(queues, issue_number)
        issue, pr = self._github_state_loader(
            issue_number,
            github_repo,
            fallback_pr_number=qa_packet.get('pr_number') if qa_packet else None,
            fallback_task=current_task,
            fallback_packet=fallback_packet,
        )
        workflow_stage, _owner_role, _escalations, recommended, unattended_safe = self._workflow_deriver(
            current_task, issue, pr, qa_packet, queues
        )
        pending_dev_packet = self._packet_preview_loader(
            queues, issue_number, schema_type='slice_result_packet', to_role='techlead'
        )
        pending_worker_packet = self._packet_preview_loader(
            queues, issue_number, schema_type='worker_result_packet', to_role='techlead'
        )
        pending_delivery_review_packet = self._packet_preview_loader(
            queues, issue_number, schema_type='delivery_review_packet', to_role='techlead'
        )

        explicit_team_worker = self._team_worker_role_for_cli(request.target_role, repo_root) if request.target_role else None
        if request.target_role == 'delivery-architect':
            if not pr:
                return {
                    'ok': False,
                    'workflow_stage': workflow_stage,
                    'reason': 'explicit_delivery_architect_emission_requires_active_pr',
                    'details': 'No PR was available from GitHub state for the selected issue, so Delivery Architect emission could not derive PR context.',
                }
            branch_name = pr.get('headRefName') or f'issue-{issue_number}'
            return {
                'ok': True,
                'workflow_stage': workflow_stage,
                'issue_number': issue_number,
                'issue_url': issue.get('url'),
                'pr_number': pr.get('number'),
                'pr_url': pr.get('url'),
                'branch': branch_name,
                'target_role': 'Delivery Architect',
                'target_role_cli': 'delivery-architect',
                'assignment_type': 'delivery_architecture_review',
                'allowed_result_types': ['ready_for_dev', 'narrow_scope', 'reject_scope'],
                'assignment_summary': (
                    f'TechLead is explicitly issuing a Delivery Architect review assignment for issue #{issue_number} '
                    f'on branch {branch_name}.'
                ),
                'source_packet_message_id': None,
                'source_packet_path': None,
                'source_packet_queue': None,
                'issue': issue,
                'pr': pr,
                'recommended_actions': recommended,
                'unattended_safe': unattended_safe,
            }

        if explicit_team_worker:
            if not pr:
                return {
                    'ok': False,
                    'workflow_stage': workflow_stage,
                    'reason': 'explicit_team_worker_emission_requires_active_pr',
                    'details': (
                        'No PR was available from GitHub state for the selected issue, so '
                        f'{explicit_team_worker.display_name} emission could not derive PR context.'
                    ),
                }
            result = self._assignment_decision_service.derive_assignment_decision(
                self._build_assignment_decision_request(
                    issue_number=issue_number,
                    issue=issue,
                    pr=pr,
                    workflow_stage=workflow_stage,
                    source_packet=None,
                    explicit_target_role=request.target_role,
                    project_slug=request.project_slug,
                    recommended_actions=recommended,
                )
            )
            context = self._assignment_result_to_context(result=result, issue=issue, pr=pr)
            context['branch'] = pr.get('headRefName') or f'issue-{issue_number}'
            return context

        if workflow_stage in {'techlead_dev_review_pending', 'techlead_worker_review_pending'} and (pending_dev_packet or pending_worker_packet):
            if not pr:
                return {
                    'ok': False,
                    'workflow_stage': workflow_stage,
                    'reason': 'dev_review_pending_but_no_pr_context',
                    'details': 'A Dev result packet is waiting for TechLead, but no PR context could be derived from GitHub state.',
                }
            source_packet = pending_worker_packet or pending_dev_packet
            result = self._assignment_decision_service.derive_assignment_decision(
                self._build_assignment_decision_request(
                    issue_number=issue_number,
                    issue=issue,
                    pr=pr,
                    workflow_stage=workflow_stage,
                    source_packet=source_packet,
                    explicit_target_role=None,
                    project_slug=request.project_slug,
                    recommended_actions=recommended,
                )
            )
            context = self._assignment_result_to_context(result=result, issue=issue, pr=pr)
            context['branch'] = pr.get('headRefName') or f'issue-{issue_number}'
            return context

        if workflow_stage == 'techlead_delivery_review_pending' and pending_delivery_review_packet:
            if not pr:
                return {
                    'ok': False,
                    'workflow_stage': workflow_stage,
                    'reason': 'delivery_review_pending_but_no_pr_context',
                    'details': 'A Delivery Architect review packet is waiting for TechLead, but no PR context could be derived from GitHub state.',
                    'recommended_actions': recommended,
                    'unattended_safe': unattended_safe,
                }
            result = self._delivery_review_decision_service.derive_delivery_review_decision(
                self._build_delivery_review_decision_request(
                    current_task=current_task,
                    issue=issue,
                    pr=pr,
                    source_packet=pending_delivery_review_packet,
                    repo_root=repo_root,
                    project_slug=request.project_slug,
                )
            )
            return self._delivery_review_result_to_context(
                result=result,
                issue=issue,
                pr=pr,
                recommended_actions=recommended,
                unattended_safe=unattended_safe,
            )

        return {
            'ok': False,
            'workflow_stage': workflow_stage,
            'reason': 'no_supported_emission_available',
            'details': (
                f'Current workflow stage {workflow_stage!r} does not support next-assignment emission in this slice. '
                'Only techlead_worker_review_pending/techlead_dev_review_pending -> QA and explicit Team Worker Role or Delivery Architect emission are supported.'
            ),
            'recommended_actions': recommended,
            'unattended_safe': unattended_safe,
        }

    @staticmethod
    def _build_assignment_decision_request(
        *,
        issue_number: int,
        issue: dict[str, Any],
        pr: dict[str, Any] | None,
        workflow_stage: str,
        source_packet: dict[str, Any] | None,
        explicit_target_role: str | None,
        project_slug: str,
        recommended_actions: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None,
    ) -> TechLeadAssignmentDecisionRequest:
        branch_name = pr.get('headRefName') if pr else None
        return TechLeadAssignmentDecisionRequest(
            project_slug=project_slug,
            issue_number=issue_number,
            issue_url=issue.get('url'),
            pr_number=pr.get('number') if pr else None,
            pr_url=pr.get('url') if pr else None,
            branch_name=branch_name or (f'issue-{issue_number}' if pr else None),
            workflow_stage=workflow_stage,
            source_packet_schema_type=source_packet.get('schema_type') if source_packet else None,
            source_packet_message_id=source_packet.get('message_id') if source_packet else None,
            source_packet_queue_name=source_packet.get('queue_name') if source_packet else None,
            source_packet_path=source_packet.get('path') if source_packet else None,
            explicit_target_role=explicit_target_role,
            recommended_actions=tuple(
                str(item.get('action_type'))
                for item in (recommended_actions or ())
                if isinstance(item, dict) and item.get('action_type')
            ) or None,
        )

    @staticmethod
    def _assignment_result_to_context(
        *,
        result: TechLeadAssignmentDecisionResult,
        issue: dict[str, Any],
        pr: dict[str, Any] | None,
    ) -> dict[str, Any]:
        summary = result.summary
        context = {
            'ok': result.ok,
            'workflow_stage': result.workflow_stage,
            'issue_number': result.issue_number,
            'issue_url': result.issue_url,
            'pr_number': result.pr_number,
            'pr_url': result.pr_url,
            'branch': result.branch_name,
            'target_role': summary.target_role,
            'target_role_cli': summary.target_role_cli,
            'assignment_type': summary.assignment_type,
            'allowed_result_types': list(summary.allowed_result_types),
            'assignment_summary': summary.assignment_summary,
            'source_packet_message_id': result.source_packet_message_id,
            'source_packet_path': result.source_packet_path,
            'source_packet_queue': result.source_packet_queue_name,
            'source_packet_schema_type': result.source_packet_schema_type,
            'issue': issue,
            'pr': pr,
            'recommended_actions': list(result.recommended_actions or ()),
            'unattended_safe': result.unattended_safe,
            'decision_reason': summary.decision_reason,
        }
        if not result.ok:
            context.update({'reason': result.reason, 'details': result.details})
        return context

    def _build_delivery_review_decision_request(
        self,
        *,
        current_task: dict[str, Any] | None,
        issue: dict[str, Any] | None,
        pr: dict[str, Any] | None,
        source_packet: dict[str, Any],
        repo_root: Path,
        project_slug: str,
    ) -> TechLeadDeliveryReviewDecisionRequest:
        payload = source_packet.get('payload') or {}
        issue_number = (current_task or {}).get('issue_number') or 0
        recommended_action = payload.get('techlead_action_recommended') or {}
        if isinstance(recommended_action, dict):
            recommended_action_name = recommended_action.get('action')
            recommended_target_role = recommended_action.get('target_role')
            recommended_reason = recommended_action.get('reason')
        else:
            recommended_action_name = None
            recommended_target_role = None
            recommended_reason = None
        normalized_target_role = self._normalize_role_name(recommended_target_role)
        team_worker = self._team_worker_role_for_label(normalized_target_role, repo_root)
        branch_name = (
            (pr or {}).get('headRefName')
            or source_packet.get('github_context', {}).get('branch')
            or (payload.get('branch') or {}).get('name')
            or f'issue-{issue_number}'
        )
        source_assignment = payload.get('source_assignment_ref') or {}
        return TechLeadDeliveryReviewDecisionRequest(
            project_slug=project_slug,
            issue_number=issue_number,
            issue_url=(issue or {}).get('url'),
            pr_number=(pr or {}).get('number'),
            pr_url=(pr or {}).get('url'),
            workflow_stage='techlead_delivery_review_pending',
            delivery_review_result_type=payload.get('result_type') or '',
            recommended_action_name=recommended_action_name,
            recommended_target_role=recommended_target_role,
            recommended_reason=recommended_reason,
            resolved_team_worker_key=team_worker.key if team_worker else None,
            resolved_team_worker_display_name=team_worker.display_name if team_worker else None,
            source_packet_schema_type=source_packet.get('schema_type'),
            source_packet_message_id=source_packet.get('message_id'),
            source_packet_path=source_assignment.get('path'),
            branch_name=branch_name,
            metadata={
                'source_queue_name': source_packet.get('queue_name'),
                'normalized_target_role': normalized_target_role,
            },
        )

    @staticmethod
    def _delivery_review_result_to_context(
        *,
        result: TechLeadDeliveryReviewDecisionResult,
        issue: dict[str, Any] | None,
        pr: dict[str, Any] | None,
        recommended_actions: list[dict[str, Any]] | None,
        unattended_safe: bool,
    ) -> dict[str, Any]:
        if not result.ok:
            return {
                'ok': False,
                'workflow_stage': result.workflow_stage,
                'reason': result.reason,
                'details': result.details,
                'recommended_actions': recommended_actions,
                'unattended_safe': unattended_safe,
            }
        target_role = result.summary.recommended_target_role or result.resolved_team_worker_display_name
        target_role_cli = result.resolved_team_worker_key
        if target_role == 'QA':
            target_role_cli = 'qa'
        return {
            'ok': True,
            'workflow_stage': result.workflow_stage,
            'issue_number': result.issue_number,
            'issue_url': result.issue_url,
            'pr_number': result.pr_number,
            'pr_url': result.pr_url,
            'branch': result.branch_name,
            'target_role': target_role,
            'target_role_cli': target_role_cli,
            'assignment_type': 'delivery_architecture_review' if target_role == 'Delivery Architect' else 'implement_authorized_slice',
            'allowed_result_types': ['implemented_ready_for_qa', 'blocked', 'needs_clarification'] if target_role != 'Delivery Architect' else ['ready_for_dev', 'narrow_scope', 'reject_scope'],
            'assignment_summary': result.summary.delivery_review_summary,
            'source_packet_message_id': result.source_packet_message_id,
            'source_packet_path': result.source_packet_path,
            'source_packet_queue': (result.metadata or {}).get('source_queue_name'),
            'source_packet_schema_type': result.source_packet_schema_type,
            'issue': issue,
            'pr': pr,
            'recommended_actions': list(result.recommended_actions or recommended_actions or ()),
            'unattended_safe': result.unattended_safe if result.unattended_safe is not None else unattended_safe,
            'decision_reason': result.summary.recommended_next_decision,
        }


__all__ = [
    'DefaultRuntimeAssignmentContextService',
    'RuntimeAssignmentContextRequest',
]

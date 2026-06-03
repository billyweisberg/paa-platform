"""Core TechLead status/report orchestration extracted from the legacy shell."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, cast


@dataclass(frozen=True)
class RuntimeStatusReportRequest:
    repo_root: Path
    project_slug: str
    authority_version: str | None = None
    captured_by_role: str = 'TechLead'
    captured_by_agent_name: str = 'TechLead Agent'
    captured_by_agent_type: str = 'automation'


class DefaultRuntimeStatusReportService:
    def __init__(
        self,
        *,
        load_authority: Callable[[Path], tuple[dict[str, Any], dict[str, Any]]],
        queue_state_loader: Callable[[Path], dict[str, Any]],
        automation_state_loader: Callable[[Path], tuple[list[dict[str, Any]], bool]],
        mirror_status_loader: Callable[[str, Path], tuple[str, list[dict[str, Any]]]],
        qa_packet_loader: Callable[[int, Path], dict[str, Any] | None],
        reports_dir_resolver: Callable[[Path], Path],
        packet_preview_loader: Callable[..., dict[str, Any] | None],
        newest_packet_preview_loader: Callable[[dict[str, Any]], dict[str, Any] | None],
        issue_number_from_packet_preview: Callable[[dict[str, Any] | None], int | None],
        github_state_loader: Callable[..., tuple[dict[str, Any], dict[str, Any] | None]],
        github_repo_resolver: Callable[[Path], str],
        workflow_deriver: Callable[[dict[str, Any] | None, dict[str, Any], dict[str, Any] | None, dict[str, Any] | None, dict[str, Any]], tuple[str, str, list[dict[str, Any]], list[dict[str, Any]], bool]],
        local_decision_loader: Callable[[int, Path], dict[str, Any] | None],
        terminal_lineage_override: Callable[..., tuple[str, str, list[dict[str, Any]], bool]],
        lineage_view_builder: Callable[[Path, str, str, str], dict[str, Any]],
        derive_execution_state: Callable[[dict[str, Any], dict[str, Any] | None], str],
        derive_ci_status: Callable[[dict[str, Any] | None], str],
        runtime_queue_names: Callable[[Path], list[str]],
        traceability_loader: Callable[[str, int | None], dict[str, Any]],
    ) -> None:
        self._load_authority = load_authority
        self._queue_state_loader = queue_state_loader
        self._automation_state_loader = automation_state_loader
        self._mirror_status_loader = mirror_status_loader
        self._qa_packet_loader = qa_packet_loader
        self._reports_dir_resolver = reports_dir_resolver
        self._packet_preview_loader = packet_preview_loader
        self._newest_packet_preview_loader = newest_packet_preview_loader
        self._issue_number_from_packet_preview = issue_number_from_packet_preview
        self._github_state_loader = github_state_loader
        self._github_repo_resolver = github_repo_resolver
        self._workflow_deriver = workflow_deriver
        self._local_decision_loader = local_decision_loader
        self._terminal_lineage_override = terminal_lineage_override
        self._lineage_view_builder = lineage_view_builder
        self._derive_execution_state = derive_execution_state
        self._derive_ci_status = derive_ci_status
        self._runtime_queue_names = runtime_queue_names
        self._traceability_loader = traceability_loader

    @staticmethod
    def _packet_dict(packet: dict[str, Any] | None) -> dict[str, Any]:
        return packet if isinstance(packet, dict) else {}

    @staticmethod
    def _task_list(current: dict[str, Any]) -> list[dict[str, Any]]:
        tasks = current.get('tasks')
        if not isinstance(tasks, list):
            return []
        return [cast(dict[str, Any], task) for task in tasks if isinstance(task, dict)]

    def active_workflow_context(self, repo_root: Path, project_slug: str) -> dict[str, Any]:
        current, manifest = self._load_authority(repo_root)
        tasks = self._task_list(current)
        current_task = tasks[0] if tasks else None
        queues = self._queue_state_loader(repo_root)
        issue = None
        pr = None
        qa_packet = None
        workflow_stage = 'blocked'
        owner_role = 'Unknown'
        recommended_actions: list[dict[str, Any]] = []
        if current_task:
            reports_dir = self._reports_dir_resolver(repo_root)
            qa_packet = self._qa_packet_loader(current_task['issue_number'], reports_dir)
            fallback_pr_number = cast(int | None, qa_packet.get('pr_number')) if qa_packet else None
            fallback_packet = self._packet_preview_loader(queues, current_task['issue_number'])
            issue, pr = self._github_state_loader(
                current_task['issue_number'],
                self._github_repo_resolver(repo_root),
                fallback_pr_number=fallback_pr_number,
                fallback_task=current_task,
                fallback_packet=fallback_packet,
            )
            workflow_stage, owner_role, _escalations, recommended_actions, _unattended_safe = self._workflow_deriver(
                current_task,
                issue,
                pr,
                qa_packet,
                queues,
            )
            local_decision_packet = self._local_decision_loader(
                current_task['issue_number'],
                reports_dir,
            )
            workflow_stage, owner_role, recommended_actions, _unattended_safe = self._terminal_lineage_override(
                local_decision_packet=local_decision_packet,
                queues=queues,
                issue=issue,
                pr=pr,
                workflow_stage=workflow_stage,
                owner_role=owner_role,
                recommended=recommended_actions,
                unattended_safe=_unattended_safe,
            )
        return {
            'authority': current,
            'manifest': manifest,
            'current_task': current_task,
            'queues': queues,
            'issue': issue,
            'pr': pr,
            'qa_packet': qa_packet,
            'workflow_stage': workflow_stage,
            'owner_role': owner_role,
            'recommended_actions': recommended_actions,
            'project_slug': project_slug,
        }

    def build_report(self, request: RuntimeStatusReportRequest) -> dict[str, Any]:
        repo_root = request.repo_root.resolve()
        current, manifest = self._load_authority(repo_root)
        tasks = self._task_list(current)
        current_task = tasks[0] if tasks else None
        queues = self._queue_state_loader(repo_root)
        auto_roles, architect_missing = self._automation_state_loader(repo_root)
        authority_version = request.authority_version or manifest['project']['authority_version']
        authority_status, mirrors = self._mirror_status_loader(authority_version, repo_root)

        active_work = None
        escalations: list[dict[str, Any]] = []
        recommended: list[dict[str, Any]] = []
        unattended_safe = True
        workflow_stage = 'blocked'
        owner_role = 'Unknown'
        lineage = {
            'canonical_branch': None,
            'active_role_branch': None,
            'branch_owner_role': None,
            'lineage_state': 'unknown',
            'latest_lineage_action': None,
            'source_branch': None,
            'superseded_branch': None,
            'worktree_hint': None,
            'reset_reason': None,
            'current_packet_type': None,
            'current_packet_message_id': None,
            'current_packet_queue': None,
            'worktree_ownership': None,
            'worktree_staleness': None,
        }

        inferred_packet = self._newest_packet_preview_loader(queues)
        inferred_issue_number = self._issue_number_from_packet_preview(inferred_packet)
        report_task: dict[str, Any] | None = current_task
        if report_task is None and inferred_issue_number is not None:
            report_task = {
                'issue_number': inferred_issue_number,
                'task_id': f'queue-inferred-issue-{inferred_issue_number}',
                'title': f'Issue #{inferred_issue_number}',
                'status': 'in_progress',
            }

        if report_task:
            reports_dir = self._reports_dir_resolver(repo_root)
            qa_packet = self._qa_packet_loader(report_task['issue_number'], reports_dir)
            fallback_pr_number = cast(int | None, qa_packet.get('pr_number')) if qa_packet else None
            fallback_packet = self._packet_preview_loader(queues, report_task['issue_number']) or inferred_packet
            local_decision_packet = self._local_decision_loader(report_task['issue_number'], reports_dir)
            issue, pr = self._github_state_loader(
                report_task['issue_number'],
                self._github_repo_resolver(repo_root),
                fallback_pr_number=fallback_pr_number,
                fallback_task=report_task,
                fallback_packet=fallback_packet,
            )
            workflow_stage, owner_role, wf_escalations, wf_recommended, wf_safe = self._workflow_deriver(
                report_task,
                issue,
                pr,
                qa_packet,
                queues,
            )
            escalations.extend(wf_escalations)
            recommended.extend(wf_recommended)
            unattended_safe = unattended_safe and wf_safe

            brief_id_external = self._brief_id_external_for_report_task(current, report_task['issue_number'])
            if brief_id_external:
                lineage_view = self._lineage_view_builder(
                    repo_root,
                    request.project_slug,
                    current.get('package_id_external') or '',
                    brief_id_external,
                )
                lineage_candidate = lineage_view.get('lineage')
                if isinstance(lineage_candidate, dict):
                    lineage = cast(dict[str, Any], lineage_candidate)

            workflow_stage, owner_role, recommended, unattended_safe = self._terminal_lineage_override(
                local_decision_packet=local_decision_packet,
                queues=queues,
                issue=issue,
                pr=pr,
                workflow_stage=workflow_stage,
                owner_role=owner_role,
                recommended=recommended,
                unattended_safe=unattended_safe,
            )

            last_qa_verdict = cast(str | None, qa_packet.get('verification_status')) if qa_packet else 'unknown'
            superseded = any(e.get('event_type') == 'qa_escalation_superseded' for e in escalations)
            reset_required = any(e.get('event_type') in {'reset_branch_required', 'reset_branch_recommended'} for e in escalations)
            architect_rejected = any(e.get('event_type') == 'architect_rejection_recorded' for e in escalations)
            if reset_required:
                effective_verification_state = 'reset_required'
            elif architect_rejected:
                effective_verification_state = 'rework_required'
            elif superseded:
                effective_verification_state = 'awaiting_fresh_qa'
            elif last_qa_verdict in {'pass', 'needs_human_review', 'fail'}:
                effective_verification_state = last_qa_verdict
            else:
                effective_verification_state = 'unknown'
            qa_packet_dict = self._packet_dict(qa_packet)
            protected_path_checks = self._packet_dict(cast(dict[str, Any] | None, qa_packet_dict.get('protected_path_checks')))
            technical_scope_checks = self._packet_dict(cast(dict[str, Any] | None, qa_packet_dict.get('technical_scope_checks')))
            verification = {
                'protected_path': 'pass' if protected_path_checks.get('protected_10000_step_parity_passed') else 'unknown',
                'scope': 'fail' if technical_scope_checks.get('unauthorized_scope_widening') else ('pass' if qa_packet and qa_packet.get('verification_status') == 'pass' else 'unknown'),
                'last_qa_verdict': last_qa_verdict,
                'effective_verification_state': effective_verification_state,
                'qa_packet_path': cast(str | None, qa_packet_dict.get('path')),
            }

            active_work = {
                'work_item': {
                    'issue_number': report_task['issue_number'],
                    'task_id': report_task['task_id'],
                    'title': report_task['title'] if current_task else (issue.get('title') or report_task['title']),
                    'status': report_task['status'],
                    'authority_version': authority_version,
                },
                'execution': {
                    'pr_number': pr['number'] if pr else None,
                    'branch': pr['headRefName'] if pr else None,
                    'state': self._derive_execution_state(issue, pr),
                    'ci_status': self._derive_ci_status(pr),
                    'is_draft': bool(pr.get('isDraft')) if pr else None,
                },
                'verification': verification,
            }

        active_issue_number = ((active_work or {}).get('work_item') or {}).get('issue_number')
        traceability = self._traceability_loader(request.project_slug, active_issue_number)

        if authority_status != 'aligned':
            unattended_safe = False
            escalations.insert(0, {
                'event_type': 'stale_authority',
                'severity': 'high',
                'work_item_ref': {'issue_number': current_task['issue_number'], 'task_id': current_task['task_id']} if current_task else None,
                'summary': 'Authority mirrors are missing or stale relative to the published authority version.',
                'details': {'current_version': authority_version},
                'recommended_route': 'TechLead',
                'status': 'open',
            })
            recommended.insert(0, {
                'priority': 1,
                'action_type': 'republish_authority',
                'reason': 'Authority mirrors are not aligned.',
                'target_role': 'TechLead',
                'blocking': True,
            })

        if architect_missing:
            unattended_safe = False
            escalations.append({
                'event_type': 'hidden_automation',
                'severity': 'medium',
                'work_item_ref': None,
                'summary': 'Architect automation is missing on disk.',
                'details': {},
                'recommended_route': 'TechLead',
                'status': 'open',
            })

        captured_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
        return {
            'report_id': f'techlead-{captured_at}',
            'project_id': request.project_slug,
            'captured_at': captured_at,
            'captured_by': {
                'role': request.captured_by_role,
                'agent_name': request.captured_by_agent_name,
                'agent_type': request.captured_by_agent_type,
            },
            'authority': {
                'current_version': authority_version,
                'status': authority_status,
                'published_at': manifest['project'].get('published_at'),
                'source_ref': manifest['project'].get('published_from_branch'),
                'local_mirrors': mirrors,
            },
            'workflow': {
                'current_stage': workflow_stage,
                'last_successful_handoff': None,
                'current_owner_role': owner_role,
                'state_consistency': 'consistent' if authority_status == 'aligned' else 'recoverable',
            },
            'active_work': active_work,
            'queues': {
                q: {
                    'ready': queues[q]['messages_ready'],
                    'unacknowledged': queues[q]['messages_unacknowledged'],
                    'latest_message': self._newest_packet_preview_loader({q: queues[q]}),
                }
                for q in self._runtime_queue_names(repo_root)
            },
            'lineage': lineage,
            'automations': {'roles': auto_roles},
            'traceability': traceability,
            'escalations': escalations,
            'recommended_actions': recommended,
            'unattended_safe': unattended_safe,
            'summary': f"Current owner: {owner_role}. Authority {authority_status}. Unattended safe: {'yes' if unattended_safe else 'no'}.",
        }

    @staticmethod
    def _brief_id_external_for_report_task(current: dict[str, Any], issue_number: int) -> str | None:
        tasks = DefaultRuntimeStatusReportService._task_list(current)
        for task in tasks:
            if task.get('issue_number') == issue_number:
                return cast(str | None, task.get('brief_id_external'))
        return None


__all__ = [
    'DefaultRuntimeStatusReportService',
    'RuntimeStatusReportRequest',
]

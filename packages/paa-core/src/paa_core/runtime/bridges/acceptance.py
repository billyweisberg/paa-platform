"""Core QA acceptance/merge helpers extracted from the legacy TechLead shell."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


@dataclass(frozen=True)
class RuntimeAcceptanceRequest:
    repo_root: Path
    issue_number: int
    package_id_external: str
    brief_id_external: str
    project_slug: str
    merge_method: str = 'merge'
    issue_close_comment: str | None = None
    claimed_by: str = 'techlead-accept-and-merge'
    canonical_branch: str | None = None
    role_branch: str | None = None
    worktree_hint: str | None = None
    output_path: Path | None = None
    review_output_path: Path | None = None


class DefaultRuntimeAcceptanceService:
    def __init__(
        self,
        *,
        github_state_loader: Callable[..., tuple[dict[str, Any], dict[str, Any] | None]],
        merge_state_loader: Callable[[int, str], dict[str, Any]],
        merge_pr: Callable[[int, str, str], dict[str, Any]],
        close_issue: Callable[[int, str, str], dict[str, Any]],
        closeout_runner: Callable[[dict[str, Any]], dict[str, Any]],
        fallback_packet_loader: Callable[[Path, int], dict[str, Any] | None],
        github_repo_resolver: Callable[[Path], str],
        ci_status_deriver: Callable[[dict[str, Any]], str],
        qa_packet_loader: Callable[[int, Path], dict[str, Any] | None],
        reports_dir_resolver: Callable[[Path], Path],
    ) -> None:
        self._github_state_loader = github_state_loader
        self._merge_state_loader = merge_state_loader
        self._merge_pr = merge_pr
        self._close_issue = close_issue
        self._closeout_runner = closeout_runner
        self._fallback_packet_loader = fallback_packet_loader
        self._github_repo_resolver = github_repo_resolver
        self._ci_status_deriver = ci_status_deriver
        self._qa_packet_loader = qa_packet_loader
        self._reports_dir_resolver = reports_dir_resolver

    def accept_and_merge_qa_pass(self, request: RuntimeAcceptanceRequest) -> dict[str, Any]:
        repo_root = request.repo_root.resolve()
        qa_packet = self._qa_packet_loader(request.issue_number, self._reports_dir_resolver(repo_root))
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

        recommended_action = (qa_packet.get('recommended_action') or {})
        merge_recommendation = recommended_action.get('merge_recommendation')
        if merge_recommendation not in {'accept_and_merge', 'merge'}:
            return {
                'ok': False,
                'reason': 'qa_packet_not_accept_and_merge',
                'details': (
                    'TechLead acceptance requires a QA recommendation of '
                    f"`accept_and_merge` or `merge`; received {merge_recommendation!r}."
                ),
                'qa_packet': qa_packet,
            }

        fallback_packet = self._fallback_packet_loader(repo_root, request.issue_number)
        github_repo = self._github_repo_resolver(repo_root)
        issue_full, pr_full = self._github_state_loader(
            request.issue_number,
            github_repo,
            fallback_pr_number=qa_packet.get('pr_number'),
            fallback_task={'issue_number': request.issue_number, 'title': f'Issue #{request.issue_number}'},
            fallback_packet=fallback_packet,
        )
        if pr_full is None:
            return {
                'ok': False,
                'reason': 'pr_not_found',
                'details': f'No PR could be resolved for issue #{request.issue_number}.',
                'qa_packet': qa_packet,
                'github_state': {'issue_state': issue_full.get('state') if issue_full else None},
            }

        merge_state = self._merge_state_loader(int(pr_full['number']), github_repo)
        ci_status = self._ci_status_deriver(merge_state)
        pr_merged = bool(merge_state.get('mergedAt'))
        pr_open = (merge_state.get('state') or '').upper() == 'OPEN'
        if not pr_merged:
            if not pr_open:
                return {
                    'ok': False,
                    'reason': 'pr_not_open_for_merge',
                    'details': f"PR #{pr_full['number']} is not open and not merged.",
                    'qa_packet': qa_packet,
                    'pr': merge_state,
                }
            if merge_state.get('isDraft'):
                return {
                    'ok': False,
                    'reason': 'pr_is_draft',
                    'details': f"PR #{pr_full['number']} is still draft and cannot be accepted by TechLead.",
                    'qa_packet': qa_packet,
                    'pr': merge_state,
                }
            if ci_status != 'green':
                return {
                    'ok': False,
                    'reason': 'pr_checks_not_green',
                    'details': f"PR #{pr_full['number']} does not have green checks.",
                    'qa_packet': qa_packet,
                    'pr': merge_state,
                    'ci_status': ci_status,
                }
            if merge_state.get('mergeStateStatus') != 'CLEAN':
                return {
                    'ok': False,
                    'reason': 'pr_not_mergeable_cleanly',
                    'details': (
                        f"PR #{pr_full['number']} is not in CLEAN merge state; "
                        f"received {merge_state.get('mergeStateStatus')!r}."
                    ),
                    'qa_packet': qa_packet,
                    'pr': merge_state,
                }

        merge_result = {
            'ok': True,
            'already_merged': pr_merged,
            'merge_method': request.merge_method,
            'pr_number': pr_full['number'],
            'pr_url': pr_full.get('url'),
        }
        if not pr_merged:
            merge_result.update(self._merge_pr(int(pr_full['number']), github_repo, request.merge_method))
            if not merge_result.get('ok'):
                return {
                    'ok': False,
                    'reason': 'pr_merge_failed',
                    'details': f"TechLead could not merge PR #{pr_full['number']}.",
                    'qa_packet': qa_packet,
                    'pr': merge_state,
                    'merge': merge_result,
                }

        issue_after_merge, pr_after_merge = self._github_state_loader(
            request.issue_number,
            github_repo,
            fallback_pr_number=pr_full.get('number'),
            fallback_task={'issue_number': request.issue_number, 'title': f'Issue #{request.issue_number}'},
            fallback_packet=fallback_packet,
        )
        issue_close = {'ok': True, 'already_closed': (issue_after_merge.get('state') or '').upper() == 'CLOSED'}
        if not issue_close['already_closed']:
            issue_close.update(
                self._close_issue(
                    request.issue_number,
                    github_repo,
                    request.issue_close_comment or f'Closed by TechLead after QA pass and merge of PR #{pr_full["number"]}.',
                )
            )
            if not issue_close.get('ok'):
                return {
                    'ok': False,
                    'reason': 'issue_close_failed',
                    'details': f'TechLead merged the PR but could not close issue #{request.issue_number}.',
                    'qa_packet': qa_packet,
                    'merge': merge_result,
                    'issue_close': issue_close,
                }

        final_issue_state, final_pr_state = self._github_state_loader(
            request.issue_number,
            github_repo,
            fallback_pr_number=pr_full.get('number'),
            fallback_task={'issue_number': request.issue_number, 'title': f'Issue #{request.issue_number}'},
            fallback_packet=fallback_packet,
        )

        closeout_result = self._closeout_runner({
            'repo_root': repo_root,
            'package_id_external': request.package_id_external,
            'brief_id_external': request.brief_id_external,
            'project_slug': request.project_slug,
            'issue_number': request.issue_number,
            'send_decision': True,
            'ack_qa_packet': True,
            'claimed_by': request.claimed_by,
            'canonical_branch': request.canonical_branch,
            'role_branch': request.role_branch,
            'worktree_hint': request.worktree_hint,
            'output': request.output_path,
            'review_output': request.review_output_path,
        })
        if not closeout_result.get('ok'):
            return {
                'ok': False,
                'reason': 'closeout_after_merge_failed',
                'details': 'TechLead merged the PR but could not record the QA-pass closeout state.',
                'qa_packet': qa_packet,
                'merge': merge_result,
                'issue_close': issue_close,
                'github_state_after_merge': {
                    'issue_state': final_issue_state.get('state') if final_issue_state else None,
                    'issue_closed_at': final_issue_state.get('closedAt') if final_issue_state else None,
                    'pr_number': final_pr_state.get('number') if final_pr_state else None,
                    'pr_state': final_pr_state.get('state') if final_pr_state else None,
                    'pr_merged_at': final_pr_state.get('mergedAt') if final_pr_state else None,
                },
                'closeout': closeout_result,
            }

        return {
            'ok': True,
            'issue_number': request.issue_number,
            'merge': merge_result,
            'issue_close': issue_close,
            'github_state_after_merge': {
                'issue_state': final_issue_state.get('state') if final_issue_state else None,
                'issue_closed_at': final_issue_state.get('closedAt') if final_issue_state else None,
                'pr_number': final_pr_state.get('number') if final_pr_state else None,
                'pr_state': final_pr_state.get('state') if final_pr_state else None,
                'pr_merged_at': final_pr_state.get('mergedAt') if final_pr_state else None,
            },
            'closeout': closeout_result,
            'next_step_hint': 'run techlead-status to confirm closed lineage and empty spoke queues',
        }


__all__ = [
    'DefaultRuntimeAcceptanceService',
    'RuntimeAcceptanceRequest',
]

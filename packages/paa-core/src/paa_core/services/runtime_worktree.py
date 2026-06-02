"""Core branch/worktree orchestration for role execution surfaces."""

from __future__ import annotations

from dataclasses import dataclass
import os
import subprocess
from pathlib import Path
from typing import Any

from paa_core.claim_ledger import load_json
from paa_core.team_worker_roles import active_team_worker_roles


@dataclass(frozen=True)
class RuntimeWorktreeBranchRequest:
    repo_root: Path
    target_role: str
    lineage_view: dict[str, Any]
    action: str = 'ensure'
    canonical_branch: str | None = None
    role_branch: str | None = None


@dataclass(frozen=True)
class RuntimeWorktreePrepareRequest:
    repo_root: Path
    target_role: str
    lineage_view: dict[str, Any]
    branch_action: str = 'ensure'
    canonical_branch: str | None = None
    role_branch: str | None = None
    worktree_path: Path | None = None


@dataclass(frozen=True)
class RuntimeWorktreeInspectRequest:
    repo_root: Path
    target_role: str
    lineage_view: dict[str, Any]
    role_branch: str | None = None
    worktree_path: Path | None = None
    assignment_path: Path | None = None
    review_output_path: Path | None = None


@dataclass(frozen=True)
class RuntimeWorktreeCleanupRequest:
    repo_root: Path
    target_role: str
    lineage_view: dict[str, Any]
    ownership_view: dict[str, Any]
    stale_view: dict[str, Any]
    decision_result: dict[str, Any]
    superseded_branch: str | None = None


class DefaultRuntimeWorktreeService:
    _STATIC_ROLE_BRANCH_SUFFIX = {
        'delivery-architect': 'delivery',
        'qa': 'qa',
    }
    _STATIC_ROLE_LABEL_BY_CLI = {
        'delivery-architect': 'Delivery Architect',
        'qa': 'QA',
    }

    def prepare_role_branch(self, request: RuntimeWorktreeBranchRequest) -> dict[str, Any]:
        repo_root = request.repo_root.resolve()
        lineage_view = request.lineage_view
        if not lineage_view.get('ok'):
            return self._ambiguous_lineage_result(lineage_view)

        issue_number = int(lineage_view['issue_number'])
        lineage = lineage_view['lineage']
        canonical_branch = self.normalize_canonical_branch(
            repo_root=repo_root,
            issue_number=issue_number,
            lineage=lineage,
            explicit=request.canonical_branch,
        )
        role_branch = self.role_branch_name(
            issue_number=issue_number,
            target_role=request.target_role,
            explicit=request.role_branch,
            repo_root=repo_root,
        )
        source_ref, source_commit = self.resolve_canonical_source_ref(repo_root, canonical_branch)
        if source_ref is None or source_commit is None:
            return {
                'ok': False,
                'reason': 'canonical_branch_unresolved',
                'details': f'Could not resolve canonical branch {canonical_branch!r} locally or from origin.',
                'lineage_view': lineage_view,
                'canonical_branch': canonical_branch,
                'role_branch': role_branch,
            }

        branch_exists_before = self.git_local_branch_exists(repo_root, role_branch)
        branch_head_before = self.git_resolve_ref(repo_root, role_branch) if branch_exists_before else None
        checked_out_paths = self.git_branch_usage(repo_root, role_branch)
        mutation_required = (not branch_exists_before) or (branch_head_before != source_commit)

        if request.action == 'ensure' and branch_exists_before and branch_head_before != source_commit:
            return {
                'ok': False,
                'reason': 'role_branch_exists_with_different_tip',
                'details': (
                    f'Role branch {role_branch!r} already exists at a different commit. '
                    f'Use --action reset to realign it to {canonical_branch!r}.'
                ),
                'lineage_view': lineage_view,
                'canonical_branch': canonical_branch,
                'canonical_source_ref': source_ref,
                'canonical_source_commit': source_commit,
                'role_branch': role_branch,
                'branch_head_before': branch_head_before,
                'branch_checked_out_in': checked_out_paths,
            }

        if request.action == 'reset' and mutation_required and checked_out_paths:
            return {
                'ok': False,
                'reason': 'role_branch_checked_out_in_worktree',
                'details': f'Cannot reset role branch {role_branch!r} while it is checked out in an active worktree.',
                'lineage_view': lineage_view,
                'canonical_branch': canonical_branch,
                'canonical_source_ref': source_ref,
                'canonical_source_commit': source_commit,
                'role_branch': role_branch,
                'branch_head_before': branch_head_before,
                'branch_checked_out_in': checked_out_paths,
            }

        mutated = False
        created = False
        reset = False
        if request.action == 'ensure':
            if not branch_exists_before:
                self.run_text(['git', 'branch', role_branch, source_ref], cwd=repo_root)
                mutated = True
                created = True
        elif request.action == 'reset':
            if not branch_exists_before or branch_head_before != source_commit:
                self.run_text(['git', 'branch', '-f', role_branch, source_ref], cwd=repo_root)
                mutated = True
                created = not branch_exists_before
                reset = branch_exists_before

        branch_head_after = self.git_resolve_ref(repo_root, role_branch)
        return {
            'ok': branch_head_after == source_commit,
            'action': request.action,
            'repo_root': str(repo_root),
            'issue_number': issue_number,
            'workflow_stage': lineage_view.get('workflow_stage'),
            'target_role': request.target_role,
            'canonical_branch': canonical_branch,
            'canonical_source_ref': source_ref,
            'canonical_source_commit': source_commit,
            'role_branch': role_branch,
            'branch_owner_role': lineage.get('branch_owner_role') or 'TechLead',
            'worktree_hint': lineage.get('worktree_hint') or role_branch,
            'mutated': mutated,
            'created': created,
            'reset': reset,
            'branch_exists_before': branch_exists_before,
            'branch_head_before': branch_head_before,
            'branch_head_after': branch_head_after,
            'branch_checked_out_in': checked_out_paths,
            'lineage_view': lineage_view,
            'next_step_hint': 'create_or_reuse_worktree_for_role' if branch_head_after == source_commit else 'investigate_branch_alignment',
        }

    def prepare_role_worktree(self, request: RuntimeWorktreePrepareRequest) -> dict[str, Any]:
        repo_root = request.repo_root.resolve()
        branch_result = self.prepare_role_branch(
            RuntimeWorktreeBranchRequest(
                repo_root=repo_root,
                target_role=request.target_role,
                lineage_view=request.lineage_view,
                action=request.branch_action,
                canonical_branch=request.canonical_branch,
                role_branch=request.role_branch,
            )
        )
        if not branch_result.get('ok'):
            return {
                'ok': False,
                'reason': 'role_branch_prepare_failed',
                'details': 'Role worktree preparation requires a successful role-branch preparation result.',
                'branch_prepare': branch_result,
            }

        role_branch = branch_result['role_branch']
        requested_path = request.worktree_path.resolve() if request.worktree_path else self.default_role_worktree_path(repo_root, role_branch)
        existing_branch_worktree = self.git_worktree_for_branch(repo_root, role_branch)
        if existing_branch_worktree is not None:
            existing_path = Path(existing_branch_worktree['path']).resolve()
            if request.worktree_path and existing_path != requested_path:
                return {
                    'ok': False,
                    'reason': 'role_branch_checked_out_elsewhere',
                    'details': f'Role branch {role_branch!r} is already checked out in another worktree.',
                    'branch_prepare': branch_result,
                    'worktree_path': str(requested_path),
                    'existing_worktree_path': str(existing_path),
                }
            return self._reuse_worktree_result(
                repo_root=repo_root,
                target_role=request.target_role,
                role_branch=role_branch,
                worktree_path=existing_path,
                worktree_entry=existing_branch_worktree,
                branch_prepare=branch_result,
            )

        existing_path_worktree = self.git_worktree_for_path(repo_root, requested_path)
        if existing_path_worktree is not None:
            existing_branch = existing_path_worktree.get('branch')
            if existing_branch != role_branch:
                return {
                    'ok': False,
                    'reason': 'worktree_path_already_bound_to_different_branch',
                    'details': f'Worktree path {str(requested_path)!r} is already registered for another branch.',
                    'branch_prepare': branch_result,
                    'worktree_path': str(requested_path),
                    'existing_branch': existing_branch,
                }
            return self._reuse_worktree_result(
                repo_root=repo_root,
                target_role=request.target_role,
                role_branch=role_branch,
                worktree_path=requested_path,
                worktree_entry=existing_path_worktree,
                branch_prepare=branch_result,
            )

        if requested_path.exists():
            return {
                'ok': False,
                'reason': 'worktree_path_exists_not_registered',
                'details': f'Worktree path {str(requested_path)!r} already exists but is not registered as a git worktree for this repo.',
                'branch_prepare': branch_result,
                'worktree_path': str(requested_path),
            }

        requested_path.parent.mkdir(parents=True, exist_ok=True)
        self.run_text(['git', 'worktree', 'add', str(requested_path), role_branch], cwd=repo_root)
        created_worktree = self.git_worktree_for_path(repo_root, requested_path)
        return {
            'ok': created_worktree is not None,
            'action': 'create',
            'repo_root': str(repo_root),
            'target_role': request.target_role,
            'role_branch': role_branch,
            'worktree_path': str(requested_path),
            'worktree_head': created_worktree.get('head') if created_worktree else None,
            'worktree_ownership': self.worktree_ownership_record(
                repo_root=repo_root,
                target_role=request.target_role,
                role_branch=role_branch,
                worktree_path=requested_path,
                worktree_entry=created_worktree,
            ),
            'branch_prepare': branch_result,
            'created': True,
            'reused': False,
            'next_step_hint': 'enter_worktree_and_execute_role',
        }

    def inspect_role_worktree(self, request: RuntimeWorktreeInspectRequest) -> dict[str, Any]:
        repo_root = request.repo_root.resolve()
        lineage_view = request.lineage_view
        if not lineage_view.get('ok'):
            return self._ambiguous_lineage_result(lineage_view)

        issue_number = int(lineage_view['issue_number'])
        role_branch = self.role_branch_name(
            issue_number=issue_number,
            target_role=request.target_role,
            explicit=request.role_branch,
            repo_root=repo_root,
        )
        worktree_path = request.worktree_path.resolve() if request.worktree_path else self.default_role_worktree_path(repo_root, role_branch)
        worktree_entry = self.git_worktree_for_path(repo_root, worktree_path)
        if worktree_entry is None:
            return {
                'ok': False,
                'reason': 'worktree_not_registered',
                'details': f'No registered git worktree was found at {str(worktree_path)!r}.',
                'lineage_view': lineage_view,
                'role_branch': role_branch,
                'worktree_path': str(worktree_path),
            }

        checked_out_branch = worktree_entry.get('branch')
        if checked_out_branch != role_branch:
            return {
                'ok': False,
                'reason': 'worktree_branch_mismatch',
                'details': f'Worktree at {str(worktree_path)!r} is not checked out on the expected role branch.',
                'lineage_view': lineage_view,
                'role_branch': role_branch,
                'checked_out_branch': checked_out_branch,
                'worktree_path': str(worktree_path),
            }

        human_role = self.role_label_for_cli(request.target_role, repo_root=repo_root)
        assignment_path, review_output_path = self._resolved_assignment_paths(
            repo_root=repo_root,
            issue_number=issue_number,
            human_role=human_role,
            assignment_path=request.assignment_path,
            review_output_path=request.review_output_path,
        )
        if not assignment_path.exists():
            return {
                'ok': False,
                'reason': 'assignment_artifact_missing',
                'details': f'No assignment artifact was found at {str(assignment_path)!r}.',
                'lineage_view': lineage_view,
                'role_branch': role_branch,
                'worktree_path': str(worktree_path),
                'assignment_path': str(assignment_path),
            }

        packet = load_json(assignment_path)
        payload = packet.get('payload') or {}
        packet_target_role = payload.get('target_role')
        if packet_target_role != human_role:
            return {
                'ok': False,
                'reason': 'assignment_target_mismatch',
                'details': f'Assignment artifact target {packet_target_role!r} does not match the requested role {human_role!r}.',
                'lineage_view': lineage_view,
                'role_branch': role_branch,
                'worktree_path': str(worktree_path),
                'assignment_path': str(assignment_path),
                'packet_target_role': packet_target_role,
            }

        current_branch = self.git_current_branch(worktree_path)
        return {
            'ok': True,
            'repo_root': str(repo_root),
            'package_id_external': lineage_view.get('package_id_external'),
            'brief_id_external': lineage_view.get('brief_id_external'),
            'target_role': human_role,
            'role_branch': role_branch,
            'worktree_path': str(worktree_path),
            'current_branch': current_branch,
            'worktree_ownership': self.worktree_ownership_record(
                repo_root=repo_root,
                target_role=request.target_role,
                role_branch=role_branch,
                worktree_path=worktree_path,
                worktree_entry=worktree_entry,
            ),
            'assignment_artifact': {
                'path': str(assignment_path),
                'review_output_path': str(review_output_path),
                'message_id': packet.get('message_id'),
                'schema_type': packet.get('schema_type'),
                'assignment_type': payload.get('assignment_type'),
                'assignment_summary': payload.get('assignment_summary'),
                'allowed_result_types': payload.get('allowed_result_types') or [],
                'canonical_branch': payload.get('canonical_branch'),
                'role_branch': payload.get('role_branch'),
                'worktree_hint': payload.get('worktree_hint'),
            },
            'lineage_view': lineage_view,
            'next_step_hint': 'open_worktree_and_begin_role_execution_manually',
        }

    def worktree_ownership_view(
        self,
        *,
        repo_root: Path,
        target_role: str,
        lineage_view: dict[str, Any],
        role_branch: str | None = None,
        worktree_path: Path | None = None,
    ) -> dict[str, Any]:
        repo_root = repo_root.resolve()
        if not lineage_view.get('ok'):
            return self._ambiguous_lineage_result(lineage_view)

        issue_number = int(lineage_view['issue_number'])
        derived_role_branch = self.role_branch_name(
            issue_number=issue_number,
            target_role=target_role,
            explicit=role_branch,
            repo_root=repo_root,
        )
        resolved_worktree_path = worktree_path.resolve() if worktree_path else self.default_role_worktree_path(repo_root, derived_role_branch)
        worktree_entry = self.git_worktree_for_path(repo_root, resolved_worktree_path)
        ownership = self.worktree_ownership_record(
            repo_root=repo_root,
            target_role=target_role,
            role_branch=derived_role_branch,
            worktree_path=resolved_worktree_path,
            worktree_entry=worktree_entry,
        )
        return {
            'ok': True,
            'repo_root': str(repo_root),
            'package_id_external': lineage_view.get('package_id_external'),
            'brief_id_external': lineage_view.get('brief_id_external'),
            'issue_number': issue_number,
            'workflow_stage': lineage_view.get('workflow_stage'),
            'worktree_ownership': ownership,
            'worktree_staleness': self.worktree_staleness_assessment(
                (lineage_view.get('lineage') or {}).get('lineage_state'),
                ownership,
            ),
            'lineage_view': lineage_view,
            'next_step_hint': (
                'role_automation_may_prepare_or_reuse_its_owned_worktree'
                if not ownership.get('registered')
                else 'role_automation_may_enter_owned_worktree'
            ),
        }

    def worktree_stale_view(
        self,
        *,
        repo_root: Path,
        target_role: str,
        lineage_view: dict[str, Any],
        role_branch: str | None = None,
        worktree_path: Path | None = None,
    ) -> dict[str, Any]:
        ownership_view = self.worktree_ownership_view(
            repo_root=repo_root,
            target_role=target_role,
            lineage_view=lineage_view,
            role_branch=role_branch,
            worktree_path=worktree_path,
        )
        if not ownership_view.get('ok'):
            return ownership_view
        assessment = ownership_view.get('worktree_staleness')
        return {
            'ok': True,
            'repo_root': ownership_view.get('repo_root'),
            'package_id_external': ownership_view.get('package_id_external'),
            'brief_id_external': ownership_view.get('brief_id_external'),
            'issue_number': ownership_view.get('issue_number'),
            'workflow_stage': ownership_view.get('workflow_stage'),
            'worktree_ownership': ownership_view.get('worktree_ownership'),
            'worktree_staleness': assessment,
            'lineage_view': ownership_view.get('lineage_view'),
            'next_step_hint': assessment.get('recommended_action') if assessment else None,
        }

    def reset_required_lifecycle(self, request: RuntimeWorktreeCleanupRequest) -> dict[str, Any]:
        if request.target_role != 'python-team':
            return {
                'ok': False,
                'reason': 'unsupported_target_role_for_reset_required',
                'details': 'Phase H3 reset-required lifecycle mutation supports only python-team in this slice.',
                'target_role': request.target_role,
            }
        ownership_view = request.ownership_view
        stale_view = request.stale_view
        if not ownership_view.get('ok'):
            return {
                'ok': False,
                'reason': 'worktree_ownership_unavailable',
                'details': 'Reset-required lifecycle mutation requires a successful worktree ownership query.',
                'ownership_view': ownership_view,
            }
        if not stale_view.get('ok'):
            return {
                'ok': False,
                'reason': 'worktree_staleness_unavailable',
                'details': 'Reset-required lifecycle mutation requires a successful stale-worktree query.',
                'ownership_view': ownership_view,
                'stale_view': stale_view,
            }
        lineage_view = ownership_view.get('lineage_view') or request.lineage_view or {}
        workflow_stage = lineage_view.get('workflow_stage')
        if workflow_stage != 'dev_reset_required':
            return {
                'ok': False,
                'reason': 'reset_required_not_supported_for_current_stage',
                'details': 'Reset-required lifecycle mutation is only supported when the current workflow is dev_reset_required.',
                'workflow_stage': workflow_stage,
                'target_role': request.target_role,
                'ownership_view': ownership_view,
                'stale_view': stale_view,
            }
        decision_result = request.decision_result
        if not decision_result.get('ok'):
            return {
                'ok': False,
                'reason': 'reset_required_decision_failed',
                'details': 'Reset-required lifecycle mutation could not emit the underlying TechLead decision.',
                'workflow_stage': workflow_stage,
                'target_role': request.target_role,
                'ownership_view': ownership_view,
                'stale_view': stale_view,
                'decision_result': decision_result,
            }
        ownership = ownership_view.get('worktree_ownership') or {}
        staleness = dict(stale_view.get('worktree_staleness') or {})
        staleness['status'] = 'stale'
        staleness['stale'] = True
        staleness['cleanup_candidate'] = True
        reasons = list(staleness.get('reasons') or [])
        if 'lineage_state_reset_required' not in reasons:
            reasons.append('lineage_state_reset_required')
        staleness['reasons'] = reasons
        if not staleness.get('recommended_action'):
            staleness['recommended_action'] = 'investigate_and_cleanup_after_lifecycle_review'
        return {
            'ok': True,
            'workflow_stage': workflow_stage,
            'target_role': request.target_role,
            'canonical_branch': (lineage_view.get('lineage') or {}).get('canonical_branch'),
            'role_branch': ownership.get('role_branch'),
            'worktree_path': ownership.get('worktree_path'),
            'worktree_ownership': ownership,
            'worktree_staleness': staleness,
            'decision_result': decision_result,
            'cleanup_candidate': True,
            'next_step_hint': 'record_reset_required_and_preserve_worktree_for_later_cleanup',
            'lineage_view': lineage_view,
        }

    def reset_cleanup(self, request: RuntimeWorktreeCleanupRequest) -> dict[str, Any]:
        lifecycle = self.reset_required_lifecycle(request)
        if not lifecycle.get('ok'):
            return {
                'ok': False,
                'reason': 'reset_required_lifecycle_unavailable',
                'details': 'Physical reset cleanup requires a successful reset-required lifecycle mutation result.',
                'lifecycle': lifecycle,
            }
        ownership = lifecycle.get('worktree_ownership') or {}
        staleness = lifecycle.get('worktree_staleness') or {}
        worktree_path_value = ownership.get('worktree_path')
        default_path_value = ownership.get('default_worktree_path')
        role_branch = ownership.get('role_branch')
        if not ownership.get('registered'):
            return {
                'ok': False,
                'reason': 'reset_cleanup_requires_registered_worktree',
                'details': 'Physical reset cleanup only runs when the owned role worktree is currently registered.',
                'lifecycle': lifecycle,
            }
        if not staleness.get('stale') or not staleness.get('cleanup_candidate'):
            return {
                'ok': False,
                'reason': 'reset_cleanup_requires_stale_cleanup_candidate',
                'details': 'Physical reset cleanup only runs when stale detection marks the worktree as a cleanup candidate.',
                'lifecycle': lifecycle,
            }
        if not worktree_path_value or not default_path_value:
            return {
                'ok': False,
                'reason': 'reset_cleanup_missing_worktree_path',
                'details': 'Physical reset cleanup requires a concrete owned worktree path.',
                'lifecycle': lifecycle,
            }
        worktree_path = Path(worktree_path_value).resolve()
        default_worktree_path = Path(default_path_value).resolve()
        if worktree_path != default_worktree_path:
            return {
                'ok': False,
                'reason': 'reset_cleanup_requires_default_owned_worktree_path',
                'details': 'Physical reset cleanup only runs against the deterministic owned worktree path in this slice.',
                'lifecycle': lifecycle,
            }
        entry_before = self.git_worktree_for_path(request.repo_root.resolve(), worktree_path)
        if entry_before is None:
            return {
                'ok': False,
                'reason': 'reset_cleanup_requires_registered_worktree_entry',
                'details': 'The owned worktree is no longer registered; refusing to run physical cleanup against an ambiguous state.',
                'lifecycle': lifecycle,
            }
        code, _stdout, error = self.run_text_with_errors(['git', 'worktree', 'remove', str(worktree_path)], cwd=request.repo_root.resolve())
        if code != 0:
            return {
                'ok': False,
                'reason': 'git_worktree_remove_failed',
                'details': 'git worktree remove did not complete successfully.',
                'cleanup_candidate': True,
                'worktree_path': str(worktree_path),
                'role_branch': role_branch,
                'prior_worktree_ownership': ownership,
                'prior_worktree_staleness': staleness,
                'decision_result': lifecycle.get('decision_result'),
                'git_error': error,
            }
        entry_after = self.git_worktree_for_path(request.repo_root.resolve(), worktree_path)
        branch_preserved = bool(role_branch and self.git_local_branch_exists(request.repo_root.resolve(), role_branch))
        return {
            'ok': True,
            'workflow_stage': lifecycle.get('workflow_stage'),
            'target_role': request.target_role,
            'canonical_branch': lifecycle.get('canonical_branch'),
            'role_branch': role_branch,
            'worktree_path': str(worktree_path),
            'cleanup_performed': entry_after is None,
            'cleanup_result': {
                'command': ['git', 'worktree', 'remove', str(worktree_path)],
                'worktree_removed': entry_after is None,
                'worktree_still_registered': entry_after is not None,
                'branch_preserved': branch_preserved,
            },
            'prior_worktree_ownership': ownership,
            'prior_worktree_staleness': staleness,
            'decision_result': lifecycle.get('decision_result'),
            'next_step_hint': (
                'prepare_fresh_role_worktree_before_next_python_run'
                if entry_after is None
                else 'investigate_remaining_registered_worktree_state'
            ),
            'lineage_view': lifecycle.get('lineage_view'),
        }

    def superseded_cleanup(self, request: RuntimeWorktreeCleanupRequest) -> dict[str, Any]:
        return self._cleanup_for_lineage_state(
            request=request,
            expected_lineage_state='superseded',
            unsupported_reason='unsupported_target_role_for_superseded_cleanup',
            unsupported_details='Phase H5 superseded cleanup supports only python-team in this slice.',
            decision_failed_reason='superseded_decision_failed',
            decision_failed_details='Superseded cleanup could not emit the underlying TechLead decision.',
            requires_registered_reason='superseded_cleanup_requires_registered_worktree',
            requires_registered_details='Superseded cleanup only runs when the owned role worktree is currently registered.',
            requires_stale_reason='superseded_cleanup_requires_stale_cleanup_candidate',
            requires_stale_details='Superseded cleanup only runs when stale detection marks the worktree as a cleanup candidate.',
            missing_path_reason='superseded_cleanup_missing_worktree_path',
            missing_path_details='Superseded cleanup requires a concrete owned worktree path.',
            default_path_reason='superseded_cleanup_requires_default_owned_worktree_path',
            default_path_details='Superseded cleanup only runs against the deterministic owned worktree path in this slice.',
            entry_reason='superseded_cleanup_requires_registered_worktree_entry',
            entry_details='The owned worktree is no longer registered; refusing to run physical cleanup against an ambiguous state.',
            next_step_hint='prepare_replacement_role_worktree_only_if_new_assignment_requires_it',
            preserved_flags=('branch_preserved',),
            preserved_values=lambda role_branch, canonical_branch, request: {
                'branch_preserved': bool(
                    (request.superseded_branch or role_branch)
                    and self.git_local_branch_exists(request.repo_root.resolve(), request.superseded_branch or role_branch)
                )
            },
        )

    def closed_cleanup(self, request: RuntimeWorktreeCleanupRequest) -> dict[str, Any]:
        return self._cleanup_for_lineage_state(
            request=request,
            expected_lineage_state='closed',
            unsupported_reason='unsupported_target_role_for_closed_cleanup',
            unsupported_details='Phase H6 closed cleanup supports only python-team in this slice.',
            decision_failed_reason='closed_decision_failed',
            decision_failed_details='Closed cleanup could not emit the underlying TechLead decision.',
            requires_registered_reason='closed_cleanup_requires_registered_worktree',
            requires_registered_details='Closed cleanup only runs when the owned role worktree is currently registered.',
            requires_stale_reason='closed_cleanup_requires_stale_cleanup_candidate',
            requires_stale_details='Closed cleanup only runs when stale detection marks the worktree as a cleanup candidate.',
            missing_path_reason='closed_cleanup_missing_worktree_path',
            missing_path_details='Closed cleanup requires a concrete owned worktree path.',
            default_path_reason='closed_cleanup_requires_default_owned_worktree_path',
            default_path_details='Closed cleanup only runs against the deterministic owned worktree path in this slice.',
            entry_reason='closed_cleanup_requires_registered_worktree_entry',
            entry_details='The owned worktree is no longer registered; refusing to run physical cleanup against an ambiguous state.',
            next_step_hint='retain_closed_lineage_branches_for_audit_until_explicit_retirement_policy_exists',
            preserved_flags=('role_branch_preserved', 'canonical_branch_preserved'),
            preserved_values=lambda role_branch, canonical_branch, request: {
                'role_branch_preserved': bool(role_branch and self.git_local_branch_exists(request.repo_root.resolve(), role_branch)),
                'canonical_branch_preserved': bool(canonical_branch and self.git_local_branch_exists(request.repo_root.resolve(), canonical_branch)),
            },
        )

    @classmethod
    def role_branch_name(cls, *, issue_number: int, target_role: str, explicit: str | None, repo_root: Path) -> str:
        if explicit:
            return explicit
        suffix = cls._role_branch_suffix(target_role, repo_root=repo_root)
        return f'issue-{issue_number}-{suffix}'

    @classmethod
    def role_label_for_cli(cls, target_role: str, *, repo_root: Path) -> str:
        worker_roles = {role.key: role.display_name for role in active_team_worker_roles(repo_root=repo_root)}
        return worker_roles.get(target_role) or cls._STATIC_ROLE_LABEL_BY_CLI[target_role]

    @staticmethod
    def default_role_worktree_root(repo_root: Path) -> Path:
        override = os.environ.get('PAA_ROLE_WORKTREE_ROOT')
        if override:
            return Path(override).expanduser().resolve()
        return (repo_root / '.codex-work' / 'worktrees' / 'paa').resolve()

    @classmethod
    def default_role_worktree_path(cls, repo_root: Path, role_branch: str) -> Path:
        return cls.default_role_worktree_root(repo_root) / role_branch

    @staticmethod
    def default_assignment_paths(repo_root: Path, issue_number: int, target_role: str) -> tuple[Path, Path]:
        slug = target_role.replace(' ', '-').lower()
        reports_dir = repo_root / '.project' / 'data' / 'paa' / 'reports'
        output = reports_dir / f'techlead-assignment.issue{issue_number}.{slug}.json'
        review = reports_dir / f'techlead-assignment.issue{issue_number}.{slug}.md'
        return output, review

    @classmethod
    def normalize_canonical_branch(
        cls,
        *,
        repo_root: Path,
        issue_number: int,
        lineage: dict[str, Any],
        explicit: str | None,
    ) -> str:
        if explicit:
            return explicit
        preferred = f'issue-{issue_number}'
        if cls.git_local_branch_exists(repo_root, preferred) or cls.git_remote_branch_exists(repo_root, preferred):
            return preferred
        lineage_branch = lineage.get('canonical_branch')
        if lineage_branch:
            return str(lineage_branch)
        return preferred

    @staticmethod
    def git_local_branch_exists(repo_root: Path, branch_name: str) -> bool:
        return subprocess.run(
            ['git', 'show-ref', '--verify', '--quiet', f'refs/heads/{branch_name}'],
            cwd=str(repo_root),
        ).returncode == 0

    @staticmethod
    def git_remote_branch_exists(repo_root: Path, branch_name: str) -> bool:
        return subprocess.run(
            ['git', 'show-ref', '--verify', '--quiet', f'refs/remotes/origin/{branch_name}'],
            cwd=str(repo_root),
        ).returncode == 0

    @staticmethod
    def git_resolve_ref(repo_root: Path, ref_name: str) -> str | None:
        code, stdout, _error = DefaultRuntimeWorktreeService.run_text_with_errors(['git', 'rev-parse', '--verify', ref_name], cwd=repo_root)
        if code != 0 or stdout is None:
            return None
        return stdout.strip()

    @classmethod
    def resolve_canonical_source_ref(cls, repo_root: Path, canonical_branch: str) -> tuple[str | None, str | None]:
        if cls.git_fetch_branch(repo_root, canonical_branch) and cls.git_remote_branch_exists(repo_root, canonical_branch):
            remote_ref = f'origin/{canonical_branch}'
            return remote_ref, cls.git_resolve_ref(repo_root, remote_ref)
        if cls.git_remote_branch_exists(repo_root, canonical_branch):
            remote_ref = f'origin/{canonical_branch}'
            return remote_ref, cls.git_resolve_ref(repo_root, remote_ref)
        if cls.git_local_branch_exists(repo_root, canonical_branch):
            return canonical_branch, cls.git_resolve_ref(repo_root, canonical_branch)
        return None, None

    @staticmethod
    def git_fetch_branch(repo_root: Path, branch_name: str) -> bool:
        code, _stdout, _error = DefaultRuntimeWorktreeService.run_text_with_errors(['git', 'fetch', 'origin', branch_name], cwd=repo_root)
        return code == 0

    @staticmethod
    def git_branch_usage(repo_root: Path, branch_name: str) -> list[str]:
        code, stdout, _error = DefaultRuntimeWorktreeService.run_text_with_errors(['git', 'worktree', 'list', '--porcelain'], cwd=repo_root)
        if code != 0 or stdout is None:
            return []
        usages: list[str] = []
        current_worktree = None
        for raw_line in stdout.splitlines():
            line = raw_line.strip()
            if not line:
                current_worktree = None
                continue
            if line.startswith('worktree '):
                current_worktree = line.split(' ', 1)[1]
                continue
            if line.startswith('branch refs/heads/') and current_worktree:
                checked_out = line.removeprefix('branch refs/heads/')
                if checked_out == branch_name:
                    usages.append(current_worktree)
        return usages

    @staticmethod
    def git_worktree_entries(repo_root: Path) -> list[dict[str, Any]]:
        code, stdout, _error = DefaultRuntimeWorktreeService.run_text_with_errors(['git', 'worktree', 'list', '--porcelain'], cwd=repo_root)
        if code != 0 or stdout is None:
            return []
        entries: list[dict[str, Any]] = []
        current: dict[str, Any] | None = None
        for raw_line in stdout.splitlines():
            line = raw_line.strip()
            if not line:
                if current:
                    entries.append(current)
                current = None
                continue
            if line.startswith('worktree '):
                if current:
                    entries.append(current)
                current = {'path': line.split(' ', 1)[1], 'branch': None, 'head': None, 'detached': False}
                continue
            if current is None:
                continue
            if line.startswith('HEAD '):
                current['head'] = line.split(' ', 1)[1]
            elif line.startswith('branch refs/heads/'):
                current['branch'] = line.removeprefix('branch refs/heads/')
            elif line == 'detached':
                current['detached'] = True
        if current:
            entries.append(current)
        return entries

    @classmethod
    def git_worktree_for_branch(cls, repo_root: Path, branch_name: str) -> dict[str, Any] | None:
        for entry in cls.git_worktree_entries(repo_root):
            if entry.get('branch') == branch_name:
                return entry
        return None

    @classmethod
    def git_worktree_for_path(cls, repo_root: Path, worktree_path: Path) -> dict[str, Any] | None:
        target = str(worktree_path.resolve())
        for entry in cls.git_worktree_entries(repo_root):
            if Path(entry['path']).resolve().as_posix() == Path(target).as_posix():
                return entry
        return None

    @staticmethod
    def git_current_branch(repo_root: Path) -> str | None:
        code, stdout, _error = DefaultRuntimeWorktreeService.run_text_with_errors(['git', 'symbolic-ref', '--short', 'HEAD'], cwd=repo_root)
        if code != 0 or stdout is None:
            return None
        return stdout.strip()

    @classmethod
    def worktree_ownership_record(
        cls,
        *,
        repo_root: Path,
        target_role: str,
        role_branch: str,
        worktree_path: Path,
        worktree_entry: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        entry = worktree_entry or cls.git_worktree_for_path(repo_root, worktree_path)
        checked_out_branch = entry.get('branch') if entry else None
        return {
            'ownership_model': 'role_automation_self_service',
            'lineage_owner_role': 'TechLead',
            'runtime_owner_role': cls.role_label_for_cli(target_role, repo_root=repo_root),
            'runtime_owner_role_cli': target_role,
            'admin_surface_role': 'TechLead',
            'ownership_source': 'deterministic_role_worktree_contract',
            'role_branch': role_branch,
            'worktree_path': str(worktree_path),
            'default_worktree_path': str(cls.default_role_worktree_path(repo_root, role_branch)),
            'uses_default_worktree_path': worktree_path.resolve() == cls.default_role_worktree_path(repo_root, role_branch).resolve(),
            'registered': entry is not None,
            'checked_out_branch': checked_out_branch,
            'branch_aligned': checked_out_branch == role_branch if checked_out_branch is not None else None,
            'worktree_head': entry.get('head') if entry else None,
        }

    @staticmethod
    def worktree_staleness_assessment(lineage_state: str | None, ownership: dict[str, Any] | None) -> dict[str, Any] | None:
        if ownership is None:
            return None
        reasons: list[str] = []
        warnings: list[str] = []
        registered = bool(ownership.get('registered'))
        branch_aligned = ownership.get('branch_aligned')
        uses_default_path = bool(ownership.get('uses_default_worktree_path'))
        if not uses_default_path:
            warnings.append('nondefault_worktree_path')
        if not registered:
            return {
                'status': 'absent',
                'stale': False,
                'cleanup_candidate': False,
                'reasons': reasons,
                'warnings': warnings,
                'recommended_action': 'prepare_or_reuse_worktree_when_role_runs',
            }
        if branch_aligned is False:
            reasons.append('registered_worktree_branch_mismatch')
        if lineage_state in {'reset_required', 'superseded', 'closed'}:
            reasons.append(f'lineage_state_{lineage_state}')
        stale = len(reasons) > 0
        return {
            'status': 'stale' if stale else 'active',
            'stale': stale,
            'cleanup_candidate': stale,
            'reasons': reasons,
            'warnings': warnings,
            'recommended_action': (
                'investigate_and_cleanup_after_lifecycle_review'
                if stale
                else 'keep_registered_for_role_execution'
            ),
        }

    @staticmethod
    def run_text(cmd: list[str], cwd: Path | None = None) -> str:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(cwd) if cwd else None)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f'command failed: {cmd}')
        return result.stdout

    @staticmethod
    def run_text_with_errors(cmd: list[str], cwd: Path | None = None) -> tuple[int, str | None, str | None]:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(cwd) if cwd else None)
        if result.returncode != 0:
            return result.returncode, None, result.stderr.strip() or result.stdout.strip() or f'command failed: {cmd}'
        return 0, result.stdout, None

    @classmethod
    def _role_branch_suffix(cls, target_role: str, *, repo_root: Path) -> str:
        worker_roles = {role.key: role.branch_suffix for role in active_team_worker_roles(repo_root=repo_root)}
        if target_role in worker_roles:
            return worker_roles[target_role]
        return cls._STATIC_ROLE_BRANCH_SUFFIX[target_role]

    def _reuse_worktree_result(
        self,
        *,
        repo_root: Path,
        target_role: str,
        role_branch: str,
        worktree_path: Path,
        worktree_entry: dict[str, Any],
        branch_prepare: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            'ok': True,
            'action': 'reuse',
            'repo_root': str(repo_root),
            'target_role': target_role,
            'role_branch': role_branch,
            'worktree_path': str(worktree_path),
            'worktree_head': worktree_entry.get('head'),
            'worktree_ownership': self.worktree_ownership_record(
                repo_root=repo_root,
                target_role=target_role,
                role_branch=role_branch,
                worktree_path=worktree_path,
                worktree_entry=worktree_entry,
            ),
            'branch_prepare': branch_prepare,
            'created': False,
            'reused': True,
            'next_step_hint': 'enter_worktree_and_execute_role',
        }

    def _cleanup_for_lineage_state(
        self,
        *,
        request: RuntimeWorktreeCleanupRequest,
        expected_lineage_state: str,
        unsupported_reason: str,
        unsupported_details: str,
        decision_failed_reason: str,
        decision_failed_details: str,
        requires_registered_reason: str,
        requires_registered_details: str,
        requires_stale_reason: str,
        requires_stale_details: str,
        missing_path_reason: str,
        missing_path_details: str,
        default_path_reason: str,
        default_path_details: str,
        entry_reason: str,
        entry_details: str,
        next_step_hint: str,
        preserved_flags: tuple[str, ...],
        preserved_values,
    ) -> dict[str, Any]:
        repo_root = request.repo_root.resolve()
        if request.target_role != 'python-team':
            return {
                'ok': False,
                'reason': unsupported_reason,
                'details': unsupported_details,
                'target_role': request.target_role,
            }
        lineage_view = request.lineage_view
        if not lineage_view.get('ok'):
            return self._ambiguous_lineage_result(lineage_view)
        lineage = lineage_view.get('lineage') or {}
        workflow_stage = lineage_view.get('workflow_stage')
        if lineage.get('lineage_state') != expected_lineage_state:
            return {
                'ok': False,
                'reason': f'{expected_lineage_state}_not_supported_for_current_stage',
                'details': f'{expected_lineage_state.capitalize()} cleanup is only supported when lineage state is {expected_lineage_state}.',
                'workflow_stage': workflow_stage,
                'lineage_view': lineage_view,
            }
        ownership_view = request.ownership_view
        stale_view = request.stale_view
        if not ownership_view.get('ok'):
            return {
                'ok': False,
                'reason': 'worktree_ownership_unavailable',
                'details': f'{expected_lineage_state.capitalize()} cleanup requires a successful worktree ownership query.',
                'ownership_view': ownership_view,
                'lineage_view': lineage_view,
            }
        if not stale_view.get('ok'):
            return {
                'ok': False,
                'reason': 'worktree_staleness_unavailable',
                'details': f'{expected_lineage_state.capitalize()} cleanup requires a successful stale-worktree query.',
                'ownership_view': ownership_view,
                'stale_view': stale_view,
                'lineage_view': lineage_view,
            }
        decision_result = request.decision_result
        if not decision_result.get('ok'):
            return {
                'ok': False,
                'reason': decision_failed_reason,
                'details': decision_failed_details,
                'workflow_stage': workflow_stage,
                'ownership_view': ownership_view,
                'stale_view': stale_view,
                'decision_result': decision_result,
                'lineage_view': lineage_view,
            }
        ownership = ownership_view.get('worktree_ownership') or {}
        staleness = stale_view.get('worktree_staleness') or {}
        worktree_path_value = ownership.get('worktree_path')
        default_path_value = ownership.get('default_worktree_path')
        role_branch = ownership.get('role_branch')
        canonical_branch = lineage.get('canonical_branch')
        if not ownership.get('registered'):
            return {
                'ok': False,
                'reason': requires_registered_reason,
                'details': requires_registered_details,
                'lineage_view': lineage_view,
                'ownership_view': ownership_view,
                'stale_view': stale_view,
                'decision_result': decision_result,
            }
        if not staleness.get('stale') or not staleness.get('cleanup_candidate'):
            return {
                'ok': False,
                'reason': requires_stale_reason,
                'details': requires_stale_details,
                'lineage_view': lineage_view,
                'ownership_view': ownership_view,
                'stale_view': stale_view,
                'decision_result': decision_result,
            }
        if not worktree_path_value or not default_path_value:
            return {
                'ok': False,
                'reason': missing_path_reason,
                'details': missing_path_details,
                'lineage_view': lineage_view,
                'ownership_view': ownership_view,
                'stale_view': stale_view,
                'decision_result': decision_result,
            }
        worktree_path = Path(worktree_path_value).resolve()
        default_worktree_path = Path(default_path_value).resolve()
        if worktree_path != default_worktree_path:
            return {
                'ok': False,
                'reason': default_path_reason,
                'details': default_path_details,
                'lineage_view': lineage_view,
                'ownership_view': ownership_view,
                'stale_view': stale_view,
                'decision_result': decision_result,
            }
        entry_before = self.git_worktree_for_path(repo_root, worktree_path)
        if entry_before is None:
            return {
                'ok': False,
                'reason': entry_reason,
                'details': entry_details,
                'lineage_view': lineage_view,
                'ownership_view': ownership_view,
                'stale_view': stale_view,
                'decision_result': decision_result,
            }
        code, _stdout, error = self.run_text_with_errors(['git', 'worktree', 'remove', str(worktree_path)], cwd=repo_root)
        if code != 0:
            return {
                'ok': False,
                'reason': 'git_worktree_remove_failed',
                'details': 'git worktree remove did not complete successfully.',
                'worktree_path': str(worktree_path),
                'role_branch': role_branch,
                'canonical_branch': canonical_branch,
                'prior_worktree_ownership': ownership,
                'prior_worktree_staleness': staleness,
                'decision_result': decision_result,
                'git_error': error,
                'lineage_view': lineage_view,
            }
        entry_after = self.git_worktree_for_path(repo_root, worktree_path)
        cleanup_result = {
            'command': ['git', 'worktree', 'remove', str(worktree_path)],
            'worktree_removed': entry_after is None,
            'worktree_still_registered': entry_after is not None,
        }
        cleanup_result.update(preserved_values(role_branch, canonical_branch, request))
        return {
            'ok': True,
            'workflow_stage': workflow_stage,
            'target_role': request.target_role,
            'canonical_branch': canonical_branch,
            'role_branch': role_branch,
            'superseded_branch': request.superseded_branch,
            'worktree_path': str(worktree_path),
            'cleanup_performed': entry_after is None,
            'cleanup_result': cleanup_result,
            'prior_worktree_ownership': ownership,
            'prior_worktree_staleness': staleness,
            'decision_result': decision_result,
            'next_step_hint': next_step_hint if entry_after is None else 'investigate_remaining_registered_worktree_state',
            'lineage_view': lineage_view,
        }

    @staticmethod
    def _ambiguous_lineage_result(lineage_view: dict[str, Any]) -> dict[str, Any]:
        return {
            'ok': False,
            'reason': 'ambiguous_lineage_view',
            'details': (
                'Lineage helper could not produce an unambiguous lineage view: '
                f"{', '.join(lineage_view.get('ambiguity_reasons') or [])}"
            ),
            'lineage_view': lineage_view,
        }

    def _resolved_assignment_paths(
        self,
        *,
        repo_root: Path,
        issue_number: int,
        human_role: str,
        assignment_path: Path | None,
        review_output_path: Path | None,
    ) -> tuple[Path, Path]:
        default_output_path, default_review_output_path = self.default_assignment_paths(repo_root, issue_number, human_role)
        return (
            assignment_path.resolve() if assignment_path else default_output_path.resolve(),
            review_output_path.resolve() if review_output_path else default_review_output_path.resolve(),
        )


__all__ = [
    'DefaultRuntimeWorktreeService',
    'RuntimeWorktreeBranchRequest',
    'RuntimeWorktreeCleanupRequest',
    'RuntimeWorktreeInspectRequest',
    'RuntimeWorktreePrepareRequest',
]

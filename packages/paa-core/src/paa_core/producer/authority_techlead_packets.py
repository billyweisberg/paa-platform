from __future__ import annotations

from datetime import datetime, timezone
import json
import sys
from pathlib import Path
from typing import Any

from paa_core.producer.authority_packet_support import (
    load_design_package_from_paa,
    normalize_techlead_role,
    techlead_worktree_hint,
)
from paa_core.producer.authority_resolution import build_authority_context, resolve_brief_for_packet
from paa_core.producer.authority_reviews import (
    write_techlead_assignment_review_markdown,
    write_techlead_decision_review_markdown,
)
from paa_core.producer.authority_support import load_manifest, persist_packet_compilation


def cmd_materialize_techlead_assignment_packet(args: Any) -> None:
    manifest, manifest_data = load_manifest(args.manifest)
    package = load_design_package_from_paa(
        project_slug=args.project_slug,
        package_id_external=args.package_id_external,
    )
    authority_context, _task = build_authority_context(manifest, manifest_data, package)
    try:
        selected = resolve_brief_for_packet(
            project_slug=args.project_slug,
            package_id_external=args.package_id_external,
            brief_id_external=args.brief_id_external,
            require_ready=False,
        )
    except RuntimeError as exc:
        print(json.dumps({'ok': False, 'error': str(exc)}, indent=2))
        sys.exit(1)

    brief_json = selected['brief_json']
    issue_links = [url for url in [args.issue_url, args.pr_url] if url]
    target_role_label = normalize_techlead_role(args.target_role)
    canonical_branch = args.canonical_branch or args.branch
    role_branch = args.role_branch
    branch_owner_role = args.branch_owner_role or 'TechLead'
    lineage_state = args.lineage_state or 'active'
    lineage_action = args.lineage_action or 'created'
    source_branch = args.source_branch or canonical_branch
    superseded_branch = args.superseded_branch
    worktree_hint = args.worktree_hint or techlead_worktree_hint(args.issue_number, target_role_label)
    reset_reason = args.reset_reason
    payload: dict[str, Any] = {
        'message_id': args.message_id or f"fcore-techlead-{datetime.now(timezone.utc).date().isoformat()}-issue{args.issue_number}-{args.assignment_type}",
        'schema_type': 'techlead_assignment_packet',
        'schema_version': '1.0.0',
        'project': args.packet_project,
        'from_role': 'techlead',
        'to_role': args.target_role,
        'created_at': args.created_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z'),
        'correlation_id': args.correlation_id or f'issue-{args.issue_number}',
        'github_context': {
            'repo': args.repo,
            'issue_number': args.issue_number,
            'pr_number': args.pr_number,
            'branch': args.branch,
            'links': issue_links,
        },
        'payload': {
            'issue': {
                'number': args.issue_number,
                'url': args.issue_url,
            },
            'pr': {
                'number': args.pr_number,
                'url': args.pr_url,
                'ready_for_review': True,
            },
            'target_role': target_role_label,
            'assignment_type': args.assignment_type,
            'source_context_ref': {
                'source_packet_path': args.source_packet_path,
                'source_packet_message_id': args.source_packet_message_id,
                'package_id_external': args.package_id_external,
                'brief_id_external': selected['brief_id_external'],
            },
            'canonical_branch': canonical_branch,
            'role_branch': role_branch,
            'branch_owner_role': branch_owner_role,
            'lineage_state': lineage_state,
            'lineage_action': lineage_action,
            'source_branch': source_branch,
            'superseded_branch': superseded_branch,
            'worktree_hint': worktree_hint,
            'reset_reason': reset_reason,
            'allowed_result_types': list(args.allowed_result_type),
            'assignment_summary': args.assignment_summary,
            'coder_run_brief_ref': {
                'path': selected['source_artifact'],
                'schema_path': selected['schema_path'],
                'brief_id': brief_json['brief_id'],
            },
            'coder_run_brief': brief_json,
            'coder_brief_resolution': {
                'package_id_external': args.package_id_external,
                'brief_id_external': selected['brief_id_external'],
                'readiness_state': selected['readiness_state'],
                'parallel_group_id': selected['parallel_group_id'],
            },
        },
        'authority_context': authority_context,
    }
    review_markdown = None
    if args.output:
        output_path = Path(args.output).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2) + '\n')
    if args.review_output:
        review_path = Path(args.review_output).expanduser().resolve()
        review_path.parent.mkdir(parents=True, exist_ok=True)
        write_techlead_assignment_review_markdown(review_path, payload)
        review_markdown = review_path.read_text()
    automation_run_id = None
    if args.persist_db:
        automation_run_id = persist_packet_compilation(
            project_slug=args.project_slug,
            packet=payload,
            package_id_external=args.package_id_external,
            brief_id_external=selected['brief_id_external'],
            review_markdown=review_markdown,
            output_path=str(Path(args.output).expanduser().resolve()) if args.output else None,
            review_output_path=str(Path(args.review_output).expanduser().resolve()) if args.review_output else None,
            source_packet_path=args.source_packet_path,
        )
    print(json.dumps({
        'ok': True,
        'message_id': payload['message_id'],
        'output_path': str(Path(args.output).expanduser().resolve()) if args.output else None,
        'review_output_path': str(Path(args.review_output).expanduser().resolve()) if args.review_output else None,
        'automation_run_id': automation_run_id,
        'coder_brief_resolution': payload['payload']['coder_brief_resolution'],
        'task_id': authority_context['task_id'],
        'packet': payload if not args.output else None,
    }, indent=2))


def cmd_materialize_techlead_decision_packet(args: Any) -> None:
    manifest, manifest_data = load_manifest(args.manifest)
    package = load_design_package_from_paa(
        project_slug=args.project_slug,
        package_id_external=args.package_id_external,
    )
    authority_context, _task = build_authority_context(manifest, manifest_data, package)
    try:
        selected = resolve_brief_for_packet(
            project_slug=args.project_slug,
            package_id_external=args.package_id_external,
            brief_id_external=args.brief_id_external,
            require_ready=False,
        )
    except RuntimeError as exc:
        print(json.dumps({'ok': False, 'error': str(exc)}, indent=2))
        sys.exit(1)

    brief_json = selected['brief_json']
    issue_links = [url for url in [args.issue_url, args.pr_url] if url]
    target_role_label = normalize_techlead_role(args.target_role) if args.target_role else None
    canonical_branch = args.canonical_branch or args.branch
    role_branch = args.role_branch
    branch_owner_role = args.branch_owner_role or 'TechLead'
    lineage_state = args.lineage_state or 'active'
    lineage_action = args.lineage_action or 'created'
    source_branch = args.source_branch or canonical_branch
    superseded_branch = args.superseded_branch
    worktree_hint = args.worktree_hint or techlead_worktree_hint(args.issue_number, target_role_label or 'TechLead')
    reset_reason = args.reset_reason
    payload: dict[str, Any] = {
        'message_id': args.message_id or f"fcore-techlead-{datetime.now(timezone.utc).date().isoformat()}-issue{args.issue_number}-{args.decision_type}",
        'schema_type': 'techlead_decision_packet',
        'schema_version': '1.0.0',
        'project': args.packet_project,
        'from_role': 'techlead',
        'to_role': args.to_role,
        'created_at': args.created_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z'),
        'correlation_id': args.correlation_id or f'issue-{args.issue_number}',
        'github_context': {
            'repo': args.repo,
            'issue_number': args.issue_number,
            'pr_number': args.pr_number,
            'branch': args.branch,
            'links': issue_links,
        },
        'payload': {
            'issue': {
                'number': args.issue_number,
                'url': args.issue_url,
            },
            'pr': {
                'number': args.pr_number,
                'url': args.pr_url,
                'ready_for_review': True,
            },
            'source_packet_ref': {
                'path': args.source_packet_path,
                'message_id': args.source_packet_message_id,
            },
            'decision_type': args.decision_type,
            'decision_rationale': args.decision_rationale,
            'target_role': target_role_label,
            'next_assignment_type': args.next_assignment_type,
            'canonical_branch': canonical_branch,
            'role_branch': role_branch,
            'branch_owner_role': branch_owner_role,
            'lineage_state': lineage_state,
            'lineage_action': lineage_action,
            'source_branch': source_branch,
            'superseded_branch': superseded_branch,
            'worktree_hint': worktree_hint,
            'reset_reason': reset_reason,
            'work_item_status_update_intent': args.work_item_status_update_intent,
            'coder_run_brief_ref': {
                'path': selected['source_artifact'],
                'schema_path': selected['schema_path'],
                'brief_id': brief_json['brief_id'],
            },
            'coder_run_brief': brief_json,
            'coder_brief_resolution': {
                'package_id_external': args.package_id_external,
                'brief_id_external': selected['brief_id_external'],
                'readiness_state': selected['readiness_state'],
                'parallel_group_id': selected['parallel_group_id'],
            },
        },
        'authority_context': authority_context,
    }
    review_markdown = None
    if args.output:
        output_path = Path(args.output).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2) + '\n')
    if args.review_output:
        review_path = Path(args.review_output).expanduser().resolve()
        review_path.parent.mkdir(parents=True, exist_ok=True)
        write_techlead_decision_review_markdown(review_path, payload)
        review_markdown = review_path.read_text()
    automation_run_id = None
    if args.persist_db:
        automation_run_id = persist_packet_compilation(
            project_slug=args.project_slug,
            packet=payload,
            package_id_external=args.package_id_external,
            brief_id_external=selected['brief_id_external'],
            review_markdown=review_markdown,
            output_path=str(Path(args.output).expanduser().resolve()) if args.output else None,
            review_output_path=str(Path(args.review_output).expanduser().resolve()) if args.review_output else None,
            source_packet_path=args.source_packet_path,
        )
    print(json.dumps({
        'ok': True,
        'message_id': payload['message_id'],
        'output_path': str(Path(args.output).expanduser().resolve()) if args.output else None,
        'review_output_path': str(Path(args.review_output).expanduser().resolve()) if args.review_output else None,
        'automation_run_id': automation_run_id,
        'coder_brief_resolution': payload['payload']['coder_brief_resolution'],
        'task_id': authority_context['task_id'],
        'packet': payload if not args.output else None,
    }, indent=2))

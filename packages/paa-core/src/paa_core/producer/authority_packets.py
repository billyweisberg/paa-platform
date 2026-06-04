from __future__ import annotations

from datetime import datetime, timezone
import json
import sys
from pathlib import Path
from typing import Any

from paa_core.producer.authority_packet_support import (
    derive_focus,
    derive_governance_reminders,
    derive_keep_stable,
    derive_next_move,
    derive_remaining_gap,
    load_design_package_from_paa,
    load_ready_coder_briefs_from_paa,
    unique_preserving_order,
    write_review_markdown,
)
from paa_core.producer.authority_queries import task_or_die
from paa_core.producer.authority_resolution import find_task
from paa_core.producer.authority_support import (
    load_manifest,
    persist_packet_compilation,
    sync_issue_source_into_paa,
)
from paa_core.runtime.support.runtime_paths import repo_root_from_cwd


def cmd_materialize_coder_brief(args: Any) -> None:
    briefs = load_ready_coder_briefs_from_paa(
        project_slug=args.project_slug,
        package_id_external=args.package_id_external,
    )
    if not briefs:
        print(json.dumps({
            'ok': False,
            'error': 'no coder briefs found for design package',
            'project_slug': args.project_slug,
            'package_id_external': args.package_id_external,
        }, indent=2))
        sys.exit(1)

    if args.brief_id_external:
        briefs = [brief for brief in briefs if brief['brief_id_external'] == args.brief_id_external]
        if not briefs:
            print(json.dumps({
                'ok': False,
                'error': 'requested brief_id_external not found in package',
                'project_slug': args.project_slug,
                'package_id_external': args.package_id_external,
                'brief_id_external': args.brief_id_external,
            }, indent=2))
            sys.exit(1)

    ready_states = {'execution_ready', 'parallel_ready'}
    ready_briefs = [brief for brief in briefs if brief['readiness_state'] in ready_states]

    if args.require_ready:
        if not ready_briefs:
            print(json.dumps({
                'ok': False,
                'error': 'no execution-eligible coder brief is available',
                'project_slug': args.project_slug,
                'package_id_external': args.package_id_external,
                'briefs': [
                    {
                        'brief_id_external': brief['brief_id_external'],
                        'readiness_state': brief['readiness_state'],
                        'blocking_cause': brief['blocking_cause'],
                    }
                    for brief in briefs
                ],
            }, indent=2))
            sys.exit(1)
        if len(ready_briefs) > 1 and not args.allow_parallel_ready:
            print(json.dumps({
                'ok': False,
                'error': 'multiple execution-eligible coder briefs are available; explicit selection or parallel approval is required',
                'project_slug': args.project_slug,
                'package_id_external': args.package_id_external,
                'ready_briefs': [
                    {
                        'brief_id_external': brief['brief_id_external'],
                        'readiness_state': brief['readiness_state'],
                        'parallel_group_id': brief['parallel_group_id'],
                    }
                    for brief in ready_briefs
                ],
            }, indent=2))
            sys.exit(1)
        selected = ready_briefs[0]
    else:
        selected = briefs[0]

    payload = {
        'ok': True,
        'project_slug': args.project_slug,
        'package_id_external': args.package_id_external,
        'brief_id_external': selected['brief_id_external'],
        'readiness_state': selected['readiness_state'],
        'parallel_group_id': selected['parallel_group_id'],
        'coder_run_brief_ref': {
            'path': selected['source_artifact'],
            'schema_path': selected['schema_path'],
            'brief_id': selected['brief_json']['brief_id'],
        },
        'coder_run_brief': selected['brief_json'],
    }
    print(json.dumps(payload, indent=2))


def cmd_materialize_architect_packet(args: Any) -> None:
    manifest, manifest_data = load_manifest(args.manifest)
    source_to_paa_sync = None
    if not getattr(args, 'skip_source_sync', False):
        repo_root = repo_root_from_cwd()
        source_to_paa_sync = sync_issue_source_into_paa(
            repo_root=repo_root,
            issue_number=args.next_issue_number,
        )
    package = load_design_package_from_paa(
        project_slug=args.project_slug,
        package_id_external=args.package_id_external,
    )
    briefs = load_ready_coder_briefs_from_paa(
        project_slug=args.project_slug,
        package_id_external=args.package_id_external,
    )
    ready_states = {'execution_ready', 'parallel_ready'}
    ready_briefs = [brief for brief in briefs if brief['readiness_state'] in ready_states]
    if not ready_briefs:
        print(json.dumps({
            'ok': False,
            'error': 'no execution-eligible coder brief is available',
            'project_slug': args.project_slug,
            'package_id_external': args.package_id_external,
        }, indent=2))
        sys.exit(1)
    if len(ready_briefs) > 1 and not args.allow_parallel_ready:
        print(json.dumps({
            'ok': False,
            'error': 'multiple execution-eligible coder briefs are available; explicit parallel approval is required',
            'project_slug': args.project_slug,
            'package_id_external': args.package_id_external,
            'ready_briefs': [
                {
                    'brief_id_external': brief['brief_id_external'],
                    'readiness_state': brief['readiness_state'],
                    'parallel_group_id': brief['parallel_group_id'],
                }
                for brief in ready_briefs
            ],
        }, indent=2))
        sys.exit(1)

    selected = ready_briefs[0]
    task = find_task(manifest_data, task_id=package['authority_context']['task_id'])
    selected_brief_json = selected['brief_json']
    authority_context = {
        'manifest_path': str(manifest),
        'authority_version': package['authority_context'].get('authority_version') or manifest_data['project']['authority_version'],
        'milestone_id': package['authority_context']['milestone_id'],
        'phase_id': package['authority_context']['phase_id'],
        'task_id': package['authority_context']['task_id'],
    }
    if task:
        authority_context.update({
            'authority_version': manifest_data['project']['authority_version'],
            'issue_number': task.get('issue_number'),
            'task_title': task.get('title'),
        })

    baseline = json.loads(Path(args.baseline_file).read_text())
    created_at = args.created_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
    next_issue_number = args.next_issue_number
    next_issue_url = args.next_issue_url
    links = [url for url in [args.accepted_pr_url, args.closed_issue_url, next_issue_url] if url]
    remaining_gap = args.remaining_gap or derive_remaining_gap(task, package)
    next_move = unique_preserving_order((args.next_move or []) + derive_next_move(selected, next_issue_number))
    focus = unique_preserving_order((args.focus or []) + derive_focus(selected, package))
    keep_stable = unique_preserving_order((args.keep_stable or []) + derive_keep_stable(package))
    governance_reminder = unique_preserving_order((args.governance_reminder or []) + derive_governance_reminders())
    payload = {
        'message_id': args.message_id or f"fcore-arch-{datetime.now(timezone.utc).date().isoformat()}-issue{next_issue_number}-{package['authority_context']['task_id']}",
        'schema_type': 'architect_cycle_packet',
        'schema_version': '1.0.0',
        'project': args.packet_project,
        'from_role': 'architect',
        'to_role': 'python-team',
        'created_at': created_at,
        'correlation_id': args.correlation_id or f'issue-{next_issue_number}',
        'github_context': {
            'repo': args.repo,
            'issue_number': next_issue_number,
            'pr_number': args.accepted_pr_number,
            'branch': args.branch,
            'links': links,
        },
        'payload': {
            'accepted_pr': {
                'number': args.accepted_pr_number,
                'url': args.accepted_pr_url,
            },
            'closed_issue': {
                'number': args.closed_issue_number,
                'url': args.closed_issue_url,
            },
            'next_issue': {
                'number': next_issue_number,
                'url': next_issue_url,
            },
            'current_baseline': baseline,
            'remaining_gap': remaining_gap,
            'next_move': next_move,
            'focus': focus,
            'keep_stable': keep_stable,
            'governance_reminder': governance_reminder,
            'coder_run_brief_ref': {
                'path': selected['source_artifact'],
                'schema_path': selected['schema_path'],
                'brief_id': selected_brief_json['brief_id'],
            },
            'coder_run_brief': selected_brief_json,
            'coder_brief_resolution': {
                'package_id_external': args.package_id_external,
                'brief_id_external': selected['brief_id_external'],
                'readiness_state': selected['readiness_state'],
                'parallel_group_id': selected['parallel_group_id'],
            },
            'pr_starter': {
                'branch': args.pr_starter_branch,
                'title': args.pr_starter_title,
                'body_linkage': args.pr_starter_body_linkage,
            } if any([args.pr_starter_branch, args.pr_starter_title, args.pr_starter_body_linkage]) else None,
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
            write_review_markdown(review_path, payload)
            review_markdown = review_path.read_text()
    elif args.review_output:
        review_path = Path(args.review_output).expanduser().resolve()
        review_path.parent.mkdir(parents=True, exist_ok=True)
        write_review_markdown(review_path, payload)
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
            source_input_path=args.baseline_file,
        )
    print(json.dumps({
        'ok': True,
        'message_id': payload['message_id'],
        'output_path': str(Path(args.output).expanduser().resolve()) if args.output else None,
        'review_output_path': str(Path(args.review_output).expanduser().resolve()) if args.review_output else None,
        'automation_run_id': automation_run_id,
        'source_to_paa_sync': {
            'issue_number': source_to_paa_sync.get('issue_number'),
            'package_id': source_to_paa_sync.get('package_id'),
            'brief_ids': source_to_paa_sync.get('brief_ids'),
            'materialized_obligation_count': source_to_paa_sync.get('materialized_obligation_count'),
        } if source_to_paa_sync else None,
        'coder_brief_resolution': payload['payload']['coder_brief_resolution'],
        'packet': payload if not args.output else None,
    }, indent=2))

from __future__ import annotations

from datetime import datetime, timezone
import json
import sys
from pathlib import Path
from typing import Any

from paa_core.producer.authority_packet_support import (
    load_design_package_from_paa,
    load_json_file,
    normalize_worker_role,
)
from paa_core.producer.authority_resolution import build_authority_context, resolve_brief_for_packet
from paa_core.producer.authority_reviews import (
    write_delivery_review_packet_markdown,
    write_dev_review_markdown,
    write_qa_review_markdown,
    write_worker_result_review_markdown,
)
from paa_core.producer.authority_support import load_manifest, persist_packet_compilation


def derive_dev_workflow_compliance(dev_input: dict[str, Any]) -> dict[str, Any]:
    compliance = dict(dev_input.get('workflow_compliance', {}))
    compliance.setdefault('closes_issue', True)
    compliance.setdefault('issue_side_update_comment_added', bool(dev_input.get('issue_update_comment_url')))
    compliance.setdefault('dev_did_not_merge', True)
    return compliance


def derive_dev_result_summary(dev_input: dict[str, Any], brief_json: dict[str, Any], package: dict[str, Any]) -> Any:
    if dev_input.get('result_summary'):
        return dev_input['result_summary']
    result = {
        'implemented_component': brief_json['component_assignment']['component_name'],
        'implemented_aspects': brief_json['component_assignment'].get('component_aspects', []),
        'behavioral_delta': brief_json.get('behavioral_contract', {}).get('behavior_to_add_or_change', []),
        'protected_baseline': package.get('verification_contract_basis', {}).get('protected_baseline_checks', []),
    }
    commands = dev_input.get('validation', {}).get('commands', [])
    if commands:
        result['validation_commands_count'] = len(commands)
    return result


def derive_dev_mechanism_changed(dev_input: dict[str, Any], brief_json: dict[str, Any]) -> Any:
    if dev_input.get('mechanism_changed'):
        return dev_input['mechanism_changed']
    return {
        'component': brief_json['component_assignment']['component_name'],
        'behavior_to_add_or_change': brief_json.get('behavioral_contract', {}).get('behavior_to_add_or_change', []),
        'target_modules': brief_json.get('architecture_constraints', {}).get('target_modules', []),
    }


def derive_dev_validation(dev_input: dict[str, Any]) -> dict[str, Any]:
    validation = dict(dev_input.get('validation', {}))
    validation.setdefault('commands', [])
    return validation


def derive_dev_artifacts(dev_input: dict[str, Any]) -> Any:
    return dev_input.get('artifacts', [])


def derive_dev_merge_status(dev_input: dict[str, Any]) -> dict[str, Any]:
    merge_status = dict(dev_input.get('merge_status', {}))
    merge_status.setdefault('merged', False)
    merge_status.setdefault('ready_for_architect_review', True)
    return merge_status


def derive_dev_architect_decision_needed(brief_json: dict[str, Any], pr_number: int) -> str:
    return (
        f"review PR #{pr_number} for acceptance of "
        f"{brief_json['component_assignment']['component_name']} "
        f"within the current authorized slice"
    )


def derive_qa_verification_scope(package: dict[str, Any], issue_number: int, pr_number: int) -> dict[str, Any]:
    source_docs: list[str] = []
    for item in package.get('product_and_source_basis', {}).get('source_artifacts', []):
        if isinstance(item, str):
            title = item
        else:
            title = item.get('title') or item.get('artifact_id')
        if title:
            source_docs.append(title)
    if not source_docs:
        source_docs = [
            'project-authority/fractal-core-python-authority.json',
            'project design package source artifacts',
        ]
    return {
        'authority_docs_consulted': source_docs,
        'github_records_consulted': [
            f'issue #{issue_number}',
            f'PR #{pr_number}',
        ],
    }


def derive_qa_mechanical_checks(qa_input: dict[str, Any]) -> dict[str, Any]:
    checks = dict(qa_input.get('mechanical_checks', {}))
    checks.setdefault('closes_issue', True)
    checks.setdefault('issue_update_comment_present', True)
    checks.setdefault('ready_for_review', True)
    return checks


def derive_qa_technical_scope_checks(qa_input: dict[str, Any], brief_json: dict[str, Any]) -> dict[str, Any]:
    checks = dict(qa_input.get('technical_scope_checks', {}))
    checks.setdefault('scope_match', brief_json.get('slice_scope_ref'))
    checks.setdefault('unauthorized_scope_widening', False)
    return checks


def derive_qa_protected_path_checks(qa_input: dict[str, Any], package: dict[str, Any]) -> dict[str, Any]:
    checks = dict(qa_input.get('protected_path_checks', {}))
    protected = package.get('verification_contract_basis', {}).get('protected_baseline_checks', [])
    for item in protected:
        lower = item.lower()
        if 'trace' in lower:
            checks.setdefault('trace_contract_unchanged', True)
        if 'parity' in lower:
            checks.setdefault('parity_contract_unchanged', True)
        if 'benchmark' in lower:
            checks.setdefault('benchmark_contract_unchanged', True)
    return checks


def derive_qa_artifact_checks(qa_input: dict[str, Any]) -> dict[str, Any]:
    checks = dict(qa_input.get('artifact_checks', {}))
    checks.setdefault('reviewer_usable_outputs', True)
    return checks


def derive_qa_recommended_action(qa_input: dict[str, Any], verification_status: str, pr_number: int) -> Any:
    if qa_input.get('recommended_action'):
        return qa_input['recommended_action']
    if verification_status == 'pass':
        return {
            'merge_recommendation': 'accept_and_merge',
            'next_step': f'Architect may merge PR #{pr_number} and advance authority if the acceptance gate is satisfied',
        }
    if verification_status == 'needs_human_review':
        return {
            'merge_recommendation': 'architect_scope_review_required',
            'next_step': f'Architect should review PR #{pr_number} and decide whether the slice remains within authority',
        }
    return {
        'merge_recommendation': 'do_not_merge',
        'next_step': f'PR #{pr_number} should not merge until the QA findings are resolved',
    }


def cmd_materialize_slice_result_packet(args: Any) -> None:
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
            require_ready=not args.allow_nonready_brief,
        )
    except RuntimeError as exc:
        print(json.dumps({'ok': False, 'error': str(exc)}, indent=2))
        sys.exit(1)

    dev_input = load_json_file(args.dev_input_file)
    brief_json = selected['brief_json']
    issue_links = [url for url in [args.issue_url, args.pr_url] if url]
    payload = {
        'message_id': args.message_id or f"fcore-py-{datetime.now(timezone.utc).date().isoformat()}-issue{args.issue_number}-{brief_json['brief_id']}",
        'schema_type': 'slice_result_packet',
        'schema_version': '1.0.0',
        'project': args.packet_project,
        'from_role': 'python-team',
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
            'branch': {
                'name': args.branch,
            },
            'pr': {
                'number': args.pr_number,
                'url': args.pr_url,
                'ready_for_review': dev_input.get('pr_ready_for_review', True),
            },
            'workflow_compliance': derive_dev_workflow_compliance(dev_input),
            'result_summary': derive_dev_result_summary(dev_input, brief_json, package),
            'mechanism_changed': derive_dev_mechanism_changed(dev_input, brief_json),
            'validation': derive_dev_validation(dev_input),
            'artifacts': derive_dev_artifacts(dev_input),
            'merge_status': derive_dev_merge_status(dev_input),
            'architect_decision_needed': dev_input.get('architect_decision_needed') or derive_dev_architect_decision_needed(brief_json, args.pr_number),
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
        write_dev_review_markdown(review_path, payload)
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
            source_input_path=args.dev_input_file,
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


def cmd_materialize_qa_verification_packet(args: Any) -> None:
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

    qa_input = load_json_file(args.qa_input_file)
    verification_status = args.verification_status or qa_input.get('verification_status')
    if verification_status not in {'pass', 'fail', 'needs_human_review'}:
        print(json.dumps({'ok': False, 'error': 'verification_status must be pass, fail, or needs_human_review'}, indent=2))
        sys.exit(1)

    brief_json = selected['brief_json']
    github_links = [url for url in [args.issue_url, args.pr_url, args.source_packet_path] if url]
    payload = {
        'message_id': args.message_id or f"fcore-qa-{datetime.now(timezone.utc).date().isoformat()}-issue{args.issue_number}-{brief_json['brief_id']}",
        'schema_type': 'qa_verification_packet',
        'schema_version': '1.0.0',
        'project': args.packet_project,
        'from_role': 'qa',
        'to_role': args.to_role,
        'created_at': args.created_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z'),
        'correlation_id': args.correlation_id or f'issue-{args.issue_number}',
        'github_context': {
            'repo': args.repo,
            'issue_number': args.issue_number,
            'pr_number': args.pr_number,
            'branch': args.branch,
            'links': github_links,
        },
        'payload': {
            'issue': {
                'number': args.issue_number,
                'url': args.issue_url,
            },
            'pr': {
                'number': args.pr_number,
                'url': args.pr_url,
                'ready_for_review': qa_input.get('pr_ready_for_review', True),
            },
            'verification_status': verification_status,
            'verification_scope': derive_qa_verification_scope(package, args.issue_number, args.pr_number),
            'mechanical_checks': derive_qa_mechanical_checks(qa_input),
            'technical_scope_checks': derive_qa_technical_scope_checks(qa_input, brief_json),
            'protected_path_checks': derive_qa_protected_path_checks(qa_input, package),
            'artifact_checks': derive_qa_artifact_checks(qa_input),
            'findings': qa_input.get('findings', []),
            'recommended_action': derive_qa_recommended_action(qa_input, verification_status, args.pr_number),
            'source_slice_packet_ref': {
                'path': args.source_packet_path,
            } if args.source_packet_path else None,
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
        write_qa_review_markdown(review_path, payload)
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
            source_input_path=args.qa_input_file,
            source_packet_path=args.source_packet_path,
        )
    print(json.dumps({
        'ok': True,
        'message_id': payload['message_id'],
        'output_path': str(Path(args.output).expanduser().resolve()) if args.output else None,
        'review_output_path': str(Path(args.review_output).expanduser().resolve()) if args.review_output else None,
        'automation_run_id': automation_run_id,
        'coder_brief_resolution': payload['payload']['coder_brief_resolution'],
        'verification_status': verification_status,
        'task_id': authority_context['task_id'],
        'packet': payload if not args.output else None,
    }, indent=2))


def cmd_materialize_worker_result_packet(args: Any) -> None:
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
            require_ready=not args.allow_nonready_brief,
        )
    except RuntimeError as exc:
        print(json.dumps({'ok': False, 'error': str(exc)}, indent=2))
        sys.exit(1)

    worker_input = load_json_file(args.worker_input_file)
    brief_json = selected['brief_json']
    worker_role_label = normalize_worker_role(args.worker_role)
    issue_links = [url for url in [args.issue_url, args.pr_url] if url]
    payload = {
        'message_id': args.message_id or f"fcore-worker-{datetime.now(timezone.utc).date().isoformat()}-issue{args.issue_number}-{args.worker_role}",
        'schema_type': 'worker_result_packet',
        'schema_version': '1.0.0',
        'project': args.packet_project,
        'from_role': args.worker_role,
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
            'branch': {
                'name': args.branch,
            },
            'pr': {
                'number': args.pr_number,
                'url': args.pr_url,
                'ready_for_review': worker_input.get('pr_ready_for_review', True),
            },
            'worker_role': worker_role_label,
            'worker_family': args.worker_family,
            'result_type': args.result_type,
            'workflow_compliance': worker_input.get('workflow_compliance') or derive_dev_workflow_compliance(worker_input),
            'implementation_summary': worker_input.get('implementation_summary') or derive_dev_result_summary(worker_input, brief_json, package),
            'validation_summary': worker_input.get('validation_summary') or derive_dev_validation(worker_input),
            'artifacts': worker_input.get('artifacts') or derive_dev_artifacts(worker_input),
            'merge_status': worker_input.get('merge_status') or derive_dev_merge_status(worker_input),
            'techlead_action_recommended': worker_input.get('techlead_action_recommended') or {
                'action': 'assign_qa',
                'reason': f'{worker_role_label} completed assigned work and returned a result for TechLead review.',
            },
            'source_assignment_ref': {
                'message_id': args.source_assignment_message_id,
                'assignment_type': args.source_assignment_type,
                'target_role': worker_role_label,
                'path': args.source_assignment_path,
            },
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
        write_worker_result_review_markdown(review_path, payload)
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
            source_input_path=args.worker_input_file,
            source_packet_path=args.source_assignment_path,
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


def cmd_materialize_delivery_review_packet(args: Any) -> None:
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

    delivery_input = load_json_file(args.delivery_input_file)
    brief_json = selected['brief_json']
    issue_links = [url for url in [args.issue_url, args.pr_url] if url]
    payload = {
        'message_id': args.message_id or f"fcore-delivery-{datetime.now(timezone.utc).date().isoformat()}-issue{args.issue_number}-{args.result_type}",
        'schema_type': 'delivery_review_packet',
        'schema_version': '1.0.0',
        'project': args.packet_project,
        'from_role': 'delivery-architect',
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
            'branch': {
                'name': args.branch,
            },
            'pr': {
                'number': args.pr_number,
                'url': args.pr_url,
                'ready_for_review': delivery_input.get('pr_ready_for_review', True),
            },
            'review_type': args.review_type,
            'result_type': args.result_type,
            'scope_recommendation': delivery_input.get('scope_recommendation') or {
                'action': 'proceed_as_assigned',
                'notes': ['No delivery-scope changes were requested in the review input.'],
            },
            'authority_impact': delivery_input.get('authority_impact') or {
                'level': 'none',
                'details': 'No authority change was recorded in the delivery review input.',
            },
            'branch_recommendation': delivery_input.get('branch_recommendation') or {
                'action': 'keep_current_lineage',
                'notes': [f'Continue on the current issue lineage for issue #{args.issue_number}.'],
            },
            'techlead_action_recommended': delivery_input.get('techlead_action_recommended') or {
                'action': 'assign_worker',
                'target_role': 'Python Dev',
                'reason': 'Delivery review is complete and ready for TechLead routing.',
            },
            'review_summary': delivery_input.get('review_summary') or f'Delivery review completed for {brief_json["component_assignment"]["component_name"]}.',
            'findings': delivery_input.get('findings', []),
            'source_assignment_ref': {
                'message_id': args.source_assignment_message_id,
                'assignment_type': args.source_assignment_type,
                'target_role': 'Delivery Architect',
                'path': args.source_assignment_path,
            },
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
        write_delivery_review_packet_markdown(review_path, payload)
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
            source_input_path=args.delivery_input_file,
            source_packet_path=args.source_assignment_path,
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

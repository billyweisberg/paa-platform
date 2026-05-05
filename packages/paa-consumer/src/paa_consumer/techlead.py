#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_DB_CONTAINER = 'agenthub-mm-db'
DEFAULT_DB_NAME = 'paa_dev'
DEFAULT_DB_USER = 'mmuser'
DEFAULT_PROJECT_SLUG = 'fractal-core-python'
DEFAULT_AGENT_NAME = 'Fractal Core TechLead Automation'
ROLE_CONFIG = {
    'Architect': {'dir': 'fractal-core-delivery-architect-automation', 'root': str(REPO_ROOT)},
    'Python Dev': {'dir': 'python-team-automation', 'root': str(REPO_ROOT)},
    'QA': {'dir': 'fractal-core-qa-automation', 'root': str(REPO_ROOT)},
    'TechLead': {'dir': 'fractal-core-techlead-automation', 'root': str(REPO_ROOT)},
}
QUEUE_NAMES = ['fractal-core-python', 'fractal-core-qa', 'fractal-core-architecture']


def repo_auth_script(repo_root: Path) -> Path:
    return repo_root / '.codex' / 'paa' / 'bin' / 'paa-producer'


def repo_queue_script(repo_root: Path) -> Path:
    return repo_root / '.codex' / 'paa' / 'bin' / 'paa-consumer'


def repo_automations_dir(repo_root: Path) -> Path:
    return repo_root / '.codex' / 'automations'


def repo_auth_current(repo_root: Path) -> Path:
    return repo_root / '.project' / 'data' / 'paa' / 'authority' / 'current' / 'authority' / 'fractal-core-python-authority.json'


def repo_default_schema(repo_root: Path) -> Path:
    return repo_root / '.codex' / 'paa' / 'schemas' / 'runtime-records' / 'techlead-status-report.schema.json'


def repo_reports_dir(repo_root: Path) -> Path:
    return repo_root / '.project' / 'data' / 'paa' / 'reports'


AUTH_SCRIPT = repo_auth_script(REPO_ROOT)
QUEUE_SCRIPT = repo_queue_script(REPO_ROOT)
AUTOMATIONS_DIR = repo_automations_dir(REPO_ROOT)
AUTH_CURRENT = repo_auth_current(REPO_ROOT)
DEFAULT_SCHEMA = repo_default_schema(REPO_ROOT)
QA_WORK_DIR = repo_reports_dir(REPO_ROOT)
LOCAL_MIRRORS = [AUTH_CURRENT]


def run_json(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f'command failed: {cmd}')
    return json.loads(result.stdout)


def run_json_with_errors(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return result.returncode, None, result.stderr.strip() or result.stdout.strip() or f'command failed: {cmd}'
    return 0, json.loads(result.stdout), None


def run_psql(db_container, db_name, db_user, sql):
    result = subprocess.run(
        ['docker', 'exec', '-i', db_container, 'psql', '-U', db_user, '-d', db_name, '-At', '-F', '\t'],
        input=sql,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or 'psql command failed')
    return result.stdout


def sql_literal(value):
    if value is None:
        return 'NULL'
    return "'" + str(value).replace("'", "''") + "'"


def load_authority(repo_root: Path = REPO_ROOT):
    auth_script = repo_auth_script(repo_root)
    auth_current = repo_auth_current(repo_root)
    current = run_json([str(auth_script), 'authority', 'current', '--manifest', str(auth_current)])
    manifest = json.loads(auth_current.read_text())
    return current, manifest


def load_design_package(project_slug, package_id_external):
    sql = f"""
    SELECT dp.package_json::text
    FROM paa.design_packages dp
    JOIN paa.projects p ON p.project_id = dp.project_id
    WHERE p.slug = {sql_literal(project_slug)}
      AND dp.package_id_external = {sql_literal(package_id_external)}
    LIMIT 1;
    """
    out = run_psql(DEFAULT_DB_CONTAINER, DEFAULT_DB_NAME, DEFAULT_DB_USER, sql).strip()
    if not out:
        raise RuntimeError(f'No design package found for {project_slug}:{package_id_external}')
    return json.loads(out)


def queue_state(repo_root: Path = REPO_ROOT):
    out = {}
    queue_script = repo_queue_script(repo_root)
    for q in QUEUE_NAMES:
        out[q] = run_json([str(queue_script), 'queue-check', '--repo-root', str(repo_root), '--queue', q])
    return out


def automation_state(repo_root: Path = REPO_ROOT):
    roles = []
    architect_missing = False
    automations_dir = repo_automations_dir(repo_root)
    for role, cfg in ROLE_CONFIG.items():
        d = automations_dir / cfg['dir']
        status = 'missing'
        runtime = None
        if d.exists():
            toml = d / 'automation.toml'
            if toml.exists():
                text = toml.read_text()
                status = 'visible'
                for line in text.splitlines():
                    if line.startswith('status = '):
                        raw = line.split('=', 1)[1].strip().strip('"')
                        if raw == 'PAUSED':
                            status = 'paused'
                        elif raw == 'ACTIVE':
                            status = 'active'
                    elif line.startswith('execution_environment = '):
                        runtime = line.split('=', 1)[1].strip().strip('"')
        if role == 'Architect' and status == 'missing':
            architect_missing = True
        roles.append({
            'role': role,
            'status': status,
            'runtime': runtime,
            'root': str(repo_root),
            'last_run_at': None,
        })
    return roles, architect_missing


def fetch_pr(pr_number):
    return run_json([
        'gh', 'pr', 'view', str(pr_number), '--repo', 'billyweisberg/fractal-core-python',
        '--json', 'number,title,state,isDraft,headRefName,baseRefName,url,statusCheckRollup,mergedAt,body,comments'
    ])


def github_state(issue_number, fallback_pr_number=None):
    issue = run_json([
        'gh', 'issue', 'view', str(issue_number), '--repo', 'billyweisberg/fractal-core-python',
        '--json', 'number,state,title,url,comments'
    ])
    prs = run_json([
        'gh', 'pr', 'list', '--repo', 'billyweisberg/fractal-core-python', '--search', f'{issue_number} in:title',
        '--state', 'all', '--json', 'number,title,state,isDraft,headRefName,baseRefName,url,statusCheckRollup,mergedAt,body'
    ])
    active_pr = None
    for pr in prs:
        if pr['state'] == 'OPEN':
            active_pr = pr
            break
    if active_pr is None and prs:
        active_pr = prs[0]
    if active_pr is None and fallback_pr_number is not None:
        try:
            active_pr = fetch_pr(fallback_pr_number)
        except Exception:
            active_pr = None
    if active_pr is None:
        try:
            all_prs = run_json([
                'gh', 'pr', 'list', '--repo', 'billyweisberg/fractal-core-python',
                '--state', 'all', '--json', 'number,title,state,isDraft,headRefName,baseRefName,url,statusCheckRollup,mergedAt,body'
            ])
        except Exception:
            all_prs = []
        fallback_matches = [
            pr for pr in all_prs
            if str(issue_number) in (pr.get('headRefName') or '')
            or str(issue_number) in (pr.get('title') or '')
            or str(issue_number) in (pr.get('body') or '')
        ]
        for pr in fallback_matches:
            if pr.get('state') == 'OPEN':
                active_pr = pr
                break
        if active_pr is None and fallback_matches:
            active_pr = fallback_matches[0]
    if active_pr is not None and 'comments' not in active_pr:
        try:
            active_pr = fetch_pr(active_pr['number'])
        except Exception:
            pass
    return issue, active_pr


def mirror_status(authority_version, repo_root: Path = REPO_ROOT):
    mirrors = []
    statuses = []
    for path in [repo_auth_current(repo_root)]:
        if not path.exists():
            status = 'missing'
        else:
            try:
                data = json.loads(path.read_text())
                status = 'present' if data.get('project', {}).get('authority_version') == authority_version else 'stale'
            except Exception:
                status = 'unknown'
        mirrors.append({'location': str(path), 'status': status})
        statuses.append(status)
    overall = 'aligned' if statuses and all(s == 'present' for s in statuses) else 'stale'
    return overall, mirrors


def latest_qa_packet(issue_number, reports_dir: Path = QA_WORK_DIR):
    candidates = []
    for packet_path in sorted(reports_dir.glob(f'qa-verification*issue{issue_number}*.json')):
        try:
            packet = json.loads(packet_path.read_text())
        except Exception:
            continue
        if packet.get('github_context', {}).get('issue_number') != issue_number:
            continue
        payload = packet.get('payload', {})
        created_at = packet.get('created_at')
        candidates.append({
            'path': str(packet_path),
            'message_id': packet.get('message_id'),
            'created_at': created_at,
            'verification_status': payload.get('verification_status'),
            'findings': payload.get('findings', []),
            'recommended_action': payload.get('recommended_action', {}),
            'technical_scope_checks': payload.get('technical_scope_checks', {}),
            'protected_path_checks': payload.get('protected_path_checks', {}),
            'pr_number': packet.get('github_context', {}).get('pr_number'),
            '_created_dt': parse_created_at(created_at),
            '_mtime': packet_path.stat().st_mtime,
        })
    if not candidates:
        return None
    candidates.sort(key=lambda item: (item['_created_dt'] or datetime.min.replace(tzinfo=timezone.utc), item['_mtime']))
    latest = candidates[-1]
    latest.pop('_created_dt', None)
    latest.pop('_mtime', None)
    return latest


def latest_queue_preview(queues, queue_name, issue_number):
    preview = queues.get(queue_name, {}).get('preview') or []
    for item in preview:
        payload = item.get('payload_preview') or {}
        if payload.get('correlation_id') == f'issue-{issue_number}':
            return payload
        github_ctx = payload.get('github_context') or {}
        if github_ctx.get('issue_number') == issue_number:
            return payload
    return None


def latest_packet_preview(queues, issue_number, schema_type=None, to_role=None):
    latest = None
    latest_dt = None
    for queue_name, queue_data in queues.items():
        preview = queue_data.get('preview') or []
        for item in preview:
            payload = item.get('payload_preview') or {}
            if payload.get('correlation_id') != f'issue-{issue_number}':
                continue
            if schema_type and payload.get('schema_type') != schema_type:
                continue
            if to_role and payload.get('to_role') != to_role:
                continue
            created_at = parse_created_at(payload.get('created_at'))
            if latest is None or (created_at and (latest_dt is None or created_at > latest_dt)):
                latest = dict(payload)
                latest['queue_name'] = queue_name
                latest_dt = created_at
    return latest


def newest_packet(*packets):
    latest = None
    latest_dt = None
    for packet in packets:
        if not packet:
            continue
        created_at = parse_created_at(packet.get('created_at'))
        if latest is None or (created_at and (latest_dt is None or created_at > latest_dt)):
            latest = packet
            latest_dt = created_at
    return latest


def derive_lineage_section(current_task, pr, queues, escalations):
    issue_number = current_task['issue_number'] if current_task else None
    assignment_packet = latest_packet_preview(
        queues,
        issue_number,
        schema_type='techlead_assignment_packet',
    ) if issue_number else None
    decision_packet = latest_packet_preview(
        queues,
        issue_number,
        schema_type='techlead_decision_packet',
    ) if issue_number else None
    lineage_packet = newest_packet(decision_packet, assignment_packet)
    payload = (lineage_packet or {}).get('payload') or {}
    canonical_branch = payload.get('canonical_branch') or (pr.get('headRefName') if pr else None)
    role_branch = payload.get('role_branch')
    reset_required = any(e.get('event_type') in {'reset_branch_required', 'reset_branch_recommended'} for e in escalations)
    lineage_state = payload.get('lineage_state')
    if lineage_state is None:
        if reset_required:
            lineage_state = 'reset_required'
        elif canonical_branch:
            lineage_state = 'active'
        else:
            lineage_state = 'unknown'
    return {
        'canonical_branch': canonical_branch,
        'active_role_branch': role_branch,
        'branch_owner_role': payload.get('branch_owner_role') or ('TechLead' if lineage_packet else None),
        'lineage_state': lineage_state,
        'latest_lineage_action': payload.get('lineage_action'),
        'source_branch': payload.get('source_branch'),
        'superseded_branch': payload.get('superseded_branch'),
        'worktree_hint': payload.get('worktree_hint'),
        'reset_reason': payload.get('reset_reason'),
        'current_packet_type': lineage_packet.get('schema_type') if lineage_packet else None,
        'current_packet_message_id': lineage_packet.get('message_id') if lineage_packet else None,
        'current_packet_queue': lineage_packet.get('queue_name') if lineage_packet else None,
    }


def action_type_for_role(role):
    mapping = {
        'Delivery Architect': 'route_to_delivery_architect',
        'Python Dev': 'route_to_python',
        'QA': 'route_to_qa',
        'Authority Architect': 'route_to_architect',
        'Architect': 'route_to_architect',
        'TechLead': 'route_to_techlead',
    }
    return mapping.get(role, 'route_to_techlead')


def techlead_assignment_role(raw_role):
    mapping = {
        'Python Dev': 'python-team',
        'QA': 'qa',
        'Delivery Architect': 'delivery-architect',
    }
    return mapping.get(raw_role)


def parse_created_at(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except Exception:
        return None


def latest_issue_comment(issue, prefix):
    comments = issue.get('comments') or []
    latest = None
    for comment in comments:
        body = comment.get('body') or ''
        if body.startswith(prefix):
            latest = comment
    return latest


def latest_pr_comment(pr, prefix):
    comments = (pr or {}).get('comments') or []
    latest = None
    for comment in comments:
        body = comment.get('body') or ''
        if body.startswith(prefix):
            latest = comment
    return latest


def latest_comment_with_prefixes(comments, prefixes):
    latest = None
    for comment in comments or []:
        body = comment.get('body') or ''
        if any(body.startswith(prefix) for prefix in prefixes):
            latest = comment
    return latest


def comments_with_prefix(comments, prefix):
    matches = []
    for comment in comments or []:
        body = comment.get('body') or ''
        if body.startswith(prefix):
            matches.append(comment)
    return matches


def comments_with_prefixes(comments, prefixes):
    matches = []
    for comment in comments or []:
        body = comment.get('body') or ''
        if any(body.startswith(prefix) for prefix in prefixes):
            matches.append(comment)
    return matches


def latest_comment_before(comments, timestamp):
    base_time = parse_created_at(timestamp)
    if not base_time:
        return None
    latest = None
    latest_time = None
    for comment in comments or []:
        comment_time = parse_created_at(comment.get('createdAt'))
        if not comment_time or comment_time >= base_time:
            continue
        if latest_time is None or comment_time > latest_time:
            latest = comment
            latest_time = comment_time
    return latest


def comment_is_newer(comment, timestamp):
    comment_time = parse_created_at((comment or {}).get('createdAt'))
    base_time = parse_created_at(timestamp)
    if comment_time and base_time:
        return comment_time > base_time
    return False


def qa_packet_superseded(qa_packet, dev_queue_packet):
    if not qa_packet or not dev_queue_packet:
        return False
    qa_created = parse_created_at(qa_packet.get('created_at'))
    dev_created = parse_created_at(dev_queue_packet.get('created_at'))
    if qa_created and dev_created:
        return dev_created > qa_created
    return False


def derive_execution_state(issue, pr):
    if pr and pr.get('mergedAt'):
        return 'merged'
    if pr and pr.get('state') == 'OPEN' and pr.get('isDraft'):
        return 'draft'
    if pr and pr.get('state') == 'OPEN':
        return 'open'
    return issue['state'].lower()


def derive_ci_status(pr):
    if not pr:
        return 'unknown'
    checks = pr.get('statusCheckRollup') or []
    if not checks:
        return 'unknown'
    if any(check.get('__typename') == 'CheckRun' and check.get('conclusion') == 'SUCCESS' for check in checks):
        return 'green'
    if any(check.get('__typename') == 'CheckRun' and check.get('conclusion') in {'FAILURE', 'TIMED_OUT', 'CANCELLED'} for check in checks):
        return 'red'
    return 'pending'


def derive_workflow(current_task, issue, pr, qa_packet, queues):
    stage = 'blocked'
    owner = 'Unknown'
    escalations = []
    recommended = []
    unattended_safe = True
    issue_number = current_task['issue_number'] if current_task else None
    pending_dev_packet = latest_packet_preview(
        queues,
        issue_number,
        schema_type='slice_result_packet',
        to_role='techlead',
    ) if issue_number else None
    pending_qa_queue_packet = latest_packet_preview(
        queues,
        issue_number,
        schema_type='qa_verification_packet',
        to_role='techlead',
    ) if issue_number else None
    pending_assignment_packet = latest_packet_preview(
        queues,
        issue_number,
        schema_type='techlead_assignment_packet',
    ) if issue_number else None
    pending_decision_packet = latest_packet_preview(
        queues,
        issue_number,
        schema_type='techlead_decision_packet',
    ) if issue_number else None
    issue_comments = issue.get('comments') or []
    pr_comments = (pr or {}).get('comments') or []
    latest_python_handoff = latest_issue_comment(issue, 'Python Team handoff:')
    latest_python_update = latest_comment_with_prefixes(
        issue_comments,
        [
            'Python Team update after Architect scope rejection:',
            'Python Team correction after Architect scope rejection',
        ],
    )
    latest_qa_handoff = latest_issue_comment(issue, 'QA processed')
    latest_qa_review = latest_issue_comment(issue, 'QA review status:')
    latest_architect_rejection = latest_comment_with_prefixes(
        pr_comments,
        [
            'Architect review:',
            'Architect review on ',
        ],
    )
    architect_rejection_comments = comments_with_prefixes(
        pr_comments,
        [
            'Architect review:',
            'Architect review on ',
        ],
    )
    escalation_superseded = qa_packet_superseded(qa_packet, pending_dev_packet)
    if qa_packet and not escalation_superseded:
        if comment_is_newer(latest_python_handoff, qa_packet.get('created_at')) or comment_is_newer(latest_python_update, qa_packet.get('created_at')):
            escalation_superseded = True

    architect_rejected_after_qa = (
        qa_packet
        and latest_architect_rejection
        and comment_is_newer(latest_architect_rejection, qa_packet.get('created_at'))
        and not escalation_superseded
    )
    architect_rejection_before_rework = latest_comment_before(
        architect_rejection_comments,
        (latest_python_update or {}).get('createdAt'),
    )
    reset_required_after_failed_rework = (
        architect_rejection_before_rework
        and latest_python_update
        and latest_qa_review
        and comment_is_newer(latest_qa_review, (latest_python_update or {}).get('createdAt'))
        and 'needs_human_review' in ((latest_qa_review or {}).get('body') or '')
    )

    latest_techlead_packet = newest_packet(
        pending_decision_packet,
        pending_assignment_packet,
        pending_qa_queue_packet,
        pending_dev_packet,
    )

    if latest_techlead_packet and latest_techlead_packet.get('schema_type') == 'techlead_decision_packet':
        payload = latest_techlead_packet.get('payload') or {}
        target_role = payload.get('target_role') or 'TechLead'
        stage = 'techlead_decision_recorded'
        owner = 'TechLead'
        unattended_safe = False
        escalations.append({
            'event_type': 'techlead_decision_recorded',
            'severity': 'medium',
            'work_item_ref': {'issue_number': current_task['issue_number'], 'task_id': current_task['task_id']} if current_task else None,
            'summary': 'TechLead has already recorded the next routing or merge decision for the active slice.',
            'details': {
                'message_id': latest_techlead_packet.get('message_id'),
                'queue_name': latest_techlead_packet.get('queue_name'),
                'decision_type': payload.get('decision_type'),
                'target_role': target_role,
                'next_assignment_type': payload.get('next_assignment_type'),
                'source_packet_ref': payload.get('source_packet_ref'),
            },
            'recommended_route': target_role,
            'status': 'open',
        })
        recommended.append({
            'priority': 1,
            'action_type': action_type_for_role(target_role),
            'reason': 'TechLead has already recorded the next workflow decision; follow that decision rather than re-deriving the route from older packets.',
            'target_role': target_role,
            'blocking': True,
        })
        return stage, owner, escalations, recommended, unattended_safe

    if latest_techlead_packet and latest_techlead_packet.get('schema_type') == 'techlead_assignment_packet':
        payload = latest_techlead_packet.get('payload') or {}
        target_role = payload.get('target_role') or 'TechLead'
        stage = 'techlead_assignment_issued'
        owner = target_role
        unattended_safe = False
        escalations.append({
            'event_type': 'techlead_assignment_issued',
            'severity': 'medium',
            'work_item_ref': {'issue_number': current_task['issue_number'], 'task_id': current_task['task_id']} if current_task else None,
            'summary': 'TechLead has issued the next assignment packet for the active slice.',
            'details': {
                'message_id': latest_techlead_packet.get('message_id'),
                'queue_name': latest_techlead_packet.get('queue_name'),
                'assignment_type': payload.get('assignment_type'),
                'target_role': target_role,
                'canonical_branch': payload.get('canonical_branch'),
                'role_branch': payload.get('role_branch'),
                'allowed_result_types': payload.get('allowed_result_types'),
            },
            'recommended_route': target_role,
            'status': 'open',
        })
        recommended.append({
            'priority': 1,
            'action_type': action_type_for_role(target_role),
            'reason': 'TechLead has already issued a concrete assignment packet; the next step is for the target role to claim and execute it.',
            'target_role': target_role,
            'blocking': True,
        })
        return stage, owner, escalations, recommended, unattended_safe

    if latest_techlead_packet and latest_techlead_packet.get('schema_type') == 'qa_verification_packet':
        stage = 'techlead_qa_review_pending'
        owner = 'TechLead'
        unattended_safe = False
        details = {
            'message_id': latest_techlead_packet.get('message_id'),
            'schema_type': latest_techlead_packet.get('schema_type'),
            'queue_name': latest_techlead_packet.get('queue_name'),
        }
        if qa_packet:
            details['verification_status'] = qa_packet.get('verification_status')
        escalations.append({
            'event_type': 'qa_packet_waiting_for_techlead',
            'severity': 'high',
            'work_item_ref': {'issue_number': current_task['issue_number'], 'task_id': current_task['task_id']} if current_task else None,
            'summary': 'TechLead has a waiting QA verification result packet to review.',
            'details': details,
            'recommended_route': 'TechLead',
            'status': 'open',
        })
        recommended.append({
            'priority': 1,
            'action_type': 'route_to_techlead',
            'reason': 'A QA verification packet addressed to TechLead is waiting for a merge, rework, or escalation decision.',
            'target_role': 'TechLead',
            'blocking': True,
        })
        return stage, owner, escalations, recommended, unattended_safe

    if latest_techlead_packet and latest_techlead_packet.get('schema_type') == 'slice_result_packet':
        stage = 'techlead_dev_review_pending'
        owner = 'TechLead'
        unattended_safe = False
        escalations.append({
            'event_type': 'dev_packet_waiting_for_techlead',
            'severity': 'medium',
            'work_item_ref': {'issue_number': current_task['issue_number'], 'task_id': current_task['task_id']} if current_task else None,
            'summary': 'TechLead has a waiting Dev result packet to review before QA is assigned.',
            'details': {
                'message_id': latest_techlead_packet.get('message_id'),
                'schema_type': latest_techlead_packet.get('schema_type'),
                'queue_name': latest_techlead_packet.get('queue_name'),
            },
            'recommended_route': 'TechLead',
            'status': 'open',
        })
        recommended.append({
            'priority': 1,
            'action_type': 'route_to_techlead',
            'reason': 'A Dev result packet addressed to TechLead is waiting for the next routing decision.',
            'target_role': 'TechLead',
            'blocking': True,
        })
        return stage, owner, escalations, recommended, unattended_safe

    if queues['fractal-core-architecture']['messages_ready'] > 0:
        stage = 'ready_for_acceptance'
        owner = 'Architect'
        unattended_safe = False
        preview = queues['fractal-core-architecture'].get('preview') or []
        packet = preview[0]['payload_preview'] if preview else {}
        details = {
            'message_id': packet.get('message_id_external', packet.get('message_id')),
            'schema_type': packet.get('schema_type'),
        }
        payload = packet.get('payload', {}) if isinstance(packet, dict) else {}
        if payload.get('verification_status'):
            details['verification_status'] = payload.get('verification_status')
        escalations.append({
            'event_type': 'architect_packet_waiting',
            'severity': 'high',
            'work_item_ref': {'issue_number': current_task['issue_number'], 'task_id': current_task['task_id']} if current_task else None,
            'summary': 'Architect queue has a waiting packet.',
            'details': details,
            'recommended_route': 'Architect',
            'status': 'open',
        })
        if reset_required_after_failed_rework:
            escalations.append({
                'event_type': 'reset_branch_recommended',
                'severity': 'high',
                'work_item_ref': {'issue_number': current_task['issue_number'], 'task_id': current_task['task_id']},
                'summary': 'The current slice has repeated the same scope failure after an in-place narrowing attempt; a reset branch recovery should be chosen instead of another incremental cleanup pass.',
                'details': {
                    'architect_rejection_comment_at': (architect_rejection_before_rework or {}).get('createdAt'),
                    'python_rework_comment_at': (latest_python_update or {}).get('createdAt'),
                    'qa_repeat_review_comment_at': (latest_qa_review or {}).get('createdAt'),
                },
                'recommended_route': 'Architect',
                'status': 'open',
            })
            recommended.insert(0, {
                'priority': 1,
                'action_type': 'route_to_architect_for_reset_decision',
                'reason': 'A repeated QA scope escalation after an Architect-directed rework indicates branch contamination; Architect should record a reset-branch recovery decision instead of requesting another in-place cleanup.',
                'target_role': 'Architect',
                'blocking': True,
            })
        recommended.append({
            'priority': 1,
            'action_type': 'route_to_architect',
            'reason': 'Architect queue has a waiting acceptance packet.',
            'target_role': 'Architect',
            'blocking': True,
        })
        return stage, owner, escalations, recommended, unattended_safe

    if qa_packet and escalation_superseded and issue['state'] == 'OPEN' and pr and pr.get('state') == 'OPEN':
        stage = 'qa_pending'
        owner = 'QA'
        unattended_safe = False
        escalations.append({
            'event_type': 'qa_escalation_superseded',
            'severity': 'low',
            'work_item_ref': {'issue_number': current_task['issue_number'], 'task_id': current_task['task_id']},
            'summary': 'A newer Python rework/handoff has superseded the earlier QA escalation for this issue.',
            'details': {
                'superseded_qa_packet_id': qa_packet.get('message_id'),
                'latest_python_handoff_comment_at': (latest_python_handoff or {}).get('createdAt'),
                'latest_python_update_comment_at': (latest_python_update or {}).get('createdAt'),
                'latest_qa_handoff_comment_at': (latest_qa_handoff or {}).get('createdAt'),
            },
            'recommended_route': 'QA',
            'status': 'suppressed',
        })
        recommended.append({
            'priority': 1,
            'action_type': 'route_to_qa',
            'reason': 'Python has posted a newer narrowed handoff for the same issue; fresh QA verification is the next step.',
            'target_role': 'QA',
            'blocking': True,
        })
        return stage, owner, escalations, recommended, unattended_safe

    if architect_rejected_after_qa and issue['state'] == 'OPEN' and pr and pr.get('state') == 'OPEN':
        if reset_required_after_failed_rework:
            stage = 'dev_reset_required'
        else:
            stage = 'dev_rework_required'
        owner = 'Python Dev'
        unattended_safe = False
        if reset_required_after_failed_rework:
            escalations.append({
                'event_type': 'reset_branch_required',
                'severity': 'high',
                'work_item_ref': {'issue_number': current_task['issue_number'], 'task_id': current_task['task_id']},
                'summary': 'The issue has repeated the same scope failure after an in-place rework. The correct recovery is a clean reset branch from main, not another incremental narrowing pass.',
                'details': {
                    'qa_packet_id': qa_packet.get('message_id'),
                    'verification_status': qa_packet.get('verification_status'),
                    'architect_comment_at': (architect_rejection_before_rework or {}).get('createdAt'),
                    'architect_comment_url': (architect_rejection_before_rework or {}).get('url'),
                    'python_rework_comment_at': (latest_python_update or {}).get('createdAt'),
                    'qa_repeat_review_comment_at': (latest_qa_review or {}).get('createdAt'),
                },
                'recommended_route': 'Python Dev',
                'status': 'open',
            })
            recommended.append({
                'priority': 1,
                'action_type': 'route_to_python_reset_branch',
                'reason': 'A second QA scope escalation after Architect-directed rework is a reliable contamination signal; rebuild the slice on a fresh branch from current main.',
                'target_role': 'Python Dev',
                'blocking': True,
            })
        else:
            escalations.append({
                'event_type': 'architect_rejection_recorded',
                'severity': 'high',
                'work_item_ref': {'issue_number': current_task['issue_number'], 'task_id': current_task['task_id']},
                'summary': 'Architect has already reviewed the QA escalation and rejected the current PR head pending a narrower rework.',
                'details': {
                    'qa_packet_id': qa_packet.get('message_id'),
                    'verification_status': qa_packet.get('verification_status'),
                    'architect_comment_at': (latest_architect_rejection or {}).get('createdAt'),
                    'architect_comment_url': (latest_architect_rejection or {}).get('url'),
                },
                'recommended_route': 'Python Dev',
                'status': 'open',
            })
            recommended.append({
                'priority': 1,
                'action_type': 'route_to_python',
                'reason': 'Architect has already rejected the current head and asked for the slice to be narrowed before any fresh QA review.',
                'target_role': 'Python Dev',
                'blocking': True,
            })
        return stage, owner, escalations, recommended, unattended_safe

    if qa_packet and issue['state'] == 'OPEN' and pr and pr.get('state') == 'OPEN':
        verdict = qa_packet.get('verification_status')
        if verdict == 'needs_human_review' and not escalation_superseded:
            stage = 'techlead_qa_review_pending'
            owner = 'TechLead'
            unattended_safe = False
            escalations.append({
                'event_type': 'qa_escalation_pending',
                'severity': 'high',
                'work_item_ref': {'issue_number': current_task['issue_number'], 'task_id': current_task['task_id']},
                'summary': 'QA has escalated the active slice for Architect review.',
                'details': {
                    'qa_packet_id': qa_packet.get('message_id'),
                    'verification_status': verdict,
                    'recommended_action': qa_packet.get('recommended_action', {}),
                    'scope': qa_packet.get('technical_scope_checks', {}),
                    'path': qa_packet.get('path'),
                },
                'recommended_route': 'TechLead',
                'status': 'open',
            })
            recommended.append({
                'priority': 1,
                'action_type': 'route_to_techlead',
                'reason': 'QA marked the current slice needs_human_review and TechLead should make the next routing decision.',
                'target_role': 'TechLead',
                'blocking': True,
            })
            return stage, owner, escalations, recommended, unattended_safe
        if verdict == 'pass':
            stage = 'techlead_qa_review_pending'
            owner = 'TechLead'
            unattended_safe = False
            escalations.append({
                'event_type': 'qa_pass_pending_acceptance',
                'severity': 'medium',
                'work_item_ref': {'issue_number': current_task['issue_number'], 'task_id': current_task['task_id']},
                'summary': 'QA passed the active slice, but Architect acceptance is still pending.',
                'details': {
                    'qa_packet_id': qa_packet.get('message_id'),
                    'path': qa_packet.get('path'),
                },
                'recommended_route': 'TechLead',
                'status': 'open',
            })
            recommended.append({
                'priority': 1,
                'action_type': 'route_to_techlead',
                'reason': 'QA pass is recorded locally, and TechLead should decide whether the slice is ready for merge preparation.',
                'target_role': 'TechLead',
                'blocking': True,
            })
            return stage, owner, escalations, recommended, unattended_safe

    if queues['fractal-core-python']['messages_ready'] > 0:
        stage = 'architect_authorized'
        owner = 'Python Dev'
        recommended.append({
            'priority': 1,
            'action_type': 'route_to_python',
            'reason': 'Python queue has a waiting Architect packet.',
            'target_role': 'Python Dev',
            'blocking': False,
        })
        return stage, owner, escalations, recommended, unattended_safe

    if issue['state'] == 'OPEN' and pr and pr.get('state') == 'OPEN':
        stage = 'dev_in_progress'
        owner = 'Python Dev'
        recommended.append({
            'priority': 2,
            'action_type': 'monitor_dev',
            'reason': f'Issue #{issue["number"]} has an open PR but no waiting queue handoff.',
            'target_role': 'Python Dev',
            'blocking': False,
        })
        return stage, owner, escalations, recommended, unattended_safe

    if current_task:
        stage = 'dev_in_progress'
        owner = 'Python Dev'

    return stage, owner, escalations, recommended, unattended_safe


def build_report():
    current, manifest = load_authority()
    tasks = current.get('tasks', [])
    current_task = tasks[0] if tasks else None
    queues = queue_state()
    auto_roles, architect_missing = automation_state()
    authority_version = manifest['project']['authority_version']
    authority_status, mirrors = mirror_status(authority_version)

    active_work = None
    escalations = []
    recommended = []
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
    }

    if current_task:
        qa_packet = latest_qa_packet(current_task['issue_number'])
        fallback_pr_number = qa_packet.get('pr_number') if qa_packet else None
        issue, pr = github_state(current_task['issue_number'], fallback_pr_number=fallback_pr_number)
        workflow_stage, owner_role, wf_escalations, wf_recommended, wf_safe = derive_workflow(current_task, issue, pr, qa_packet, queues)
        escalations.extend(wf_escalations)
        recommended.extend(wf_recommended)
        unattended_safe = unattended_safe and wf_safe
        lineage = derive_lineage_section(current_task, pr, queues, escalations)

        last_qa_verdict = qa_packet.get('verification_status') if qa_packet else 'unknown'
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
        verification = {
            'protected_path': 'pass' if qa_packet and qa_packet.get('protected_path_checks', {}).get('protected_10000_step_parity_passed') else 'unknown',
            'scope': 'fail' if qa_packet and qa_packet.get('technical_scope_checks', {}).get('unauthorized_scope_widening') else ('pass' if qa_packet and qa_packet.get('verification_status') == 'pass' else 'unknown'),
            'last_qa_verdict': last_qa_verdict,
            'effective_verification_state': effective_verification_state,
            'qa_packet_path': qa_packet.get('path') if qa_packet else None,
        }

        active_work = {
            'work_item': {
                'issue_number': current_task['issue_number'],
                'task_id': current_task['task_id'],
                'title': current_task['title'],
                'status': current_task['status'],
                'authority_version': authority_version,
            },
            'execution': {
                'pr_number': pr['number'] if pr else None,
                'branch': pr['headRefName'] if pr else None,
                'state': derive_execution_state(issue, pr),
                'ci_status': derive_ci_status(pr),
                'is_draft': bool(pr.get('isDraft')) if pr else None,
            },
            'verification': verification,
        }

    active_issue_number = ((active_work or {}).get('work_item') or {}).get('issue_number')
    traceability = load_traceability_section(
        DEFAULT_DB_CONTAINER,
        DEFAULT_DB_NAME,
        DEFAULT_DB_USER,
        DEFAULT_PROJECT_SLUG,
        active_issue_number,
    )

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

    report = {
        'report_id': f'techlead-{datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")}',
        'project_id': 'fractal-core-python',
        'captured_at': datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z'),
        'captured_by': {
            'role': 'TechLead',
            'agent_name': 'Fractal Core TechLead CLI',
            'agent_type': 'automation',
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
        'queues': {q: {
            'ready': queues[q]['messages_ready'],
            'unacknowledged': queues[q]['messages_unacknowledged'],
            'latest_message': (queues[q].get('preview') or [None])[0]['payload_preview'] if queues[q].get('preview') else None,
        } for q in QUEUE_NAMES},
        'lineage': lineage,
        'automations': {'roles': auto_roles},
        'traceability': traceability,
        'escalations': escalations,
        'recommended_actions': recommended,
        'unattended_safe': unattended_safe,
        'summary': f"Current owner: {owner_role}. Authority {authority_status}. Unattended safe: {'yes' if unattended_safe else 'no'}."
    }
    return report


def validate_report(report, schema_path: Path):
    try:
        import jsonschema
    except ImportError as exc:
        raise RuntimeError('jsonschema is not installed; run `python3 -m pip install --user jsonschema`') from exc
    schema = json.loads(schema_path.read_text())
    jsonschema.Draft202012Validator(schema).validate(report)


def resolve_agent_id(db_container, db_name, db_user, project_slug, agent_name):
    sql = f"""
    SELECT a.agent_id
    FROM paa.agents a
    JOIN paa.projects p ON p.project_id = a.project_id
    WHERE p.slug = {sql_literal(project_slug)}
      AND a.name = {sql_literal(agent_name)}
    LIMIT 1;
    """
    output = run_psql(db_container, db_name, db_user, sql).strip()
    return output or None


def resolve_work_item_id(db_container, db_name, db_user, project_slug, issue_number):
    if issue_number is None:
        return None
    sql = f"""
    SELECT wi.work_item_id
    FROM paa.work_items wi
    JOIN paa.projects p ON p.project_id = wi.project_id
    WHERE p.slug = {sql_literal(project_slug)}
      AND wi.issue_number = {issue_number}
    LIMIT 1;
    """
    output = run_psql(db_container, db_name, db_user, sql).strip()
    return output or None


def load_traceability_section(db_container, db_name, db_user, project_slug, active_issue_number):
    section = {
        'status': 'unavailable',
        'view_name': 'paa.v_work_item_full_chain_traceability',
        'error_message': None,
        'latest_accepted_chain': None,
        'active_work_chain': None,
    }

    def load_row(sql):
        if not sql:
            return None
        output = run_psql(db_container, db_name, db_user, sql).strip()
        if not output:
            return None
        return json.loads(output)

    try:
        latest_sql = f"""
        SELECT row_to_json(t)::text
        FROM (
          SELECT
            issue_number,
            work_item_title,
            work_item_status,
            package_id_external,
            brief_id_external,
            component_name,
            component_role,
            system_layer,
            full_chain_state,
            dev_message_id,
            qa_message_id,
            acceptance_decision,
            acceptance_created_at,
            last_transition_at
          FROM paa.v_work_item_full_chain_traceability
          WHERE project_slug = {sql_literal(project_slug)}
            AND full_chain_state = 'accepted_full_chain'
          ORDER BY COALESCE(acceptance_created_at, last_transition_at) DESC NULLS LAST, issue_number DESC
          LIMIT 1
        ) t;
        """
        active_sql = None
        if active_issue_number is not None:
            active_sql = f"""
            SELECT row_to_json(t)::text
            FROM (
              SELECT
                issue_number,
                work_item_title,
                work_item_status,
                package_id_external,
                brief_id_external,
                component_name,
                component_role,
                system_layer,
                full_chain_state,
                dev_message_id,
                qa_message_id,
                acceptance_decision,
                acceptance_created_at,
                last_transition_at
              FROM paa.v_work_item_full_chain_traceability
              WHERE project_slug = {sql_literal(project_slug)}
                AND issue_number = {sql_literal(active_issue_number)}
              LIMIT 1
            ) t;
            """
        section['latest_accepted_chain'] = load_row(latest_sql)
        section['active_work_chain'] = load_row(active_sql)
        section['status'] = 'available'
    except Exception as exc:
        section['error_message'] = str(exc)
    return section


def resolve_issue_number_from_package(package: dict, package_id_external: str) -> int:
    authority_context = package.get('authority_context') or {}
    issue_number = authority_context.get('issue_number')
    if issue_number is not None:
        return int(issue_number)
    task_issue_number = authority_context.get('task_issue_number')
    if task_issue_number is not None:
        return int(task_issue_number)
    match = re.search(r'issue(\\d+)', package_id_external)
    if match:
        return int(match.group(1))
    raise RuntimeError(
        f'Could not resolve issue_number from package {package_id_external!r}; '
        'package authority_context has no issue_number and package_id_external does not contain issueNNN.'
    )


def resolve_task_summary(manifest: dict, package: dict, issue_number: int) -> dict:
    authority_context = package.get('authority_context') or {}
    task_id = authority_context.get('task_id')
    task_title = None
    task_status = None
    for task in (manifest.get('tasks') or []):
        if task_id and task.get('task_id') == task_id:
            task_title = task.get('title')
            task_status = task.get('status')
            break
        if task.get('issue_number') == issue_number:
            task_id = task.get('task_id') or task_id
            task_title = task.get('title')
            task_status = task.get('status')
            break
    if task_id is None:
        task_id = authority_context.get('task_id') or f'issue-{issue_number}'
    return {
        'issue_number': issue_number,
        'task_id': task_id,
        'title': task_title or f'Issue #{issue_number}',
        'status': task_status or 'unknown',
    }


def default_assignment_paths(repo_root: Path, issue_number: int, target_role: str) -> tuple[Path, Path]:
    slug = target_role.replace(' ', '-').lower()
    reports_dir = repo_reports_dir(repo_root)
    output = reports_dir / f'techlead-assignment.issue{issue_number}.{slug}.json'
    review = reports_dir / f'techlead-assignment.issue{issue_number}.{slug}.md'
    return output, review


def derive_next_assignment_context(args) -> dict:
    repo_root = args.repo_root.resolve()
    current, manifest = load_authority(repo_root)
    package = load_design_package(args.project_slug, args.package_id_external)
    issue_number = resolve_issue_number_from_package(package, args.package_id_external)
    current_task = resolve_task_summary(manifest, package, issue_number)
    queues = queue_state(repo_root)
    qa_packet = latest_qa_packet(issue_number, repo_reports_dir(repo_root))
    issue, pr = github_state(issue_number, fallback_pr_number=qa_packet.get('pr_number') if qa_packet else None)
    workflow_stage, owner_role, _escalations, recommended, unattended_safe = derive_workflow(current_task, issue, pr, qa_packet, queues)
    pending_dev_packet = latest_packet_preview(
        queues,
        issue_number,
        schema_type='slice_result_packet',
        to_role='techlead',
    )
    if args.target_role == 'python-team':
        if not pr:
            return {
                'ok': False,
                'workflow_stage': workflow_stage,
                'reason': 'explicit_python_dev_emission_requires_active_pr',
                'details': 'No PR was available from GitHub state for the selected issue, so Python Dev emission could not derive PR context.',
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
            'target_role': 'Python Dev',
            'target_role_cli': 'python-team',
            'assignment_type': 'implement_authorized_slice',
            'allowed_result_types': [
                'implemented_ready_for_qa',
                'blocked',
                'needs_clarification',
            ],
            'assignment_summary': (
                f'TechLead is explicitly issuing a Python Dev implementation assignment for issue #{issue_number} '
                f'on branch {branch_name}.'
            ),
            'source_packet_message_id': None,
            'source_packet_path': None,
            'issue': issue,
            'pr': pr,
            'recommended_actions': recommended,
            'unattended_safe': unattended_safe,
        }
    if workflow_stage == 'techlead_dev_review_pending' and pending_dev_packet:
        if not pr:
            return {
                'ok': False,
                'workflow_stage': workflow_stage,
                'reason': 'dev_review_pending_but_no_pr_context',
                'details': 'A Dev result packet is waiting for TechLead, but no PR context could be derived from GitHub state.',
            }
        branch_name = pr.get('headRefName') or f'issue-{issue_number}'
        source_message_id = pending_dev_packet.get('message_id')
        return {
            'ok': True,
            'workflow_stage': workflow_stage,
            'issue_number': issue_number,
            'issue_url': issue.get('url'),
            'pr_number': pr.get('number'),
            'pr_url': pr.get('url'),
            'branch': branch_name,
            'target_role': 'QA',
            'target_role_cli': 'qa',
            'assignment_type': 'verify_authorized_slice',
            'allowed_result_types': [
                'pass',
                'fail_fixable',
                'needs_human_review',
            ],
            'assignment_summary': (
                f'TechLead is routing Dev result packet {source_message_id} '
                f'for issue #{issue_number} to QA on branch {branch_name}.'
            ),
            'source_packet_message_id': source_message_id,
            'source_packet_path': None,
            'issue': issue,
            'pr': pr,
            'recommended_actions': recommended,
            'unattended_safe': unattended_safe,
        }
    return {
        'ok': False,
        'workflow_stage': workflow_stage,
        'reason': 'no_supported_emission_available',
        'details': (
            f'Current workflow stage {workflow_stage!r} does not support next-assignment emission in this slice. '
            'Only techlead_dev_review_pending -> QA and explicit Python Dev emission are supported.'
        ),
        'recommended_actions': recommended,
        'unattended_safe': unattended_safe,
    }


def emit_next_assignment(args):
    repo_root = args.repo_root.resolve()
    context = derive_next_assignment_context(args)
    if not context.get('ok'):
        return context
    default_output_path, default_review_output_path = default_assignment_paths(
        repo_root,
        context['issue_number'],
        context['target_role'],
    )
    output_path = args.output or default_output_path
    review_output_path = args.review_output or default_review_output_path
    output_path = output_path.resolve()
    review_output_path = review_output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    review_output_path.parent.mkdir(parents=True, exist_ok=True)

    auth_script = repo_auth_script(repo_root)
    auth_current = repo_auth_current(repo_root)
    queue_script = repo_queue_script(repo_root)
    compile_cmd = [
        str(auth_script),
        'authority',
        'materialize-techlead-assignment-packet',
        '--manifest', str(auth_current),
        '--project-slug', args.project_slug,
        '--package-id-external', args.package_id_external,
        '--brief-id-external', args.brief_id_external,
        '--repo', 'billyweisberg/fractal-core-python',
        '--issue-number', str(context['issue_number']),
        '--issue-url', str(context['issue_url']),
        '--pr-number', str(context['pr_number']),
        '--pr-url', str(context['pr_url']),
        '--branch', str(context['branch']),
        '--target-role', context['target_role_cli'],
        '--assignment-type', context['assignment_type'],
        '--assignment-summary', context['assignment_summary'],
        '--output', str(output_path),
        '--review-output', str(review_output_path),
        '--persist-db',
    ]
    if context.get('source_packet_path'):
        compile_cmd.extend(['--source-packet-path', str(context['source_packet_path'])])
    if context.get('source_packet_message_id'):
        compile_cmd.extend(['--source-packet-message-id', str(context['source_packet_message_id'])])
    for allowed_result_type in context['allowed_result_types']:
        compile_cmd.extend(['--allowed-result-type', allowed_result_type])

    compile_result = run_json(compile_cmd)
    validate_cmd = [
        str(queue_script),
        'techlead-validate-packet',
        '--message-file', str(output_path),
    ]
    validate_code, validate_result, validate_error = run_json_with_errors(validate_cmd)
    result = {
        'ok': validate_code == 0,
        'workflow_stage': context['workflow_stage'],
        'derived_decision': {
            'target_role': context['target_role'],
            'assignment_type': context['assignment_type'],
            'allowed_result_types': context['allowed_result_types'],
        },
        'package_id_external': args.package_id_external,
        'brief_id_external': args.brief_id_external,
        'output_path': str(output_path),
        'review_output_path': str(review_output_path),
        'message_id': compile_result.get('message_id'),
        'automation_run_id': compile_result.get('automation_run_id'),
        'resolved_queue': validate_result.get('resolved_queue') if validate_result else None,
        'sent': False,
        'compile': compile_result,
        'validate': validate_result,
        'source_packet_ref': {
            'message_id': context.get('source_packet_message_id'),
            'path': context.get('source_packet_path'),
        },
    }
    if validate_code != 0:
        result['error'] = validate_error
        return result
    if args.send:
        send_cmd = [
            str(queue_script),
            'techlead-send-packet',
            '--repo-root', str(repo_root),
            '--message-file', str(output_path),
        ]
        send_code, send_result, send_error = run_json_with_errors(send_cmd)
        result['send'] = send_result
        result['sent'] = send_code == 0 and bool(send_result and send_result.get('ok'))
        if send_code != 0:
            result['ok'] = False
            result['error'] = send_error
    return result


def persist_report(report, args):
    agent_id = resolve_agent_id(
        args.db_container,
        args.db_name,
        args.db_user,
        args.project_slug,
        args.agent_name,
    )
    if agent_id is None:
        raise RuntimeError(
            f"Could not resolve TechLead agent {args.agent_name!r} in project {args.project_slug!r}."
        )

    issue_number = ((report.get('active_work') or {}).get('work_item') or {}).get('issue_number')
    work_item_id = resolve_work_item_id(
        args.db_container,
        args.db_name,
        args.db_user,
        args.project_slug,
        issue_number,
    )

    artifact_payload = {
        'schema_path': str(args.schema),
        'schema_validated': bool(args.validate_schema),
        'project_slug': args.project_slug,
        'active_issue_number': issue_number,
        'report': report,
    }
    captured_at = report.get('captured_at')
    trigger_type = 'techlead_status_report'
    summary = report.get('summary')
    artifact_json = json.dumps(artifact_payload)
    sql = f"""
    INSERT INTO paa.automation_runs (
      agent_id,
      work_item_id,
      trigger_type,
      status,
      started_at,
      finished_at,
      summary,
      artifacts_json
    )
    VALUES (
      {sql_literal(agent_id)},
      {sql_literal(work_item_id)},
      {sql_literal(trigger_type)},
      'completed',
      {sql_literal(captured_at)}::timestamptz,
      {sql_literal(captured_at)}::timestamptz,
      {sql_literal(summary)},
      {sql_literal(artifact_json)}::jsonb
    )
    RETURNING automation_run_id;
    """
    automation_run_id = run_psql(args.db_container, args.db_name, args.db_user, sql).strip()
    if not automation_run_id:
        raise RuntimeError('TechLead report insert did not return an automation_run_id.')
    return {
        'automation_run_id': automation_run_id,
        'agent_id': agent_id,
        'work_item_id': work_item_id,
        'project_slug': args.project_slug,
    }


def parse_args(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(description='Fractal Core TechLead runtime.')
    sub = parser.add_subparsers(dest='command')

    status = sub.add_parser('status')
    status.add_argument('--output', type=Path, help='Write the JSON report to this path.')
    status.add_argument('--schema', type=Path, default=DEFAULT_SCHEMA, help='Schema path to use with --validate-schema.')
    status.add_argument('--validate-schema', action='store_true', help='Validate the generated report against the TechLead JSON schema.')
    status.add_argument('--persist-db', action='store_true', help='Persist the generated report into paa.automation_runs.')
    status.add_argument('--db-container', default=DEFAULT_DB_CONTAINER, help='Docker container running Postgres.')
    status.add_argument('--db-name', default=DEFAULT_DB_NAME, help='Postgres database name.')
    status.add_argument('--db-user', default=DEFAULT_DB_USER, help='Postgres database user.')
    status.add_argument('--project-slug', default=DEFAULT_PROJECT_SLUG, help='PAA project slug to resolve agent and work item IDs.')
    status.add_argument('--agent-name', default=DEFAULT_AGENT_NAME, help='PAA agent name used for TechLead persistence.')

    emit = sub.add_parser('emit-next-assignment')
    emit.add_argument('--repo-root', type=Path, default=REPO_ROOT, help='Consumer repo root for dispatch commands.')
    emit.add_argument('--package-id-external', required=True)
    emit.add_argument('--brief-id-external', required=True)
    emit.add_argument('--project-slug', default=DEFAULT_PROJECT_SLUG)
    emit.add_argument('--target-role', choices=['python-team', 'qa'], help='Explicitly request a supported target role. Omit to derive from current TechLead-visible workflow state.')
    emit.add_argument('--send', action='store_true', help='Send the compiled packet after validation succeeds.')
    emit.add_argument('--output', type=Path, help='Write the compiled packet JSON to this path.')
    emit.add_argument('--review-output', type=Path, help='Write the compiled packet review markdown to this path.')

    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.command in {None, 'status'}:
        report = build_report()
        if args.validate_schema:
            validate_report(report, args.schema)
        persistence = None
        if args.persist_db:
            persistence = persist_report(report, args)
        text = json.dumps(report, indent=2)
        if args.output:
            args.output.write_text(text + '\n')
        if persistence:
            sys.stderr.write(
                f"Persisted TechLead report to {args.db_name} as automation_run_id={persistence['automation_run_id']}"
            )
            if persistence.get('work_item_id'):
                sys.stderr.write(f" work_item_id={persistence['work_item_id']}")
            sys.stderr.write('\n')
        sys.stdout.write(text)
        sys.stdout.write('\n')
        return 0
    if args.command == 'emit-next-assignment':
        result = emit_next_assignment(args)
        sys.stdout.write(json.dumps(result, indent=2))
        sys.stdout.write('\n')
        return 0 if result.get('ok') else 1
    return 2


if __name__ == '__main__':
    raise SystemExit(main())

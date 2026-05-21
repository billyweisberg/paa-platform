#!/usr/bin/env python3
import argparse
import json
import os
import re
import subprocess
import sys
from types import SimpleNamespace
from datetime import datetime, timezone
from pathlib import Path

from paa_core.db import run_psql as shared_run_psql, settings_from_profile, settings_with_overrides
from paa_core import handoff_runtime
from paa_core.policies.acceptance import DefaultAcceptancePolicy
from paa_core.policies.deployment_capability import DefaultDeploymentCapabilityPolicy
from paa_core.policies.reset_recovery import DefaultResetRecoveryPolicy
from paa_core.policies.workflow_transition import DefaultWorkflowTransitionPolicy
from paa_core.repositories.execution_package import PostgresExecutionPackageRepository
from paa_core.repositories.runtime_event import PostgresRuntimeEventRepository
from paa_core.repositories.workflow_state import PostgresWorkflowStateRepository
from paa_core.runtime_paths import repo_authority_manifest_path
from paa_core.services.execution_package_resolution import (
    DefaultExecutionPackageResolutionService,
    ExecutionPackageResolutionRequest,
)
from paa_core.services.workflow_lifecycle import (
    DefaultWorkflowLifecycleService,
    WorkflowLifecycleRequest,
)
from paa_core.team_worker_roles import (
    active_team_worker_roles,
    team_worker_role_by_display_name,
    team_worker_role_by_key,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_DB_PROFILE = os.environ.get('PAA_DB_PROFILE', 'paa_dev')
DEFAULT_DB_SETTINGS = settings_from_profile(DEFAULT_DB_PROFILE)
DEFAULT_DB_CONTAINER = DEFAULT_DB_SETTINGS.container
DEFAULT_DB_NAME = DEFAULT_DB_SETTINGS.name
DEFAULT_DB_USER = DEFAULT_DB_SETTINGS.user
DEFAULT_PROJECT_SLUG = 'fractal-core-python'
DEFAULT_AGENT_NAME = 'Fractal Core TechLead Automation'
ROLE_CONFIG = {
    'Architect': {'dir': 'fractal-core-delivery-architect-automation', 'root': str(REPO_ROOT)},
    'QA': {'dir': 'fractal-core-qa-automation', 'root': str(REPO_ROOT)},
    'TechLead': {'dir': 'fractal-core-techlead-automation', 'root': str(REPO_ROOT)},
}
for _worker_role in active_team_worker_roles(repo_root=REPO_ROOT):
    ROLE_CONFIG[_worker_role.display_name] = {'dir': _worker_role.automation_id, 'root': str(REPO_ROOT)}

ROLE_BRANCH_SUFFIX = {
    'delivery-architect': 'delivery',
    'qa': 'qa',
}
ROLE_BRANCH_SUFFIX.update({role.key: role.branch_suffix for role in active_team_worker_roles(repo_root=REPO_ROOT)})

ROLE_LABEL_BY_CLI = {
    'delivery-architect': 'Delivery Architect',
    'qa': 'QA',
}
ROLE_LABEL_BY_CLI.update({role.key: role.display_name for role in active_team_worker_roles(repo_root=REPO_ROOT)})

ROLE_CLI_BY_SUFFIX = {
    'delivery': 'delivery-architect',
    'qa': 'qa',
}
ROLE_CLI_BY_SUFFIX.update({role.branch_suffix: role.key for role in active_team_worker_roles(repo_root=REPO_ROOT)})
TEAM_WORKER_CLI_CHOICES = [role.key for role in active_team_worker_roles(repo_root=REPO_ROOT)]
ROLE_BRIDGE_TARGET_CHOICES = ['delivery-architect', *TEAM_WORKER_CLI_CHOICES, 'qa']
ROLE_EMIT_TARGET_CHOICES = ['delivery-architect', *TEAM_WORKER_CLI_CHOICES, 'qa']
PREFLIGHT_TARGET_CHOICES = ['techlead', 'delivery-architect', *TEAM_WORKER_CLI_CHOICES, 'qa']
QUEUE_NAMES = ['fractal-core-python', 'fractal-core-qa', 'fractal-core-architecture']
QUEUE_PREVIEW_DEPTH = 10
ROLE_QUEUE_GATE = {
    'delivery-architect': {
        'queue_name': 'fractal-core-architecture',
        'to_role': 'Delivery Architect',
        'schema_types': {'techlead_assignment_packet'},
    },
    'python-team': {
        'queue_name': 'fractal-core-python',
        'to_role': 'Python Dev',
        'schema_types': {'techlead_assignment_packet', 'architect_cycle_packet'},
    },
    'qa': {
        'queue_name': 'fractal-core-qa',
        'to_role': 'QA',
        'schema_types': {'techlead_assignment_packet'},
    },
}
for _worker_role in active_team_worker_roles(repo_root=REPO_ROOT):
    ROLE_QUEUE_GATE[_worker_role.key] = {
        'queue_name': 'fractal-core-python',
        'to_role': _worker_role.display_name,
        'schema_types': {'techlead_assignment_packet', 'architect_cycle_packet'},
    }
TECHLEAD_GATE_SCHEMA_TYPES = {
    'slice_result_packet',
    'worker_result_packet',
    'qa_verification_packet',
    'delivery_review_packet',
    'techlead_decision_packet',
}


def team_worker_role_for_cli(target_role: str, repo_root: Path | None = None):
    return team_worker_role_by_key(target_role, repo_root=(repo_root or REPO_ROOT))


def team_worker_role_for_label(role_label: str, repo_root: Path | None = None):
    return team_worker_role_by_display_name(role_label, repo_root=(repo_root or REPO_ROOT))


def is_team_worker_cli(target_role: str, repo_root: Path | None = None) -> bool:
    return team_worker_role_for_cli(target_role, repo_root=repo_root) is not None


def is_team_worker_label(role_label: str, repo_root: Path | None = None) -> bool:
    return team_worker_role_for_label(role_label, repo_root=repo_root) is not None


def repo_auth_script(repo_root: Path) -> Path:
    return repo_root / '.codex' / 'paa' / 'bin' / 'paa-producer'


def repo_queue_script(repo_root: Path) -> Path:
    return repo_root / '.codex' / 'paa' / 'bin' / 'paa-consumer'


def repo_automations_dir(repo_root: Path) -> Path:
    return repo_root / '.codex' / 'automations'


def _repo_auth_manifest_from_execution_context(repo_root: Path) -> Path | None:
    try:
        service = DefaultExecutionPackageResolutionService(
            repository=PostgresExecutionPackageRepository(),
            capability_policy=DefaultDeploymentCapabilityPolicy(),
        )
        view = service.resolve_execution_context_for_repo_root(
            str(repo_root.resolve()),
            ExecutionPackageResolutionRequest(
                required_artifact_refs=('installed_manifest',),
                metadata={'consumer': 'techlead'},
            ),
        )
    except Exception:
        return None
    if not view.capability_summary.allowed or not view.manifest_path:
        return None
    manifest_path = Path(view.manifest_path).expanduser().resolve()
    if not manifest_path.exists():
        return None
    return manifest_path


def workflow_lifecycle_worker_result_evaluation(
    *,
    current_task: dict | None,
    packet: dict,
    project_slug: str = DEFAULT_PROJECT_SLUG,
    db_profile: str = DEFAULT_DB_PROFILE,
    db_container: str = DEFAULT_DB_CONTAINER,
    db_name: str = DEFAULT_DB_NAME,
    db_user: str = DEFAULT_DB_USER,
):
    if not current_task:
        return None
    issue_number = current_task.get('issue_number')
    work_item_id = resolve_work_item_id(
        db_container,
        db_name,
        db_user,
        project_slug,
        issue_number,
    )
    if not work_item_id:
        return None
    settings = resolve_db_settings(
        db_profile=db_profile,
        db_container=db_container,
        db_name=db_name,
        db_user=db_user,
    )
    service = DefaultWorkflowLifecycleService(
        workflow_state_repository=PostgresWorkflowStateRepository(settings=settings),
        runtime_event_repository=PostgresRuntimeEventRepository(settings=settings),
        execution_package_resolution_service=DefaultExecutionPackageResolutionService(
            repository=PostgresExecutionPackageRepository(settings=settings),
            capability_policy=DefaultDeploymentCapabilityPolicy(),
        ),
        workflow_transition_policy=DefaultWorkflowTransitionPolicy(),
        acceptance_policy=DefaultAcceptancePolicy(),
        reset_recovery_policy=DefaultResetRecoveryPolicy(),
    )
    return service.evaluate_workflow_transition(
        WorkflowLifecycleRequest(
            project_id=project_slug,
            work_item_id=work_item_id,
            requested_transition_type='worker_result_returned',
            requested_from_stage='worker_execution_in_progress',
            source_message_id_external=packet.get('message_id_external', packet.get('message_id')),
            source_packet_schema_type=packet.get('schema_type'),
            metadata={
                'consumer': 'techlead',
                'packet_queue_name': packet.get('queue_name'),
            },
        )
    )


def workflow_lifecycle_apply_for_packet(
    *,
    current_task: dict | None,
    packet: dict,
    project_slug: str = DEFAULT_PROJECT_SLUG,
    db_profile: str = DEFAULT_DB_PROFILE,
    db_container: str = DEFAULT_DB_CONTAINER,
    db_name: str = DEFAULT_DB_NAME,
    db_user: str = DEFAULT_DB_USER,
):
    if not current_task:
        return None
    schema_type = packet.get('schema_type')
    transition_type = None
    requested_from_stage = None
    if schema_type == 'worker_result_packet':
        transition_type = 'worker_result_returned'
        requested_from_stage = 'worker_execution_in_progress'
    elif schema_type == 'qa_verification_packet':
        transition_type = 'qa_result_returned'
        requested_from_stage = 'qa_execution_in_progress'
    else:
        return None

    issue_number = current_task.get('issue_number')
    work_item_id = resolve_work_item_id(
        db_container,
        db_name,
        db_user,
        project_slug,
        issue_number,
    )
    if not work_item_id:
        return None
    settings = resolve_db_settings(
        db_profile=db_profile,
        db_container=db_container,
        db_name=db_name,
        db_user=db_user,
    )
    service = DefaultWorkflowLifecycleService(
        workflow_state_repository=PostgresWorkflowStateRepository(settings=settings),
        runtime_event_repository=PostgresRuntimeEventRepository(settings=settings),
        execution_package_resolution_service=DefaultExecutionPackageResolutionService(
            repository=PostgresExecutionPackageRepository(settings=settings),
            capability_policy=DefaultDeploymentCapabilityPolicy(),
        ),
        workflow_transition_policy=DefaultWorkflowTransitionPolicy(),
        acceptance_policy=DefaultAcceptancePolicy(),
        reset_recovery_policy=DefaultResetRecoveryPolicy(),
    )
    return service.apply_workflow_transition(
        WorkflowLifecycleRequest(
            project_id=project_slug,
            work_item_id=work_item_id,
            requested_transition_type=transition_type,
            requested_from_stage=requested_from_stage,
            source_message_id_external=packet.get('message_id_external', packet.get('message_id')),
            source_packet_schema_type=schema_type,
            metadata={
                'consumer': 'techlead',
                'packet_queue_name': packet.get('queue_name'),
                'runtime_action': 'emit_next_assignment',
            },
        )
    )


def repo_auth_current(repo_root: Path) -> Path:
    resolved = _repo_auth_manifest_from_execution_context(repo_root)
    if resolved is not None:
        return resolved
    return repo_authority_manifest_path(repo_root)


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


def claimed_source_assignment_claims(message_id: str, queue_name: str):
    matches = []
    for claim in handoff_runtime.list_claims(queue=queue_name, status='claimed'):
        envelope = claim.get('original_envelope') or {}
        if envelope.get('message_id') == message_id:
            matches.append(claim)
    return matches


def acknowledge_existing_claim(claim_id: str):
    path, claim = handoff_runtime.load_claim(claim_id)
    claim['status'] = 'done'
    claim['acked_at'] = handoff_runtime.utc_now()
    handoff_runtime.save_json(path, claim)
    handoff_runtime.update_queue_message_status(
        (claim.get('original_envelope') or {}).get('message_id'),
        'acknowledged',
        'completed',
        'acknowledged_at',
    )
    return {
        'ok': True,
        'claim_id': claim_id,
        'status': claim.get('status'),
        'state_dir': claim.get('state_dir'),
        'message_id': (claim.get('original_envelope') or {}).get('message_id'),
    }


def acknowledge_source_assignment(repo_root: Path, message_id: str, queue_name: str, claimed_by: str):
    matching_claims = claimed_source_assignment_claims(message_id, queue_name)
    if len(matching_claims) > 1:
        return {
            'ok': False,
            'reason': 'multiple_open_claims_for_source_assignment',
            'details': f'More than one active claim exists for source assignment {message_id!r}.',
            'message_id': message_id,
            'queue_name': queue_name,
            'matching_claim_ids': [claim.get('claim_id') for claim in matching_claims],
        }
    if len(matching_claims) == 1:
        ack_result = acknowledge_existing_claim(matching_claims[0]['claim_id'])
        ack_result['ack_mode'] = 'existing_claim'
        ack_result['queue_name'] = queue_name
        return ack_result

    queue_script = repo_queue_script(repo_root)
    claim_cmd = [
        str(queue_script),
        'queue-claim-next',
        '--repo-root', str(repo_root),
        '--queue', queue_name,
        '--claimed-by', claimed_by,
    ]
    claim_code, claim_result, claim_error = run_json_with_errors(claim_cmd)
    if claim_code != 0 or claim_result is None:
        return {
            'ok': False,
            'reason': 'source_assignment_claim_failed',
            'details': claim_error,
            'message_id': message_id,
            'queue_name': queue_name,
            'claim_command': claim_cmd,
        }
    if not claim_result.get('claimed'):
        return {
            'ok': False,
            'reason': 'source_assignment_not_claimable',
            'details': f'No claimable queue message was available while trying to close source assignment {message_id!r}.',
            'message_id': message_id,
            'queue_name': queue_name,
            'claim_result': claim_result,
        }
    if claim_result.get('message_id') != message_id:
        requeue_cmd = [
            str(queue_script),
            'queue-requeue',
            '--repo-root', str(repo_root),
            '--claim-id', claim_result['claim_id'],
        ]
        requeue_code, requeue_result, requeue_error = run_json_with_errors(requeue_cmd)
        return {
            'ok': False,
            'reason': 'unexpected_queue_head_when_closing_source_assignment',
            'details': 'The next claimable queue message was not the expected source assignment; refusing to acknowledge the wrong packet.',
            'message_id': message_id,
            'queue_name': queue_name,
            'claim_result': claim_result,
            'requeue': requeue_result if requeue_code == 0 else {
                'ok': False,
                'error': requeue_error,
                'claim_id': claim_result['claim_id'],
            },
        }

    ack_result = acknowledge_existing_claim(claim_result['claim_id'])
    ack_result['ack_mode'] = 'claim_then_ack'
    ack_result['queue_name'] = queue_name
    return ack_result


def run_text(cmd, cwd: Path | None = None) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(cwd) if cwd else None)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f'command failed: {cmd}')
    return result.stdout


def run_text_with_errors(cmd, cwd: Path | None = None):
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(cwd) if cwd else None)
    if result.returncode != 0:
        return result.returncode, None, result.stderr.strip() or result.stdout.strip() or f'command failed: {cmd}'
    return 0, result.stdout, None


def resolve_db_settings(db_profile=None, db_container=None, db_name=None, db_user=None):
    profile = db_profile or DEFAULT_DB_PROFILE
    return settings_with_overrides(
        profile,
        container=db_container,
        name=db_name,
        user=db_user,
    )


def run_psql(db_container, db_name, db_user, sql, db_profile=DEFAULT_DB_PROFILE):
    settings = resolve_db_settings(
        db_profile=db_profile,
        db_container=db_container,
        db_name=db_name,
        db_user=db_user,
    )
    return shared_run_psql(sql, settings=settings)


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
        out[q] = run_json([
            str(queue_script),
            'queue-check',
            '--repo-root',
            str(repo_root),
            '--queue',
            q,
            '--preview',
            str(QUEUE_PREVIEW_DEPTH),
        ])
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


def github_repo_for_root(repo_root: Path) -> str:
    manifest_path = repo_auth_current(repo_root)
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text())
        except Exception:
            manifest = {}
        repo = (manifest.get('project') or {}).get('repo')
        if repo:
            return str(repo)
    return 'billyweisberg/fractal-core-python'


def _select_issue_url_from_packet(packet: dict | None, issue_number: int) -> str | None:
    packet = packet or {}
    payload = packet.get('payload') or {}
    for candidate in [payload.get('next_issue'), payload.get('closed_issue')]:
        if isinstance(candidate, dict) and candidate.get('number') == issue_number:
            return candidate.get('url')
    for link in ((packet.get('github_context') or {}).get('links') or []):
        if f'/issues/{issue_number}' in str(link):
            return str(link)
    return None


def _select_pr_url_from_packet(packet: dict | None, pr_number: int) -> str | None:
    packet = packet or {}
    payload = packet.get('payload') or {}
    accepted_pr = payload.get('accepted_pr') or {}
    if isinstance(accepted_pr, dict) and accepted_pr.get('number') == pr_number:
        return accepted_pr.get('url')
    for link in ((packet.get('github_context') or {}).get('links') or []):
        if f'/pull/{pr_number}' in str(link):
            return str(link)
    return None


def _fallback_issue_record(issue_number: int, fallback_task: dict | None = None, fallback_packet: dict | None = None) -> dict:
    return {
        'number': issue_number,
        'state': 'OPEN',
        'title': (fallback_task or {}).get('title') or f'Issue #{issue_number}',
        'url': _select_issue_url_from_packet(fallback_packet, issue_number),
        'comments': [],
    }


def _fallback_pr_record(
    fallback_pr_number: int | None,
    fallback_packet: dict | None = None,
) -> dict | None:
    packet = fallback_packet or {}
    github_context = packet.get('github_context') or {}
    pr_number = fallback_pr_number or github_context.get('pr_number')
    branch = github_context.get('branch')
    if pr_number is None and branch is None:
        return None
    return {
        'number': pr_number,
        'title': f'Proof PR #{pr_number}' if pr_number is not None else 'Proof PR',
        'state': 'OPEN',
        'isDraft': False,
        'headRefName': branch,
        'baseRefName': 'main',
        'url': _select_pr_url_from_packet(packet, pr_number) if pr_number is not None else None,
        'statusCheckRollup': [],
        'mergedAt': None,
        'body': '',
        'comments': [],
    }


def fetch_pr(pr_number, github_repo):
    return run_json([
        'gh', 'pr', 'view', str(pr_number), '--repo', github_repo,
        '--json', 'number,title,state,isDraft,headRefName,baseRefName,url,statusCheckRollup,mergedAt,body,comments'
    ])


def github_state(issue_number, github_repo, fallback_pr_number=None, fallback_task=None, fallback_packet=None):
    try:
        issue = run_json([
            'gh', 'issue', 'view', str(issue_number), '--repo', github_repo,
            '--json', 'number,state,title,url,comments'
        ])
    except Exception:
        issue = _fallback_issue_record(issue_number, fallback_task=fallback_task, fallback_packet=fallback_packet)
    try:
        prs = run_json([
            'gh', 'pr', 'list', '--repo', github_repo, '--search', f'{issue_number} in:title',
            '--state', 'all', '--json', 'number,title,state,isDraft,headRefName,baseRefName,url,statusCheckRollup,mergedAt,body'
        ])
    except Exception:
        prs = []
    active_pr = None
    for pr in prs:
        if pr['state'] == 'OPEN':
            active_pr = pr
            break
    if active_pr is None and prs:
        active_pr = prs[0]
    if active_pr is None and fallback_pr_number is not None:
        try:
            active_pr = fetch_pr(fallback_pr_number, github_repo)
        except Exception:
            active_pr = None
    if active_pr is None:
        try:
            all_prs = run_json([
                'gh', 'pr', 'list', '--repo', github_repo,
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
    if active_pr is None:
        active_pr = _fallback_pr_record(fallback_pr_number, fallback_packet=fallback_packet)
    if active_pr is not None and 'comments' not in active_pr:
        try:
            active_pr = fetch_pr(active_pr['number'], github_repo)
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


def latest_techlead_decision_packet(issue_number, reports_dir: Path = QA_WORK_DIR):
    candidates = []
    for packet_path in sorted(reports_dir.glob(f'techlead-decision.issue{issue_number}.*.json')):
        try:
            packet = json.loads(packet_path.read_text())
        except Exception:
            continue
        if packet.get('schema_type') != 'techlead_decision_packet':
            continue
        if packet.get('github_context', {}).get('issue_number') not in {None, issue_number}:
            continue
        created_at = packet.get('created_at')
        candidates.append({
            'path': str(packet_path),
            'message_id': packet.get('message_id'),
            'schema_type': packet.get('schema_type'),
            'created_at': created_at,
            'from_role': packet.get('from_role'),
            'to_role': packet.get('to_role'),
            'payload': packet.get('payload') or {},
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


def git_local_branch_exists(repo_root: Path, branch_name: str) -> bool:
    return subprocess.run(
        ['git', 'show-ref', '--verify', '--quiet', f'refs/heads/{branch_name}'],
        cwd=str(repo_root),
    ).returncode == 0


def git_remote_branch_exists(repo_root: Path, branch_name: str) -> bool:
    return subprocess.run(
        ['git', 'show-ref', '--verify', '--quiet', f'refs/remotes/origin/{branch_name}'],
        cwd=str(repo_root),
    ).returncode == 0


def git_resolve_ref(repo_root: Path, ref_name: str) -> str | None:
    code, stdout, _error = run_text_with_errors(['git', 'rev-parse', '--verify', ref_name], cwd=repo_root)
    if code != 0 or stdout is None:
        return None
    return stdout.strip()


def git_fetch_branch(repo_root: Path, branch_name: str) -> bool:
    code, _stdout, _error = run_text_with_errors(['git', 'fetch', 'origin', branch_name], cwd=repo_root)
    return code == 0


def git_branch_usage(repo_root: Path, branch_name: str) -> list[str]:
    code, stdout, _error = run_text_with_errors(['git', 'worktree', 'list', '--porcelain'], cwd=repo_root)
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


def git_worktree_entries(repo_root: Path) -> list[dict]:
    code, stdout, _error = run_text_with_errors(['git', 'worktree', 'list', '--porcelain'], cwd=repo_root)
    if code != 0 or stdout is None:
        return []
    entries: list[dict] = []
    current: dict | None = None
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


def git_worktree_for_branch(repo_root: Path, branch_name: str) -> dict | None:
    for entry in git_worktree_entries(repo_root):
        if entry.get('branch') == branch_name:
            return entry
    return None


def git_worktree_for_path(repo_root: Path, worktree_path: Path) -> dict | None:
    target = str(worktree_path.resolve())
    for entry in git_worktree_entries(repo_root):
        if Path(entry['path']).resolve().as_posix() == Path(target).as_posix():
            return entry
    return None


def normalize_canonical_branch(repo_root: Path, issue_number: int, lineage: dict, explicit: str | None) -> str:
    if explicit:
        return explicit
    preferred = f'issue-{issue_number}'
    if git_local_branch_exists(repo_root, preferred) or git_remote_branch_exists(repo_root, preferred):
        return preferred
    lineage_branch = lineage.get('canonical_branch')
    if lineage_branch:
        return str(lineage_branch)
    return preferred


def role_branch_name(issue_number: int, target_role: str, explicit: str | None) -> str:
    if explicit:
        return explicit
    suffix = ROLE_BRANCH_SUFFIX[target_role]
    return f'issue-{issue_number}-{suffix}'


def role_label_for_cli(target_role: str) -> str:
    return ROLE_LABEL_BY_CLI[target_role]


def target_role_for_branch(role_branch: str | None) -> str | None:
    if not role_branch:
        return None
    for suffix, target_role in ROLE_CLI_BY_SUFFIX.items():
        if role_branch.endswith(f'-{suffix}'):
            return target_role
    return None


def worktree_ownership_record(
    repo_root: Path,
    target_role: str,
    role_branch: str,
    worktree_path: Path,
    worktree_entry: dict | None = None,
) -> dict:
    entry = worktree_entry or git_worktree_for_path(repo_root, worktree_path)
    checked_out_branch = entry.get('branch') if entry else None
    return {
        'ownership_model': 'role_automation_self_service',
        'lineage_owner_role': 'TechLead',
        'runtime_owner_role': role_label_for_cli(target_role),
        'runtime_owner_role_cli': target_role,
        'admin_surface_role': 'TechLead',
        'ownership_source': 'deterministic_role_worktree_contract',
        'role_branch': role_branch,
        'worktree_path': str(worktree_path),
        'default_worktree_path': str(default_role_worktree_path(repo_root, role_branch)),
        'uses_default_worktree_path': worktree_path.resolve() == default_role_worktree_path(repo_root, role_branch).resolve(),
        'registered': entry is not None,
        'checked_out_branch': checked_out_branch,
        'branch_aligned': checked_out_branch == role_branch if checked_out_branch is not None else None,
        'worktree_head': entry.get('head') if entry else None,
    }


def worktree_staleness_assessment(
    lineage_state: str | None,
    ownership: dict | None,
) -> dict | None:
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


def default_role_worktree_root(repo_root: Path) -> Path:
    override = os.environ.get('PAA_ROLE_WORKTREE_ROOT')
    if override:
        return Path(override).expanduser().resolve()
    return (repo_root / '.codex-work' / 'worktrees' / 'paa').resolve()


def default_role_worktree_path(repo_root: Path, role_branch: str) -> Path:
    return default_role_worktree_root(repo_root) / role_branch


def git_current_branch(repo_root: Path) -> str | None:
    code, stdout, _error = run_text_with_errors(['git', 'symbolic-ref', '--short', 'HEAD'], cwd=repo_root)
    if code != 0 or stdout is None:
        return None
    return stdout.strip()


def resolve_canonical_source_ref(repo_root: Path, canonical_branch: str) -> tuple[str | None, str | None]:
    if git_fetch_branch(repo_root, canonical_branch) and git_remote_branch_exists(repo_root, canonical_branch):
        remote_ref = f'origin/{canonical_branch}'
        return remote_ref, git_resolve_ref(repo_root, remote_ref)
    if git_remote_branch_exists(repo_root, canonical_branch):
        remote_ref = f'origin/{canonical_branch}'
        return remote_ref, git_resolve_ref(repo_root, remote_ref)
    if git_local_branch_exists(repo_root, canonical_branch):
        return canonical_branch, git_resolve_ref(repo_root, canonical_branch)
    return None, None


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


def issue_number_from_packet_preview(payload: dict | None) -> int | None:
    if not payload:
        return None
    github_ctx = payload.get('github_context') or {}
    issue_number = github_ctx.get('issue_number')
    if issue_number is None:
        correlation_id = payload.get('correlation_id') or ''
        match = re.fullmatch(r'issue-(\d+)', str(correlation_id))
        if match:
            issue_number = match.group(1)
    try:
        return int(issue_number) if issue_number is not None else None
    except Exception:
        return None


def newest_queue_preview(queue_data: dict) -> dict | None:
    preview = queue_data.get('preview') or []
    newest = None
    newest_dt = None
    for item in preview:
        payload = item.get('payload_preview') or {}
        created_at = parse_created_at(payload.get('created_at'))
        if newest is None or (created_at and (newest_dt is None or created_at > newest_dt)):
            newest = payload
            newest_dt = created_at
    return newest


def newest_packet_preview_across_queues(queues) -> dict | None:
    newest = None
    newest_dt = None
    for queue_name, queue_data in queues.items():
        preview = queue_data.get('preview') or []
        for item in preview:
            payload = item.get('payload_preview') or {}
            created_at = parse_created_at(payload.get('created_at'))
            if newest is None or (created_at and (newest_dt is None or created_at > newest_dt)):
                newest = dict(payload)
                newest['queue_name'] = queue_name
                newest_dt = created_at
    return newest


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


def queue_gate_candidates(
    queues,
    *,
    queue_name: str | None = None,
    to_role: str | None = None,
    schema_types: set[str] | None = None,
):
    candidates = []
    normalized_to_role = handoff_runtime.normalize_role_name(to_role) if to_role else None
    for current_queue_name, queue_data in queues.items():
        if queue_name and current_queue_name != queue_name:
            continue
        preview = queue_data.get('preview') or []
        for item in preview:
            payload = item.get('payload_preview') or {}
            payload_to_role = handoff_runtime.normalize_role_name(payload.get('to_role'))
            if normalized_to_role and payload_to_role != normalized_to_role:
                continue
            if schema_types and payload.get('schema_type') not in schema_types:
                continue
            candidate = dict(payload)
            candidate['queue_name'] = current_queue_name
            candidate['issue_number'] = issue_number_from_packet_preview(payload)
            candidates.append(candidate)
    candidates.sort(
        key=lambda candidate: parse_created_at(candidate.get('created_at')) or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    return candidates


def active_workflow_context(repo_root: Path, project_slug: str):
    current, manifest = load_authority(repo_root)
    tasks = current.get('tasks', [])
    current_task = tasks[0] if tasks else None
    queues = queue_state(repo_root)
    issue = None
    pr = None
    qa_packet = None
    workflow_stage = 'blocked'
    owner_role = 'Unknown'
    recommended_actions = []
    if current_task:
        qa_packet = latest_qa_packet(current_task['issue_number'], reports_dir=repo_reports_dir(repo_root))
        fallback_pr_number = qa_packet.get('pr_number') if qa_packet else None
        fallback_packet = latest_packet_preview(queues, current_task['issue_number'])
        issue, pr = github_state(
            current_task['issue_number'],
            github_repo_for_root(repo_root),
            fallback_pr_number=fallback_pr_number,
            fallback_task=current_task,
            fallback_packet=fallback_packet,
        )
        workflow_stage, owner_role, _escalations, recommended_actions, _unattended_safe = derive_workflow(
            current_task,
            issue,
            pr,
            qa_packet,
            queues,
        )
        local_decision_packet = latest_techlead_decision_packet(current_task['issue_number'], reports_dir=repo_reports_dir(repo_root))
        workflow_stage, owner_role, recommended_actions, _unattended_safe = apply_terminal_lineage_override(
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


def apply_terminal_lineage_override(
    *,
    local_decision_packet: dict | None,
    queues: dict,
    issue: dict | None,
    pr: dict | None,
    workflow_stage: str,
    owner_role: str,
    recommended: list,
    unattended_safe: bool,
) -> tuple[str, str, list, bool]:
    if not local_decision_packet:
        return workflow_stage, owner_role, recommended, unattended_safe
    payload = local_decision_packet.get('payload') or {}
    if payload.get('lineage_state') != 'closed':
        return workflow_stage, owner_role, recommended, unattended_safe
    if any((queue_data.get('preview') or []) for queue_data in queues.values()):
        return workflow_stage, owner_role, recommended, unattended_safe
    latest_lineage_action = payload.get('lineage_action')
    if latest_lineage_action == 'proof_only_closed':
        return 'proof_only_closed', 'TechLead', [], True
    if pr and pr.get('mergedAt') and (issue and (issue.get('state') or '').upper() == 'CLOSED'):
        return 'techlead_decision_recorded', 'TechLead', [], True
    return workflow_stage, owner_role, recommended, unattended_safe


def automation_preflight(args):
    repo_root = args.repo_root.resolve()
    target_role = args.target_role
    context = active_workflow_context(repo_root, args.project_slug)
    queues = context['queues']
    current_task = context['current_task']
    active_issue_number = current_task.get('issue_number') if current_task else None
    workflow_stage = context['workflow_stage']
    owner_role = context['owner_role']

    queue_snapshot = {
        queue_name: {
            'messages_ready': queue_data.get('messages_ready'),
            'messages_unacknowledged': queue_data.get('messages_unacknowledged'),
        }
        for queue_name, queue_data in queues.items()
    }

    if target_role == 'techlead':
        queue_candidates = queue_gate_candidates(
            queues,
            to_role='TechLead',
            schema_types=TECHLEAD_GATE_SCHEMA_TYPES,
        )
        owner_match = owner_role == 'TechLead'
        recommendation_match = any(
            (action.get('target_role') or '') == 'TechLead'
            for action in (context.get('recommended_actions') or [])
        )
        should_invoke_model = bool(queue_candidates or owner_match or recommendation_match)
        if queue_candidates:
            gate_reason = 'queue_packet_for_techlead'
        elif owner_match:
            gate_reason = 'active_techlead_work_in_progress'
        elif recommendation_match:
            gate_reason = 'recommended_action_targets_techlead'
        else:
            gate_reason = 'no_techlead_work_detected'
    else:
        gate = ROLE_QUEUE_GATE[target_role]
        queue_candidates = queue_gate_candidates(
            queues,
            queue_name=gate['queue_name'],
            to_role=gate['to_role'],
            schema_types=gate['schema_types'],
        )
        owner_match = owner_role == ROLE_LABEL_BY_CLI[target_role]
        should_invoke_model = bool(queue_candidates or owner_match)
        if queue_candidates:
            gate_reason = 'claimable_assignment_packet_available'
        elif owner_match:
            gate_reason = 'active_role_work_in_progress'
        else:
            gate_reason = 'no_role_work_detected'

    return {
        'ok': True,
        'repo_root': str(repo_root),
        'target_role': target_role,
        'role_label': 'TechLead' if target_role == 'techlead' else ROLE_LABEL_BY_CLI[target_role],
        'should_invoke_model': should_invoke_model,
        'skip_model_invocation': not should_invoke_model,
        'gate_reason': gate_reason,
        'workflow_stage': workflow_stage,
        'current_owner_role': owner_role,
        'active_issue_number': active_issue_number,
        'queue_candidates': [
            {
                'message_id': candidate.get('message_id'),
                'schema_type': candidate.get('schema_type'),
                'queue_name': candidate.get('queue_name'),
                'issue_number': candidate.get('issue_number'),
                'from_role': candidate.get('from_role'),
                'to_role': candidate.get('to_role'),
                'created_at': candidate.get('created_at'),
            }
            for candidate in queue_candidates
        ],
        'queue_snapshot': queue_snapshot,
        'next_step_hint': (
            'invoke_model_for_role_run'
            if should_invoke_model
            else 'exit_without_model_invocation'
        ),
    }


def derive_lineage_section(current_task, pr, queues, escalations, reports_dir: Path = QA_WORK_DIR):
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
    local_decision_packet = latest_techlead_decision_packet(issue_number, reports_dir=reports_dir) if issue_number else None
    lineage_packet = newest_packet(decision_packet, assignment_packet, local_decision_packet)
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
    worktree_target_role = target_role_for_branch(role_branch)
    worktree_path = None
    worktree_entry = None
    worktree_ownership = None
    if worktree_target_role and role_branch:
        worktree_path = default_role_worktree_path(REPO_ROOT, role_branch)
        worktree_entry = git_worktree_for_path(REPO_ROOT, worktree_path)
        worktree_ownership = worktree_ownership_record(
            REPO_ROOT,
            worktree_target_role,
            role_branch,
            worktree_path,
            worktree_entry=worktree_entry,
        )
    worktree_staleness = worktree_staleness_assessment(lineage_state, worktree_ownership)
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
        'worktree_ownership': worktree_ownership,
        'worktree_staleness': worktree_staleness,
    }


def build_lineage_view(repo_root: Path, project_slug: str, package_id_external: str, brief_id_external: str) -> dict:
    _current, manifest = load_authority(repo_root)
    package = load_design_package(project_slug, package_id_external)
    issue_number = resolve_issue_number_from_package(package, package_id_external, project_slug)
    current_task = resolve_task_summary(manifest, package, issue_number)
    queues = queue_state(repo_root)
    local_decision_packet = latest_techlead_decision_packet(issue_number, reports_dir=repo_reports_dir(repo_root))
    qa_packet = latest_qa_packet(issue_number, repo_reports_dir(repo_root))
    fallback_packet = latest_packet_preview(queues, issue_number)
    issue, pr = github_state(
        issue_number,
        github_repo_for_root(repo_root),
        fallback_pr_number=qa_packet.get('pr_number') if qa_packet else None,
        fallback_task=current_task,
        fallback_packet=fallback_packet,
    )
    workflow_stage, owner_role, escalations, recommended, unattended_safe = derive_workflow(current_task, issue, pr, qa_packet, queues)
    lineage = derive_lineage_section(current_task, pr, queues, escalations, reports_dir=repo_reports_dir(repo_root))
    workflow_stage, owner_role, recommended, unattended_safe = apply_terminal_lineage_override(
        local_decision_packet=local_decision_packet,
        queues=queues,
        issue=issue,
        pr=pr,
        workflow_stage=workflow_stage,
        owner_role=owner_role,
        recommended=recommended,
        unattended_safe=unattended_safe,
    )
    ambiguity_reasons = []
    if lineage['current_packet_type'] is None and lineage['canonical_branch'] is None and not pr:
        ambiguity_reasons.append('no_lineage_packet_or_pr_context')
    return {
        'ok': len(ambiguity_reasons) == 0,
        'project_slug': project_slug,
        'package_id_external': package_id_external,
        'brief_id_external': brief_id_external,
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
    pending_worker_packet = latest_packet_preview(
        queues,
        issue_number,
        schema_type='worker_result_packet',
        to_role='techlead',
    ) if issue_number else None
    pending_qa_queue_packet = latest_packet_preview(
        queues,
        issue_number,
        schema_type='qa_verification_packet',
        to_role='techlead',
    ) if issue_number else None
    pending_delivery_review_packet = latest_packet_preview(
        queues,
        issue_number,
        schema_type='delivery_review_packet',
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
        pending_delivery_review_packet,
        pending_qa_queue_packet,
        pending_worker_packet,
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

    if latest_techlead_packet and latest_techlead_packet.get('schema_type') == 'delivery_review_packet':
        stage = 'techlead_delivery_review_pending'
        owner = 'TechLead'
        unattended_safe = False
        delivery_payload = latest_techlead_packet.get('payload') or {}
        escalations.append({
            'event_type': 'delivery_review_waiting_for_techlead',
            'severity': 'medium',
            'work_item_ref': {'issue_number': current_task['issue_number'], 'task_id': current_task['task_id']} if current_task else None,
            'summary': 'TechLead has a waiting Delivery Architect review packet to review.',
            'details': {
                'message_id': latest_techlead_packet.get('message_id'),
                'schema_type': latest_techlead_packet.get('schema_type'),
                'queue_name': latest_techlead_packet.get('queue_name'),
                'review_type': delivery_payload.get('review_type'),
                'result_type': delivery_payload.get('result_type'),
                'techlead_action_recommended': delivery_payload.get('techlead_action_recommended'),
            },
            'recommended_route': 'TechLead',
            'status': 'open',
        })
        recommended.append({
            'priority': 1,
            'action_type': 'route_to_techlead',
            'reason': 'A Delivery Architect review packet addressed to TechLead is waiting for the next routing decision.',
            'target_role': 'TechLead',
            'blocking': True,
        })
        return stage, owner, escalations, recommended, unattended_safe

    if latest_techlead_packet and latest_techlead_packet.get('schema_type') == 'worker_result_packet':
        worker_payload = latest_techlead_packet.get('payload') or {}
        worker_role = worker_payload.get('worker_role')
        if not worker_role:
            packet_from_role = handoff_runtime.normalize_role_name(latest_techlead_packet.get('from_role'))
            worker_role = packet_from_role or 'Worker'
        lifecycle_result = None
        try:
            lifecycle_result = workflow_lifecycle_worker_result_evaluation(
                current_task=current_task,
                packet=latest_techlead_packet,
            )
        except Exception:
            lifecycle_result = None
        lifecycle_target_stage = None
        if lifecycle_result is not None:
            lifecycle_target_stage = (
                (lifecycle_result.decision_summary.metadata or {}).get('resolved_to_stage')
                or 'techlead_worker_review_pending'
            )
        if worker_role == 'Python Dev':
            stage = 'techlead_dev_review_pending'
            summary = 'TechLead has a waiting Python worker result packet to review before QA is assigned.'
            reason = 'A Python worker result packet addressed to TechLead is waiting for the next routing decision.'
        else:
            stage = lifecycle_target_stage or 'techlead_worker_review_pending'
            summary = f'TechLead has a waiting {worker_role} result packet to review.'
            reason = 'A worker result packet addressed to TechLead is waiting for the next routing decision.'
        owner = 'TechLead'
        unattended_safe = False
        details = {
            'message_id': latest_techlead_packet.get('message_id'),
            'schema_type': latest_techlead_packet.get('schema_type'),
            'queue_name': latest_techlead_packet.get('queue_name'),
            'worker_role': worker_role,
            'worker_family': worker_payload.get('worker_family'),
            'result_type': worker_payload.get('result_type'),
            'techlead_action_recommended': worker_payload.get('techlead_action_recommended'),
        }
        if lifecycle_result is not None:
            details.update({
                'workflow_transition_allowed': lifecycle_result.decision_summary.transition_allowed,
                'workflow_blocking_reasons': list(lifecycle_result.decision_summary.blocking_reasons),
                'workflow_notes': list(lifecycle_result.decision_summary.notes),
                'workflow_recommended_next_action': lifecycle_result.recommended_next_action,
                'workflow_target_stage': lifecycle_target_stage,
            })
        escalations.append({
            'event_type': 'worker_packet_waiting_for_techlead',
            'severity': 'medium',
            'work_item_ref': {'issue_number': current_task['issue_number'], 'task_id': current_task['task_id']} if current_task else None,
            'summary': summary,
            'details': details,
            'recommended_route': 'TechLead',
            'status': 'open',
        })
        recommended.append({
            'priority': 1,
            'action_type': 'route_to_techlead',
            'reason': reason,
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


def build_report(repo_root: Path = REPO_ROOT, project_slug: str = DEFAULT_PROJECT_SLUG):
    current, manifest = load_authority(repo_root)
    tasks = current.get('tasks', [])
    current_task = tasks[0] if tasks else None
    queues = queue_state(repo_root)
    auto_roles, architect_missing = automation_state(repo_root)
    authority_version = manifest['project']['authority_version']
    authority_status, mirrors = mirror_status(authority_version, repo_root)

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
        'worktree_ownership': None,
        'worktree_staleness': None,
    }

    inferred_packet = newest_packet_preview_across_queues(queues)
    inferred_issue_number = issue_number_from_packet_preview(inferred_packet)
    report_task = current_task
    if report_task is None and inferred_issue_number is not None:
        report_task = {
            'issue_number': inferred_issue_number,
            'task_id': f'queue-inferred-issue-{inferred_issue_number}',
            'title': f'Issue #{inferred_issue_number}',
            'status': 'in_progress',
        }

    if report_task:
        qa_packet = latest_qa_packet(report_task['issue_number'], reports_dir=repo_reports_dir(repo_root))
        fallback_pr_number = qa_packet.get('pr_number') if qa_packet else None
        fallback_packet = latest_packet_preview(queues, report_task['issue_number']) or inferred_packet
        local_decision_packet = latest_techlead_decision_packet(report_task['issue_number'], reports_dir=repo_reports_dir(repo_root))
        issue, pr = github_state(
            report_task['issue_number'],
            github_repo_for_root(repo_root),
            fallback_pr_number=fallback_pr_number,
            fallback_task=report_task,
            fallback_packet=fallback_packet,
        )
        workflow_stage, owner_role, wf_escalations, wf_recommended, wf_safe = derive_workflow(report_task, issue, pr, qa_packet, queues)
        escalations.extend(wf_escalations)
        recommended.extend(wf_recommended)
        unattended_safe = unattended_safe and wf_safe
        lineage = derive_lineage_section(report_task, pr, queues, escalations)
        workflow_stage, owner_role, recommended, unattended_safe = apply_terminal_lineage_override(
            local_decision_packet=local_decision_packet,
            queues=queues,
            issue=issue,
            pr=pr,
            workflow_stage=workflow_stage,
            owner_role=owner_role,
            recommended=recommended,
            unattended_safe=unattended_safe,
        )

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
                'issue_number': report_task['issue_number'],
                'task_id': report_task['task_id'],
                'title': report_task['title'] if current_task else (issue.get('title') or report_task['title']),
                'status': report_task['status'],
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
        project_slug,
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
            'latest_message': newest_queue_preview(queues[q]),
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


def package_execution_mode(package: dict | None) -> str:
    authority_context = (package or {}).get('authority_context') or {}
    mode = authority_context.get('execution_mode')
    if not mode:
        return 'live_delivery'
    return str(mode)


def persist_techlead_acceptance_event(
    db_container,
    db_name,
    db_user,
    project_slug,
    issue_number,
    qa_packet,
    pr_state,
    *,
    decision='accepted',
    decision_notes=None,
    metadata_extra=None,
):
    issue_number = int(issue_number)
    resolved_notes = decision_notes or (
        f"TechLead accepted issue #{issue_number} after QA pass from packet "
        f"{qa_packet.get('message_id')} and merged PR #{pr_state.get('number')}."
    )
    metadata = {
        'qa_packet_id': qa_packet.get('message_id'),
        'qa_verification_status': qa_packet.get('verification_status'),
        'merge_recommendation': ((qa_packet.get('recommended_action') or {}).get('merge_recommendation')),
        'pr_number': pr_state.get('number'),
        'pr_url': pr_state.get('url'),
        'merge_state_status': pr_state.get('mergeStateStatus'),
        'merged_at': pr_state.get('mergedAt'),
    }
    if metadata_extra:
        metadata.update(metadata_extra)
    metadata_json = json.dumps(metadata)
    sql = f"""
    WITH project AS (
      SELECT project_id FROM paa.projects WHERE slug = {sql_literal(project_slug)}
    ), work_item AS (
      SELECT wi.work_item_id
      FROM paa.work_items wi
      JOIN project p ON p.project_id = wi.project_id
      WHERE wi.issue_number = {issue_number}
      LIMIT 1
    ), techlead_agent AS (
      SELECT a.agent_id
      FROM paa.agents a
      JOIN project p ON p.project_id = a.project_id
      WHERE a.name = 'Fractal Core TechLead Automation'
      LIMIT 1
    ), techlead_role AS (
      SELECT r.role_id
      FROM paa.roles r
      JOIN project p ON p.project_id = r.project_id
      WHERE r.name = 'TechLead'
      LIMIT 1
    )
    INSERT INTO paa.acceptance_events (
      project_id,
      work_item_id,
      accepted_by_agent_id,
      accepted_by_role_id,
      decision,
      notes,
      merge_commit_sha,
      metadata_json,
      created_at
    )
    SELECT
      project.project_id,
      work_item.work_item_id,
      techlead_agent.agent_id,
      techlead_role.role_id,
      {sql_literal(decision)}::paa.acceptance_decision,
      {sql_literal(resolved_notes)},
      {sql_literal(pr_state.get('mergeCommit', {}).get('oid'))},
      {sql_literal(metadata_json)}::jsonb,
      {sql_literal(pr_state.get('mergedAt') or qa_packet.get('created_at'))}::timestamptz
    FROM project
    JOIN work_item ON TRUE
    LEFT JOIN techlead_agent ON TRUE
    LEFT JOIN techlead_role ON TRUE
    WHERE NOT EXISTS (
      SELECT 1
      FROM paa.acceptance_events ae
      WHERE ae.work_item_id = work_item.work_item_id
        AND ae.decision = {sql_literal(decision)}::paa.acceptance_decision
        AND ae.metadata_json->>'qa_packet_id' = {sql_literal(qa_packet.get('message_id'))}
    );
    """
    run_psql(db_container, db_name, db_user, sql)


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


def resolve_issue_number_from_package(package: dict, package_id_external: str, project_slug: str | None = None) -> int:
    authority_context = package.get('authority_context') or {}
    issue_number = authority_context.get('issue_number')
    if issue_number is not None:
        return int(issue_number)
    task_issue_number = authority_context.get('task_issue_number')
    if task_issue_number is not None:
        return int(task_issue_number)
    resolved_project_slug = project_slug or authority_context.get('project_slug')
    if resolved_project_slug:
        sql = f"""
        SELECT wi.issue_number
        FROM paa.design_packages dp
        JOIN paa.projects p ON p.project_id = dp.project_id
        JOIN paa.work_items wi ON wi.work_item_id = dp.work_item_id
        WHERE p.slug = {sql_literal(resolved_project_slug)}
          AND dp.package_id_external = {sql_literal(package_id_external)}
        LIMIT 1;
        """
        out = run_psql(DEFAULT_DB_CONTAINER, DEFAULT_DB_NAME, DEFAULT_DB_USER, sql).strip()
        if out:
            return int(out)
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


def default_result_input_path(repo_root: Path, issue_number: int, target_role: str) -> Path:
    slug = target_role.replace(' ', '-').lower()
    reports_dir = repo_reports_dir(repo_root)
    return reports_dir / f'role-result-input.issue{issue_number}.{slug}.json'


def default_result_packet_paths(repo_root: Path, issue_number: int, target_role: str) -> tuple[Path, Path]:
    slug = target_role.replace(' ', '-').lower()
    reports_dir = repo_reports_dir(repo_root)
    if target_role == 'Delivery Architect':
        stem = f'delivery-review.issue{issue_number}.{slug}'
    elif is_team_worker_label(target_role, repo_root=repo_root):
        stem = f'worker-result.issue{issue_number}.{slug}'
    else:
        stem = f'qa-verification.issue{issue_number}.{slug}'
    return reports_dir / f'{stem}.json', reports_dir / f'{stem}.md'


def derive_next_assignment_context(args) -> dict:
    repo_root = args.repo_root.resolve()
    current, manifest = load_authority(repo_root)
    github_repo = github_repo_for_root(repo_root)
    package = load_design_package(args.project_slug, args.package_id_external)
    issue_number = resolve_issue_number_from_package(package, args.package_id_external, args.project_slug)
    current_task = resolve_task_summary(manifest, package, issue_number)
    queues = queue_state(repo_root)
    qa_packet = latest_qa_packet(issue_number, repo_reports_dir(repo_root))
    fallback_packet = latest_packet_preview(queues, issue_number)
    issue, pr = github_state(
        issue_number,
        github_repo,
        fallback_pr_number=qa_packet.get('pr_number') if qa_packet else None,
        fallback_task=current_task,
        fallback_packet=fallback_packet,
    )
    workflow_stage, owner_role, _escalations, recommended, unattended_safe = derive_workflow(current_task, issue, pr, qa_packet, queues)
    pending_dev_packet = latest_packet_preview(
        queues,
        issue_number,
        schema_type='slice_result_packet',
        to_role='techlead',
    )
    pending_worker_packet = latest_packet_preview(
        queues,
        issue_number,
        schema_type='worker_result_packet',
        to_role='techlead',
    )
    pending_delivery_review_packet = latest_packet_preview(
        queues,
        issue_number,
        schema_type='delivery_review_packet',
        to_role='techlead',
    )
    explicit_team_worker = team_worker_role_for_cli(args.target_role, repo_root=repo_root) if args.target_role else None
    if args.target_role == 'delivery-architect':
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
            'allowed_result_types': [
                'ready_for_dev',
                'narrow_scope',
                'reject_scope',
            ],
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
        branch_name = pr.get('headRefName') or f'issue-{issue_number}'
        return {
            'ok': True,
            'workflow_stage': workflow_stage,
            'issue_number': issue_number,
            'issue_url': issue.get('url'),
            'pr_number': pr.get('number'),
            'pr_url': pr.get('url'),
            'branch': branch_name,
            'target_role': explicit_team_worker.display_name,
            'target_role_cli': explicit_team_worker.key,
            'assignment_type': 'implement_authorized_slice',
            'allowed_result_types': [
                'implemented_ready_for_qa',
                'blocked',
                'needs_clarification',
            ],
            'assignment_summary': (
                f'TechLead is explicitly issuing a {explicit_team_worker.display_name} implementation assignment '
                f'for issue #{issue_number} on branch {branch_name}.'
            ),
            'source_packet_message_id': None,
            'source_packet_path': None,
            'source_packet_queue': None,
            'issue': issue,
            'pr': pr,
            'recommended_actions': recommended,
            'unattended_safe': unattended_safe,
        }
    if workflow_stage in {'techlead_dev_review_pending', 'techlead_worker_review_pending'} and (pending_dev_packet or pending_worker_packet):
        if not pr:
            return {
                'ok': False,
                'workflow_stage': workflow_stage,
                'reason': 'dev_review_pending_but_no_pr_context',
                'details': 'A Dev result packet is waiting for TechLead, but no PR context could be derived from GitHub state.',
            }
        branch_name = pr.get('headRefName') or f'issue-{issue_number}'
        source_packet = pending_worker_packet or pending_dev_packet
        source_message_id = source_packet.get('message_id')
        source_packet_path = source_packet.get('path')
        source_packet_queue = source_packet.get('queue_name')
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
            'source_packet_path': source_packet_path,
            'source_packet_queue': source_packet_queue,
            'source_packet_schema_type': source_packet.get('schema_type'),
            'issue': issue,
            'pr': pr,
            'recommended_actions': recommended,
            'unattended_safe': unattended_safe,
        }
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
        delivery_payload = pending_delivery_review_packet.get('payload') or {}
        recommended_action = delivery_payload.get('techlead_action_recommended')
        result_type = delivery_payload.get('result_type')
        if isinstance(recommended_action, dict):
            recommended_action_name = recommended_action.get('action')
            recommended_target_role = recommended_action.get('target_role')
            recommended_reason = recommended_action.get('reason')
        else:
            recommended_action_name = None
            recommended_target_role = None
            recommended_reason = None
        normalized_target_role = handoff_runtime.normalize_role_name(recommended_target_role)
        recommended_team_worker = team_worker_role_for_label(normalized_target_role, repo_root=repo_root)
        if result_type == 'ready_for_dev':
            if recommended_action_name != 'assign_worker':
                return {
                    'ok': False,
                    'workflow_stage': workflow_stage,
                    'reason': 'delivery_review_ready_for_dev_without_assign_worker',
                    'details': 'Delivery review reported ready_for_dev, but the recommended TechLead action was not assign_worker.',
                    'recommended_actions': recommended,
                    'unattended_safe': unattended_safe,
                }
            if not recommended_team_worker:
                return {
                    'ok': False,
                    'workflow_stage': workflow_stage,
                    'reason': 'delivery_review_ready_for_dev_target_not_supported',
                    'details': (
                        'Delivery review recommended assign_worker, but the target role does not match an active '
                        f'Team Worker Role in the project registry. Received target role: {recommended_target_role!r}.'
                    ),
                    'recommended_actions': recommended,
                    'unattended_safe': unattended_safe,
                }
            branch_name = (
                pr.get('headRefName')
                or pending_delivery_review_packet.get('github_context', {}).get('branch')
                or (delivery_payload.get('branch') or {}).get('name')
                or f'issue-{issue_number}'
            )
            source_message_id = pending_delivery_review_packet.get('message_id')
            source_assignment = delivery_payload.get('source_assignment_ref') or {}
            source_packet_path = source_assignment.get('path')
            return {
                'ok': True,
                'workflow_stage': workflow_stage,
                'issue_number': issue_number,
                'issue_url': issue.get('url'),
                'pr_number': pr.get('number'),
                'pr_url': pr.get('url'),
                'branch': branch_name,
                'target_role': recommended_team_worker.display_name,
                'target_role_cli': recommended_team_worker.key,
                'assignment_type': 'implement_authorized_slice',
                'allowed_result_types': [
                    'implemented_ready_for_qa',
                    'blocked',
                    'needs_clarification',
                ],
                'assignment_summary': (
                    f'TechLead is routing Delivery Architect review packet {source_message_id} '
                    f'for issue #{issue_number} to {recommended_team_worker.display_name} on branch {branch_name}.'
                ),
                'source_packet_message_id': source_message_id,
                'source_packet_path': source_packet_path,
                'source_packet_queue': 'fractal-core-architecture',
                'source_packet_schema_type': pending_delivery_review_packet.get('schema_type'),
                'issue': issue,
                'pr': pr,
                'recommended_actions': recommended,
                'unattended_safe': unattended_safe,
                'decision_reason': recommended_reason,
            }
        unsupported_reason_by_result_type = {
            'narrow_scope': 'delivery_review_narrow_scope_requires_manual_techlead_decision',
            'reject_scope': 'delivery_review_reject_scope_requires_manual_techlead_decision',
            'request_reset': 'delivery_review_request_reset_requires_manual_techlead_decision',
            'needs_authority_clarification': 'delivery_review_authority_clarification_requires_manual_techlead_decision',
        }
        return {
            'ok': False,
            'workflow_stage': workflow_stage,
            'reason': unsupported_reason_by_result_type.get(
                result_type,
                'delivery_review_pending_requires_manual_techlead_decision',
            ),
            'details': (
                'Delivery review packets are visible to TechLead, but this result type does not yet support '
                f'automatic next-assignment derivation in this slice. result_type={result_type!r}, '
                f'recommended_action={recommended_action_name!r}, target_role={recommended_target_role!r}.'
            ),
            'recommended_actions': recommended,
            'unattended_safe': unattended_safe,
        }
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


def emit_next_assignment(args):
    repo_root = args.repo_root.resolve()
    context = derive_next_assignment_context(args)
    if not context.get('ok'):
        return context
    source_packet = None
    source_packet_path = context.get('source_packet_path')
    if source_packet_path:
        try:
            source_packet = handoff_runtime.load_json(Path(source_packet_path).resolve())
        except Exception:
            source_packet = None
    if source_packet is None and context.get('source_packet_schema_type'):
        source_packet = {
            'schema_type': context.get('source_packet_schema_type'),
            'message_id': context.get('source_packet_message_id'),
            'queue_name': context.get('source_packet_queue'),
        }
    workflow_transition = None
    current_task = {
        'issue_number': context.get('issue_number'),
        'task_id': f"issue-{context.get('issue_number')}",
    }
    if source_packet and source_packet.get('schema_type') in {'worker_result_packet', 'qa_verification_packet'}:
        workflow_transition = workflow_lifecycle_apply_for_packet(
            current_task=current_task,
            packet=source_packet,
            project_slug=args.project_slug,
            db_profile=getattr(args, 'db_profile', DEFAULT_DB_PROFILE),
            db_container=args.db_container,
            db_name=args.db_name,
            db_user=args.db_user,
        )
        if workflow_transition is not None and not workflow_transition.applied:
            return {
                'ok': False,
                'workflow_stage': context['workflow_stage'],
                'reason': 'workflow_transition_rejected',
                'details': workflow_transition.recommended_next_action
                or 'Workflow lifecycle service rejected the return transition for the source packet.',
                'workflow_transition': {
                    'requested_transition_type': workflow_transition.requested_transition_type,
                    'blocking_reasons': list(workflow_transition.decision_summary.blocking_reasons),
                    'notes': list(workflow_transition.decision_summary.notes),
                    'metadata': dict(workflow_transition.metadata),
                },
            }
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
        '--repo', github_repo_for_root(repo_root),
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
        'workflow_transition': (
            None
            if workflow_transition is None
            else {
                'requested_transition_type': workflow_transition.requested_transition_type,
                'applied': workflow_transition.applied,
                'workflow_stage': workflow_transition.state_view.workflow_stage
                if workflow_transition.state_view
                else None,
                'recommended_next_action': workflow_transition.recommended_next_action,
            }
        ),
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
        source_packet_message_id = context.get('source_packet_message_id')
        source_packet_path = context.get('source_packet_path')
        source_packet_queue = context.get('source_packet_queue')
        source_packet_ack = None
        if source_packet_message_id and (source_packet_path or source_packet_queue):
            source_queue = source_packet_queue
            if source_packet_path:
                from paa_consumer.inbox import resolve_packet_queue
                source_packet = handoff_runtime.load_json(Path(source_packet_path).resolve())
                source_queue = resolve_packet_queue(source_packet)
            if source_queue:
                source_packet_ack = acknowledge_source_assignment(
                    repo_root,
                    source_packet_message_id,
                    source_queue,
                    claimed_by='techlead-emit-next-assignment',
                )
                result['source_packet_ack'] = source_packet_ack
                if not source_packet_ack.get('ok'):
                    result['ok'] = False
                    result['error'] = 'sent_next_assignment_but_failed_to_close_source_packet'
                    return result
    return result


def latest_escalation_of_type(escalations: list[dict], event_type: str) -> dict | None:
    for escalation in reversed(escalations):
        if escalation.get('event_type') == event_type:
            return escalation
    return None


def derive_decision_context(args) -> dict:
    repo_root = args.repo_root.resolve()
    lineage_view = build_lineage_view(
        repo_root,
        args.project_slug,
        args.package_id_external,
        args.brief_id_external,
    )
    if not lineage_view.get('ok') and args.decision_type in {'superseded', 'closed'}:
        return {
            'ok': False,
            'workflow_stage': lineage_view.get('workflow_stage'),
            'reason': 'ambiguous_lineage_view',
            'details': f"Lineage helper could not produce an unambiguous lineage view: {', '.join(lineage_view.get('ambiguity_reasons') or [])}",
        }
    issue_number = lineage_view['issue_number']
    issue_url = lineage_view['issue_url']
    pr_number = lineage_view['pr_number']
    pr_url = lineage_view['pr_url']
    workflow_stage = lineage_view['workflow_stage']
    recommended = lineage_view['recommended_actions']
    unattended_safe = lineage_view['unattended_safe']
    lineage = lineage_view['lineage']
    canonical_branch = args.canonical_branch or lineage.get('canonical_branch') or f'issue-{issue_number}'
    branch_name = canonical_branch
    if lineage.get('active_role_branch'):
        branch_name = lineage['active_role_branch']
    elif lineage.get('canonical_branch'):
        branch_name = lineage['canonical_branch']
    role_branch = args.role_branch
    if role_branch is None and branch_name != canonical_branch:
        role_branch = branch_name
    source_packet_path = str(args.source_packet_path.resolve()) if args.source_packet_path else lineage_view.get('source_packet_path')
    issue = {'url': issue_url, 'state': 'CLOSED' if pr_url and workflow_stage == 'dev_in_progress' and pr_number else 'OPEN'}
    pr = {'number': pr_number, 'url': pr_url, 'headRefName': branch_name, 'mergedAt': None}
    if pr_number is None:
        pr = None

    if args.decision_type == 'reset_required':
        _current, manifest = load_authority(repo_root)
        github_repo = github_repo_for_root(repo_root)
        package = load_design_package(args.project_slug, args.package_id_external)
        current_task = resolve_task_summary(manifest, package, issue_number)
        queues = queue_state(repo_root)
        qa_packet = latest_qa_packet(issue_number, repo_reports_dir(repo_root))
        fallback_packet = latest_packet_preview(queues, issue_number)
        issue_full, pr_full = github_state(
            issue_number,
            github_repo,
            fallback_pr_number=qa_packet.get('pr_number') if qa_packet else None,
            fallback_task=current_task,
            fallback_packet=fallback_packet,
        )
        _workflow_stage, _owner_role, escalations, _recommended, _unattended = derive_workflow(current_task, issue_full, pr_full, qa_packet, queues)
        reset_escalation = latest_escalation_of_type(escalations, 'reset_branch_required') or latest_escalation_of_type(escalations, 'reset_branch_recommended')
        if workflow_stage != 'dev_reset_required' and not reset_escalation:
            return {
                'ok': False,
                'workflow_stage': workflow_stage,
                'reason': 'reset_required_not_supported_for_current_stage',
                'details': 'reset_required decisions are only supported when TechLead detects a reset-required recovery state.',
            }
        if source_packet_path is None:
            return {
                'ok': False,
                'workflow_stage': workflow_stage,
                'reason': 'reset_required_missing_source_packet',
                'details': 'reset_required decision emission requires a source QA packet path.',
            }
        reset_reason = args.reset_reason or (reset_escalation or {}).get('summary') or 'TechLead determined the current lineage requires a clean reset.'
        superseded_branch = args.superseded_branch or role_branch or (branch_name if branch_name != canonical_branch else None)
        return {
            'ok': True,
            'workflow_stage': workflow_stage,
            'issue_number': issue_number,
            'issue_url': issue_url,
            'pr_number': pr_full.get('number') if pr_full else None,
            'pr_url': pr_full.get('url') if pr_full else None,
            'branch': branch_name,
            'to_role': 'techlead',
            'target_role_cli': 'python-team',
            'decision_type': 'reset_branch',
            'decision_rationale': reset_reason,
            'next_assignment_type': 'implement_authorized_slice',
            'work_item_status_update_intent': 'blocked',
            'canonical_branch': canonical_branch,
            'role_branch': role_branch,
            'branch_owner_role': 'TechLead',
            'lineage_state': 'reset_required',
            'lineage_action': 'reset',
            'source_branch': canonical_branch,
            'superseded_branch': superseded_branch,
            'worktree_hint': args.worktree_hint or f'issue-{issue_number}-dev',
            'reset_reason': reset_reason,
            'source_packet_path': source_packet_path,
            'recommended_actions': recommended,
            'unattended_safe': unattended_safe,
        }

    if args.decision_type == 'superseded':
        _current, manifest = load_authority(repo_root)
        github_repo = github_repo_for_root(repo_root)
        package = load_design_package(args.project_slug, args.package_id_external)
        current_task = resolve_task_summary(manifest, package, issue_number)
        queues = queue_state(repo_root)
        qa_packet = latest_qa_packet(issue_number, repo_reports_dir(repo_root))
        fallback_packet = latest_packet_preview(queues, issue_number)
        issue_full, pr_full = github_state(
            issue_number,
            github_repo,
            fallback_pr_number=qa_packet.get('pr_number') if qa_packet else None,
            fallback_task=current_task,
            fallback_packet=fallback_packet,
        )
        _workflow_stage, _owner_role, escalations, _recommended, _unattended = derive_workflow(current_task, issue_full, pr_full, qa_packet, queues)
        superseded_escalation = latest_escalation_of_type(escalations, 'qa_escalation_superseded')
        if superseded_escalation is None:
            return {
                'ok': False,
                'workflow_stage': workflow_stage,
                'reason': 'superseded_not_supported_for_current_stage',
                'details': 'superseded decisions are only supported when TechLead has detected a superseded QA escalation.',
            }
        if source_packet_path is None:
            return {
                'ok': False,
                'workflow_stage': workflow_stage,
                'reason': 'superseded_missing_source_packet',
                'details': 'superseded decision emission requires a source QA packet path.',
            }
        superseded_branch = args.superseded_branch or role_branch or (branch_name if branch_name != canonical_branch else canonical_branch)
        rationale = args.reset_reason or superseded_escalation.get('summary') or 'TechLead is recording that the prior branch lineage has been superseded.'
        return {
            'ok': True,
            'workflow_stage': workflow_stage,
            'issue_number': issue_number,
            'issue_url': issue_url,
            'pr_number': pr_full.get('number') if pr_full else None,
            'pr_url': pr_full.get('url') if pr_full else None,
            'branch': branch_name,
            'to_role': 'techlead',
            'target_role_cli': None,
            'decision_type': 'supersede_branch_lineage',
            'decision_rationale': rationale,
            'next_assignment_type': None,
            'work_item_status_update_intent': 'superseded',
            'canonical_branch': canonical_branch,
            'role_branch': role_branch,
            'branch_owner_role': 'TechLead',
            'lineage_state': 'superseded',
            'lineage_action': 'superseded',
            'source_branch': canonical_branch,
            'superseded_branch': superseded_branch,
            'worktree_hint': args.worktree_hint,
            'reset_reason': None,
            'source_packet_path': source_packet_path,
            'recommended_actions': recommended,
            'unattended_safe': unattended_safe,
        }

    if args.decision_type in {'closed', 'proof_only_closed'}:
        if pr_number is None and issue_url is None:
            return {
                'ok': False,
                'workflow_stage': workflow_stage,
                'reason': 'closed_not_supported_for_current_stage',
                'details': 'closed decisions require a closed lineage context with issue or PR identity.',
            }
        if source_packet_path is None:
            return {
                'ok': False,
                'workflow_stage': workflow_stage,
                'reason': 'closed_missing_source_packet',
                'details': 'closed decision emission requires an explicit source packet path or a resolved QA packet path.',
            }
        is_proof_only = args.decision_type == 'proof_only_closed'
        return {
            'ok': True,
            'workflow_stage': workflow_stage,
            'issue_number': issue_number,
            'issue_url': issue_url,
            'pr_number': pr_number,
            'pr_url': pr_url,
            'branch': branch_name,
            'to_role': 'techlead',
            'target_role_cli': None,
            'decision_type': 'proof_only_close_slice' if is_proof_only else 'close_slice',
            'decision_rationale': (
                'TechLead is recording the proof slice as proof-only closed after QA pass without requiring live merge or issue closure.'
                if is_proof_only
                else 'TechLead is recording the branch lineage as closed after the active slice reached merged/closed state.'
            ),
            'next_assignment_type': None,
            'work_item_status_update_intent': 'proof_only_closed' if is_proof_only else 'accepted',
            'canonical_branch': canonical_branch,
            'role_branch': role_branch,
            'branch_owner_role': 'TechLead',
            'lineage_state': 'closed',
            'lineage_action': 'proof_only_closed' if is_proof_only else 'closed',
            'source_branch': canonical_branch,
            'superseded_branch': args.superseded_branch,
            'worktree_hint': args.worktree_hint,
            'reset_reason': None,
            'source_packet_path': source_packet_path,
            'recommended_actions': recommended,
            'unattended_safe': unattended_safe,
        }

    return {
        'ok': False,
        'workflow_stage': workflow_stage,
        'reason': 'unsupported_decision_type',
        'details': f"Unsupported decision type {args.decision_type!r}.",
    }


def emit_decision(args):
    repo_root = args.repo_root.resolve()
    context = derive_decision_context(args)
    if not context.get('ok'):
        return context
    output_stem = args.decision_type.replace('_', '-')
    output_path = args.output or (repo_reports_dir(repo_root) / f'techlead-decision.issue{context["issue_number"]}.{output_stem}.json')
    review_output_path = args.review_output or (repo_reports_dir(repo_root) / f'techlead-decision.issue{context["issue_number"]}.{output_stem}.md')
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
        'materialize-techlead-decision-packet',
        '--manifest', str(auth_current),
        '--project-slug', args.project_slug,
        '--package-id-external', args.package_id_external,
        '--brief-id-external', args.brief_id_external,
        '--repo', github_repo_for_root(repo_root),
        '--issue-number', str(context['issue_number']),
        '--issue-url', str(context['issue_url']),
        '--pr-number', str(context['pr_number']),
        '--pr-url', str(context['pr_url']),
        '--branch', str(context['branch']),
        '--canonical-branch', str(context['canonical_branch']),
        '--to-role', context['to_role'],
        '--decision-type', context['decision_type'],
        '--decision-rationale', context['decision_rationale'],
        '--work-item-status-update-intent', context['work_item_status_update_intent'],
        '--source-packet-path', str(context['source_packet_path']),
        '--branch-owner-role', context['branch_owner_role'],
        '--lineage-state', context['lineage_state'],
        '--lineage-action', context['lineage_action'],
        '--source-branch', context['source_branch'],
        '--output', str(output_path),
        '--review-output', str(review_output_path),
        '--persist-db',
    ]
    if context.get('pr_number') is None or context.get('pr_url') is None:
        return {
            'ok': False,
            'workflow_stage': context['workflow_stage'],
            'reason': 'decision_missing_pr_context',
            'details': 'TechLead decision emission requires PR context in this slice.',
        }
    if context.get('target_role_cli'):
        compile_cmd.extend(['--target-role', context['target_role_cli']])
    if context.get('next_assignment_type'):
        compile_cmd.extend(['--next-assignment-type', context['next_assignment_type']])
    if context.get('role_branch'):
        compile_cmd.extend(['--role-branch', str(context['role_branch'])])
    if context.get('superseded_branch'):
        compile_cmd.extend(['--superseded-branch', str(context['superseded_branch'])])
    if context.get('worktree_hint'):
        compile_cmd.extend(['--worktree-hint', str(context['worktree_hint'])])
    if context.get('reset_reason'):
        compile_cmd.extend(['--reset-reason', context['reset_reason']])

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
            'decision_type': context['decision_type'],
            'lineage_state': context['lineage_state'],
            'lineage_action': context['lineage_action'],
            'target_role': context.get('target_role_cli'),
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
        'source_packet_path': context.get('source_packet_path'),
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


def closeout_qa_pass(args):
    repo_root = args.repo_root.resolve()
    package = load_design_package(args.project_slug, args.package_id_external)
    execution_mode = package_execution_mode(package)
    proof_only = execution_mode == 'proof_only'
    qa_packet = latest_qa_packet(args.issue_number, repo_reports_dir(repo_root))
    if qa_packet is None:
        return {
            'ok': False,
            'reason': 'qa_packet_not_found',
            'details': f'No repo-local QA verification packet was found for issue #{args.issue_number}.',
        }
    if qa_packet.get('verification_status') != 'pass':
        return {
            'ok': False,
            'reason': 'qa_packet_not_pass',
            'details': f"QA packet {qa_packet.get('message_id')!r} is not a passing packet.",
            'qa_packet': qa_packet,
        }

    fallback_packet = latest_packet_preview(queue_state(repo_root), args.issue_number)
    issue_full, pr_full = github_state(
        args.issue_number,
        github_repo_for_root(repo_root),
        fallback_pr_number=qa_packet.get('pr_number'),
        fallback_task={'issue_number': args.issue_number, 'title': f'Issue #{args.issue_number}'},
        fallback_packet=fallback_packet,
    )
    pr_merged = bool(pr_full and pr_full.get('mergedAt'))
    issue_closed = (issue_full.get('state') or '').upper() == 'CLOSED'
    if not pr_merged and not issue_closed and not proof_only:
        return {
            'ok': False,
            'reason': 'slice_not_merged_or_closed',
            'details': 'QA pass closeout requires a merged PR or a closed issue before TechLead records closed lineage.',
            'qa_packet': qa_packet,
            'github_state': {
                'issue_state': issue_full.get('state'),
                'pr_state': pr_full.get('state') if pr_full else None,
                'pr_merged_at': pr_full.get('mergedAt') if pr_full else None,
            },
        }

    persist_techlead_acceptance_event(
        getattr(args, 'db_container', DEFAULT_DB_CONTAINER),
        getattr(args, 'db_name', DEFAULT_DB_NAME),
        getattr(args, 'db_user', DEFAULT_DB_USER),
        args.project_slug,
        args.issue_number,
        qa_packet,
        pr_full or {},
        decision='proof_only_closed' if proof_only else 'accepted',
        decision_notes=(
            f"TechLead recorded proof-only closeout for issue #{args.issue_number} after QA pass from packet "
            f"{qa_packet.get('message_id')} without requiring live merge or issue closure."
            if proof_only
            else None
        ),
        metadata_extra={
            'closeout_mode': 'proof_only' if proof_only else 'live_delivery',
            'proof_only_closeout': proof_only,
            'issue_closed_at_closeout': issue_closed,
            'pr_merged_at_closeout': pr_merged,
        },
    )

    emit_args = SimpleNamespace(
        repo_root=repo_root,
        package_id_external=args.package_id_external,
        brief_id_external=args.brief_id_external,
        project_slug=args.project_slug,
        decision_type='proof_only_closed' if proof_only else 'closed',
        send=args.send_decision,
        source_packet_path=Path(qa_packet['path']),
        canonical_branch=args.canonical_branch,
        role_branch=args.role_branch,
        superseded_branch=None,
        worktree_hint=args.worktree_hint,
        reset_reason=None,
        output=args.output,
        review_output=args.review_output,
    )
    decision_result = emit_decision(emit_args)
    if not decision_result.get('ok'):
        return {
            'ok': False,
            'reason': 'decision_emission_failed',
            'details': 'TechLead could not record the closed decision for the passing QA packet.',
            'qa_packet': qa_packet,
            'decision': decision_result,
        }

    qa_ack = None
    if args.ack_qa_packet:
        architecture_state = queue_state(repo_root).get('fractal-core-architecture', {})
        architecture_preview = architecture_state.get('preview') or []
        head_payload = (architecture_preview[0] or {}).get('payload_preview') if architecture_preview else None
        if not head_payload or head_payload.get('message_id') != qa_packet.get('message_id'):
            return {
                'ok': False,
                'reason': 'qa_packet_not_queue_head',
                'details': 'The passing QA packet is not the next claimable architecture-queue message; refusing to acknowledge the wrong packet.',
                'qa_packet': qa_packet,
                'architecture_queue_head': head_payload,
                'decision': decision_result,
            }
        claim_cmd = [
            str(repo_queue_script(repo_root)),
            'queue-claim-next',
            '--repo-root', str(repo_root),
            '--queue', 'fractal-core-architecture',
            '--claimed-by', args.claimed_by,
        ]
        claim_result = run_json(claim_cmd)
        if claim_result.get('message_id') != qa_packet.get('message_id'):
            return {
                'ok': False,
                'reason': 'claimed_wrong_packet',
                'details': 'Architecture queue claim did not return the expected passing QA packet.',
                'qa_packet': qa_packet,
                'claim': claim_result,
                'decision': decision_result,
            }
        ack_cmd = [
            str(repo_queue_script(repo_root)),
            'queue-ack',
            '--repo-root', str(repo_root),
            '--queue', 'fractal-core-architecture',
            '--claim-id', claim_result['claim_id'],
        ]
        qa_ack = run_json(ack_cmd)

    decision_ack = None
    if args.send_decision and decision_result.get('sent'):
        architecture_state = queue_state(repo_root).get('fractal-core-architecture', {})
        architecture_preview = architecture_state.get('preview') or []
        head_payload = (architecture_preview[0] or {}).get('payload_preview') if architecture_preview else None
        decision_message_id = decision_result.get('message_id')
        if head_payload and head_payload.get('message_id') == decision_message_id:
            claim_cmd = [
                str(repo_queue_script(repo_root)),
                'queue-claim-next',
                '--repo-root', str(repo_root),
                '--queue', 'fractal-core-architecture',
                '--claimed-by', f"{args.claimed_by}-decision",
            ]
            claim_result = run_json(claim_cmd)
            if claim_result.get('message_id') == decision_message_id:
                ack_cmd = [
                    str(repo_queue_script(repo_root)),
                    'queue-ack',
                    '--repo-root', str(repo_root),
                    '--queue', 'fractal-core-architecture',
                    '--claim-id', claim_result['claim_id'],
                ]
                decision_ack = run_json(ack_cmd)
            else:
                decision_ack = {
                    'ok': False,
                    'reason': 'claimed_wrong_decision_packet',
                    'expected_message_id': decision_message_id,
                    'claim': claim_result,
                }
        else:
            decision_ack = {
                'ok': False,
                'reason': 'decision_packet_not_queue_head',
                'expected_message_id': decision_message_id,
                'architecture_queue_head': head_payload,
            }

    return {
        'ok': True,
        'issue_number': args.issue_number,
        'execution_mode': execution_mode,
        'closeout_mode': 'proof_only' if proof_only else 'live_delivery',
        'qa_packet': qa_packet,
        'github_state': {
            'issue_state': issue_full.get('state'),
            'issue_closed_at': issue_full.get('closedAt'),
            'pr_number': pr_full.get('number') if pr_full else None,
            'pr_state': pr_full.get('state') if pr_full else None,
            'pr_merged_at': pr_full.get('mergedAt') if pr_full else None,
        },
        'decision': decision_result,
        'qa_ack': qa_ack,
        'decision_ack': decision_ack,
        'next_step_hint': 'run_closed_cleanup_if_registered_role_worktrees_should_be_pruned',
    }


def accept_and_merge_qa_pass(args):
    repo_root = args.repo_root.resolve()
    qa_packet = latest_qa_packet(args.issue_number, repo_reports_dir(repo_root))
    if qa_packet is None:
        return {
            'ok': False,
            'reason': 'qa_packet_not_found',
            'details': f'No repo-local QA verification packet was found for issue #{args.issue_number}.',
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

    fallback_packet = latest_packet_preview(queue_state(repo_root), args.issue_number)
    github_repo = github_repo_for_root(repo_root)
    issue_full, pr_full = github_state(
        args.issue_number,
        github_repo,
        fallback_pr_number=qa_packet.get('pr_number'),
        fallback_task={'issue_number': args.issue_number, 'title': f'Issue #{args.issue_number}'},
        fallback_packet=fallback_packet,
    )
    if pr_full is None:
        return {
            'ok': False,
            'reason': 'pr_not_found',
            'details': f'No PR could be resolved for issue #{args.issue_number}.',
            'qa_packet': qa_packet,
            'github_state': {'issue_state': issue_full.get('state') if issue_full else None},
        }

    merge_state = run_json([
        'gh', 'pr', 'view', str(pr_full['number']),
        '--repo', github_repo,
        '--json', 'number,state,isDraft,mergeStateStatus,mergedAt,statusCheckRollup,url',
    ])
    ci_status = derive_ci_status(merge_state)
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
        'merge_method': args.merge_method,
        'pr_number': pr_full['number'],
        'pr_url': pr_full.get('url'),
    }
    if not pr_merged:
        merge_cmd = [
            'gh', 'pr', 'merge', str(pr_full['number']),
            '--repo', github_repo,
            f'--{args.merge_method}',
        ]
        merge_code, merge_stdout, merge_error = run_text_with_errors(merge_cmd)
        merge_result.update({
            'ok': merge_code == 0,
            'stdout': merge_stdout.strip() if merge_stdout else '',
            'stderr': merge_error if merge_code != 0 else '',
        })
        if merge_code != 0:
            return {
                'ok': False,
                'reason': 'pr_merge_failed',
                'details': f"TechLead could not merge PR #{pr_full['number']}.",
                'qa_packet': qa_packet,
                'pr': merge_state,
                'merge': merge_result,
            }

    issue_after_merge, pr_after_merge = github_state(
        args.issue_number,
        github_repo,
        fallback_pr_number=pr_full.get('number'),
        fallback_task={'issue_number': args.issue_number, 'title': f'Issue #{args.issue_number}'},
        fallback_packet=fallback_packet,
    )
    issue_close = {'ok': True, 'already_closed': (issue_after_merge.get('state') or '').upper() == 'CLOSED'}
    if not issue_close['already_closed']:
        close_cmd = [
            'gh', 'issue', 'close', str(args.issue_number),
            '--repo', github_repo,
            '--reason', 'completed',
            '--comment', args.issue_close_comment or f'Closed by TechLead after QA pass and merge of PR #{pr_full["number"]}.',
        ]
        close_code, close_stdout, close_error = run_text_with_errors(close_cmd)
        issue_close.update({
            'ok': close_code == 0,
            'stdout': close_stdout.strip() if close_stdout else '',
            'stderr': close_error if close_code != 0 else '',
        })
        if close_code != 0:
            return {
                'ok': False,
                'reason': 'issue_close_failed',
                'details': f'TechLead merged the PR but could not close issue #{args.issue_number}.',
                'qa_packet': qa_packet,
                'merge': merge_result,
                'issue_close': issue_close,
            }

    final_issue_state, final_pr_state = github_state(
        args.issue_number,
        github_repo,
        fallback_pr_number=pr_full.get('number'),
        fallback_task={'issue_number': args.issue_number, 'title': f'Issue #{args.issue_number}'},
        fallback_packet=fallback_packet,
    )

    closeout_args = SimpleNamespace(
        repo_root=repo_root,
        package_id_external=args.package_id_external,
        brief_id_external=args.brief_id_external,
        project_slug=args.project_slug,
        issue_number=args.issue_number,
        send_decision=True,
        ack_qa_packet=True,
        claimed_by=args.claimed_by,
        canonical_branch=args.canonical_branch,
        role_branch=args.role_branch,
        worktree_hint=args.worktree_hint,
        output=args.output,
        review_output=args.review_output,
    )
    closeout_result = closeout_qa_pass(closeout_args)
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
        'issue_number': args.issue_number,
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


def prepare_role_branch(args):
    repo_root = args.repo_root.resolve()
    lineage_view = build_lineage_view(
        repo_root,
        args.project_slug,
        args.package_id_external,
        args.brief_id_external,
    )
    if not lineage_view.get('ok'):
        return {
            'ok': False,
            'reason': 'ambiguous_lineage_view',
            'details': f"Lineage helper could not produce an unambiguous lineage view: {', '.join(lineage_view.get('ambiguity_reasons') or [])}",
            'lineage_view': lineage_view,
        }

    issue_number = lineage_view['issue_number']
    lineage = lineage_view['lineage']
    canonical_branch = normalize_canonical_branch(repo_root, issue_number, lineage, args.canonical_branch)
    role_branch = role_branch_name(issue_number, args.target_role, args.role_branch)
    source_ref, source_commit = resolve_canonical_source_ref(repo_root, canonical_branch)
    if source_ref is None or source_commit is None:
        return {
            'ok': False,
            'reason': 'canonical_branch_unresolved',
            'details': f'Could not resolve canonical branch {canonical_branch!r} locally or from origin.',
            'lineage_view': lineage_view,
            'canonical_branch': canonical_branch,
            'role_branch': role_branch,
        }

    branch_exists_before = git_local_branch_exists(repo_root, role_branch)
    branch_head_before = git_resolve_ref(repo_root, role_branch) if branch_exists_before else None
    checked_out_paths = git_branch_usage(repo_root, role_branch)
    mutation_required = (not branch_exists_before) or (branch_head_before != source_commit)

    if args.action == 'ensure' and branch_exists_before and branch_head_before != source_commit:
        return {
            'ok': False,
            'reason': 'role_branch_exists_with_different_tip',
            'details': f'Role branch {role_branch!r} already exists at a different commit. Use --action reset to realign it to {canonical_branch!r}.',
            'lineage_view': lineage_view,
            'canonical_branch': canonical_branch,
            'canonical_source_ref': source_ref,
            'canonical_source_commit': source_commit,
            'role_branch': role_branch,
            'branch_head_before': branch_head_before,
            'branch_checked_out_in': checked_out_paths,
        }

    if args.action == 'reset' and mutation_required and checked_out_paths:
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
    if args.action == 'ensure':
        if not branch_exists_before:
            run_text(['git', 'branch', role_branch, source_ref], cwd=repo_root)
            mutated = True
            created = True
    elif args.action == 'reset':
        if not branch_exists_before or branch_head_before != source_commit:
            run_text(['git', 'branch', '-f', role_branch, source_ref], cwd=repo_root)
            mutated = True
            created = not branch_exists_before
            reset = branch_exists_before

    branch_head_after = git_resolve_ref(repo_root, role_branch)
    return {
        'ok': branch_head_after == source_commit,
        'action': args.action,
        'repo_root': str(repo_root),
        'issue_number': issue_number,
        'workflow_stage': lineage_view.get('workflow_stage'),
        'target_role': args.target_role,
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


def prepare_role_worktree(args):
    repo_root = args.repo_root.resolve()
    branch_args = SimpleNamespace(
        repo_root=repo_root,
        project_slug=args.project_slug,
        package_id_external=args.package_id_external,
        brief_id_external=args.brief_id_external,
        target_role=args.target_role,
        action=args.branch_action,
        canonical_branch=args.canonical_branch,
        role_branch=args.role_branch,
    )
    branch_result = prepare_role_branch(branch_args)
    if not branch_result.get('ok'):
        return {
            'ok': False,
            'reason': 'role_branch_prepare_failed',
            'details': 'Role worktree preparation requires a successful role-branch preparation result.',
            'branch_prepare': branch_result,
        }

    role_branch = branch_result['role_branch']
    existing_branch_worktree = git_worktree_for_branch(repo_root, role_branch)
    requested_path = (args.worktree_path.resolve() if args.worktree_path else default_role_worktree_path(repo_root, role_branch))

    if existing_branch_worktree is not None:
        existing_path = Path(existing_branch_worktree['path']).resolve()
        if args.worktree_path and existing_path != requested_path:
            return {
                'ok': False,
                'reason': 'role_branch_checked_out_elsewhere',
                'details': f'Role branch {role_branch!r} is already checked out in another worktree.',
                'branch_prepare': branch_result,
                'worktree_path': str(requested_path),
                'existing_worktree_path': str(existing_path),
            }
        return {
            'ok': True,
            'action': 'reuse',
            'repo_root': str(repo_root),
            'target_role': args.target_role,
            'role_branch': role_branch,
            'worktree_path': str(existing_path),
            'worktree_head': existing_branch_worktree.get('head'),
            'worktree_ownership': worktree_ownership_record(
                repo_root,
                args.target_role,
                role_branch,
                existing_path,
                worktree_entry=existing_branch_worktree,
            ),
            'branch_prepare': branch_result,
            'created': False,
            'reused': True,
            'next_step_hint': 'enter_worktree_and_execute_role',
        }

    existing_path_worktree = git_worktree_for_path(repo_root, requested_path)
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
        return {
            'ok': True,
            'action': 'reuse',
            'repo_root': str(repo_root),
            'target_role': args.target_role,
            'role_branch': role_branch,
            'worktree_path': str(requested_path),
            'worktree_head': existing_path_worktree.get('head'),
            'worktree_ownership': worktree_ownership_record(
                repo_root,
                args.target_role,
                role_branch,
                requested_path,
                worktree_entry=existing_path_worktree,
            ),
            'branch_prepare': branch_result,
            'created': False,
            'reused': True,
            'next_step_hint': 'enter_worktree_and_execute_role',
        }

    if requested_path.exists():
        return {
            'ok': False,
            'reason': 'worktree_path_exists_not_registered',
            'details': f'Worktree path {str(requested_path)!r} already exists but is not registered as a git worktree for this repo.',
            'branch_prepare': branch_result,
            'worktree_path': str(requested_path),
        }

    requested_path.parent.mkdir(parents=True, exist_ok=True)
    run_text(['git', 'worktree', 'add', str(requested_path), role_branch], cwd=repo_root)
    created_worktree = git_worktree_for_path(repo_root, requested_path)
    return {
        'ok': created_worktree is not None,
        'action': 'create',
        'repo_root': str(repo_root),
        'target_role': args.target_role,
        'role_branch': role_branch,
        'worktree_path': str(requested_path),
        'worktree_head': created_worktree.get('head') if created_worktree else None,
        'worktree_ownership': worktree_ownership_record(
            repo_root,
            args.target_role,
            role_branch,
            requested_path,
            worktree_entry=created_worktree,
        ),
        'branch_prepare': branch_result,
        'created': True,
        'reused': False,
        'next_step_hint': 'enter_worktree_and_execute_role',
    }


def handoff_to_role_worktree(args):
    repo_root = args.repo_root.resolve()
    emit_args = SimpleNamespace(
        repo_root=repo_root,
        package_id_external=args.package_id_external,
        brief_id_external=args.brief_id_external,
        project_slug=args.project_slug,
        target_role=args.target_role,
        send=args.send,
        output=args.output,
        review_output=args.review_output,
    )
    assignment_result = emit_next_assignment(emit_args)
    if not assignment_result.get('ok'):
        return {
            'ok': False,
            'reason': 'assignment_emission_failed',
            'details': 'Role-worktree handoff requires a successful TechLead assignment emission result.',
            'assignment': assignment_result,
        }

    derived_target_role = ((assignment_result.get('derived_decision') or {}).get('target_role') or '').strip()
    role_cli = None
    if derived_target_role == 'QA':
        role_cli = 'qa'
    elif derived_target_role == 'Delivery Architect':
        role_cli = 'delivery-architect'
    else:
        worker_role = team_worker_role_for_label(derived_target_role, repo_root=repo_root)
        if worker_role:
            role_cli = worker_role.key
    if role_cli is None:
        return {
            'ok': False,
            'reason': 'unsupported_assignment_target_for_worktree',
            'details': f'Assignment target {derived_target_role!r} is not supported for role-worktree preparation in this slice.',
            'assignment': assignment_result,
        }

    worktree_args = SimpleNamespace(
        repo_root=repo_root,
        package_id_external=args.package_id_external,
        brief_id_external=args.brief_id_external,
        project_slug=args.project_slug,
        target_role=role_cli,
        branch_action=args.branch_action,
        canonical_branch=args.canonical_branch,
        role_branch=args.role_branch,
        worktree_path=args.worktree_path,
    )
    worktree_result = prepare_role_worktree(worktree_args)
    return {
        'ok': bool(assignment_result.get('ok')) and bool(worktree_result.get('ok')),
        'repo_root': str(repo_root),
        'package_id_external': args.package_id_external,
        'brief_id_external': args.brief_id_external,
        'target_role': derived_target_role,
        'sent': bool(assignment_result.get('sent')),
        'resolved_queue': assignment_result.get('resolved_queue'),
        'assignment': assignment_result,
        'worktree': worktree_result,
        'next_step_hint': 'enter_prepared_worktree_and_execute_role' if worktree_result.get('ok') else 'investigate_worktree_preparation',
    }


def inspect_role_worktree(args):
    repo_root = args.repo_root.resolve()
    lineage_view = build_lineage_view(
        repo_root,
        args.project_slug,
        args.package_id_external,
        args.brief_id_external,
    )
    if not lineage_view.get('ok'):
        return {
            'ok': False,
            'reason': 'ambiguous_lineage_view',
            'details': f"Lineage helper could not produce an unambiguous lineage view: {', '.join(lineage_view.get('ambiguity_reasons') or [])}",
            'lineage_view': lineage_view,
        }

    issue_number = lineage_view['issue_number']
    role_branch = role_branch_name(issue_number, args.target_role, args.role_branch)
    worktree_path = (args.worktree_path.resolve() if args.worktree_path else default_role_worktree_path(repo_root, role_branch))
    worktree_entry = git_worktree_for_path(repo_root, worktree_path)
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

    human_role = role_label_for_cli(args.target_role)
    default_output_path, default_review_output_path = default_assignment_paths(repo_root, issue_number, human_role)
    assignment_path = (args.assignment_path.resolve() if args.assignment_path else default_output_path.resolve())
    review_output_path = (args.review_output.resolve() if args.review_output else default_review_output_path.resolve())
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

    packet = handoff_runtime.load_json(assignment_path)
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

    current_branch = git_current_branch(worktree_path)
    return {
        'ok': True,
        'repo_root': str(repo_root),
        'package_id_external': args.package_id_external,
        'brief_id_external': args.brief_id_external,
        'target_role': human_role,
        'role_branch': role_branch,
        'worktree_path': str(worktree_path),
        'current_branch': current_branch,
        'worktree_ownership': worktree_ownership_record(
            repo_root,
            args.target_role,
            role_branch,
            worktree_path,
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


def worktree_ownership(args):
    repo_root = args.repo_root.resolve()
    lineage_view = build_lineage_view(
        repo_root,
        args.project_slug,
        args.package_id_external,
        args.brief_id_external,
    )
    if not lineage_view.get('ok'):
        return {
            'ok': False,
            'reason': 'ambiguous_lineage_view',
            'details': f"Lineage helper could not produce an unambiguous lineage view: {', '.join(lineage_view.get('ambiguity_reasons') or [])}",
            'lineage_view': lineage_view,
        }

    issue_number = lineage_view['issue_number']
    role_branch = role_branch_name(issue_number, args.target_role, args.role_branch)
    worktree_path = (args.worktree_path.resolve() if args.worktree_path else default_role_worktree_path(repo_root, role_branch))
    worktree_entry = git_worktree_for_path(repo_root, worktree_path)
    ownership = worktree_ownership_record(
        repo_root,
        args.target_role,
        role_branch,
        worktree_path,
        worktree_entry=worktree_entry,
    )
    return {
        'ok': True,
        'repo_root': str(repo_root),
        'package_id_external': args.package_id_external,
        'brief_id_external': args.brief_id_external,
        'issue_number': issue_number,
        'workflow_stage': lineage_view.get('workflow_stage'),
        'worktree_ownership': ownership,
        'worktree_staleness': worktree_staleness_assessment(
            (lineage_view.get('lineage') or {}).get('lineage_state'),
            ownership,
        ),
        'lineage_view': lineage_view,
        'next_step_hint': 'role_automation_may_prepare_or_reuse_its_owned_worktree' if not ownership.get('registered') else 'role_automation_may_enter_owned_worktree',
    }


def worktree_stale(args):
    ownership_view = worktree_ownership(args)
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


def reset_required_lifecycle(args):
    repo_root = args.repo_root.resolve()
    target_role = args.target_role or 'python-team'
    if target_role != 'python-team':
        return {
            'ok': False,
            'reason': 'unsupported_target_role_for_reset_required',
            'details': 'Phase H3 reset-required lifecycle mutation supports only python-team in this slice.',
            'target_role': target_role,
        }

    ownership_args = SimpleNamespace(
        repo_root=repo_root,
        project_slug=args.project_slug,
        package_id_external=args.package_id_external,
        brief_id_external=args.brief_id_external,
        target_role=target_role,
        role_branch=args.role_branch,
        worktree_path=args.worktree_path,
    )
    ownership_view = worktree_ownership(ownership_args)
    if not ownership_view.get('ok'):
        return {
            'ok': False,
            'reason': 'worktree_ownership_unavailable',
            'details': 'Reset-required lifecycle mutation requires a successful worktree ownership query.',
            'ownership_view': ownership_view,
        }

    stale_view = worktree_stale(ownership_args)
    if not stale_view.get('ok'):
        return {
            'ok': False,
            'reason': 'worktree_staleness_unavailable',
            'details': 'Reset-required lifecycle mutation requires a successful stale-worktree query.',
            'ownership_view': ownership_view,
            'stale_view': stale_view,
        }

    lineage_view = ownership_view.get('lineage_view') or {}
    workflow_stage = lineage_view.get('workflow_stage')
    if workflow_stage != 'dev_reset_required':
        return {
            'ok': False,
            'reason': 'reset_required_not_supported_for_current_stage',
            'details': 'Reset-required lifecycle mutation is only supported when the current workflow is dev_reset_required.',
            'workflow_stage': workflow_stage,
            'target_role': target_role,
            'ownership_view': ownership_view,
            'stale_view': stale_view,
        }

    decision_args = SimpleNamespace(
        repo_root=repo_root,
        package_id_external=args.package_id_external,
        brief_id_external=args.brief_id_external,
        project_slug=args.project_slug,
        decision_type='reset_required',
        send=bool(args.send_decision),
        source_packet_path=args.source_packet_path,
        canonical_branch=args.canonical_branch,
        role_branch=args.role_branch,
        superseded_branch=args.superseded_branch,
        worktree_hint=args.worktree_hint,
        reset_reason=args.reset_reason,
        output=args.output,
        review_output=args.review_output,
    )
    decision_result = emit_decision(decision_args)
    if not decision_result.get('ok'):
        return {
            'ok': False,
            'reason': 'reset_required_decision_failed',
            'details': 'Reset-required lifecycle mutation could not emit the underlying TechLead decision.',
            'workflow_stage': workflow_stage,
            'target_role': target_role,
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
        'target_role': target_role,
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


def reset_cleanup(args):
    repo_root = args.repo_root.resolve()
    target_role = args.target_role or 'python-team'
    if target_role != 'python-team':
        return {
            'ok': False,
            'reason': 'unsupported_target_role_for_reset_cleanup',
            'details': 'Phase H4 physical reset cleanup supports only python-team in this slice.',
            'target_role': target_role,
        }

    reset_args = SimpleNamespace(
        repo_root=repo_root,
        package_id_external=args.package_id_external,
        brief_id_external=args.brief_id_external,
        project_slug=args.project_slug,
        target_role=target_role,
        role_branch=args.role_branch,
        worktree_path=args.worktree_path,
        send_decision=bool(args.send_decision),
        source_packet_path=args.source_packet_path,
        canonical_branch=args.canonical_branch,
        superseded_branch=args.superseded_branch,
        worktree_hint=args.worktree_hint,
        reset_reason=args.reset_reason,
        output=args.output,
        review_output=args.review_output,
    )
    lifecycle = reset_required_lifecycle(reset_args)
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

    entry_before = git_worktree_for_path(repo_root, worktree_path)
    if entry_before is None:
        return {
            'ok': False,
            'reason': 'reset_cleanup_requires_registered_worktree_entry',
            'details': 'The owned worktree is no longer registered; refusing to run physical cleanup against an ambiguous state.',
            'lifecycle': lifecycle,
        }

    code, _stdout, error = run_text_with_errors(
        ['git', 'worktree', 'remove', str(worktree_path)],
        cwd=repo_root,
    )
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

    entry_after = git_worktree_for_path(repo_root, worktree_path)
    branch_preserved = bool(role_branch and git_local_branch_exists(repo_root, role_branch))

    return {
        'ok': True,
        'workflow_stage': lifecycle.get('workflow_stage'),
        'target_role': target_role,
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


def superseded_cleanup(args):
    repo_root = args.repo_root.resolve()
    target_role = args.target_role or 'python-team'
    if target_role != 'python-team':
        return {
            'ok': False,
            'reason': 'unsupported_target_role_for_superseded_cleanup',
            'details': 'Phase H5 superseded cleanup supports only python-team in this slice.',
            'target_role': target_role,
        }

    lineage_view = build_lineage_view(
        repo_root,
        args.project_slug,
        args.package_id_external,
        args.brief_id_external,
    )
    if not lineage_view.get('ok'):
        return {
            'ok': False,
            'reason': 'ambiguous_lineage_view',
            'details': f"Lineage helper could not produce an unambiguous lineage view: {', '.join(lineage_view.get('ambiguity_reasons') or [])}",
            'lineage_view': lineage_view,
        }
    lineage = lineage_view.get('lineage') or {}
    workflow_stage = lineage_view.get('workflow_stage')
    if lineage.get('lineage_state') != 'superseded':
        return {
            'ok': False,
            'reason': 'superseded_not_supported_for_current_stage',
            'details': 'Superseded cleanup is only supported when lineage state is superseded.',
            'workflow_stage': workflow_stage,
            'lineage_view': lineage_view,
        }
    if not (args.superseded_branch or lineage.get('superseded_branch')):
        return {
            'ok': False,
            'reason': 'superseded_cleanup_requires_superseded_branch',
            'details': 'Superseded cleanup requires lineage to identify a superseded branch.',
            'workflow_stage': workflow_stage,
            'lineage_view': lineage_view,
        }

    ownership_args = SimpleNamespace(
        repo_root=repo_root,
        project_slug=args.project_slug,
        package_id_external=args.package_id_external,
        brief_id_external=args.brief_id_external,
        target_role=target_role,
        role_branch=args.role_branch,
        worktree_path=args.worktree_path,
    )
    ownership_view = worktree_ownership(ownership_args)
    if not ownership_view.get('ok'):
        return {
            'ok': False,
            'reason': 'worktree_ownership_unavailable',
            'details': 'Superseded cleanup requires a successful worktree ownership query.',
            'ownership_view': ownership_view,
            'lineage_view': lineage_view,
        }

    stale_view = worktree_stale(ownership_args)
    if not stale_view.get('ok'):
        return {
            'ok': False,
            'reason': 'worktree_staleness_unavailable',
            'details': 'Superseded cleanup requires a successful stale-worktree query.',
            'ownership_view': ownership_view,
            'stale_view': stale_view,
            'lineage_view': lineage_view,
        }

    decision_args = SimpleNamespace(
        repo_root=repo_root,
        package_id_external=args.package_id_external,
        brief_id_external=args.brief_id_external,
        project_slug=args.project_slug,
        decision_type='superseded',
        send=bool(args.send_decision),
        source_packet_path=args.source_packet_path,
        canonical_branch=args.canonical_branch,
        role_branch=args.role_branch,
        superseded_branch=args.superseded_branch or lineage.get('superseded_branch'),
        worktree_hint=args.worktree_hint,
        reset_reason=args.reset_reason,
        output=args.output,
        review_output=args.review_output,
    )
    decision_result = emit_decision(decision_args)
    if not decision_result.get('ok'):
        return {
            'ok': False,
            'reason': 'superseded_decision_failed',
            'details': 'Superseded cleanup could not emit the underlying TechLead decision.',
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
    superseded_branch = args.superseded_branch or lineage.get('superseded_branch') or role_branch

    if not ownership.get('registered'):
        return {
            'ok': False,
            'reason': 'superseded_cleanup_requires_registered_worktree',
            'details': 'Superseded cleanup only runs when the owned role worktree is currently registered.',
            'lineage_view': lineage_view,
            'ownership_view': ownership_view,
            'stale_view': stale_view,
            'decision_result': decision_result,
        }
    if not staleness.get('stale') or not staleness.get('cleanup_candidate'):
        return {
            'ok': False,
            'reason': 'superseded_cleanup_requires_stale_cleanup_candidate',
            'details': 'Superseded cleanup only runs when stale detection marks the worktree as a cleanup candidate.',
            'lineage_view': lineage_view,
            'ownership_view': ownership_view,
            'stale_view': stale_view,
            'decision_result': decision_result,
        }
    if not worktree_path_value or not default_path_value:
        return {
            'ok': False,
            'reason': 'superseded_cleanup_missing_worktree_path',
            'details': 'Superseded cleanup requires a concrete owned worktree path.',
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
            'reason': 'superseded_cleanup_requires_default_owned_worktree_path',
            'details': 'Superseded cleanup only runs against the deterministic owned worktree path in this slice.',
            'lineage_view': lineage_view,
            'ownership_view': ownership_view,
            'stale_view': stale_view,
            'decision_result': decision_result,
        }

    entry_before = git_worktree_for_path(repo_root, worktree_path)
    if entry_before is None:
        return {
            'ok': False,
            'reason': 'superseded_cleanup_requires_registered_worktree_entry',
            'details': 'The owned worktree is no longer registered; refusing to run physical cleanup against an ambiguous state.',
            'lineage_view': lineage_view,
            'ownership_view': ownership_view,
            'stale_view': stale_view,
            'decision_result': decision_result,
        }

    code, _stdout, error = run_text_with_errors(
        ['git', 'worktree', 'remove', str(worktree_path)],
        cwd=repo_root,
    )
    if code != 0:
        return {
            'ok': False,
            'reason': 'git_worktree_remove_failed',
            'details': 'git worktree remove did not complete successfully.',
            'worktree_path': str(worktree_path),
            'role_branch': role_branch,
            'superseded_branch': superseded_branch,
            'prior_worktree_ownership': ownership,
            'prior_worktree_staleness': staleness,
            'decision_result': decision_result,
            'git_error': error,
            'lineage_view': lineage_view,
        }

    entry_after = git_worktree_for_path(repo_root, worktree_path)
    branch_preserved = bool(superseded_branch and git_local_branch_exists(repo_root, superseded_branch))

    return {
        'ok': True,
        'workflow_stage': workflow_stage,
        'target_role': target_role,
        'canonical_branch': lineage.get('canonical_branch'),
        'role_branch': role_branch,
        'superseded_branch': superseded_branch,
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
        'decision_result': decision_result,
        'next_step_hint': (
            'prepare_replacement_role_worktree_only_if_new_assignment_requires_it'
            if entry_after is None
            else 'investigate_remaining_registered_worktree_state'
        ),
        'lineage_view': lineage_view,
    }


def closed_cleanup(args):
    repo_root = args.repo_root.resolve()
    target_role = args.target_role or 'python-team'
    if target_role != 'python-team':
        return {
            'ok': False,
            'reason': 'unsupported_target_role_for_closed_cleanup',
            'details': 'Phase H6 closed cleanup supports only python-team in this slice.',
            'target_role': target_role,
        }

    lineage_view = build_lineage_view(
        repo_root,
        args.project_slug,
        args.package_id_external,
        args.brief_id_external,
    )
    if not lineage_view.get('ok'):
        return {
            'ok': False,
            'reason': 'ambiguous_lineage_view',
            'details': f"Lineage helper could not produce an unambiguous lineage view: {', '.join(lineage_view.get('ambiguity_reasons') or [])}",
            'lineage_view': lineage_view,
        }
    lineage = lineage_view.get('lineage') or {}
    workflow_stage = lineage_view.get('workflow_stage')
    if lineage.get('lineage_state') != 'closed':
        return {
            'ok': False,
            'reason': 'closed_not_supported_for_current_stage',
            'details': 'Closed cleanup is only supported when lineage state is closed.',
            'workflow_stage': workflow_stage,
            'lineage_view': lineage_view,
        }

    ownership_args = SimpleNamespace(
        repo_root=repo_root,
        project_slug=args.project_slug,
        package_id_external=args.package_id_external,
        brief_id_external=args.brief_id_external,
        target_role=target_role,
        role_branch=args.role_branch,
        worktree_path=args.worktree_path,
    )
    ownership_view = worktree_ownership(ownership_args)
    if not ownership_view.get('ok'):
        return {
            'ok': False,
            'reason': 'worktree_ownership_unavailable',
            'details': 'Closed cleanup requires a successful worktree ownership query.',
            'ownership_view': ownership_view,
            'lineage_view': lineage_view,
        }

    stale_view = worktree_stale(ownership_args)
    if not stale_view.get('ok'):
        return {
            'ok': False,
            'reason': 'worktree_staleness_unavailable',
            'details': 'Closed cleanup requires a successful stale-worktree query.',
            'ownership_view': ownership_view,
            'stale_view': stale_view,
            'lineage_view': lineage_view,
        }

    decision_args = SimpleNamespace(
        repo_root=repo_root,
        package_id_external=args.package_id_external,
        brief_id_external=args.brief_id_external,
        project_slug=args.project_slug,
        decision_type='closed',
        send=bool(args.send_decision),
        source_packet_path=args.source_packet_path,
        canonical_branch=args.canonical_branch,
        role_branch=args.role_branch,
        superseded_branch=args.superseded_branch,
        worktree_hint=args.worktree_hint,
        reset_reason=args.reset_reason,
        output=args.output,
        review_output=args.review_output,
    )
    decision_result = emit_decision(decision_args)
    if not decision_result.get('ok'):
        return {
            'ok': False,
            'reason': 'closed_decision_failed',
            'details': 'Closed cleanup could not emit the underlying TechLead decision.',
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
            'reason': 'closed_cleanup_requires_registered_worktree',
            'details': 'Closed cleanup only runs when the owned role worktree is currently registered.',
            'lineage_view': lineage_view,
            'ownership_view': ownership_view,
            'stale_view': stale_view,
            'decision_result': decision_result,
        }
    if not staleness.get('stale') or not staleness.get('cleanup_candidate'):
        return {
            'ok': False,
            'reason': 'closed_cleanup_requires_stale_cleanup_candidate',
            'details': 'Closed cleanup only runs when stale detection marks the worktree as a cleanup candidate.',
            'lineage_view': lineage_view,
            'ownership_view': ownership_view,
            'stale_view': stale_view,
            'decision_result': decision_result,
        }
    if not worktree_path_value or not default_path_value:
        return {
            'ok': False,
            'reason': 'closed_cleanup_missing_worktree_path',
            'details': 'Closed cleanup requires a concrete owned worktree path.',
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
            'reason': 'closed_cleanup_requires_default_owned_worktree_path',
            'details': 'Closed cleanup only runs against the deterministic owned worktree path in this slice.',
            'lineage_view': lineage_view,
            'ownership_view': ownership_view,
            'stale_view': stale_view,
            'decision_result': decision_result,
        }

    entry_before = git_worktree_for_path(repo_root, worktree_path)
    if entry_before is None:
        return {
            'ok': False,
            'reason': 'closed_cleanup_requires_registered_worktree_entry',
            'details': 'The owned worktree is no longer registered; refusing to run physical cleanup against an ambiguous state.',
            'lineage_view': lineage_view,
            'ownership_view': ownership_view,
            'stale_view': stale_view,
            'decision_result': decision_result,
        }

    code, _stdout, error = run_text_with_errors(
        ['git', 'worktree', 'remove', str(worktree_path)],
        cwd=repo_root,
    )
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

    entry_after = git_worktree_for_path(repo_root, worktree_path)
    role_branch_preserved = bool(role_branch and git_local_branch_exists(repo_root, role_branch))
    canonical_branch_preserved = bool(canonical_branch and git_local_branch_exists(repo_root, canonical_branch))

    return {
        'ok': True,
        'workflow_stage': workflow_stage,
        'target_role': target_role,
        'canonical_branch': canonical_branch,
        'role_branch': role_branch,
        'worktree_path': str(worktree_path),
        'cleanup_performed': entry_after is None,
        'cleanup_result': {
            'command': ['git', 'worktree', 'remove', str(worktree_path)],
            'worktree_removed': entry_after is None,
            'worktree_still_registered': entry_after is not None,
            'role_branch_preserved': role_branch_preserved,
            'canonical_branch_preserved': canonical_branch_preserved,
        },
        'prior_worktree_ownership': ownership,
        'prior_worktree_staleness': staleness,
        'decision_result': decision_result,
        'next_step_hint': (
            'retain_closed_lineage_branches_for_audit_until_explicit_retirement_policy_exists'
            if entry_after is None
            else 'investigate_remaining_registered_worktree_state'
        ),
        'lineage_view': lineage_view,
    }


def role_entry_helper(args):
    inspection_args = SimpleNamespace(
        repo_root=args.repo_root,
        package_id_external=args.package_id_external,
        brief_id_external=args.brief_id_external,
        project_slug=args.project_slug,
        target_role=args.target_role,
        role_branch=args.role_branch,
        worktree_path=args.worktree_path,
        assignment_path=args.assignment_path,
        review_output=args.review_output,
    )
    inspection = inspect_role_worktree(inspection_args)
    if not inspection.get('ok'):
        return {
            'ok': False,
            'reason': 'inspection_failed',
            'details': 'Role entry helper requires a successful role-worktree inspection result.',
            'inspection': inspection,
        }

    repo_root = args.repo_root.resolve()
    worktree_path = Path(inspection['worktree_path']).resolve()
    current_branch = inspection['current_branch']
    role_branch = inspection['role_branch']
    artifact = inspection['assignment_artifact']
    role_label = inspection['target_role']
    branch_alignment = {
        'ok': current_branch == role_branch,
        'current_branch': current_branch,
        'expected_role_branch': role_branch,
        'assignment_role_branch': artifact.get('role_branch'),
        'assignment_canonical_branch': artifact.get('canonical_branch'),
    }
    if artifact.get('role_branch') and artifact.get('role_branch') != role_branch:
        return {
            'ok': False,
            'reason': 'assignment_role_branch_mismatch',
            'details': 'The assignment artifact names a different role branch than the prepared worktree context.',
            'inspection': inspection,
            'branch_alignment': branch_alignment,
        }
    if current_branch != role_branch:
        return {
            'ok': False,
            'reason': 'worktree_branch_not_aligned',
            'details': 'The prepared worktree is no longer on the expected role branch.',
            'inspection': inspection,
            'branch_alignment': branch_alignment,
        }

    producer_wrapper = repo_root / '.codex' / 'paa' / 'bin' / 'paa-producer'
    issue_number = inspection['lineage_view']['issue_number']
    issue_url = inspection['lineage_view']['issue_url']
    pr_number = inspection['lineage_view']['pr_number']
    pr_url = inspection['lineage_view']['pr_url']
    team_worker = team_worker_role_for_label(role_label, repo_root=repo_root)
    if role_label == 'Delivery Architect':
        result_command = [
            str(producer_wrapper),
            'authority',
            'materialize-delivery-review-packet',
            '--project-slug', args.project_slug,
            '--package-id-external', args.package_id_external,
            '--brief-id-external', args.brief_id_external,
            '--repo', str(worktree_path),
            '--issue-number', str(issue_number),
            '--issue-url', str(issue_url),
            '--pr-number', str(pr_number),
            '--pr-url', str(pr_url),
            '--branch', current_branch,
            '--result-type', '<delivery_result_type>',
            '--delivery-input-file', '<delivery_input_json>',
            '--source-assignment-path', artifact['path'],
            '--source-assignment-type', artifact['assignment_type'],
            '--persist-db',
        ]
    elif team_worker:
        result_command = [
            str(producer_wrapper),
            'authority',
            'materialize-worker-result-packet',
            '--project-slug', args.project_slug,
            '--package-id-external', args.package_id_external,
            '--brief-id-external', args.brief_id_external,
            '--worker-role', team_worker.key,
            '--worker-family', team_worker.family,
            '--result-type', '<worker_result_type>',
            '--repo', str(worktree_path),
            '--issue-number', str(issue_number),
            '--issue-url', str(issue_url),
            '--pr-number', str(pr_number),
            '--pr-url', str(pr_url),
            '--branch', current_branch,
            '--worker-input-file', '<worker_input_json>',
            '--source-assignment-path', artifact['path'],
            '--source-assignment-type', artifact['assignment_type'],
            '--persist-db',
        ]
    else:
        result_command = [
            str(producer_wrapper),
            'authority',
            'materialize-qa-verification-packet',
            '--project-slug', args.project_slug,
            '--package-id-external', args.package_id_external,
            '--brief-id-external', args.brief_id_external,
            '--repo', str(worktree_path),
            '--issue-number', str(issue_number),
            '--issue-url', str(issue_url),
            '--pr-number', str(pr_number),
            '--pr-url', str(pr_url),
            '--branch', current_branch,
            '--qa-input-file', '<qa_input_json>',
            '--persist-db',
        ]

    return {
        'ok': True,
        'repo_root': str(repo_root),
        'target_role': role_label,
        'worktree_path': str(worktree_path),
        'assignment_artifact': artifact,
        'branch_alignment': branch_alignment,
        'manual_execution_surfaces': {
            'enter_worktree_command': f'cd {worktree_path}',
            'assignment_json_command': f'cat {artifact["path"]}',
            'assignment_review_command': f'cat {artifact["review_output_path"]}',
            'result_compile_command': ' '.join(result_command),
            'producer_wrapper_path': str(producer_wrapper),
        },
        'inspection': inspection,
        'next_step_hint': 'review_assignment_and_begin_role_work_manually',
    }


def role_result_assist(args):
    entry_args = SimpleNamespace(
        repo_root=args.repo_root,
        package_id_external=args.package_id_external,
        brief_id_external=args.brief_id_external,
        project_slug=args.project_slug,
        target_role=args.target_role,
        role_branch=args.role_branch,
        worktree_path=args.worktree_path,
        assignment_path=args.assignment_path,
        review_output=args.review_output,
    )
    entry = role_entry_helper(entry_args)
    if not entry.get('ok'):
        return {
            'ok': False,
            'reason': 'role_entry_failed',
            'details': 'Role result assist requires a successful role-entry context.',
            'role_entry': entry,
        }

    inspection = entry['inspection']
    lineage_view = inspection['lineage_view']
    role_label = entry['target_role']
    worktree_path = Path(entry['worktree_path']).resolve()
    branch_alignment = entry['branch_alignment']
    artifact = entry['assignment_artifact']
    repo_root = args.repo_root.resolve()
    issue_number = lineage_view.get('issue_number')
    issue_url = lineage_view.get('issue_url')
    pr_number = lineage_view.get('pr_number')
    pr_url = lineage_view.get('pr_url')
    current_branch = branch_alignment.get('current_branch')
    required_context = {
        'issue_number': issue_number,
        'issue_url': issue_url,
        'pr_number': pr_number,
        'pr_url': pr_url,
        'branch': current_branch,
        'package_id_external': args.package_id_external,
        'brief_id_external': args.brief_id_external,
        'assignment_artifact_path': artifact.get('path'),
        'allowed_result_types': artifact.get('allowed_result_types') or [],
    }
    missing_fields = [
        field_name for field_name, field_value in required_context.items()
        if field_value in (None, '', [])
    ]
    if not branch_alignment.get('ok'):
        missing_fields.append('aligned_role_branch')
    if artifact.get('assignment_type') is None:
        missing_fields.append('assignment_type')

    result_input_path = (
        args.result_input_path.resolve()
        if getattr(args, 'result_input_path', None)
        else default_result_input_path(repo_root, issue_number, role_label)
    )

    team_worker = team_worker_role_for_label(role_label, repo_root=repo_root)
    if role_label == 'Delivery Architect':
        result_family = 'delivery_review_packet'
        input_flag = '--delivery-input-file'
        expected_assignment_type = 'delivery_architecture_review'
        input_contract = {
            'required_top_level_keys': [
                'result_type',
                'scope_recommendation',
                'authority_impact',
                'branch_recommendation',
                'techlead_action_recommended',
                'review_summary',
                'findings',
            ],
            'recommended_result_types': [
                'ready_for_dev',
                'narrow_scope',
                'reject_scope',
            ],
        }
    elif team_worker:
        result_family = 'worker_result_packet'
        input_flag = '--worker-input-file'
        expected_assignment_type = 'implement_authorized_slice'
        input_contract = {
            'required_top_level_keys': [
                'result_type',
                'implementation_summary',
                'validation_summary',
                'artifacts',
                'merge_status',
            ],
            'recommended_result_types': [
                'implemented_ready_for_qa',
                'blocked',
                'needs_clarification',
            ],
        }
    else:
        result_family = 'qa_verification_packet'
        input_flag = '--qa-input-file'
        expected_assignment_type = 'verify_authorized_slice'
        input_contract = {
            'required_top_level_keys': [
                'verification_status',
                'mechanical_checks',
                'technical_scope_checks',
                'protected_path_checks',
                'artifact_checks',
                'findings',
            ],
            'recommended_result_types': [
                'pass',
                'fail_fixable',
                'needs_human_review',
            ],
        }

    if artifact.get('assignment_type') != expected_assignment_type:
        return {
            'ok': False,
            'reason': 'assignment_type_not_supported_for_role_result',
            'details': f'Assignment type {artifact.get("assignment_type")!r} is not supported for role {role_label!r} in the current Phase E bridge.',
            'role_entry': entry,
            'expected_assignment_type': expected_assignment_type,
        }

    producer_wrapper = repo_root / '.codex' / 'paa' / 'bin' / 'paa-producer'
    if role_label == 'Delivery Architect':
        result_compile_command = [
            str(producer_wrapper),
            'authority',
            'materialize-delivery-review-packet',
            '--project-slug', args.project_slug,
            '--package-id-external', args.package_id_external,
            '--brief-id-external', args.brief_id_external,
            '--repo', str(worktree_path),
            '--issue-number', str(issue_number),
            '--issue-url', str(issue_url),
            '--pr-number', str(pr_number),
            '--pr-url', str(pr_url),
            '--branch', str(current_branch),
            '--result-type', '<delivery_result_type>',
            '--delivery-input-file', str(result_input_path),
            '--source-assignment-path', str(artifact.get('path')),
            '--source-assignment-type', str(artifact.get('assignment_type')),
            '--persist-db',
        ]
    elif team_worker:
        result_compile_command = [
            str(producer_wrapper),
            'authority',
            'materialize-worker-result-packet',
            '--project-slug', args.project_slug,
            '--package-id-external', args.package_id_external,
            '--brief-id-external', args.brief_id_external,
            '--worker-role', team_worker.key,
            '--worker-family', team_worker.family,
            '--result-type', '<worker_result_type>',
            '--repo', str(worktree_path),
            '--issue-number', str(issue_number),
            '--issue-url', str(issue_url),
            '--pr-number', str(pr_number),
            '--pr-url', str(pr_url),
            '--branch', str(current_branch),
            '--worker-input-file', str(result_input_path),
            '--source-assignment-path', str(artifact.get('path')),
            '--source-assignment-type', str(artifact.get('assignment_type')),
            '--persist-db',
        ]
    else:
        result_compile_command = [
            str(producer_wrapper),
            'authority',
            'materialize-qa-verification-packet',
            '--project-slug', args.project_slug,
            '--package-id-external', args.package_id_external,
            '--brief-id-external', args.brief_id_external,
            '--repo', str(worktree_path),
            '--issue-number', str(issue_number),
            '--issue-url', str(issue_url),
            '--pr-number', str(pr_number),
            '--pr-url', str(pr_url),
            '--branch', str(current_branch),
            '--qa-input-file', str(result_input_path),
            '--persist-db',
        ]

    return {
        'ok': len(missing_fields) == 0,
        'repo_root': str(repo_root),
        'target_role': role_label,
        'result_family': result_family,
        'worktree_path': str(worktree_path),
        'branch_alignment': branch_alignment,
        'assignment_artifact': artifact,
        'required_context': required_context,
        'missing_fields': missing_fields,
        'result_input_contract': input_contract,
        'manual_result_surfaces': {
            'enter_worktree_command': entry['manual_execution_surfaces']['enter_worktree_command'],
            'assignment_json_command': entry['manual_execution_surfaces']['assignment_json_command'],
            'assignment_review_command': entry['manual_execution_surfaces']['assignment_review_command'],
            'result_input_template_path': str(result_input_path),
            'result_compile_command': ' '.join(result_compile_command),
            'producer_wrapper_path': str(producer_wrapper),
        },
        'role_entry': entry,
        'next_step_hint': 'prepare_role_result_input_and_compile_manually' if len(missing_fields) == 0 else 'resolve_missing_role_result_context',
    }


def role_return_bridge(args):
    assist_args = SimpleNamespace(
        repo_root=args.repo_root,
        package_id_external=args.package_id_external,
        brief_id_external=args.brief_id_external,
        project_slug=args.project_slug,
        target_role=args.target_role,
        role_branch=args.role_branch,
        worktree_path=args.worktree_path,
        assignment_path=args.assignment_path,
        review_output=args.assignment_review_output,
        result_input_path=args.result_input_path,
    )
    assist = role_result_assist(assist_args)
    if not assist.get('ok'):
        return {
            'ok': False,
            'reason': 'role_result_assist_failed',
            'details': 'Role return bridge requires a successful role-result assist context.',
            'assist': assist,
        }

    result_input_path = Path(assist['manual_result_surfaces']['result_input_template_path']).resolve()
    if not result_input_path.exists():
        return {
            'ok': False,
            'reason': 'result_input_missing',
            'details': f'No role result input file was found at {str(result_input_path)!r}.',
            'assist': assist,
            'result_input_path': str(result_input_path),
        }

    repo_root = args.repo_root.resolve()
    issue_number = assist['required_context']['issue_number']
    role_label = assist['target_role']
    default_output_path, default_review_output_path = default_result_packet_paths(repo_root, issue_number, role_label)
    output_path = args.output.resolve() if getattr(args, 'output', None) else default_output_path.resolve()
    review_output_path = args.review_output.resolve() if getattr(args, 'review_output', None) else default_review_output_path.resolve()

    compile_command = assist['manual_result_surfaces']['result_compile_command'].split()
    if role_label == 'Delivery Architect' or is_team_worker_label(role_label, repo_root=repo_root):
        result_input = handoff_runtime.load_json(result_input_path)
        result_type = result_input.get('result_type')
        if not result_type:
            return {
                'ok': False,
                'reason': 'result_type_missing',
                'details': f'{role_label} return bridge requires result_input_file to include a top-level result_type.',
                'assist': assist,
                'result_input_path': str(result_input_path),
            }
        compile_command = [
            result_type
            if token in {'<delivery_result_type>', '<worker_result_type>'}
            else token
            for token in compile_command
        ]
    compile_command.extend([
        '--output', str(output_path),
        '--review-output', str(review_output_path),
    ])
    code, compile_result, compile_error = run_json_with_errors(compile_command)
    if code != 0 or compile_result is None:
        return {
            'ok': False,
            'reason': 'result_compile_failed',
            'details': compile_error,
            'assist': assist,
            'compile_command': compile_command,
        }

    packet_path = Path(compile_result['output_path']).resolve()
    packet = handoff_runtime.load_json(packet_path)
    errors = handoff_runtime.validate_envelope(packet, require_authority=True)
    from paa_consumer.inbox import resolve_packet_queue
    resolved_queue = resolve_packet_queue(packet)
    validate_result = {
        'ok': not errors,
        'message_file': str(packet_path),
        'message_id': packet.get('message_id'),
        'schema_type': packet.get('schema_type'),
        'resolved_queue': resolved_queue,
        'from_role': packet.get('from_role'),
        'to_role': packet.get('to_role'),
        'errors': errors,
    }
    if errors:
        return {
            'ok': False,
            'reason': 'result_packet_validation_failed',
            'details': 'Compiled role result packet failed envelope validation.',
            'assist': assist,
            'compile': compile_result,
            'validate': validate_result,
        }

    send_result = None
    source_assignment_ack = None
    if args.send:
        from paa_consumer.inbox import dispatch_packet
        send_result = dispatch_packet(repo_root, packet_path)
        if not send_result.get('ok'):
            return {
                'ok': False,
                'reason': 'result_packet_send_failed',
                'details': 'Compiled role result packet could not be sent through the queue runtime.',
                'assist': assist,
                'compile': compile_result,
                'validate': validate_result,
                'send': send_result,
            }
        assignment_artifact = assist.get('assignment_artifact') or {}
        source_assignment_message_id = assignment_artifact.get('message_id')
        source_assignment_path = assignment_artifact.get('path')
        source_assignment_queue = None
        if source_assignment_path:
            from paa_consumer.inbox import resolve_packet_queue
            source_assignment_packet = handoff_runtime.load_json(Path(source_assignment_path).resolve())
            source_assignment_queue = resolve_packet_queue(source_assignment_packet)
        if source_assignment_message_id and source_assignment_queue:
            source_assignment_ack = acknowledge_source_assignment(
                repo_root,
                source_assignment_message_id,
                source_assignment_queue,
                claimed_by=f"{args.target_role}-role-return",
            )
            if not source_assignment_ack.get('ok'):
                return {
                    'ok': False,
                    'reason': 'source_assignment_ack_failed',
                    'details': 'Role result packet was sent, but the source assignment packet could not be closed cleanly.',
                    'assist': assist,
                    'compile': compile_result,
                    'validate': validate_result,
                    'send': send_result,
                    'source_assignment_ack': source_assignment_ack,
                }

    return {
        'ok': True,
        'repo_root': str(repo_root),
        'target_role': role_label,
        'result_family': assist['result_family'],
        'result_input_path': str(result_input_path),
        'output_path': str(packet_path),
        'review_output_path': str(review_output_path),
        'compile': compile_result,
        'validate': validate_result,
        'send': send_result,
        'source_assignment_ack': source_assignment_ack,
        'sent': bool(send_result and send_result.get('ok')),
        'resolved_queue': resolved_queue,
        'assist': assist,
        'next_step_hint': 'techlead_should_review_returned_result' if args.send else 'review_compiled_role_result_packet',
    }


def persist_report(report, args):
    db_settings = resolve_db_settings(args.db_profile, args.db_container, args.db_name, args.db_user)
    agent_id = resolve_agent_id(
        db_settings.container,
        db_settings.name,
        db_settings.user,
        args.project_slug,
        args.agent_name,
    )
    if agent_id is None:
        raise RuntimeError(
            f"Could not resolve TechLead agent {args.agent_name!r} in project {args.project_slug!r}."
        )

    issue_number = ((report.get('active_work') or {}).get('work_item') or {}).get('issue_number')
    work_item_id = resolve_work_item_id(
        db_settings.container,
        db_settings.name,
        db_settings.user,
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
    automation_run_id = run_psql(
        db_settings.container,
        db_settings.name,
        db_settings.user,
        sql,
        db_profile=args.db_profile,
    ).strip()
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
    status.add_argument('--repo-root', type=Path, default=REPO_ROOT, help='Consumer repo root for TechLead status generation.')
    status.add_argument('--output', type=Path, help='Write the JSON report to this path.')
    status.add_argument('--schema', type=Path, default=DEFAULT_SCHEMA, help='Schema path to use with --validate-schema.')
    status.add_argument('--validate-schema', action='store_true', help='Validate the generated report against the TechLead JSON schema.')
    status.add_argument('--persist-db', action='store_true', help='Persist the generated report into paa.automation_runs.')
    status.add_argument('--db-profile', default=DEFAULT_DB_PROFILE, help='DB profile defined in paa_core.db.')
    status.add_argument('--db-container', help='Override Docker container running Postgres.')
    status.add_argument('--db-name', help='Override Postgres database name.')
    status.add_argument('--db-user', help='Override Postgres database user.')
    status.add_argument('--project-slug', default=DEFAULT_PROJECT_SLUG, help='PAA project slug to resolve agent and work item IDs.')
    status.add_argument('--agent-name', default=DEFAULT_AGENT_NAME, help='PAA agent name used for TechLead persistence.')

    emit = sub.add_parser('emit-next-assignment')
    emit.add_argument('--repo-root', type=Path, default=REPO_ROOT, help='Consumer repo root for dispatch commands.')
    emit.add_argument('--package-id-external', required=True)
    emit.add_argument('--brief-id-external', required=True)
    emit.add_argument('--project-slug', default=DEFAULT_PROJECT_SLUG)
    emit.add_argument('--target-role', choices=ROLE_EMIT_TARGET_CHOICES, help='Explicitly request a supported target role. Omit to derive from current TechLead-visible workflow state.')
    emit.add_argument('--send', action='store_true', help='Send the compiled packet after validation succeeds.')
    emit.add_argument('--output', type=Path, help='Write the compiled packet JSON to this path.')
    emit.add_argument('--review-output', type=Path, help='Write the compiled packet review markdown to this path.')

    lineage = sub.add_parser('lineage')
    lineage.add_argument('--repo-root', type=Path, default=REPO_ROOT, help='Consumer repo root for lineage inspection.')
    lineage.add_argument('--package-id-external', required=True)
    lineage.add_argument('--brief-id-external', required=True)
    lineage.add_argument('--project-slug', default=DEFAULT_PROJECT_SLUG)

    branch = sub.add_parser('prepare-role-branch')
    branch.add_argument('--repo-root', type=Path, default=REPO_ROOT, help='Consumer repo root where role branches are managed.')
    branch.add_argument('--package-id-external', required=True)
    branch.add_argument('--brief-id-external', required=True)
    branch.add_argument('--project-slug', default=DEFAULT_PROJECT_SLUG)
    branch.add_argument('--target-role', choices=ROLE_BRIDGE_TARGET_CHOICES, required=True)
    branch.add_argument('--action', choices=['ensure', 'reset'], required=True)
    branch.add_argument('--canonical-branch')
    branch.add_argument('--role-branch')

    worktree = sub.add_parser('prepare-role-worktree')
    worktree.add_argument('--repo-root', type=Path, default=REPO_ROOT, help='Consumer repo root where role worktrees are managed.')
    worktree.add_argument('--package-id-external', required=True)
    worktree.add_argument('--brief-id-external', required=True)
    worktree.add_argument('--project-slug', default=DEFAULT_PROJECT_SLUG)
    worktree.add_argument('--target-role', choices=ROLE_BRIDGE_TARGET_CHOICES, required=True)
    worktree.add_argument('--branch-action', choices=['ensure', 'reset'], default='ensure')
    worktree.add_argument('--canonical-branch')
    worktree.add_argument('--role-branch')
    worktree.add_argument('--worktree-path', type=Path)

    handoff = sub.add_parser('handoff-to-role-worktree')
    handoff.add_argument('--repo-root', type=Path, default=REPO_ROOT, help='Consumer repo root for assignment emission and role worktree preparation.')
    handoff.add_argument('--package-id-external', required=True)
    handoff.add_argument('--brief-id-external', required=True)
    handoff.add_argument('--project-slug', default=DEFAULT_PROJECT_SLUG)
    handoff.add_argument('--target-role', choices=ROLE_BRIDGE_TARGET_CHOICES, help='Explicitly request a supported target role. Omit to derive from current TechLead-visible workflow state.')
    handoff.add_argument('--send', action='store_true', help='Send the compiled assignment packet after validation succeeds.')
    handoff.add_argument('--output', type=Path, help='Write the compiled assignment packet JSON to this path.')
    handoff.add_argument('--review-output', type=Path, help='Write the compiled assignment packet review markdown to this path.')
    handoff.add_argument('--branch-action', choices=['ensure', 'reset'], default='ensure')
    handoff.add_argument('--canonical-branch')
    handoff.add_argument('--role-branch')
    handoff.add_argument('--worktree-path', type=Path)

    inspect = sub.add_parser('inspect-role-worktree')
    inspect.add_argument('--repo-root', type=Path, default=REPO_ROOT, help='Consumer repo root for role-worktree inspection.')
    inspect.add_argument('--package-id-external', required=True)
    inspect.add_argument('--brief-id-external', required=True)
    inspect.add_argument('--project-slug', default=DEFAULT_PROJECT_SLUG)
    inspect.add_argument('--target-role', choices=ROLE_BRIDGE_TARGET_CHOICES, required=True)
    inspect.add_argument('--role-branch')
    inspect.add_argument('--worktree-path', type=Path)
    inspect.add_argument('--assignment-path', type=Path)
    inspect.add_argument('--review-output', type=Path)

    ownership = sub.add_parser('worktree-ownership')
    ownership.add_argument('--repo-root', type=Path, default=REPO_ROOT, help='Consumer repo root for worktree ownership inspection.')
    ownership.add_argument('--package-id-external', required=True)
    ownership.add_argument('--brief-id-external', required=True)
    ownership.add_argument('--project-slug', default=DEFAULT_PROJECT_SLUG)
    ownership.add_argument('--target-role', choices=ROLE_BRIDGE_TARGET_CHOICES, required=True)
    ownership.add_argument('--role-branch')
    ownership.add_argument('--worktree-path', type=Path)

    stale = sub.add_parser('worktree-stale')
    stale.add_argument('--repo-root', type=Path, default=REPO_ROOT, help='Consumer repo root for stale worktree inspection.')
    stale.add_argument('--package-id-external', required=True)
    stale.add_argument('--brief-id-external', required=True)
    stale.add_argument('--project-slug', default=DEFAULT_PROJECT_SLUG)
    stale.add_argument('--target-role', choices=ROLE_BRIDGE_TARGET_CHOICES, required=True)
    stale.add_argument('--role-branch')
    stale.add_argument('--worktree-path', type=Path)

    reset_lifecycle = sub.add_parser('reset-required')
    reset_lifecycle.add_argument('--repo-root', type=Path, default=REPO_ROOT, help='Consumer repo root for reset-required lifecycle mutation planning.')
    reset_lifecycle.add_argument('--package-id-external', required=True)
    reset_lifecycle.add_argument('--brief-id-external', required=True)
    reset_lifecycle.add_argument('--project-slug', default=DEFAULT_PROJECT_SLUG)
    reset_lifecycle.add_argument('--target-role', choices=['python-team'], default='python-team')
    reset_lifecycle.add_argument('--role-branch')
    reset_lifecycle.add_argument('--worktree-path', type=Path)
    reset_lifecycle.add_argument('--send-decision', action='store_true')
    reset_lifecycle.add_argument('--source-packet-path', type=Path)
    reset_lifecycle.add_argument('--canonical-branch')
    reset_lifecycle.add_argument('--superseded-branch')
    reset_lifecycle.add_argument('--worktree-hint')
    reset_lifecycle.add_argument('--reset-reason')
    reset_lifecycle.add_argument('--output', type=Path)
    reset_lifecycle.add_argument('--review-output', type=Path)

    reset_cleanup_parser = sub.add_parser('reset-cleanup')
    reset_cleanup_parser.add_argument('--repo-root', type=Path, default=REPO_ROOT, help='Consumer repo root for physical reset cleanup.')
    reset_cleanup_parser.add_argument('--package-id-external', required=True)
    reset_cleanup_parser.add_argument('--brief-id-external', required=True)
    reset_cleanup_parser.add_argument('--project-slug', default=DEFAULT_PROJECT_SLUG)
    reset_cleanup_parser.add_argument('--target-role', choices=['python-team'], default='python-team')
    reset_cleanup_parser.add_argument('--role-branch')
    reset_cleanup_parser.add_argument('--worktree-path', type=Path)
    reset_cleanup_parser.add_argument('--send-decision', action='store_true')
    reset_cleanup_parser.add_argument('--source-packet-path', type=Path)
    reset_cleanup_parser.add_argument('--canonical-branch')
    reset_cleanup_parser.add_argument('--superseded-branch')
    reset_cleanup_parser.add_argument('--worktree-hint')
    reset_cleanup_parser.add_argument('--reset-reason')
    reset_cleanup_parser.add_argument('--output', type=Path)
    reset_cleanup_parser.add_argument('--review-output', type=Path)

    superseded_cleanup_parser = sub.add_parser('superseded-cleanup')
    superseded_cleanup_parser.add_argument('--repo-root', type=Path, default=REPO_ROOT, help='Consumer repo root for superseded physical cleanup.')
    superseded_cleanup_parser.add_argument('--package-id-external', required=True)
    superseded_cleanup_parser.add_argument('--brief-id-external', required=True)
    superseded_cleanup_parser.add_argument('--project-slug', default=DEFAULT_PROJECT_SLUG)
    superseded_cleanup_parser.add_argument('--target-role', choices=['python-team'], default='python-team')
    superseded_cleanup_parser.add_argument('--role-branch')
    superseded_cleanup_parser.add_argument('--worktree-path', type=Path)
    superseded_cleanup_parser.add_argument('--send-decision', action='store_true')
    superseded_cleanup_parser.add_argument('--source-packet-path', type=Path)
    superseded_cleanup_parser.add_argument('--canonical-branch')
    superseded_cleanup_parser.add_argument('--superseded-branch')
    superseded_cleanup_parser.add_argument('--worktree-hint')
    superseded_cleanup_parser.add_argument('--reset-reason')
    superseded_cleanup_parser.add_argument('--output', type=Path)
    superseded_cleanup_parser.add_argument('--review-output', type=Path)

    closed_cleanup_parser = sub.add_parser('closed-cleanup')
    closed_cleanup_parser.add_argument('--repo-root', type=Path, default=REPO_ROOT, help='Consumer repo root for closed physical cleanup.')
    closed_cleanup_parser.add_argument('--package-id-external', required=True)
    closed_cleanup_parser.add_argument('--brief-id-external', required=True)
    closed_cleanup_parser.add_argument('--project-slug', default=DEFAULT_PROJECT_SLUG)
    closed_cleanup_parser.add_argument('--target-role', choices=['python-team'], default='python-team')
    closed_cleanup_parser.add_argument('--role-branch')
    closed_cleanup_parser.add_argument('--worktree-path', type=Path)
    closed_cleanup_parser.add_argument('--send-decision', action='store_true')
    closed_cleanup_parser.add_argument('--source-packet-path', type=Path)
    closed_cleanup_parser.add_argument('--canonical-branch')
    closed_cleanup_parser.add_argument('--superseded-branch')
    closed_cleanup_parser.add_argument('--worktree-hint')
    closed_cleanup_parser.add_argument('--reset-reason')
    closed_cleanup_parser.add_argument('--output', type=Path)
    closed_cleanup_parser.add_argument('--review-output', type=Path)

    entry = sub.add_parser('role-entry')
    entry.add_argument('--repo-root', type=Path, default=REPO_ROOT, help='Consumer repo root for role entry guidance.')
    entry.add_argument('--package-id-external', required=True)
    entry.add_argument('--brief-id-external', required=True)
    entry.add_argument('--project-slug', default=DEFAULT_PROJECT_SLUG)
    entry.add_argument('--target-role', choices=ROLE_BRIDGE_TARGET_CHOICES, required=True)
    entry.add_argument('--role-branch')
    entry.add_argument('--worktree-path', type=Path)
    entry.add_argument('--assignment-path', type=Path)
    entry.add_argument('--review-output', type=Path)

    result_assist = sub.add_parser('role-result-assist')
    result_assist.add_argument('--repo-root', type=Path, default=REPO_ROOT, help='Consumer repo root for role result guidance.')
    result_assist.add_argument('--package-id-external', required=True)
    result_assist.add_argument('--brief-id-external', required=True)
    result_assist.add_argument('--project-slug', default=DEFAULT_PROJECT_SLUG)
    result_assist.add_argument('--target-role', choices=ROLE_BRIDGE_TARGET_CHOICES, required=True)
    result_assist.add_argument('--role-branch')
    result_assist.add_argument('--worktree-path', type=Path)
    result_assist.add_argument('--assignment-path', type=Path)
    result_assist.add_argument('--review-output', type=Path)
    result_assist.add_argument('--result-input-path', type=Path)

    role_return = sub.add_parser('role-return')
    role_return.add_argument('--repo-root', type=Path, default=REPO_ROOT, help='Consumer repo root for role result compile/send bridge.')
    role_return.add_argument('--package-id-external', required=True)
    role_return.add_argument('--brief-id-external', required=True)
    role_return.add_argument('--project-slug', default=DEFAULT_PROJECT_SLUG)
    role_return.add_argument('--target-role', choices=ROLE_BRIDGE_TARGET_CHOICES, required=True)
    role_return.add_argument('--role-branch')
    role_return.add_argument('--worktree-path', type=Path)
    role_return.add_argument('--assignment-path', type=Path)
    role_return.add_argument('--assignment-review-output', type=Path)
    role_return.add_argument('--result-input-path', type=Path)
    role_return.add_argument('--output', type=Path)
    role_return.add_argument('--review-output', type=Path)
    role_return.add_argument('--send', action='store_true')

    decision = sub.add_parser('emit-decision')
    decision.add_argument('--repo-root', type=Path, default=REPO_ROOT, help='Consumer repo root for dispatch commands.')
    decision.add_argument('--package-id-external', required=True)
    decision.add_argument('--brief-id-external', required=True)
    decision.add_argument('--project-slug', default=DEFAULT_PROJECT_SLUG)
    decision.add_argument('--decision-type', choices=['reset_required', 'superseded', 'closed'], required=True)
    decision.add_argument('--send', action='store_true', help='Send the compiled decision packet after validation succeeds.')
    decision.add_argument('--source-packet-path', type=Path, help='Explicit source packet path to use when runtime inference is insufficient.')
    decision.add_argument('--canonical-branch')
    decision.add_argument('--role-branch')
    decision.add_argument('--superseded-branch')
    decision.add_argument('--worktree-hint')
    decision.add_argument('--reset-reason')
    decision.add_argument('--output', type=Path, help='Write the compiled packet JSON to this path.')
    decision.add_argument('--review-output', type=Path, help='Write the compiled packet review markdown to this path.')

    closeout = sub.add_parser('closeout-qa-pass')
    closeout.add_argument('--repo-root', type=Path, default=REPO_ROOT, help='Consumer repo root for closeout commands.')
    closeout.add_argument('--package-id-external', required=True)
    closeout.add_argument('--brief-id-external', required=True)
    closeout.add_argument('--project-slug', default=DEFAULT_PROJECT_SLUG)
    closeout.add_argument('--issue-number', type=int, required=True)
    closeout.add_argument('--send-decision', action='store_true', help='Send the compiled closed decision packet after validation succeeds.')
    closeout.add_argument('--ack-qa-packet', action='store_true', help='Acknowledge the passing QA packet after the closeout decision succeeds.')
    closeout.add_argument('--claimed-by', default='techlead-closeout-qa-pass')
    closeout.add_argument('--canonical-branch')
    closeout.add_argument('--role-branch')
    closeout.add_argument('--worktree-hint')
    closeout.add_argument('--output', type=Path)
    closeout.add_argument('--review-output', type=Path)

    accept = sub.add_parser('accept-and-merge')
    accept.add_argument('--repo-root', type=Path, default=REPO_ROOT, help='Consumer repo root for autonomous TechLead acceptance commands.')
    accept.add_argument('--package-id-external', required=True)
    accept.add_argument('--brief-id-external', required=True)
    accept.add_argument('--project-slug', default=DEFAULT_PROJECT_SLUG)
    accept.add_argument('--issue-number', type=int, required=True)
    accept.add_argument('--merge-method', choices=['merge', 'squash', 'rebase'], default='merge')
    accept.add_argument('--issue-close-comment')
    accept.add_argument('--claimed-by', default='techlead-accept-and-merge')
    accept.add_argument('--canonical-branch')
    accept.add_argument('--role-branch')
    accept.add_argument('--worktree-hint')
    accept.add_argument('--output', type=Path)
    accept.add_argument('--review-output', type=Path)

    preflight = sub.add_parser('automation-preflight')
    preflight.add_argument('--repo-root', type=Path, default=REPO_ROOT, help='Consumer repo root for non-model automation preflight.')
    preflight.add_argument('--project-slug', default=DEFAULT_PROJECT_SLUG)
    preflight.add_argument('--target-role', choices=PREFLIGHT_TARGET_CHOICES, required=True)

    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.command in {None, 'status'}:
        report = build_report(args.repo_root.resolve(), args.project_slug)
        if args.validate_schema:
            validate_report(report, args.schema)
        persistence = None
        if args.persist_db:
            persistence = persist_report(report, args)
        text = json.dumps(report, indent=2)
        if args.output:
            args.output.write_text(text + '\n')
        if persistence:
            persisted_db_name = args.db_name or resolve_db_settings(args.db_profile, args.db_container, args.db_name, args.db_user).name
            sys.stderr.write(
                f"Persisted TechLead report to {persisted_db_name} as automation_run_id={persistence['automation_run_id']}"
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
    if args.command == 'lineage':
        result = build_lineage_view(
            args.repo_root.resolve(),
            args.project_slug,
            args.package_id_external,
            args.brief_id_external,
        )
        sys.stdout.write(json.dumps(result, indent=2))
        sys.stdout.write('\n')
        return 0 if result.get('ok') else 1
    if args.command == 'prepare-role-branch':
        result = prepare_role_branch(args)
        sys.stdout.write(json.dumps(result, indent=2))
        sys.stdout.write('\n')
        return 0 if result.get('ok') else 1
    if args.command == 'prepare-role-worktree':
        result = prepare_role_worktree(args)
        sys.stdout.write(json.dumps(result, indent=2))
        sys.stdout.write('\n')
        return 0 if result.get('ok') else 1
    if args.command == 'handoff-to-role-worktree':
        result = handoff_to_role_worktree(args)
        sys.stdout.write(json.dumps(result, indent=2))
        sys.stdout.write('\n')
        return 0 if result.get('ok') else 1
    if args.command == 'inspect-role-worktree':
        result = inspect_role_worktree(args)
        sys.stdout.write(json.dumps(result, indent=2))
        sys.stdout.write('\n')
        return 0 if result.get('ok') else 1
    if args.command == 'worktree-ownership':
        result = worktree_ownership(args)
        sys.stdout.write(json.dumps(result, indent=2))
        sys.stdout.write('\n')
        return 0 if result.get('ok') else 1
    if args.command == 'worktree-stale':
        result = worktree_stale(args)
        sys.stdout.write(json.dumps(result, indent=2))
        sys.stdout.write('\n')
        return 0 if result.get('ok') else 1
    if args.command == 'reset-required':
        result = reset_required_lifecycle(args)
        sys.stdout.write(json.dumps(result, indent=2))
        sys.stdout.write('\n')
        return 0 if result.get('ok') else 1
    if args.command == 'reset-cleanup':
        result = reset_cleanup(args)
        sys.stdout.write(json.dumps(result, indent=2))
        sys.stdout.write('\n')
        return 0 if result.get('ok') else 1
    if args.command == 'superseded-cleanup':
        result = superseded_cleanup(args)
        sys.stdout.write(json.dumps(result, indent=2))
        sys.stdout.write('\n')
        return 0 if result.get('ok') else 1
    if args.command == 'closed-cleanup':
        result = closed_cleanup(args)
        sys.stdout.write(json.dumps(result, indent=2))
        sys.stdout.write('\n')
        return 0 if result.get('ok') else 1
    if args.command == 'role-entry':
        result = role_entry_helper(args)
        sys.stdout.write(json.dumps(result, indent=2))
        sys.stdout.write('\n')
        return 0 if result.get('ok') else 1
    if args.command == 'role-result-assist':
        result = role_result_assist(args)
        sys.stdout.write(json.dumps(result, indent=2))
        sys.stdout.write('\n')
        return 0 if result.get('ok') else 1
    if args.command == 'role-return':
        result = role_return_bridge(args)
        sys.stdout.write(json.dumps(result, indent=2))
        sys.stdout.write('\n')
        return 0 if result.get('ok') else 1
    if args.command == 'emit-decision':
        result = emit_decision(args)
        sys.stdout.write(json.dumps(result, indent=2))
        sys.stdout.write('\n')
        return 0 if result.get('ok') else 1
    if args.command == 'closeout-qa-pass':
        result = closeout_qa_pass(args)
        sys.stdout.write(json.dumps(result, indent=2))
        sys.stdout.write('\n')
        return 0 if result.get('ok') else 1
    if args.command == 'accept-and-merge':
        result = accept_and_merge_qa_pass(args)
        sys.stdout.write(json.dumps(result, indent=2))
        sys.stdout.write('\n')
        return 0 if result.get('ok') else 1
    if args.command == 'automation-preflight':
        result = automation_preflight(args)
        sys.stdout.write(json.dumps(result, indent=2))
        sys.stdout.write('\n')
        return 0 if result.get('ok') else 1
    return 2


if __name__ == '__main__':
    raise SystemExit(main())

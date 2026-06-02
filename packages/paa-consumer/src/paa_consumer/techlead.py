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
from paa_core.config import runtime_queue_name_for_role, runtime_queue_name_for_schema
from paa_core.policies.acceptance import DefaultAcceptancePolicy
from paa_core.policies.deployment_capability import DefaultDeploymentCapabilityPolicy
from paa_core.policies.reset_recovery import DefaultResetRecoveryPolicy
from paa_core.policies.workflow_transition import DefaultWorkflowTransitionPolicy
from paa_core.repositories.execution_package import PostgresExecutionPackageRepository
from paa_core.repositories.runtime_event import PostgresRuntimeEventRepository
from paa_core.repositories.workflow_state import PostgresWorkflowStateRepository
from paa_core.runtime_paths import repo_authority_manifest_path, resolved_repo_runtime_queue_topology
from paa_core.services.runtime_queue_admin import DefaultRuntimeQueueAdminService
from paa_core.services.execution_package_resolution import (
    DefaultExecutionPackageResolutionService,
    ExecutionPackageResolutionRequest,
)
from paa_core.services.techlead_assignment_decision import (
    DefaultTechLeadAssignmentDecisionService,
    TechLeadAssignmentDecisionRequest,
)
from paa_core.services.techlead_acceptance_decision import (
    DefaultTechLeadAcceptanceDecisionService,
    TechLeadAcceptanceDecisionRequest,
)
from paa_core.services.techlead_closeout_decision import (
    DefaultTechLeadCloseoutDecisionService,
    TechLeadCloseoutDecisionRequest,
)
from paa_core.services.techlead_delivery_review_decision import (
    DefaultTechLeadDeliveryReviewDecisionService,
    TechLeadDeliveryReviewDecisionRequest,
)
from paa_core.services.techlead_reset_recovery_decision import (
    DefaultTechLeadResetRecoveryDecisionService,
    TechLeadResetRecoveryDecisionRequest,
)
from paa_core.services.techlead_lineage_decision import (
    DefaultTechLeadLineageDecisionService,
    TechLeadLineageDecisionRequest,
)
from paa_core.services.techlead_worker_review_routing import (
    DefaultTechLeadWorkerReviewRoutingService,
    TechLeadWorkerReviewRoutingRequest,
)
from paa_core.services.workflow_lifecycle import (
    DefaultWorkflowLifecycleService,
    WorkflowLifecycleRequest,
)
from paa_core.services.runtime_worktree import (
    DefaultRuntimeWorktreeService,
    RuntimeWorktreeBranchRequest,
    RuntimeWorktreeCleanupRequest,
    RuntimeWorktreeInspectRequest,
    RuntimeWorktreePrepareRequest,
)
from paa_core.services.runtime_role_bridge import (
    DefaultRuntimeRoleBridgeService,
    RuntimeRoleEntryRequest,
    RuntimeRoleResultAssistRequest,
    RuntimeRoleReturnBridgeRequest,
)
from paa_core.services.runtime_decision_bridge import (
    DefaultRuntimeDecisionBridgeService,
    RuntimeDecisionBridgeRequest,
)
from paa_core.services.runtime_assignment_bridge import (
    DefaultRuntimeAssignmentBridgeService,
    RuntimeAssignmentBridgeRequest,
)
from paa_core.services.runtime_assignment_context import (
    DefaultRuntimeAssignmentContextService,
    RuntimeAssignmentContextRequest,
)
from paa_core.services.runtime_lineage import (
    DefaultRuntimeLineageService,
    RuntimeLineageRequest,
)
from paa_core.services.runtime_status_report import (
    DefaultRuntimeStatusReportService,
    RuntimeStatusReportRequest,
)
from paa_core.services.runtime_closeout import (
    DefaultRuntimeCloseoutService,
    RuntimeQaCloseoutRequest,
)
from paa_core.services.runtime_acceptance import (
    DefaultRuntimeAcceptanceService,
    RuntimeAcceptanceRequest,
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
DEFAULT_PROJECT_SLUG = 'paa-platform'
DEFAULT_AGENT_NAME = 'TechLead Agent'
DEV_ROLE_LABEL = 'Dev'
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
QUEUE_PREVIEW_DEPTH = 10
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


def normalize_runtime_role_label(role_label: str | None) -> str | None:
    if role_label == 'Python Dev':
        return DEV_ROLE_LABEL
    return role_label


def runtime_queue_topology(repo_root: Path = REPO_ROOT):
    return resolved_repo_runtime_queue_topology(repo_root)


def queue_name_by_key(queue_key: str, repo_root: Path = REPO_ROOT) -> str:
    topology = runtime_queue_topology(repo_root)
    queue_name = topology.queue_names.get(queue_key)
    if not queue_name:
        raise RuntimeError(f'Queue topology does not define queue key {queue_key!r}.')
    return queue_name


def techlead_queue_name(repo_root: Path = REPO_ROOT) -> str:
    return queue_name_by_key('techlead', repo_root=repo_root)


def dev_queue_name(repo_root: Path = REPO_ROOT) -> str:
    return queue_name_by_key('dev', repo_root=repo_root)


def qa_queue_name(repo_root: Path = REPO_ROOT) -> str:
    return queue_name_by_key('qa', repo_root=repo_root)


def runtime_queue_names(repo_root: Path = REPO_ROOT) -> list[str]:
    topology = runtime_queue_topology(repo_root)
    return list(topology.queue_names.values())


def role_queue_gate(repo_root: Path = REPO_ROOT) -> dict[str, dict[str, object]]:
    gate = {
        'delivery-architect': {
            'queue_name': techlead_queue_name(repo_root),
            'to_role': 'Delivery Architect',
            'schema_types': {'techlead_assignment_packet'},
        },
        'python-team': {
            'queue_name': dev_queue_name(repo_root),
            'to_role': DEV_ROLE_LABEL,
            'schema_types': {'techlead_assignment_packet', 'architect_cycle_packet'},
        },
        'qa': {
            'queue_name': qa_queue_name(repo_root),
            'to_role': 'QA',
            'schema_types': {'techlead_assignment_packet'},
        },
    }
    for _worker_role in active_team_worker_roles(repo_root=repo_root):
        gate[_worker_role.key] = {
            'queue_name': dev_queue_name(repo_root),
            'to_role': normalize_runtime_role_label(_worker_role.display_name),
            'schema_types': {'techlead_assignment_packet', 'architect_cycle_packet'},
        }
    return gate


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
    for q in runtime_queue_names(repo_root):
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
    return 'billyweisberg/paa-platform'


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
    return DefaultRuntimeStatusReportService(
        load_authority=load_authority,
        queue_state_loader=queue_state,
        automation_state_loader=automation_state,
        mirror_status_loader=mirror_status,
        qa_packet_loader=latest_qa_packet,
        reports_dir_resolver=repo_reports_dir,
        packet_preview_loader=latest_packet_preview,
        newest_packet_preview_loader=newest_packet_preview_across_queues,
        issue_number_from_packet_preview=issue_number_from_packet_preview,
        github_state_loader=github_state,
        github_repo_resolver=github_repo_for_root,
        workflow_deriver=derive_workflow,
        local_decision_loader=latest_techlead_decision_packet,
        terminal_lineage_override=apply_terminal_lineage_override,
        lineage_view_builder=build_lineage_view,
        derive_execution_state=derive_execution_state,
        derive_ci_status=derive_ci_status,
        runtime_queue_names=runtime_queue_names,
        traceability_loader=lambda resolved_project_slug, active_issue_number: load_traceability_section(
            DEFAULT_DB_CONTAINER,
            DEFAULT_DB_NAME,
            DEFAULT_DB_USER,
            resolved_project_slug,
            active_issue_number,
        ),
    ).active_workflow_context(repo_root, project_slug)


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
        gate = role_queue_gate(repo_root)[target_role]
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
    return DefaultRuntimeLineageService(
        load_authority=load_authority,
        load_design_package=load_design_package,
        resolve_issue_number_from_package=resolve_issue_number_from_package,
        resolve_task_summary=resolve_task_summary,
        queue_state_loader=queue_state,
        local_decision_loader=latest_techlead_decision_packet,
        qa_packet_loader=latest_qa_packet,
        reports_dir_resolver=repo_reports_dir,
        packet_preview_loader=latest_packet_preview,
        github_state_loader=github_state,
        github_repo_resolver=github_repo_for_root,
        workflow_deriver=derive_workflow,
        newest_packet=newest_packet,
        target_role_for_branch=target_role_for_branch,
        default_role_worktree_path=default_role_worktree_path,
        git_worktree_for_path=git_worktree_for_path,
        worktree_ownership_record=worktree_ownership_record,
        worktree_staleness_assessment=worktree_staleness_assessment,
    ).derive_lineage_section(
        repo_root=REPO_ROOT,
        current_task=current_task,
        pr=pr,
        queues=queues,
        escalations=escalations,
        reports_dir=reports_dir,
    )


def build_lineage_view(repo_root: Path, project_slug: str, package_id_external: str, brief_id_external: str) -> dict:
    return DefaultRuntimeLineageService(
        load_authority=load_authority,
        load_design_package=load_design_package,
        resolve_issue_number_from_package=resolve_issue_number_from_package,
        resolve_task_summary=resolve_task_summary,
        queue_state_loader=queue_state,
        local_decision_loader=latest_techlead_decision_packet,
        qa_packet_loader=latest_qa_packet,
        reports_dir_resolver=repo_reports_dir,
        packet_preview_loader=latest_packet_preview,
        github_state_loader=github_state,
        github_repo_resolver=github_repo_for_root,
        workflow_deriver=derive_workflow,
        newest_packet=newest_packet,
        target_role_for_branch=target_role_for_branch,
        default_role_worktree_path=default_role_worktree_path,
        git_worktree_for_path=git_worktree_for_path,
        worktree_ownership_record=worktree_ownership_record,
        worktree_staleness_assessment=worktree_staleness_assessment,
    ).build_lineage_view(
        RuntimeLineageRequest(
            repo_root=repo_root,
            project_slug=project_slug,
            package_id_external=package_id_external,
            brief_id_external=brief_id_external,
        )
    )


def action_type_for_role(role):
    mapping = {
        'Delivery Architect': 'route_to_delivery_architect',
        DEV_ROLE_LABEL: 'route_to_dev',
        'Python Dev': 'route_to_dev',
        'QA': 'route_to_qa',
        'Authority Architect': 'route_to_architect',
        'Architect': 'route_to_architect',
        'TechLead': 'route_to_techlead',
    }
    return mapping.get(role, 'route_to_techlead')


def techlead_assignment_role(raw_role):
    mapping = {
        DEV_ROLE_LABEL: 'python-team',
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
        acceptance_decision_result = None
        try:
            acceptance_decision_service = DefaultTechLeadAcceptanceDecisionService()
            acceptance_decision_request = _build_acceptance_decision_request(
                current_task=current_task,
                pr=pr,
                qa_packet=qa_packet,
                source_packet=latest_techlead_packet,
                workflow_stage=stage,
            )
            acceptance_decision_result = acceptance_decision_service.derive_acceptance_decision(
                acceptance_decision_request
            )
        except Exception:
            acceptance_decision_result = None
        details = {
            'message_id': latest_techlead_packet.get('message_id'),
            'schema_type': latest_techlead_packet.get('schema_type'),
            'queue_name': latest_techlead_packet.get('queue_name'),
        }
        if qa_packet:
            details['verification_status'] = qa_packet.get('verification_status')
        if acceptance_decision_result is not None:
            details.update({
                'acceptance_decision_supported': acceptance_decision_result.summary.decision_supported,
                'acceptance_next_decision': acceptance_decision_result.summary.recommended_next_decision,
                'acceptance_allowed': acceptance_decision_result.summary.acceptance_allowed,
                'closeout_allowed': acceptance_decision_result.summary.closeout_allowed,
                'acceptance_blocking_reasons': list(acceptance_decision_result.summary.blocking_reasons),
                'acceptance_reason': acceptance_decision_result.reason,
            })
        escalations.append({
            'event_type': 'qa_packet_waiting_for_techlead',
            'severity': 'high',
            'work_item_ref': {'issue_number': current_task['issue_number'], 'task_id': current_task['task_id']} if current_task else None,
            'summary': (
                acceptance_decision_result.summary.decision_summary
                if acceptance_decision_result is not None and acceptance_decision_result.summary.decision_summary
                else 'TechLead has a waiting QA verification result packet to review.'
            ),
            'details': details,
            'recommended_route': 'TechLead',
            'status': 'open',
        })
        recommended.append({
            'priority': 1,
            'action_type': 'route_to_techlead',
            'reason': (
                acceptance_decision_result.summary.decision_summary
                if acceptance_decision_result is not None and acceptance_decision_result.summary.decision_summary
                else 'A QA verification packet addressed to TechLead is waiting for a merge, rework, or escalation decision.'
            ),
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
        review_routing_result = None
        derived_review_stage = _resolve_worker_review_stage(
            worker_role=worker_role,
            lifecycle_target_stage=lifecycle_target_stage,
        )
        try:
            review_routing_service = DefaultTechLeadWorkerReviewRoutingService()
            review_routing_request = _build_worker_review_routing_request(
                current_task=current_task,
                pr=pr,
                worker_role=worker_role,
                worker_result_packet=latest_techlead_packet,
                lifecycle_target_stage=lifecycle_target_stage,
                workflow_lifecycle_result=lifecycle_result,
            )
            review_routing_result = review_routing_service.derive_worker_review_routing(
                review_routing_request
            )
        except Exception:
            review_routing_result = None
        routed_workflow_stage = (
            getattr(review_routing_result, 'workflow_stage', None)
            if review_routing_result is not None
            else None
        )
        stage = routed_workflow_stage or derived_review_stage
        if review_routing_result is not None and review_routing_result.summary.review_summary:
            summary = review_routing_result.summary.review_summary
        elif worker_role in {DEV_ROLE_LABEL, 'Python Dev'}:
            summary = 'TechLead has a waiting Dev worker result packet to review before QA is assigned.'
        else:
            summary = f'TechLead has a waiting {worker_role} result packet to review.'
        if worker_role in {DEV_ROLE_LABEL, 'Python Dev'}:
            reason = 'A Dev worker result packet addressed to TechLead is waiting for the next routing decision.'
        else:
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
        if review_routing_result is not None:
            details.update({
                'review_routing_decision_supported': review_routing_result.summary.decision_supported,
                'review_routing_next_decision': review_routing_result.summary.recommended_next_decision,
                'review_routing_target_role': review_routing_result.summary.recommended_target_role,
                'review_routing_qa_allowed': review_routing_result.summary.qa_assignment_allowed,
                'review_routing_blocking_reasons': list(review_routing_result.summary.blocking_reasons),
                'review_routing_reason': review_routing_result.reason,
            })
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
            'action_type': action_type_for_role(
                review_routing_result.summary.recommended_target_role
                if review_routing_result is not None and review_routing_result.summary.recommended_target_role
                else 'TechLead'
            ),
            'reason': (
                review_routing_result.summary.review_summary
                if review_routing_result is not None and review_routing_result.summary.review_summary
                else reason
            ),
            'target_role': (
                review_routing_result.summary.recommended_target_role
                if review_routing_result is not None and review_routing_result.summary.recommended_target_role
                else 'TechLead'
            ),
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

    architecture_queue = queues.get(techlead_queue_name()) or queues.get('fractal-core-architecture') or {}
    if architecture_queue.get('messages_ready', 0) > 0:
        stage = 'ready_for_acceptance'
        owner = 'Architect'
        unattended_safe = False
        preview = architecture_queue.get('preview') or []
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
        owner = DEV_ROLE_LABEL
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
                'recommended_route': DEV_ROLE_LABEL,
                'status': 'open',
            })
            recommended.append({
                'priority': 1,
                'action_type': 'route_to_dev_reset_branch',
                'reason': 'A second QA scope escalation after Architect-directed rework is a reliable contamination signal; rebuild the slice on a fresh branch from current main.',
                'target_role': DEV_ROLE_LABEL,
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
                'recommended_route': DEV_ROLE_LABEL,
                'status': 'open',
            })
            recommended.append({
                'priority': 1,
                'action_type': 'route_to_dev',
                'reason': 'Architect has already rejected the current head and asked for the slice to be narrowed before any fresh QA review.',
                'target_role': DEV_ROLE_LABEL,
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
            acceptance_decision_result = None
            try:
                acceptance_decision_service = DefaultTechLeadAcceptanceDecisionService()
                acceptance_decision_request = _build_acceptance_decision_request(
                    current_task=current_task,
                    pr=pr,
                    qa_packet=qa_packet,
                    source_packet=qa_packet,
                    workflow_stage=stage,
                )
                acceptance_decision_result = acceptance_decision_service.derive_acceptance_decision(
                    acceptance_decision_request
                )
            except Exception:
                acceptance_decision_result = None
            escalations.append({
                'event_type': 'qa_pass_pending_acceptance',
                'severity': 'medium',
                'work_item_ref': {'issue_number': current_task['issue_number'], 'task_id': current_task['task_id']},
                'summary': (
                    acceptance_decision_result.summary.decision_summary
                    if acceptance_decision_result is not None and acceptance_decision_result.summary.decision_summary
                    else 'QA passed the active slice, but Architect acceptance is still pending.'
                ),
                'details': {
                    'qa_packet_id': qa_packet.get('message_id'),
                    'path': qa_packet.get('path'),
                    'acceptance_decision_supported': (
                        acceptance_decision_result.summary.decision_supported
                        if acceptance_decision_result is not None
                        else None
                    ),
                    'acceptance_next_decision': (
                        acceptance_decision_result.summary.recommended_next_decision
                        if acceptance_decision_result is not None
                        else None
                    ),
                },
                'recommended_route': 'TechLead',
                'status': 'open',
            })
            recommended.append({
                'priority': 1,
                'action_type': 'route_to_techlead',
                'reason': (
                    acceptance_decision_result.summary.decision_summary
                    if acceptance_decision_result is not None and acceptance_decision_result.summary.decision_summary
                    else 'QA pass is recorded locally, and TechLead should decide whether the slice is ready for merge preparation.'
                ),
                'target_role': 'TechLead',
                'blocking': True,
            })
            return stage, owner, escalations, recommended, unattended_safe

    if queues[dev_queue_name(repo_root)]['messages_ready'] > 0:
        stage = 'architect_authorized'
        owner = DEV_ROLE_LABEL
        recommended.append({
            'priority': 1,
            'action_type': 'route_to_dev',
            'reason': 'Python queue has a waiting Architect packet.',
            'target_role': DEV_ROLE_LABEL,
            'blocking': False,
        })
        return stage, owner, escalations, recommended, unattended_safe

    if issue['state'] == 'OPEN' and pr and pr.get('state') == 'OPEN':
        stage = 'dev_in_progress'
        owner = DEV_ROLE_LABEL
        recommended.append({
            'priority': 2,
            'action_type': 'monitor_dev',
            'reason': f'Issue #{issue["number"]} has an open PR but no waiting queue handoff.',
            'target_role': DEV_ROLE_LABEL,
            'blocking': False,
        })
        return stage, owner, escalations, recommended, unattended_safe

    if current_task:
        stage = 'dev_in_progress'
        owner = DEV_ROLE_LABEL

    return stage, owner, escalations, recommended, unattended_safe


def build_report(repo_root: Path = REPO_ROOT, project_slug: str = DEFAULT_PROJECT_SLUG):
    return DefaultRuntimeStatusReportService(
        load_authority=load_authority,
        queue_state_loader=queue_state,
        automation_state_loader=automation_state,
        mirror_status_loader=mirror_status,
        qa_packet_loader=latest_qa_packet,
        reports_dir_resolver=repo_reports_dir,
        packet_preview_loader=latest_packet_preview,
        newest_packet_preview_loader=newest_packet_preview_across_queues,
        issue_number_from_packet_preview=issue_number_from_packet_preview,
        github_state_loader=github_state,
        github_repo_resolver=github_repo_for_root,
        workflow_deriver=derive_workflow,
        local_decision_loader=latest_techlead_decision_packet,
        terminal_lineage_override=apply_terminal_lineage_override,
        lineage_view_builder=build_lineage_view,
        derive_execution_state=derive_execution_state,
        derive_ci_status=derive_ci_status,
        runtime_queue_names=runtime_queue_names,
        traceability_loader=lambda resolved_project_slug, active_issue_number: load_traceability_section(
            DEFAULT_DB_CONTAINER,
            DEFAULT_DB_NAME,
            DEFAULT_DB_USER,
            resolved_project_slug,
            active_issue_number,
        ),
    ).build_report(
        RuntimeStatusReportRequest(
            repo_root=repo_root,
            project_slug=project_slug,
            captured_by_agent_name=DEFAULT_AGENT_NAME,
        )
    )


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
      WHERE a.name = {sql_literal(DEFAULT_AGENT_NAME)}
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


def _build_assignment_decision_request(
    *,
    issue_number: int,
    issue: dict,
    pr: dict | None,
    workflow_stage: str,
    source_packet: dict | None,
    explicit_target_role: str | None,
    project_slug: str,
    recommended_actions: list[dict] | tuple[dict, ...] | None,
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
        recommended_actions=tuple(recommended_actions or ()),
    )


def _assignment_result_to_context(
    *,
    result,
    issue: dict,
    pr: dict | None,
) -> dict:
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
        context.update(
            {
                'reason': result.reason,
                'details': result.details,
            }
        )
    return context


def _build_worker_review_routing_request(
    *,
    current_task: dict | None,
    pr: dict | None,
    worker_role: str,
    worker_result_packet: dict,
    lifecycle_target_stage: str | None,
    workflow_lifecycle_result,
) -> TechLeadWorkerReviewRoutingRequest:
    payload = worker_result_packet.get('payload') or {}
    issue_number = (current_task or {}).get('issue_number') or 0
    return TechLeadWorkerReviewRoutingRequest(
        project_slug=DEFAULT_PROJECT_SLUG,
        issue_number=issue_number,
        pr_number=pr.get('number') if pr else None,
        workflow_stage=_resolve_worker_review_stage(
            worker_role=worker_role,
            lifecycle_target_stage=lifecycle_target_stage,
        ),
        worker_role=worker_role,
        worker_result_type=payload.get('result_type') or '',
        source_packet_schema_type=worker_result_packet.get('schema_type'),
        source_packet_message_id=worker_result_packet.get('message_id'),
        workflow_lifecycle_result=workflow_lifecycle_result,
        metadata={
            'source_queue_name': worker_result_packet.get('queue_name'),
            'source_worker_family': payload.get('worker_family'),
        },
    )


def _build_acceptance_decision_request(
    *,
    current_task: dict | None,
    pr: dict | None,
    qa_packet: dict | None,
    source_packet: dict,
    workflow_stage: str,
) -> TechLeadAcceptanceDecisionRequest:
    payload = source_packet.get('payload') or {}
    issue_number = (current_task or {}).get('issue_number') or 0
    recommended_action = (qa_packet or {}).get('recommended_action') or payload.get('recommended_action') or {}
    merge_recommendation = recommended_action.get('merge_recommendation')
    execution_mode = 'proof_only' if merge_recommendation == 'do_not_merge_proof_slice' else 'live_delivery'
    merge_ready = None
    if execution_mode == 'live_delivery' and pr is not None:
        merge_ready = True
    return TechLeadAcceptanceDecisionRequest(
        project_slug=DEFAULT_PROJECT_SLUG,
        issue_number=issue_number,
        pr_number=pr.get('number') if pr else None,
        workflow_stage=workflow_stage,
        qa_result_type=(qa_packet or {}).get('verification_status') or payload.get('verification_status') or '',
        source_packet_schema_type=source_packet.get('schema_type'),
        source_packet_message_id=source_packet.get('message_id'),
        merge_state={
            'execution_mode': execution_mode,
            'merge_ready': merge_ready,
            'merge_recommendation': merge_recommendation,
        },
        metadata={
            'execution_mode': execution_mode,
            'source_queue_name': source_packet.get('queue_name'),
            'qa_packet_path': (qa_packet or {}).get('path'),
        },
    )


def _build_delivery_review_decision_request(
    *,
    current_task: dict | None,
    issue: dict | None,
    pr: dict | None,
    source_packet: dict,
    repo_root: Path,
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
    normalized_target_role = handoff_runtime.normalize_role_name(recommended_target_role)
    team_worker = team_worker_role_for_label(normalized_target_role, repo_root=repo_root)
    branch_name = (
        (pr or {}).get('headRefName')
        or source_packet.get('github_context', {}).get('branch')
        or (payload.get('branch') or {}).get('name')
        or f'issue-{issue_number}'
    )
    source_assignment = payload.get('source_assignment_ref') or {}
    return TechLeadDeliveryReviewDecisionRequest(
        project_slug=DEFAULT_PROJECT_SLUG,
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


def _delivery_review_result_to_context(
    *,
    result,
    issue: dict | None,
    pr: dict | None,
    recommended_actions: list[dict] | None,
    unattended_safe: bool,
) -> dict:
    if not result.ok:
        return {
            'ok': False,
            'workflow_stage': result.workflow_stage,
            'reason': result.reason,
            'details': result.details,
            'recommended_actions': recommended_actions,
            'unattended_safe': unattended_safe,
        }
    return {
        'ok': True,
        'workflow_stage': result.workflow_stage,
        'issue_number': result.issue_number,
        'issue_url': result.issue_url or ((issue or {}).get('url')),
        'pr_number': result.pr_number,
        'pr_url': result.pr_url or ((pr or {}).get('url')),
        'branch': result.branch_name or ((pr or {}).get('headRefName')) or f'issue-{result.issue_number}',
        'target_role': result.summary.recommended_target_role,
        'target_role_cli': result.resolved_team_worker_key,
        'assignment_type': 'implement_authorized_slice',
        'allowed_result_types': [
            'implemented_ready_for_qa',
            'blocked',
            'needs_clarification',
        ],
        'assignment_summary': result.summary.delivery_review_summary,
        'source_packet_message_id': result.source_packet_message_id,
        'source_packet_path': result.source_packet_path,
        'source_packet_queue': (result.metadata or {}).get('source_queue_name'),
        'source_packet_schema_type': result.source_packet_schema_type,
        'issue': issue,
        'pr': pr,
        'recommended_actions': recommended_actions,
        'unattended_safe': unattended_safe,
        'decision_reason': result.reason,
    }


def _build_reset_recovery_decision_request(
    *,
    issue_number: int,
    issue_url: str | None,
    pr_full: dict | None,
    workflow_stage: str,
    lineage_state: str,
    reset_escalation: dict | None,
    source_packet_path: str | None,
    branch_name: str,
    canonical_branch: str,
    role_branch: str | None,
) -> TechLeadResetRecoveryDecisionRequest:
    reset_escalation_type = (reset_escalation or {}).get('event_type')
    return TechLeadResetRecoveryDecisionRequest(
        project_slug=DEFAULT_PROJECT_SLUG,
        issue_number=issue_number,
        issue_url=issue_url,
        pr_number=pr_full.get('number') if pr_full else None,
        pr_url=pr_full.get('url') if pr_full else None,
        workflow_stage=workflow_stage,
        lineage_state=lineage_state,
        reset_escalation_type=reset_escalation_type,
        reset_escalation_summary=(reset_escalation or {}).get('summary'),
        reset_escalation_details=(reset_escalation or {}).get('details'),
        source_packet_schema_type='qa_verification_packet' if source_packet_path else None,
        source_packet_message_id=(reset_escalation or {}).get('details', {}).get('qa_packet_id'),
        source_packet_path=source_packet_path,
        branch_name=branch_name,
        metadata={
            'canonical_branch': canonical_branch,
            'role_branch': role_branch,
        },
    )


def _reset_recovery_result_to_context(
    *,
    result,
    issue_number: int,
    canonical_branch: str,
    branch_name: str,
    role_branch: str | None,
    recommended_actions: list[dict] | None,
    unattended_safe: bool,
    reset_reason: str | None,
    superseded_branch: str | None,
    worktree_hint: str,
) -> dict:
    if not result.ok:
        return {
            'ok': False,
            'workflow_stage': result.workflow_stage,
            'reason': result.reason,
            'details': result.details,
        }
    return {
        'ok': True,
        'workflow_stage': result.workflow_stage,
        'issue_number': result.issue_number,
        'issue_url': result.issue_url,
        'pr_number': result.pr_number,
        'pr_url': result.pr_url,
        'branch': result.branch_name or branch_name,
        'to_role': 'techlead',
        'target_role_cli': 'python-team',
        'decision_type': result.summary.recommended_next_decision,
        'decision_rationale': reset_reason or result.summary.reset_recovery_summary,
        'next_assignment_type': 'implement_authorized_slice',
        'work_item_status_update_intent': 'blocked',
        'canonical_branch': canonical_branch,
        'role_branch': role_branch,
        'branch_owner_role': 'TechLead',
        'lineage_state': 'reset_required',
        'lineage_action': 'reset',
        'source_branch': canonical_branch,
        'superseded_branch': superseded_branch,
        'worktree_hint': worktree_hint,
        'reset_reason': reset_reason or result.summary.reset_recovery_summary,
        'source_packet_path': result.source_packet_path,
        'recommended_actions': recommended_actions,
        'unattended_safe': unattended_safe,
    }




def _build_lineage_decision_request(
    *,
    issue_number: int,
    issue_url: str | None,
    pr_full: dict | None,
    workflow_stage: str,
    lineage_state: str,
    superseded_escalation: dict | None,
    source_packet_path: str | None,
    branch_name: str,
    superseded_branch: str | None,
    canonical_branch: str,
    role_branch: str | None,
) -> TechLeadLineageDecisionRequest:
    superseded_escalation_type = (superseded_escalation or {}).get('event_type')
    return TechLeadLineageDecisionRequest(
        project_slug=DEFAULT_PROJECT_SLUG,
        issue_number=issue_number,
        issue_url=issue_url,
        pr_number=pr_full.get('number') if pr_full else None,
        pr_url=pr_full.get('url') if pr_full else None,
        workflow_stage=workflow_stage,
        lineage_state=lineage_state,
        superseded_escalation_type=superseded_escalation_type,
        superseded_escalation_summary=(superseded_escalation or {}).get('summary'),
        superseded_escalation_details=(superseded_escalation or {}).get('details'),
        source_packet_schema_type='qa_verification_packet' if source_packet_path else None,
        source_packet_message_id=(superseded_escalation or {}).get('details', {}).get('superseded_qa_packet_id'),
        source_packet_path=source_packet_path,
        branch_name=branch_name,
        superseded_branch=superseded_branch,
        metadata={
            'canonical_branch': canonical_branch,
            'role_branch': role_branch,
        },
    )


def _lineage_decision_result_to_context(
    *,
    result,
    canonical_branch: str,
    branch_name: str,
    role_branch: str | None,
    recommended_actions: list[dict] | None,
    unattended_safe: bool,
    worktree_hint: str | None,
) -> dict:
    if not result.ok:
        return {
            'ok': False,
            'workflow_stage': result.workflow_stage,
            'reason': result.reason,
            'details': result.details,
        }
    return {
        'ok': True,
        'workflow_stage': result.workflow_stage,
        'issue_number': result.issue_number,
        'issue_url': result.issue_url,
        'pr_number': result.pr_number,
        'pr_url': result.pr_url,
        'branch': result.branch_name or branch_name,
        'to_role': 'techlead',
        'target_role_cli': None,
        'decision_type': result.summary.recommended_next_decision,
        'decision_rationale': result.summary.lineage_decision_summary,
        'next_assignment_type': None,
        'work_item_status_update_intent': 'superseded',
        'canonical_branch': canonical_branch,
        'role_branch': role_branch,
        'branch_owner_role': 'TechLead',
        'lineage_state': 'superseded',
        'lineage_action': 'superseded',
        'source_branch': canonical_branch,
        'superseded_branch': result.superseded_branch,
        'worktree_hint': worktree_hint,
        'reset_reason': None,
        'source_packet_path': result.source_packet_path,
        'recommended_actions': recommended_actions,
        'unattended_safe': unattended_safe,
    }



def _build_closeout_decision_request(
    *,
    issue_number: int,
    issue_url: str | None,
    pr_number: int | None,
    pr_url: str | None,
    workflow_stage: str,
    decision_type: str,
    proof_only_mode: bool,
    source_packet_path: str | None,
    branch_name: str,
    canonical_branch: str,
) -> TechLeadCloseoutDecisionRequest:
    return TechLeadCloseoutDecisionRequest(
        project_slug=DEFAULT_PROJECT_SLUG,
        issue_number=issue_number,
        issue_url=issue_url,
        pr_number=pr_number,
        pr_url=pr_url,
        workflow_stage=workflow_stage,
        decision_type=decision_type,
        proof_only_mode=proof_only_mode,
        source_packet_schema_type='qa_verification_packet' if source_packet_path else None,
        source_packet_message_id=None,
        source_packet_path=source_packet_path,
        branch_name=branch_name,
        canonical_branch=canonical_branch,
    )


def _closeout_decision_result_to_context(
    *,
    result,
    branch_name: str,
    canonical_branch: str,
    role_branch: str | None,
    recommended_actions: list[dict] | None,
    unattended_safe: bool,
    decision_type: str,
    superseded_branch: str | None,
    worktree_hint: str | None,
) -> dict:
    if not result.ok:
        return {
            'ok': False,
            'workflow_stage': result.workflow_stage,
            'reason': result.reason,
            'details': result.details,
        }
    is_proof_only = decision_type == 'proof_only_closed'
    return {
        'ok': True,
        'workflow_stage': result.workflow_stage,
        'issue_number': result.issue_number,
        'issue_url': result.issue_url,
        'pr_number': result.pr_number,
        'pr_url': result.pr_url,
        'branch': result.branch_name or branch_name,
        'to_role': 'techlead',
        'target_role_cli': None,
        'decision_type': result.summary.recommended_next_decision,
        'decision_rationale': result.summary.closeout_decision_summary,
        'next_assignment_type': None,
        'work_item_status_update_intent': 'proof_only_closed' if is_proof_only else 'accepted',
        'canonical_branch': canonical_branch,
        'role_branch': role_branch,
        'branch_owner_role': 'TechLead',
        'lineage_state': 'closed',
        'lineage_action': 'proof_only_closed' if is_proof_only else 'closed',
        'source_branch': canonical_branch,
        'superseded_branch': superseded_branch,
        'worktree_hint': worktree_hint,
        'reset_reason': None,
        'source_packet_path': result.source_packet_path,
        'recommended_actions': recommended_actions,
        'unattended_safe': unattended_safe,
    }

def _resolve_worker_review_stage(
    *,
    worker_role: str,
    lifecycle_target_stage: str | None,
) -> str:
    if worker_role in {DEV_ROLE_LABEL, 'Python Dev'}:
        return 'techlead_dev_review_pending'
    return lifecycle_target_stage or 'techlead_worker_review_pending'


def derive_next_assignment_context(args) -> dict:
    return DefaultRuntimeAssignmentContextService(
        load_authority=load_authority,
        github_repo_resolver=github_repo_for_root,
        load_design_package=load_design_package,
        resolve_issue_number_from_package=resolve_issue_number_from_package,
        resolve_task_summary=resolve_task_summary,
        queue_state_loader=queue_state,
        qa_packet_loader=latest_qa_packet,
        reports_dir_resolver=repo_reports_dir,
        packet_preview_loader=latest_packet_preview,
        github_state_loader=github_state,
        workflow_deriver=derive_workflow,
        team_worker_role_for_cli=team_worker_role_for_cli,
        team_worker_role_for_label=team_worker_role_for_label,
        normalize_role_name=handoff_runtime.normalize_role_name,
        assignment_decision_service=DefaultTechLeadAssignmentDecisionService(),
        delivery_review_decision_service=DefaultTechLeadDeliveryReviewDecisionService(),
    ).derive_next_assignment_context(
        RuntimeAssignmentContextRequest(
            repo_root=args.repo_root.resolve(),
            project_slug=args.project_slug,
            package_id_external=args.package_id_external,
            target_role=getattr(args, 'target_role', None),
        )
    )


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
    result = DefaultRuntimeAssignmentBridgeService().emit_next_assignment(
        RuntimeAssignmentBridgeRequest(
            repo_root=repo_root,
            project_slug=args.project_slug,
            package_id_external=args.package_id_external,
            brief_id_external=args.brief_id_external,
            github_repo=github_repo_for_root(repo_root),
            issue_number=context['issue_number'],
            issue_url=context['issue_url'],
            pr_number=context['pr_number'],
            pr_url=context['pr_url'],
            branch=context['branch'],
            workflow_stage=context['workflow_stage'],
            target_role=context['target_role'],
            target_role_cli=context['target_role_cli'],
            assignment_type=context['assignment_type'],
            assignment_summary=context['assignment_summary'],
            allowed_result_types=tuple(context['allowed_result_types']),
            source_packet_message_id=context.get('source_packet_message_id'),
            source_packet_path=context.get('source_packet_path'),
            source_packet_queue=context.get('source_packet_queue'),
            source_packet_schema_type=context.get('source_packet_schema_type'),
            output_path=args.output,
            review_output_path=args.review_output,
            send=bool(args.send),
        )
    )
    result['workflow_transition'] = (
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
    )
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
        reset_recovery_service = DefaultTechLeadResetRecoveryDecisionService()
        reset_recovery_request = _build_reset_recovery_decision_request(
            issue_number=issue_number,
            issue_url=issue_url,
            pr_full=pr_full,
            workflow_stage=workflow_stage,
            lineage_state='reset_required',
            reset_escalation=reset_escalation,
            source_packet_path=source_packet_path,
            branch_name=branch_name,
            canonical_branch=canonical_branch,
            role_branch=role_branch,
        )
        reset_recovery_result = reset_recovery_service.derive_reset_recovery_decision(
            reset_recovery_request
        )
        return _reset_recovery_result_to_context(
            result=reset_recovery_result,
            issue_number=issue_number,
            canonical_branch=canonical_branch,
            branch_name=branch_name,
            role_branch=role_branch,
            recommended_actions=recommended,
            unattended_safe=unattended_safe,
            reset_reason=reset_reason,
            superseded_branch=superseded_branch,
            worktree_hint=args.worktree_hint or f'issue-{issue_number}-dev',
        )

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
        lineage_decision_service = DefaultTechLeadLineageDecisionService()
        lineage_decision_request = _build_lineage_decision_request(
            issue_number=issue_number,
            issue_url=issue_url,
            pr_full=pr_full,
            workflow_stage=workflow_stage,
            lineage_state='superseded',
            superseded_escalation=superseded_escalation,
            source_packet_path=source_packet_path,
            branch_name=branch_name,
            superseded_branch=superseded_branch,
            canonical_branch=canonical_branch,
            role_branch=role_branch,
        )
        lineage_decision_result = lineage_decision_service.derive_lineage_decision(
            lineage_decision_request
        )
        return _lineage_decision_result_to_context(
            result=lineage_decision_result,
            canonical_branch=canonical_branch,
            branch_name=branch_name,
            role_branch=role_branch,
            recommended_actions=recommended,
            unattended_safe=unattended_safe,
            worktree_hint=args.worktree_hint,
        )

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
        closeout_decision_service = DefaultTechLeadCloseoutDecisionService()
        closeout_decision_request = _build_closeout_decision_request(
            issue_number=issue_number,
            issue_url=issue_url,
            pr_number=pr_number,
            pr_url=pr_url,
            workflow_stage=workflow_stage,
            decision_type=args.decision_type,
            proof_only_mode=is_proof_only,
            source_packet_path=source_packet_path,
            branch_name=branch_name,
            canonical_branch=canonical_branch,
        )
        closeout_decision_result = closeout_decision_service.derive_closeout_decision(
            closeout_decision_request
        )
        return _closeout_decision_result_to_context(
            result=closeout_decision_result,
            branch_name=branch_name,
            canonical_branch=canonical_branch,
            role_branch=role_branch,
            recommended_actions=recommended,
            unattended_safe=unattended_safe,
            decision_type=args.decision_type,
            superseded_branch=args.superseded_branch,
            worktree_hint=args.worktree_hint,
        )

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
    return DefaultRuntimeDecisionBridgeService().emit_decision(
        RuntimeDecisionBridgeRequest(
            repo_root=repo_root,
            project_slug=args.project_slug,
            package_id_external=args.package_id_external,
            brief_id_external=args.brief_id_external,
            issue_number=context['issue_number'],
            issue_url=context['issue_url'],
            pr_number=context['pr_number'],
            pr_url=context['pr_url'],
            branch=context['branch'],
            canonical_branch=context['canonical_branch'],
            to_role=context['to_role'],
            decision_type=context['decision_type'],
            decision_rationale=context['decision_rationale'],
            work_item_status_update_intent=context['work_item_status_update_intent'],
            source_packet_path=context['source_packet_path'],
            branch_owner_role=context['branch_owner_role'],
            lineage_state=context['lineage_state'],
            lineage_action=context['lineage_action'],
            workflow_stage=context.get('workflow_stage'),
            target_role_cli=context.get('target_role_cli'),
            next_assignment_type=context.get('next_assignment_type'),
            role_branch=context.get('role_branch'),
            superseded_branch=context.get('superseded_branch'),
            worktree_hint=context.get('worktree_hint'),
            reset_reason=context.get('reset_reason'),
            output_path=args.output,
            review_output_path=args.review_output,
            send=bool(args.send),
        )
    )


def closeout_qa_pass(args):
    repo_root = args.repo_root.resolve()
    package = load_design_package(args.project_slug, args.package_id_external)
    execution_mode = package_execution_mode(package)
    qa_packet = latest_qa_packet(args.issue_number, repo_reports_dir(repo_root))
    fallback_packet = latest_packet_preview(queue_state(repo_root), args.issue_number)
    issue_full, pr_full = github_state(
        args.issue_number,
        github_repo_for_root(repo_root),
        fallback_pr_number=qa_packet.get('pr_number') if qa_packet else None,
        fallback_task={'issue_number': args.issue_number, 'title': f'Issue #{args.issue_number}'},
        fallback_packet=fallback_packet,
    )

    def _persist_acceptance(project_slug, issue_number, qa_packet_arg, pr_full_arg, decision, decision_notes, metadata_extra):
        return persist_techlead_acceptance_event(
            getattr(args, 'db_container', DEFAULT_DB_CONTAINER),
            getattr(args, 'db_name', DEFAULT_DB_NAME),
            getattr(args, 'db_user', DEFAULT_DB_USER),
            project_slug,
            issue_number,
            qa_packet_arg,
            pr_full_arg,
            decision=decision,
            decision_notes=decision_notes,
            metadata_extra=metadata_extra,
        )

    def _emit_decision(payload):
        return emit_decision(SimpleNamespace(**payload))

    return DefaultRuntimeCloseoutService(
        queue_admin_service=DefaultRuntimeQueueAdminService(),
        acceptance_event_persister=_persist_acceptance,
        decision_emitter=_emit_decision,
    ).closeout_qa_pass(
        RuntimeQaCloseoutRequest(
            repo_root=repo_root,
            issue_number=args.issue_number,
            execution_mode=execution_mode,
            qa_packet=qa_packet,
            issue_full=issue_full,
            pr_full=pr_full,
            package_id_external=args.package_id_external,
            brief_id_external=args.brief_id_external,
            project_slug=args.project_slug,
            architecture_queue=techlead_queue_name(repo_root),
            send_decision=bool(args.send_decision),
            ack_qa_packet=bool(args.ack_qa_packet),
            claimed_by=args.claimed_by,
            canonical_branch=args.canonical_branch,
            role_branch=args.role_branch,
            worktree_hint=args.worktree_hint,
            output_path=args.output,
            review_output_path=args.review_output,
        )
    )


def accept_and_merge_qa_pass(args):
    repo_root = args.repo_root.resolve()

    def _merge_state_loader(pr_number: int, github_repo: str):
        return run_json([
            'gh', 'pr', 'view', str(pr_number),
            '--repo', github_repo,
            '--json', 'number,state,isDraft,mergeStateStatus,mergedAt,statusCheckRollup,url',
        ])

    def _merge_pr(pr_number: int, github_repo: str, merge_method: str):
        merge_cmd = [
            'gh', 'pr', 'merge', str(pr_number),
            '--repo', github_repo,
            f'--{merge_method}',
        ]
        merge_code, merge_stdout, merge_error = run_text_with_errors(merge_cmd)
        return {
            'ok': merge_code == 0,
            'stdout': merge_stdout.strip() if merge_stdout else '',
            'stderr': merge_error if merge_code != 0 else '',
        }

    def _close_issue(issue_number: int, github_repo: str, comment: str):
        close_cmd = [
            'gh', 'issue', 'close', str(issue_number),
            '--repo', github_repo,
            '--reason', 'completed',
            '--comment', comment,
        ]
        close_code, close_stdout, close_error = run_text_with_errors(close_cmd)
        return {
            'ok': close_code == 0,
            'stdout': close_stdout.strip() if close_stdout else '',
            'stderr': close_error if close_code != 0 else '',
        }

    def _closeout_runner(payload):
        return closeout_qa_pass(SimpleNamespace(**payload))

    def _fallback_packet_loader(resolved_repo_root: Path, issue_number: int):
        return latest_packet_preview(queue_state(resolved_repo_root), issue_number)

    return DefaultRuntimeAcceptanceService(
        github_state_loader=github_state,
        merge_state_loader=_merge_state_loader,
        merge_pr=_merge_pr,
        close_issue=_close_issue,
        closeout_runner=_closeout_runner,
        fallback_packet_loader=_fallback_packet_loader,
        github_repo_resolver=github_repo_for_root,
        ci_status_deriver=derive_ci_status,
        qa_packet_loader=latest_qa_packet,
        reports_dir_resolver=repo_reports_dir,
    ).accept_and_merge_qa_pass(
        RuntimeAcceptanceRequest(
            repo_root=repo_root,
            issue_number=args.issue_number,
            package_id_external=args.package_id_external,
            brief_id_external=args.brief_id_external,
            project_slug=args.project_slug,
            merge_method=args.merge_method,
            issue_close_comment=args.issue_close_comment,
            claimed_by=args.claimed_by,
            canonical_branch=args.canonical_branch,
            role_branch=args.role_branch,
            worktree_hint=args.worktree_hint,
            output_path=args.output,
            review_output_path=args.review_output,
        )
    )


def prepare_role_branch(args):
    repo_root = args.repo_root.resolve()
    lineage_view = build_lineage_view(
        repo_root,
        args.project_slug,
        args.package_id_external,
        args.brief_id_external,
    )
    lineage_view.setdefault('package_id_external', args.package_id_external)
    lineage_view.setdefault('brief_id_external', args.brief_id_external)
    return DefaultRuntimeWorktreeService().prepare_role_branch(
        RuntimeWorktreeBranchRequest(
            repo_root=repo_root,
            target_role=args.target_role,
            lineage_view=lineage_view,
            action=args.action,
            canonical_branch=args.canonical_branch,
            role_branch=args.role_branch,
        )
    )


def prepare_role_worktree(args):
    repo_root = args.repo_root.resolve()
    lineage_view = build_lineage_view(
        repo_root,
        args.project_slug,
        args.package_id_external,
        args.brief_id_external,
    )
    lineage_view.setdefault('package_id_external', args.package_id_external)
    lineage_view.setdefault('brief_id_external', args.brief_id_external)
    return DefaultRuntimeWorktreeService().prepare_role_worktree(
        RuntimeWorktreePrepareRequest(
            repo_root=repo_root,
            target_role=args.target_role,
            lineage_view=lineage_view,
            branch_action=args.branch_action,
            canonical_branch=args.canonical_branch,
            role_branch=args.role_branch,
            worktree_path=args.worktree_path,
        )
    )


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
    lineage_view.setdefault('package_id_external', args.package_id_external)
    lineage_view.setdefault('brief_id_external', args.brief_id_external)
    return DefaultRuntimeWorktreeService().inspect_role_worktree(
        RuntimeWorktreeInspectRequest(
            repo_root=repo_root,
            target_role=args.target_role,
            lineage_view=lineage_view,
            role_branch=args.role_branch,
            worktree_path=args.worktree_path,
            assignment_path=args.assignment_path,
            review_output_path=args.review_output,
        )
    )


def worktree_ownership(args):
    repo_root = args.repo_root.resolve()
    lineage_view = build_lineage_view(
        repo_root,
        args.project_slug,
        args.package_id_external,
        args.brief_id_external,
    )
    lineage_view.setdefault('package_id_external', args.package_id_external)
    lineage_view.setdefault('brief_id_external', args.brief_id_external)
    return DefaultRuntimeWorktreeService().worktree_ownership_view(
        repo_root=repo_root,
        target_role=args.target_role,
        lineage_view=lineage_view,
        role_branch=args.role_branch,
        worktree_path=args.worktree_path,
    )


def worktree_stale(args):
    repo_root = args.repo_root.resolve()
    lineage_view = build_lineage_view(
        repo_root,
        args.project_slug,
        args.package_id_external,
        args.brief_id_external,
    )
    lineage_view.setdefault('package_id_external', args.package_id_external)
    lineage_view.setdefault('brief_id_external', args.brief_id_external)
    return DefaultRuntimeWorktreeService().worktree_stale_view(
        repo_root=repo_root,
        target_role=args.target_role,
        lineage_view=lineage_view,
        role_branch=args.role_branch,
        worktree_path=args.worktree_path,
    )


def reset_required_lifecycle(args):
    repo_root = args.repo_root.resolve()
    target_role = args.target_role or 'python-team'

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
    stale_view = worktree_stale(ownership_args)

    decision_result = emit_decision(
        SimpleNamespace(
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
    )

    return DefaultRuntimeWorktreeService().reset_required_lifecycle(
        RuntimeWorktreeCleanupRequest(
            repo_root=repo_root,
            target_role=target_role,
            lineage_view=ownership_view.get('lineage_view') or {},
            ownership_view=ownership_view,
            stale_view=stale_view,
            decision_result=decision_result,
            superseded_branch=args.superseded_branch,
        )
    )


def reset_cleanup(args):
    repo_root = args.repo_root.resolve()
    target_role = args.target_role or 'python-team'

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
    stale_view = worktree_stale(ownership_args)

    decision_result = emit_decision(
        SimpleNamespace(
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
    )

    return DefaultRuntimeWorktreeService().reset_cleanup(
        RuntimeWorktreeCleanupRequest(
            repo_root=repo_root,
            target_role=target_role,
            lineage_view=ownership_view.get('lineage_view') or {},
            ownership_view=ownership_view,
            stale_view=stale_view,
            decision_result=decision_result,
            superseded_branch=args.superseded_branch,
        )
    )


def superseded_cleanup(args):
    repo_root = args.repo_root.resolve()
    target_role = args.target_role or 'python-team'
    lineage_view = build_lineage_view(
        repo_root,
        args.project_slug,
        args.package_id_external,
        args.brief_id_external,
    )
    lineage = lineage_view.get('lineage') or {}

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
    stale_view = worktree_stale(ownership_args)

    decision_result = emit_decision(
        SimpleNamespace(
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
    )

    return DefaultRuntimeWorktreeService().superseded_cleanup(
        RuntimeWorktreeCleanupRequest(
            repo_root=repo_root,
            target_role=target_role,
            lineage_view=lineage_view,
            ownership_view=ownership_view,
            stale_view=stale_view,
            decision_result=decision_result,
            superseded_branch=args.superseded_branch or lineage.get('superseded_branch'),
        )
    )


def closed_cleanup(args):
    repo_root = args.repo_root.resolve()
    target_role = args.target_role or 'python-team'
    lineage_view = build_lineage_view(
        repo_root,
        args.project_slug,
        args.package_id_external,
        args.brief_id_external,
    )

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
    stale_view = worktree_stale(ownership_args)

    decision_result = emit_decision(
        SimpleNamespace(
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
    )

    return DefaultRuntimeWorktreeService().closed_cleanup(
        RuntimeWorktreeCleanupRequest(
            repo_root=repo_root,
            target_role=target_role,
            lineage_view=lineage_view,
            ownership_view=ownership_view,
            stale_view=stale_view,
            decision_result=decision_result,
            superseded_branch=args.superseded_branch,
        )
    )


def role_entry_helper(args):
    repo_root = args.repo_root.resolve()
    lineage_view = build_lineage_view(
        repo_root,
        args.project_slug,
        args.package_id_external,
        args.brief_id_external,
    )
    lineage_view.setdefault('package_id_external', args.package_id_external)
    lineage_view.setdefault('brief_id_external', args.brief_id_external)
    return DefaultRuntimeRoleBridgeService().role_entry_helper(
        RuntimeRoleEntryRequest(
            repo_root=repo_root,
            package_id_external=args.package_id_external,
            brief_id_external=args.brief_id_external,
            project_slug=args.project_slug,
            target_role=args.target_role,
            lineage_view=lineage_view,
            role_branch=args.role_branch,
            worktree_path=args.worktree_path,
            assignment_path=args.assignment_path,
            review_output_path=args.review_output,
        )
    )


def role_result_assist(args):
    repo_root = args.repo_root.resolve()
    lineage_view = build_lineage_view(
        repo_root,
        args.project_slug,
        args.package_id_external,
        args.brief_id_external,
    )
    lineage_view.setdefault('package_id_external', args.package_id_external)
    lineage_view.setdefault('brief_id_external', args.brief_id_external)
    return DefaultRuntimeRoleBridgeService().role_result_assist(
        RuntimeRoleResultAssistRequest(
            repo_root=repo_root,
            package_id_external=args.package_id_external,
            brief_id_external=args.brief_id_external,
            project_slug=args.project_slug,
            target_role=args.target_role,
            lineage_view=lineage_view,
            role_branch=args.role_branch,
            worktree_path=args.worktree_path,
            assignment_path=args.assignment_path,
            review_output_path=args.review_output,
            result_input_path=getattr(args, 'result_input_path', None),
        )
    )


def role_return_bridge(args):
    repo_root = args.repo_root.resolve()
    lineage_view = build_lineage_view(
        repo_root,
        args.project_slug,
        args.package_id_external,
        args.brief_id_external,
    )
    lineage_view.setdefault('package_id_external', args.package_id_external)
    lineage_view.setdefault('brief_id_external', args.brief_id_external)
    return DefaultRuntimeRoleBridgeService().role_return_bridge(
        RuntimeRoleReturnBridgeRequest(
            repo_root=repo_root,
            package_id_external=args.package_id_external,
            brief_id_external=args.brief_id_external,
            project_slug=args.project_slug,
            target_role=args.target_role,
            lineage_view=lineage_view,
            role_branch=args.role_branch,
            worktree_path=args.worktree_path,
            assignment_path=args.assignment_path,
            assignment_review_output_path=args.assignment_review_output,
            result_input_path=args.result_input_path,
            output_path=getattr(args, 'output', None),
            review_output_path=getattr(args, 'review_output', None),
            send=bool(args.send),
        )
    )


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

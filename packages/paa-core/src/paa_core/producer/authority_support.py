"""Shared support helpers for producer authority tooling."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from paa_core.config import load_producer_project_config
from paa_core.db import run_psql as shared_run_psql
from paa_core.runtime_paths import (
    default_installed_manifest_path,
    producer_manifest_candidates,
    repo_root_from_cwd,
)
from paa_core.team_worker_roles import (
    active_team_worker_roles,
    team_worker_role_by_key,
)
from paa_core.producer.issue_loader import load_issue_into_paa

MANIFEST_ENV = 'FRACTAL_CORE_AUTHORITY_MANIFEST'
CURRENT_MANIFEST = default_installed_manifest_path()
PAA_PROJECT_SLUG = os.environ.get('PAA_PROJECT_SLUG', 'fractal-core-python')
DEFAULT_GOVERNANCE_REMINDERS = [
    'Dev owns implementation, validation, and keeping the PR current',
    'Architect / Spec Owner owns acceptance and merge',
    'do not merge your own slice',
]
PACKET_COMPILER_AGENT_BY_SCHEMA = {
    'architect_cycle_packet': 'Fractal Core Architect Automation',
    'slice_result_packet': 'Python Team Automation',
    'qa_verification_packet': 'Fractal Core QA Automation',
    'delivery_review_packet': 'Fractal Core Delivery Architect Automation',
    'techlead_assignment_packet': 'Fractal Core TechLead Automation',
    'techlead_decision_packet': 'Fractal Core TechLead Automation',
}
TEAM_WORKER_CLI_CHOICES = [role.key for role in active_team_worker_roles(repo_root=repo_root_from_cwd())]
TEAM_WORKER_DECISION_CHOICES = ['delivery-architect', *TEAM_WORKER_CLI_CHOICES, 'qa', 'authority-architect']


def packet_compiler_agent_name_for_worker_role(role_display_name: str | None) -> str:
    if role_display_name in {'Python Dev', 'Frontend Dev', 'Backend Dev', 'Infra Dev', 'Docs Dev', 'Dev'}:
        return 'Dev Agent'
    if role_display_name == 'QA':
        return 'QA Agent'
    if role_display_name == 'TechLead':
        return 'TechLead Agent'
    return 'Dev Agent'


def resolve_manifest(explicit: str | None = None) -> Path:
    if explicit:
        path = Path(explicit).expanduser().resolve()
        if path.exists():
            return path
        raise FileNotFoundError(path)

    env = os.environ.get(MANIFEST_ENV)
    if env:
        path = Path(env).expanduser().resolve()
        if path.exists():
            return path
        raise FileNotFoundError(path)

    candidates = [
        (Path.cwd() / '.project/data/paa/authority/current/authority/fractal-core-python-authority.json').resolve(),
        CURRENT_MANIFEST,
        *producer_manifest_candidates(Path.cwd()),
        (Path.cwd() / 'docs/architecture/tom-baby7-fractal-core/project-authority/fractal-core-python-authority.json').resolve(),
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError('No authority manifest found. Set FRACTAL_CORE_AUTHORITY_MANIFEST or pass --manifest.')


def load_manifest(explicit: str | None = None) -> tuple[Path, dict[str, Any]]:
    manifest = resolve_manifest(explicit)
    return manifest, json.loads(manifest.read_text())


def write_manifest(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2) + '\n')


def sql_literal(value: object | None) -> str:
    if value is None:
        return 'NULL'
    return "'" + str(value).replace("'", "''") + "'"


def run_psql(sql: str) -> str:
    return shared_run_psql(sql)


def resolve_work_item_id(project_slug: str, issue_number: int | None) -> str | None:
    if issue_number is None:
        return None
    sql = f"""
    SELECT wi.work_item_id
    FROM paa.work_items wi
    JOIN paa.projects p ON p.project_id = wi.project_id
    WHERE p.slug = {sql_literal(project_slug)}
      AND wi.issue_number = {sql_literal(issue_number)}
    LIMIT 1;
    """
    out = run_psql(sql).strip()
    return out or None


def resolve_producer_project_config_path(repo_root: Path) -> Path:
    config_path = repo_root / '.codex' / 'paa' / 'project-config.json'
    if not config_path.exists():
        raise FileNotFoundError(
            f'No producer project config found at {config_path}. '
            'Install producer runtime and configure .codex/paa/project-config.json first.'
        )
    return config_path


def sync_issue_source_into_paa(
    *,
    repo_root: Path,
    issue_number: int,
    verification_key_prefix: str | None = None,
    scope_authority_label: str | None = None,
) -> dict[str, Any]:
    config = load_producer_project_config(resolve_producer_project_config_path(repo_root))
    return load_issue_into_paa(
        repo_root=repo_root,
        config=config,
        issue_number=issue_number,
        verification_key_prefix=verification_key_prefix,
        scope_authority_label=scope_authority_label,
        dry_run=False,
    )


def persist_packet_compilation(
    *,
    project_slug: str,
    packet: dict[str, Any],
    package_id_external: str | None,
    brief_id_external: str | None,
    review_markdown: str | None,
    output_path: str | None,
    review_output_path: str | None,
    source_input_path: str | None = None,
    source_packet_path: str | None = None,
) -> str:
    issue_number_raw = (packet.get('github_context') or {}).get('issue_number')
    issue_number = issue_number_raw if isinstance(issue_number_raw, int) else None
    work_item_id = resolve_work_item_id(project_slug, issue_number)
    schema_type = str(packet['schema_type'])
    if schema_type == 'worker_result_packet':
        from_role_raw = packet.get('from_role')
        from_role = from_role_raw if isinstance(from_role_raw, str) else None
        role = team_worker_role_by_key(from_role, repo_root=repo_root_from_cwd()) if from_role else None
        agent_name = packet_compiler_agent_name_for_worker_role(role.display_name if role else None)
    else:
        agent_name = PACKET_COMPILER_AGENT_BY_SCHEMA[schema_type]
    artifacts = {
        'packet_schema_type': schema_type,
        'package_id_external': package_id_external,
        'brief_id_external': brief_id_external,
        'message_id': packet.get('message_id'),
        'correlation_id': packet.get('correlation_id'),
        'review_markdown': review_markdown,
        'output_path': output_path,
        'review_output_path': review_output_path,
        'source_input_path': source_input_path,
        'source_packet_path': source_packet_path,
        'packet_json': packet,
        'persistence_version': '1.0.0',
    }
    summary = f"Compiled {schema_type} for issue #{issue_number}" if issue_number is not None else f"Compiled {schema_type}"
    sql = f"""
    WITH project AS (
      SELECT project_id FROM paa.projects WHERE slug = {sql_literal(project_slug)} LIMIT 1
    ), agent AS (
      SELECT a.agent_id
      FROM paa.agents a
      JOIN project p ON p.project_id = a.project_id
      WHERE a.name = {sql_literal(agent_name)}
      LIMIT 1
    )
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
    SELECT
      agent.agent_id,
      {sql_literal(work_item_id)}::uuid,
      {sql_literal(f'packet_compilation:{schema_type}')},
      'completed'::paa.automation_run_status,
      {sql_literal(packet.get('created_at'))}::timestamptz,
      {sql_literal(packet.get('created_at'))}::timestamptz,
      {sql_literal(summary)},
      {sql_literal(json.dumps(artifacts))}::jsonb
    FROM agent;
    """
    run_psql(sql)
    sql2 = f"""
    SELECT automation_run_id
    FROM paa.automation_runs ar
    JOIN paa.agents a ON a.agent_id = ar.agent_id
    WHERE a.name = {sql_literal(agent_name)}
      AND ar.trigger_type = {sql_literal(f'packet_compilation:{schema_type}')}
      AND ar.summary = {sql_literal(summary)}
    ORDER BY ar.created_at DESC
    LIMIT 1;
    """
    return run_psql(sql2).strip()

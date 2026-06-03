"""Packet and review helpers shared by producer authority tooling."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from paa_core.runtime_paths import default_installed_artifact_path, repo_root_from_cwd
from paa_core.team_worker_roles import team_worker_role_by_display_name, team_worker_role_by_key
from paa_core.producer.authority_support import DEFAULT_GOVERNANCE_REMINDERS, run_psql, sql_literal


def load_ready_coder_briefs_from_paa(
    *,
    project_slug: str,
    package_id_external: str,
) -> list[dict[str, Any]]:
    sql = f"""
    WITH package AS (
      SELECT dp.design_package_id, dp.project_id, dp.package_id_external
      FROM paa.design_packages dp
      JOIN paa.projects p ON p.project_id = dp.project_id
      WHERE p.slug = {sql_literal(project_slug)}
        AND dp.package_id_external = {sql_literal(package_id_external)}
      LIMIT 1
    ), latest_sequence AS (
      SELECT DISTINCT ON (s.coder_run_brief_id)
        s.coder_run_brief_id,
        s.readiness_state::text AS readiness_state,
        s.blocking_cause,
        s.parallel_group_id,
        s.computed_at
      FROM paa.coder_brief_sequence_states s
      JOIN package pkg ON pkg.design_package_id = s.design_package_id
      ORDER BY s.coder_run_brief_id, s.computed_at DESC, s.coder_brief_sequence_state_id DESC
    )
    SELECT
      cb.brief_id_external,
      cb.brief_json::text,
      coalesce(ls.readiness_state, cb.brief_json #>> '{{execution_readiness,readiness_class}}') AS readiness_state,
      ls.blocking_cause,
      ls.parallel_group_id,
      coalesce(cb.generated_from_json->>'source_artifact', ''),
      {sql_literal(str(default_installed_artifact_path('coder_run_brief.schema.json')))}
    FROM paa.coder_run_briefs cb
    JOIN package pkg ON pkg.project_id = cb.project_id
    LEFT JOIN latest_sequence ls ON ls.coder_run_brief_id = cb.coder_run_brief_id
    WHERE cb.generated_from_json->>'design_package_id_external' = {sql_literal(package_id_external)}
    ORDER BY cb.brief_id_external;
    """
    rows: list[dict[str, Any]] = []
    for line in run_psql(sql).splitlines():
        if not line.strip():
            continue
        brief_id_external, brief_json, readiness_state, blocking_cause, parallel_group_id, source_artifact, schema_path = line.split('\t')
        brief_json_obj = json.loads(brief_json)
        source_artifact_path = Path(source_artifact).expanduser().resolve() if source_artifact else None
        if source_artifact_path and source_artifact_path.exists():
            brief_json_obj = json.loads(source_artifact_path.read_text())
        rows.append({
            'brief_id_external': brief_id_external,
            'brief_json': brief_json_obj,
            'readiness_state': readiness_state,
            'blocking_cause': blocking_cause or None,
            'parallel_group_id': parallel_group_id or None,
            'source_artifact': str(source_artifact_path) if source_artifact_path else None,
            'schema_path': schema_path,
        })
    return rows


def load_design_package_from_paa(
    *,
    project_slug: str,
    package_id_external: str,
) -> dict[str, Any]:
    sql = f"""
    SELECT dp.package_json::text
    FROM paa.design_packages dp
    JOIN paa.projects p ON p.project_id = dp.project_id
    WHERE p.slug = {sql_literal(project_slug)}
      AND dp.package_id_external = {sql_literal(package_id_external)}
    LIMIT 1;
    """
    out = run_psql(sql).strip()
    if not out:
        raise RuntimeError(f'No design package found for {project_slug}:{package_id_external}')
    return json.loads(out)


def unique_preserving_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if not item:
            continue
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def derive_keep_stable(package: dict[str, Any]) -> list[str]:
    protected = package.get('verification_contract_basis', {}).get('protected_baseline_checks', [])
    labels: list[str] = []
    for item in protected:
        lower = str(item).lower()
        if 'trace' in lower:
            labels.append('trace')
        if 'parity' in lower:
            labels.append('parity')
        if 'benchmark' in lower:
            labels.append('benchmark')
    return unique_preserving_order(labels) or ['trace', 'parity', 'benchmark']


def derive_focus(selected_brief: dict[str, Any], package: dict[str, Any]) -> list[str]:
    del package
    focus: list[str] = []
    assignment = selected_brief['brief_json']['component_assignment']
    focus.append(f"{assignment['component_name']} ({assignment['component_role']})")
    focus.extend(selected_brief['brief_json']['change_budget'].get('expected_touch_surfaces', []))
    focus.extend(selected_brief['brief_json']['execution_prerequisites'].get('blocking_dependency_edges', []))
    return unique_preserving_order(focus)


def derive_next_move(selected_brief: dict[str, Any], next_issue_number: int) -> list[str]:
    brief = selected_brief['brief_json']
    assignment = brief['component_assignment']
    moves = [
        'create branch from main',
        f"implement the {assignment['component_name']} brief",
        'run the required validation and protected baseline checks',
    ]
    prereqs = brief.get('execution_prerequisites', {}).get('prerequisite_briefs', [])
    if prereqs:
        moves.append('do not begin execution until prerequisite brief readiness is satisfied')
    if next_issue_number:
        moves.append(f'keep PR linkage and issue commentary current for issue #{next_issue_number}')
    return unique_preserving_order(moves)


def derive_remaining_gap(task: dict[str, Any] | None, package: dict[str, Any]) -> str:
    if task and task.get('authoring', {}).get('current_gap'):
        current_gap = task['authoring']['current_gap']
        if isinstance(current_gap, list):
            return ' '.join(str(item) for item in current_gap[:2])
        return str(current_gap)
    gaps = package.get('implementation_target', {}).get('current_gap', [])
    if gaps:
        return ' '.join(str(item) for item in gaps[:2])
    return str(
        package.get('product_and_source_basis', {}).get(
            'product_outcome_statement',
            'remaining implementation gap requires the next execution-ready slice',
        )
    )


def derive_governance_reminders() -> list[str]:
    return list(DEFAULT_GOVERNANCE_REMINDERS)


def write_review_markdown(path: Path, packet: dict[str, Any]) -> None:
    brief = packet['payload']['coder_run_brief']
    review = [
        f"# Architect Packet Review: {packet['message_id']}",
        '',
        '## Resolution',
        f"- package: `{packet['payload']['coder_brief_resolution']['package_id_external']}`",
        f"- brief: `{packet['payload']['coder_brief_resolution']['brief_id_external']}`",
        f"- readiness: `{packet['payload']['coder_brief_resolution']['readiness_state']}`",
        '',
        '## GitHub context',
        f"- closed issue: `#{packet['payload']['closed_issue']['number']}`",
        f"- accepted PR: `#{packet['payload']['accepted_pr']['number']}`",
        f"- next issue: `#{packet['payload']['next_issue']['number']}`",
        '',
        '## Next move',
    ]
    review.extend([f"- {item}" for item in packet['payload']['next_move']])
    review.extend(['', '## Focus'])
    review.extend([f"- {item}" for item in packet['payload']['focus']])
    review.extend([
        '',
        '## Selected component',
        f"- component: `{brief['component_assignment']['component_name']}`",
        f"- role: `{brief['component_assignment']['component_role']}`",
        f"- layer: `{brief['component_assignment']['system_layer']}`",
        '',
        '## Allowed edit surfaces',
    ])
    review.extend([f"- {item}" for item in brief['architecture_constraints']['allowed_edit_surfaces']])
    review.extend([
        '',
        '## Blocking / prerequisites',
    ])
    prereq = brief.get('execution_prerequisites', {})
    review.extend([f"- prerequisite briefs: {', '.join(prereq.get('prerequisite_briefs', [])) or '(none)'}"])
    review.extend([f"- blocking edges: {', '.join(prereq.get('blocking_dependency_edges', [])) or '(none)'}"])
    review.extend([f"- parallel-safe with: {', '.join(prereq.get('parallel_safe_with', [])) or '(none)'}"])
    review.extend(['', '## Protected baseline'])
    review.extend([f"- {item}" for item in packet['payload']['keep_stable']])
    path.write_text('\n'.join(review) + '\n')


def load_json_file(path: str) -> dict[str, Any]:
    return json.loads(Path(path).expanduser().resolve().read_text())


def normalize_techlead_role(raw_role: str) -> str:
    mapping = {
        'python-team': 'Python Dev',
        'qa': 'QA',
        'delivery-architect': 'Delivery Architect',
        'authority-architect': 'Authority Architect',
        'techlead': 'TechLead',
    }
    dynamic_role = team_worker_role_by_key(raw_role, repo_root=repo_root_from_cwd())
    if dynamic_role:
        return dynamic_role.display_name
    return mapping.get(raw_role, raw_role)


def normalize_worker_role(raw_role: str) -> str:
    dynamic_role = team_worker_role_by_key(raw_role, repo_root=repo_root_from_cwd())
    if dynamic_role:
        return dynamic_role.display_name
    return raw_role


def techlead_worktree_hint(issue_number: int, target_role: str | None) -> str | None:
    if target_role is None:
        return None
    dynamic_role = team_worker_role_by_display_name(target_role, repo_root=repo_root_from_cwd())
    if dynamic_role:
        return f'issue-{issue_number}-{dynamic_role.branch_suffix}'
    suffix_map = {
        'QA': 'qa',
        'Delivery Architect': 'delivery',
        'Authority Architect': 'authority',
        'TechLead': 'techlead',
    }
    suffix = suffix_map.get(target_role)
    if suffix is None:
        return None
    return f'issue-{issue_number}-{suffix}'

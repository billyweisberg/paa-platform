"""Generic source-to-PAA issue loader for producer-side artifacts."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from paa_core.config import ProducerProjectConfig
from paa_core.db import run_psql, sql_literal
from paa_core.producer.obligation_loader import (
    _find_stage1_package_path,
    build_obligation_rows,
    load_stage1_package,
)


@dataclass(frozen=True)
class IssueArtifactBundle:
    issue_number: int
    package_path: Path
    package_json: dict[str, Any]
    brief_paths: list[Path]
    brief_jsons: list[dict[str, Any]]
    manifest_task: dict[str, Any] | None


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _find_issue_brief_paths(
    *,
    repo_root: Path,
    config: ProducerProjectConfig,
    issue_number: int,
) -> list[Path]:
    matches: list[Path] = []
    for raw in config.artifact_paths:
        if f"coder_run_brief.issue{issue_number}." not in raw:
            continue
        path = (repo_root / raw).resolve()
        if path.exists():
            matches.append(path)
    if not matches:
        raise FileNotFoundError(f"No coder run brief artifacts found for issue #{issue_number}")
    return sorted(matches)


def _load_manifest_task(
    *,
    repo_root: Path,
    config: ProducerProjectConfig,
    issue_number: int,
) -> dict[str, Any] | None:
    manifest_path = (repo_root / config.authority_manifest_path).resolve()
    manifest = json.loads(manifest_path.read_text())
    for task in manifest.get("tasks", []):
        if task.get("issue_number") == issue_number:
            return task
    return None


def load_issue_bundle(
    *,
    repo_root: Path,
    config: ProducerProjectConfig,
    issue_number: int,
) -> IssueArtifactBundle:
    package_path = _find_stage1_package_path(
        repo_root=repo_root,
        config=config,
        issue_number=issue_number,
    )
    brief_paths = _find_issue_brief_paths(
        repo_root=repo_root,
        config=config,
        issue_number=issue_number,
    )
    return IssueArtifactBundle(
        issue_number=issue_number,
        package_path=package_path,
        package_json=load_stage1_package(package_path),
        brief_paths=brief_paths,
        brief_jsons=[_load_json(path) for path in brief_paths],
        manifest_task=_load_manifest_task(repo_root=repo_root, config=config, issue_number=issue_number),
    )


def _map_manifest_status(task_status: str | None) -> str:
    mapping = {
        "todo": "draft",
        "queued": "authorized",
        "authorized": "authorized",
        "in_dev": "in_progress",
        "ready_for_verification": "ready_for_verification",
        "in_qa": "in_qa",
        "ready_for_acceptance": "ready_for_acceptance",
        "complete": "accepted",
        "blocked": "blocked",
        "superseded": "superseded",
        "deferred": "deferred",
    }
    return mapping.get(task_status or "", "authorized")


def _normalize_design_package_status(status: str | None) -> str:
    if status in {"draft", "under_review", "approved_for_derivation", "superseded", "rejected"}:
        return status
    return "approved_for_derivation"


def _normalize_brief_status(status: str | None) -> str:
    if status in {"draft", "approved", "active", "superseded", "consumed", "rejected"}:
        return status
    return "approved"


def _normalize_readiness_state(state: str | None) -> str:
    if state in {
        "not_derivation_ready",
        "derivation_ready",
        "blocked_on_dependency",
        "blocked_on_contract",
        "execution_ready",
        "parallel_ready",
        "active",
        "completed",
    }:
        return state
    return "execution_ready"


def _resolve_primary_component_name(package: dict[str, Any]) -> str | None:
    return (package.get("component_model_slice") or {}).get("primary_component")


def _work_item_insert_sql(bundle: IssueArtifactBundle) -> str:
    package = bundle.package_json
    ctx = package.get("authority_context") or {}
    task = bundle.manifest_task or {}
    title = task.get("task_title") or ctx.get("task_title") or f"Issue #{bundle.issue_number}"
    authority_version = ctx.get("authority_version")
    merge_policy = task.get("merge_policy") or "qa_required"
    requires_qa = task.get("requires_qa")
    if requires_qa is None:
        requires_qa = True
    status = _map_manifest_status(task.get("status"))
    implementation_target_ref = (package.get("implementation_target") or {}).get("implementation_target_id")
    spec_fragment_ref = (package.get("spec_fragment") or {}).get("spec_fragment_id")
    domain_ref = {
        "delta_family": (package.get("spec_fragment") or {}).get("authorized_delta_family"),
        "real_slice": True,
        "source": "paa-producer load-issue-into-paa",
    }
    return f"""
WITH project AS (
  SELECT project_id FROM paa.projects WHERE slug='fractal-core-python'
), av AS (
  SELECT authority_version_id FROM paa.authority_versions WHERE version_label={sql_literal(authority_version)} LIMIT 1
)
INSERT INTO paa.work_items (
  project_id, authority_version_id, title, status, merge_policy, requires_qa, issue_number, implementation_target_ref, spec_fragment_ref, domain_ref
)
SELECT
  project.project_id,
  av.authority_version_id,
  {sql_literal(title)},
  {sql_literal(status)}::paa.work_item_status,
  {sql_literal(merge_policy)},
  {'true' if requires_qa else 'false'},
  {bundle.issue_number},
  {sql_literal(implementation_target_ref)},
  {sql_literal(spec_fragment_ref)},
  {sql_literal(json.dumps(domain_ref))}::jsonb
FROM project
LEFT JOIN av ON TRUE
WHERE NOT EXISTS (
  SELECT 1 FROM paa.work_items wi
  WHERE wi.project_id = project.project_id
    AND wi.issue_number = {bundle.issue_number}
);
""".strip()


def _design_package_insert_sql(bundle: IssueArtifactBundle) -> str:
    package = bundle.package_json
    ctx = package.get("authority_context") or {}
    implementation_target_ref = (package.get("implementation_target") or {}).get("implementation_target_id")
    spec_fragment_ref = (package.get("spec_fragment") or {}).get("spec_fragment_id")
    primary_component_name = _resolve_primary_component_name(package)
    return f"""
WITH project AS (
  SELECT project_id FROM paa.projects WHERE slug='fractal-core-python'
), wi AS (
  SELECT wi.work_item_id
  FROM paa.work_items wi
  JOIN project p ON p.project_id = wi.project_id
  WHERE wi.issue_number = {bundle.issue_number}
  LIMIT 1
), av AS (
  SELECT authority_version_id FROM paa.authority_versions WHERE version_label={sql_literal(ctx.get('authority_version'))} LIMIT 1
)
INSERT INTO paa.design_packages (
  project_id, work_item_id, spec_fragment_id, implementation_target_id, authority_version_id, primary_component_id,
  package_id_external, schema_version, status, package_json, provenance_json, metadata_json
)
SELECT
  project.project_id,
  wi.work_item_id,
  NULL,
  NULL,
  av.authority_version_id,
  (
    SELECT c.component_id
    FROM paa.components c
    WHERE c.project_id = project.project_id
      AND c.name = {sql_literal(primary_component_name)}
    LIMIT 1
  ),
  {sql_literal(package.get('package_id'))},
  {sql_literal(package.get('schema_version') or '1.0.0')},
  {sql_literal(_normalize_design_package_status(package.get('status')))}::paa.design_package_status,
  {sql_literal(json.dumps(package))}::jsonb,
  {sql_literal(json.dumps({'source_artifact': str(bundle.package_path), 'loader': 'paa-producer load-issue-into-paa'}))}::jsonb,
  {sql_literal(json.dumps({'real_slice': True, 'issue_number': bundle.issue_number, 'implementation_target_ref': implementation_target_ref, 'spec_fragment_ref': spec_fragment_ref}))}::jsonb
FROM project, wi
LEFT JOIN av ON TRUE
WHERE NOT EXISTS (
  SELECT 1 FROM paa.design_packages dp
  WHERE dp.project_id = project.project_id
    AND dp.package_id_external = {sql_literal(package.get('package_id'))}
);
""".strip()


def _brief_insert_sql(bundle: IssueArtifactBundle, brief_path: Path, brief: dict[str, Any]) -> str:
    authority_context = brief.get("authority_context") or {}
    component_assignment = brief.get("component_assignment") or {}
    package_id_external = bundle.package_json.get("package_id")
    brief_id = brief.get("brief_id")
    return f"""
WITH project AS (
  SELECT project_id FROM paa.projects WHERE slug='fractal-core-python'
), wi AS (
  SELECT wi.work_item_id
  FROM paa.work_items wi
  JOIN project p ON p.project_id = wi.project_id
  WHERE wi.issue_number = {bundle.issue_number}
  LIMIT 1
), av AS (
  SELECT authority_version_id FROM paa.authority_versions WHERE version_label={sql_literal(authority_context.get('authority_version'))} LIMIT 1
)
INSERT INTO paa.coder_run_briefs (
  project_id, work_item_id, spec_fragment_id, implementation_target_id, authority_version_id, primary_component_id,
  brief_id_external, schema_version, status, slice_scope_ref_json, component_assignment_json, architecture_constraints_json,
  collaboration_context_json, dependency_contract_json, behavioral_contract_json, test_contract_json, change_budget_json,
  anti_goals_json, brief_json, generated_from_json, metadata_json
)
SELECT
  project.project_id,
  wi.work_item_id,
  NULL,
  NULL,
  av.authority_version_id,
  (
    SELECT c.component_id
    FROM paa.components c
    WHERE c.project_id = project.project_id
      AND c.name = {sql_literal(component_assignment.get('component_name'))}
    LIMIT 1
  ),
  {sql_literal(brief_id)},
  {sql_literal(brief.get('schema_version') or '1.1.0')},
  {sql_literal(_normalize_brief_status(brief.get('status')))}::paa.coder_brief_status,
  {sql_literal(json.dumps(brief.get('slice_scope_ref') or {}))}::jsonb,
  {sql_literal(json.dumps(component_assignment))}::jsonb,
  {sql_literal(json.dumps(brief.get('architecture_constraints') or {}))}::jsonb,
  {sql_literal(json.dumps(brief.get('collaboration_context') or {}))}::jsonb,
  {sql_literal(json.dumps(brief.get('dependency_contract') or {}))}::jsonb,
  {sql_literal(json.dumps(brief.get('behavioral_contract') or {}))}::jsonb,
  {sql_literal(json.dumps(brief.get('test_contract') or {}))}::jsonb,
  {sql_literal(json.dumps(brief.get('change_budget') or {}))}::jsonb,
  {sql_literal(json.dumps(brief.get('anti_goals') or {}))}::jsonb,
  {sql_literal(json.dumps(brief))}::jsonb,
  {sql_literal(json.dumps({'source_artifact': str(brief_path), 'design_package_id_external': package_id_external}))}::jsonb,
  {sql_literal(json.dumps({'real_slice': True, 'issue_number': bundle.issue_number, 'loader': 'paa-producer load-issue-into-paa'}))}::jsonb
FROM project, wi
LEFT JOIN av ON TRUE
WHERE NOT EXISTS (
  SELECT 1 FROM paa.coder_run_briefs cb
  WHERE cb.project_id = project.project_id
    AND cb.brief_id_external = {sql_literal(brief_id)}
);
""".strip()


def _sequence_insert_sql(bundle: IssueArtifactBundle, brief: dict[str, Any]) -> str:
    authority_context = brief.get("authority_context") or {}
    component_assignment = brief.get("component_assignment") or {}
    execution_readiness = brief.get("execution_readiness") or {}
    blocking_causes = execution_readiness.get("blocking_causes") or []
    blocking_cause = "; ".join(str(item) for item in blocking_causes) if blocking_causes else None
    return f"""
WITH project AS (
  SELECT project_id FROM paa.projects WHERE slug='fractal-core-python'
), dp AS (
  SELECT dp.design_package_id
  FROM paa.design_packages dp
  JOIN project p ON p.project_id = dp.project_id
  WHERE dp.package_id_external = {sql_literal(bundle.package_json.get('package_id'))}
  LIMIT 1
), cb AS (
  SELECT cb.coder_run_brief_id
  FROM paa.coder_run_briefs cb
  JOIN project p ON p.project_id = cb.project_id
  WHERE cb.brief_id_external = {sql_literal(brief.get('brief_id'))}
  LIMIT 1
)
INSERT INTO paa.coder_brief_sequence_states (
  project_id, design_package_id, coder_run_brief_id, primary_component_id, readiness_state, blocking_cause, parallel_group_id, computed_at, metadata_json
)
SELECT
  project.project_id,
  dp.design_package_id,
  cb.coder_run_brief_id,
  (
    SELECT c.component_id
    FROM paa.components c
    WHERE c.project_id = project.project_id
      AND c.name = {sql_literal(component_assignment.get('component_name'))}
    LIMIT 1
  ),
  {sql_literal(_normalize_readiness_state(execution_readiness.get('readiness_class')))}::paa.readiness_state,
  {sql_literal(blocking_cause)},
  {sql_literal(execution_readiness.get('parallel_group_id'))},
  now(),
  {sql_literal(json.dumps({
        'source': 'paa-producer load-issue-into-paa',
        'issue_number': bundle.issue_number,
        'authority_version': authority_context.get('authority_version'),
    }))}::jsonb
FROM project, dp, cb
WHERE NOT EXISTS (
  SELECT 1
  FROM paa.coder_brief_sequence_states s
  WHERE s.design_package_id = dp.design_package_id
    AND s.coder_run_brief_id = cb.coder_run_brief_id
);
""".strip()


def build_issue_load_plan(
    bundle: IssueArtifactBundle,
    *,
    verification_key_prefix: str | None = None,
    scope_authority_label: str | None = None,
) -> dict[str, Any]:
    default_issue_slug = verification_key_prefix or _derive_default_issue_slug(bundle.package_path, bundle.issue_number)
    package = bundle.package_json
    plan = {
        "issue_number": bundle.issue_number,
        "package_path": str(bundle.package_path),
        "package_id": package.get("package_id"),
        "brief_paths": [str(path) for path in bundle.brief_paths],
        "brief_ids": [brief.get("brief_id") for brief in bundle.brief_jsons],
        "work_item_title": (bundle.manifest_task or {}).get("task_title") or (package.get("authority_context") or {}).get("task_title"),
        "manifest_status": (bundle.manifest_task or {}).get("status"),
        "mapped_work_item_status": _map_manifest_status((bundle.manifest_task or {}).get("status")),
        "primary_component": _resolve_primary_component_name(package),
        "verification_key_prefix": default_issue_slug,
        "scope_authority_label": scope_authority_label or default_issue_slug.replace("_", "-"),
        "sequence_states": {
            brief.get("brief_id"): (brief.get("execution_readiness") or {}).get("readiness_class")
            for brief in bundle.brief_jsons
        },
        "obligations": [
            {
                "verification_key": row.verification_key,
                "verification_type": row.verification_type,
                "method": row.method,
            }
            for row in build_obligation_rows(
                issue_number=bundle.issue_number,
                package=package,
                verification_key_prefix=default_issue_slug,
                scope_authority_label=scope_authority_label,
            )
        ],
    }
    return plan


def _derive_default_issue_slug(package_path: Path, issue_number: int) -> str:
    stem = package_path.stem
    marker = f"issue{issue_number}."
    if marker in stem:
        return stem.split(marker, 1)[1].replace("_", "-")
    return stem.replace("_", "-")


def load_issue_into_paa(
    *,
    repo_root: Path,
    config: ProducerProjectConfig,
    issue_number: int,
    verification_key_prefix: str | None = None,
    scope_authority_label: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    bundle = load_issue_bundle(repo_root=repo_root, config=config, issue_number=issue_number)
    plan = build_issue_load_plan(
        bundle,
        verification_key_prefix=verification_key_prefix,
        scope_authority_label=scope_authority_label,
    )
    if dry_run:
        plan["dry_run"] = True
        return plan

    statements = [
        _work_item_insert_sql(bundle),
        _design_package_insert_sql(bundle),
        *(_brief_insert_sql(bundle, path, brief) for path, brief in zip(bundle.brief_paths, bundle.brief_jsons)),
        *(_sequence_insert_sql(bundle, brief) for brief in bundle.brief_jsons),
    ]
    run_psql("BEGIN;\n" + "\n\n".join(statements) + "\nCOMMIT;\n")
    materialized = materialize_issue_obligations(
        repo_root=repo_root,
        config=config,
        issue_number=issue_number,
        verification_key_prefix=verification_key_prefix,
        scope_authority_label=scope_authority_label,
    )
    return {
        **plan,
        "dry_run": False,
        "materialized_obligation_count": len(materialized["obligations"]),
    }


def materialize_issue_obligations(
    *,
    repo_root: Path,
    config: ProducerProjectConfig,
    issue_number: int,
    verification_key_prefix: str | None = None,
    scope_authority_label: str | None = None,
) -> dict[str, Any]:
    bundle = load_issue_bundle(repo_root=repo_root, config=config, issue_number=issue_number)
    return _materialize_obligations_for_bundle(
        repo_root=repo_root,
        bundle=bundle,
        verification_key_prefix=verification_key_prefix,
        scope_authority_label=scope_authority_label,
    )


def _materialize_obligations_for_bundle(
    *,
    repo_root: Path,
    bundle: IssueArtifactBundle,
    verification_key_prefix: str | None = None,
    scope_authority_label: str | None = None,
) -> dict[str, Any]:
    from paa_core.producer.obligation_loader import materialize_verification_obligations

    issue_slug = verification_key_prefix or _derive_default_issue_slug(bundle.package_path, bundle.issue_number)
    scope_label = scope_authority_label or issue_slug.replace("_", "-")
    return materialize_verification_obligations(
        repo_root=repo_root,
        config=None,
        issue_number=bundle.issue_number,
        package_path=bundle.package_path,
        verification_key_prefix=issue_slug,
        scope_authority_label=scope_label,
        dry_run=False,
    )

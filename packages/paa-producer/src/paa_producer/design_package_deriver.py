"""Producer-side Stage 1 design-package derivation and persistence."""

from __future__ import annotations

from dataclasses import dataclass
import json
import subprocess
from pathlib import Path
from typing import Any

from paa_core.db import run_psql, sql_literal

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover - dependency guard
    Draft202012Validator = None

DEFAULT_STAGE1_SCHEMA_CANDIDATES = (
    Path('/Users/billyweisberg/Repos/billyweisberg/paa-platform/schemas/derivation/stage1_design_package.schema.json'),
    Path('/Users/billyweisberg/Repos/Individual-Centricity/appdev/docs/architecture/tom-baby7-fractal-core/artifact-schemas/stage1_design_package.schema.json'),
)

STANDARD_SIGNOFF_ROLE_ORDER = (
    ('Architect', 'architecture', 10),
    ('Project Designer', 'architecture', 20),
    ('Product Owner', 'coordination', 30),
    ('TechLead', 'coordination', 40),
)


@dataclass(frozen=True)
class DerivedDesignPackageResult:
    project_slug: str
    package_id: str
    package_path: str
    schema_path: str
    authority_version: str
    project_id: str | None
    authority_version_id: str | None
    spec_fragment_id: str | None
    implementation_target_id: str | None
    component_id: str | None
    work_item_id: str | None
    design_package_id: str | None
    dry_run: bool


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _resolve_stage1_schema_path(explicit: Path | None = None) -> Path:
    candidates = [explicit] if explicit else []
    candidates.extend(DEFAULT_STAGE1_SCHEMA_CANDIDATES)
    for candidate in candidates:
        if candidate is None:
            continue
        path = candidate.expanduser().resolve()
        if path.exists():
            return path
    looked = [str(c) for c in candidates if c is not None]
    raise FileNotFoundError(
        'No Stage 1 design package schema found. Provide --schema-path or install the schema at one of: '
        + ', '.join(looked)
    )


def _require_jsonschema() -> None:
    if Draft202012Validator is None:
        raise RuntimeError('jsonschema is required for derive-design-package; install jsonschema in the producer environment')


def validate_stage1_design_package(package_path: Path, schema_path: Path) -> dict[str, Any]:
    _require_jsonschema()
    schema = _load_json(schema_path)
    package = _load_json(package_path)
    Draft202012Validator(schema).validate(package)
    return package


def _project_name_from_slug(slug: str) -> str:
    return ' '.join(part.capitalize() for part in slug.replace('_', '-').split('-') if part) or slug


def _git_remote_url(repo_root: Path | None) -> str | None:
    if repo_root is None:
        return None
    result = subprocess.run(
        ['git', 'config', '--get', 'remote.origin.url'],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    value = result.stdout.strip()
    return value or None


def _query_scalar(sql: str) -> str | None:
    for line in run_psql(sql).splitlines():
        value = line.strip()
        if value:
            return value
    return None


def _json_literal(value: Any) -> str:
    return sql_literal(json.dumps(value)) + '::jsonb'


def _ensure_project(*, slug: str, name: str, repo_url: str | None) -> str:
    sql = f"""
    INSERT INTO paa.projects (slug, name, repo_url, execution_surface, status)
    VALUES (
      {sql_literal(slug)},
      {sql_literal(name)},
      {sql_literal(repo_url)},
      'github',
      'active'::paa.project_status
    )
    ON CONFLICT (slug) DO UPDATE SET
      name = EXCLUDED.name,
      repo_url = COALESCE(EXCLUDED.repo_url, paa.projects.repo_url),
      updated_at = now()
    RETURNING project_id;
    """
    project_id = _query_scalar(sql)
    if not project_id:
        raise RuntimeError(f'failed to resolve project id for {slug}')
    return project_id


def _ensure_roles(*, project_id: str, signoff: dict[str, Any]) -> dict[str, str]:
    role_ids: dict[str, str] = {}
    for role_name, category, sort_order in STANDARD_SIGNOFF_ROLE_ORDER:
        signer_name = signoff.get(role_name.lower().replace(' ', '_'))
        if signer_name is None and role_name == 'TechLead':
            continue
        sql = f"""
        INSERT INTO paa.roles (
          project_id, name, category, description, sort_order, is_human_capable, is_automation_capable, active
        )
        VALUES (
          {sql_literal(project_id)}::uuid,
          {sql_literal(role_name)},
          {sql_literal(category)}::paa.role_category,
          {sql_literal(f'{role_name} role for producer-side design-package derivation governance.')},
          {sort_order},
          true,
          true,
          true
        )
        ON CONFLICT (project_id, name) DO UPDATE SET
          category = EXCLUDED.category,
          description = EXCLUDED.description,
          sort_order = EXCLUDED.sort_order,
          updated_at = now()
        RETURNING role_id;
        """
        role_id = _query_scalar(sql)
        if role_id:
            role_ids[role_name] = role_id
    return role_ids


def _ensure_authority_version(*, project_id: str, version_label: str, package_path: Path, repo_root: Path | None) -> str:
    source_commit = None
    published_from_ref = None
    if repo_root is not None:
        source_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo_root, text=True).strip()
        published_from_ref = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=repo_root, text=True).strip()
    sql = f"""
    INSERT INTO paa.authority_versions (
      project_id, version_label, source_commit, published_from_ref, manifest_path, published_at, status, notes
    )
    VALUES (
      {sql_literal(project_id)}::uuid,
      {sql_literal(version_label)},
      {sql_literal(source_commit)},
      {sql_literal(published_from_ref)},
      {sql_literal(str(package_path))},
      now(),
      'published'::paa.authority_status,
      'Derived via paa-producer derive-design-package.'
    )
    ON CONFLICT (project_id, version_label) DO UPDATE SET
      source_commit = COALESCE(EXCLUDED.source_commit, paa.authority_versions.source_commit),
      published_from_ref = COALESCE(EXCLUDED.published_from_ref, paa.authority_versions.published_from_ref),
      manifest_path = EXCLUDED.manifest_path,
      status = EXCLUDED.status,
      updated_at = now()
    RETURNING authority_version_id;
    """
    authority_version_id = _query_scalar(sql)
    if not authority_version_id:
        raise RuntimeError(f'failed to resolve authority version {version_label}')
    return authority_version_id


def _node_for_primary_component(package: dict[str, Any]) -> dict[str, Any]:
    primary_name = (package.get('component_model_slice') or {}).get('primary_component')
    nodes = (package.get('dependency_graph_slice') or {}).get('nodes') or []
    for node in nodes:
        if node.get('component_name') == primary_name:
            return node
    return {}


def _ensure_spec_fragment(*, project_id: str, package: dict[str, Any]) -> str:
    fragment = package['spec_fragment']
    metadata = {
        'spec_fragment_id_external': fragment.get('spec_fragment_id'),
        'authorized_delta_family': fragment.get('authorized_delta_family'),
        'out_of_scope_delta_families': fragment.get('out_of_scope_delta_families') or [],
        'expected_touch_surfaces': (package.get('implementation_target') or {}).get('expected_touch_surfaces') or [],
    }
    sql = f"""
    WITH existing AS (
      SELECT spec_fragment_id
      FROM paa.spec_fragments
      WHERE project_id = {sql_literal(project_id)}::uuid
        AND delta_family = {sql_literal(fragment.get('authorized_delta_family'))}
      LIMIT 1
    ), upserted AS (
      INSERT INTO paa.spec_fragments (
        project_id, title, canonical_statement, fragment_kind, delta_family, status, metadata_json
      )
      SELECT
        {sql_literal(project_id)}::uuid,
        {sql_literal(fragment.get('spec_fragment_title'))},
        {sql_literal(fragment.get('canonical_statement'))},
        'artifact_contract'::paa.fragment_kind,
        {sql_literal(fragment.get('authorized_delta_family'))},
        'approved',
        {_json_literal(metadata)}
      WHERE NOT EXISTS (SELECT 1 FROM existing)
      RETURNING spec_fragment_id
    )
    SELECT spec_fragment_id FROM existing
    UNION ALL
    SELECT spec_fragment_id FROM upserted
    LIMIT 1;
    """
    spec_fragment_id = _query_scalar(sql)
    if not spec_fragment_id:
        raise RuntimeError('failed to resolve spec fragment id')
    return spec_fragment_id


def _ensure_implementation_target(*, spec_fragment_id: str, package: dict[str, Any]) -> str:
    fragment = package['spec_fragment']
    target = package['implementation_target']
    title = f"{fragment.get('spec_fragment_title')} implementation target"
    external_id = target.get('implementation_target_id')
    metadata = {
        'implementation_target_id_external': external_id,
        'pre_handoff_scope_checks': target.get('pre_handoff_scope_checks') or [],
        'expected_touch_surfaces': target.get('expected_touch_surfaces') or [],
    }
    sql = f"""
    WITH existing AS (
      SELECT implementation_target_id
      FROM paa.implementation_targets
      WHERE spec_fragment_id = {sql_literal(spec_fragment_id)}::uuid
        AND (
          metadata_json->>'implementation_target_id_external' = {sql_literal(external_id)}
          OR title = {sql_literal(title)}
        )
      ORDER BY created_at ASC
      LIMIT 1
    ), updated AS (
      UPDATE paa.implementation_targets target_row
      SET
        title = {sql_literal(title)},
        current_gap_json = {_json_literal(target.get('current_gap') or [])},
        desired_state_json = {_json_literal(target.get('desired_state') or [])},
        protected_baseline_json = {_json_literal(target.get('protected_baseline') or [])},
        out_of_scope_json = {_json_literal(target.get('out_of_scope_items') or [])},
        risk_level = {sql_literal(target.get('risk_level') or 'medium')}::paa.risk_level,
        status = 'approved',
        metadata_json = {_json_literal(metadata)},
        updated_at = now()
      FROM existing
      WHERE target_row.implementation_target_id = existing.implementation_target_id
      RETURNING target_row.implementation_target_id
    ), inserted AS (
      INSERT INTO paa.implementation_targets (
        spec_fragment_id, title, current_gap_json, desired_state_json, protected_baseline_json,
        out_of_scope_json, risk_level, status, metadata_json
      )
      SELECT
        {sql_literal(spec_fragment_id)}::uuid,
        {sql_literal(title)},
        {_json_literal(target.get('current_gap') or [])},
        {_json_literal(target.get('desired_state') or [])},
        {_json_literal(target.get('protected_baseline') or [])},
        {_json_literal(target.get('out_of_scope_items') or [])},
        {sql_literal(target.get('risk_level') or 'medium')}::paa.risk_level,
        'approved',
        {_json_literal(metadata)}
      WHERE NOT EXISTS (SELECT 1 FROM existing)
      RETURNING implementation_target_id
    )
    SELECT implementation_target_id FROM updated
    UNION ALL
    SELECT implementation_target_id FROM inserted
    LIMIT 1;
    """
    implementation_target_id = _query_scalar(sql)
    if not implementation_target_id:
        raise RuntimeError('failed to resolve implementation target id')
    return implementation_target_id


def _ensure_component(*, project_id: str, package: dict[str, Any]) -> str:
    component_slice = package['component_model_slice']
    node = _node_for_primary_component(package)
    primary_name = component_slice.get('primary_component')
    role = node.get('component_role') or (component_slice.get('component_roles') or [primary_name])[0]
    system_layer = node.get('system_layer') or 'domain-services'
    tier = node.get('tier') or 'runtime'
    metadata = {
        'component_spec_path': package.get('metadata_json', {}).get('component_spec_path'),
        'source_package_id': package.get('package_id'),
    }
    sql = f"""
    INSERT INTO paa.components (
      project_id, name, role, system_layer, tier, description, status, metadata_json
    )
    VALUES (
      {sql_literal(project_id)}::uuid,
      {sql_literal(primary_name)},
      {sql_literal(role)},
      {sql_literal(system_layer)}::paa.system_layer,
      {sql_literal(tier)}::paa.component_tier,
      {sql_literal(role)},
      'active'::paa.component_status,
      {_json_literal(metadata)}
    )
    ON CONFLICT (project_id, name) DO UPDATE SET
      role = EXCLUDED.role,
      system_layer = EXCLUDED.system_layer,
      tier = EXCLUDED.tier,
      description = EXCLUDED.description,
      metadata_json = paa.components.metadata_json || EXCLUDED.metadata_json,
      updated_at = now()
    RETURNING component_id;
    """
    component_id = _query_scalar(sql)
    if not component_id:
        raise RuntimeError(f'failed to resolve component {primary_name}')
    return component_id


def _ensure_work_item(*, project_id: str, authority_version_id: str, spec_fragment_id: str, implementation_target_id: str, package: dict[str, Any]) -> str:
    ctx = package['authority_context']
    issue_number = ctx.get('issue_number')
    task_key = ctx.get('task_id') or (package['spec_fragment'].get('spec_fragment_id'))
    spec_fragment_ref = package['spec_fragment'].get('spec_fragment_id')
    existing_predicate = (
        f"(wi.issue_number = {int(issue_number)} OR wi.spec_fragment_ref = {sql_literal(spec_fragment_ref)})"
        if issue_number is not None
        else f"wi.spec_fragment_ref = {sql_literal(spec_fragment_ref)}"
    )
    sql = f"""
    WITH existing AS (
      SELECT work_item_id
      FROM paa.work_items wi
      WHERE wi.project_id = {sql_literal(project_id)}::uuid
        AND {existing_predicate}
      LIMIT 1
    ), updated AS (
      UPDATE paa.work_items wi
      SET
        authority_version_id = {sql_literal(authority_version_id)}::uuid,
        title = {sql_literal(ctx.get('task_title'))},
        status = 'authorized'::paa.work_item_status,
        merge_policy = 'architect_review_required',
        requires_qa = false,
        issue_number = COALESCE({sql_literal(issue_number)}, wi.issue_number),
        implementation_target_ref = {sql_literal(package['implementation_target'].get('implementation_target_id'))},
        spec_fragment_ref = {sql_literal(spec_fragment_ref)},
        domain_ref = {_json_literal({'task_id': task_key, 'task_title': ctx.get('task_title'), 'milestone_id': ctx.get('milestone_id'), 'phase_id': ctx.get('phase_id'), 'proof_slice': issue_number is None})},
        spec_fragment_id = {sql_literal(spec_fragment_id)}::uuid,
        implementation_target_id = {sql_literal(implementation_target_id)}::uuid,
        updated_at = now()
      WHERE wi.work_item_id IN (SELECT work_item_id FROM existing)
      RETURNING wi.work_item_id
    ), upserted AS (
      INSERT INTO paa.work_items (
        project_id, authority_version_id, title, status, merge_policy, requires_qa, issue_number,
        implementation_target_ref, spec_fragment_ref, domain_ref, spec_fragment_id, implementation_target_id
      )
      SELECT
        {sql_literal(project_id)}::uuid,
        {sql_literal(authority_version_id)}::uuid,
        {sql_literal(ctx.get('task_title'))},
        'authorized'::paa.work_item_status,
        'architect_review_required',
        false,
        {sql_literal(issue_number)},
        {sql_literal(package['implementation_target'].get('implementation_target_id'))},
        {sql_literal(spec_fragment_ref)},
        {_json_literal({'task_id': task_key, 'task_title': ctx.get('task_title'), 'milestone_id': ctx.get('milestone_id'), 'phase_id': ctx.get('phase_id'), 'proof_slice': issue_number is None})},
        {sql_literal(spec_fragment_id)}::uuid,
        {sql_literal(implementation_target_id)}::uuid
      WHERE NOT EXISTS (SELECT 1 FROM existing)
      RETURNING work_item_id
    )
    SELECT work_item_id FROM updated
    UNION ALL
    SELECT work_item_id FROM upserted
    LIMIT 1;
    """
    work_item_id = _query_scalar(sql)
    if not work_item_id:
        raise RuntimeError('failed to resolve work item id')
    return work_item_id


def _ensure_design_package(
    *,
    project_id: str,
    work_item_id: str,
    spec_fragment_id: str,
    implementation_target_id: str,
    authority_version_id: str,
    component_id: str,
    package_path: Path,
    package: dict[str, Any],
    created_by_role_id: str | None,
) -> str:
    provenance = {
        'source_artifact': str(package_path),
        'loader': 'paa-producer derive-design-package',
    }
    metadata = {
        'task_id': package['authority_context'].get('task_id'),
        'issue_number': package['authority_context'].get('issue_number'),
        'execution_mode': package['authority_context'].get('execution_mode') or 'live_delivery',
        'proof_slice': (
            (package['authority_context'].get('execution_mode') == 'proof_only')
            or package['authority_context'].get('issue_number') is None
        ),
    }
    sql = f"""
    INSERT INTO paa.design_packages (
      project_id, work_item_id, spec_fragment_id, implementation_target_id, authority_version_id,
      primary_component_id, package_id_external, schema_version, status, package_json, provenance_json,
      metadata_json, created_by_role_id, created_by_agent_id
    )
    VALUES (
      {sql_literal(project_id)}::uuid,
      {sql_literal(work_item_id)}::uuid,
      {sql_literal(spec_fragment_id)}::uuid,
      {sql_literal(implementation_target_id)}::uuid,
      {sql_literal(authority_version_id)}::uuid,
      {sql_literal(component_id)}::uuid,
      {sql_literal(package.get('package_id'))},
      {sql_literal(package.get('schema_version') or '1.0.0')},
      {sql_literal(package.get('status') or 'approved_for_derivation')}::paa.design_package_status,
      {sql_literal(json.dumps(package))}::jsonb,
      {_json_literal(provenance)},
      {_json_literal(metadata)},
      {sql_literal(created_by_role_id)}::uuid,
      NULL
    )
    ON CONFLICT (project_id, package_id_external) DO UPDATE SET
      work_item_id = EXCLUDED.work_item_id,
      spec_fragment_id = EXCLUDED.spec_fragment_id,
      implementation_target_id = EXCLUDED.implementation_target_id,
      authority_version_id = EXCLUDED.authority_version_id,
      primary_component_id = EXCLUDED.primary_component_id,
      schema_version = EXCLUDED.schema_version,
      status = EXCLUDED.status,
      package_json = EXCLUDED.package_json,
      provenance_json = EXCLUDED.provenance_json,
      metadata_json = EXCLUDED.metadata_json,
      created_by_role_id = COALESCE(EXCLUDED.created_by_role_id, paa.design_packages.created_by_role_id),
      updated_at = now()
    RETURNING design_package_id;
    """
    design_package_id = _query_scalar(sql)
    if not design_package_id:
        raise RuntimeError('failed to resolve design package id')
    return design_package_id


def _ensure_signoffs(*, design_package_id: str, project_id: str, signoff: dict[str, Any]) -> None:
    for role_name, _, _ in STANDARD_SIGNOFF_ROLE_ORDER:
        signer_value = signoff.get(role_name.lower().replace(' ', '_'))
        if signer_value is None and role_name == 'TechLead':
            continue
        sql = f"""
        INSERT INTO paa.design_package_signoffs (
          design_package_id, role_id, signer_name, signoff_status, notes, signed_at, metadata_json
        )
        SELECT
          {sql_literal(design_package_id)}::uuid,
          r.role_id,
          {sql_literal(signer_value)},
          'approved',
          {sql_literal(f'{role_name} approval recorded by paa-producer derive-design-package.')},
          now(),
          '{{}}'::jsonb
        FROM paa.roles r
        WHERE r.project_id = {sql_literal(project_id)}::uuid
          AND r.name = {sql_literal(role_name)}
        ON CONFLICT (design_package_id, role_id) DO UPDATE SET
          signer_name = EXCLUDED.signer_name,
          signoff_status = EXCLUDED.signoff_status,
          notes = EXCLUDED.notes,
          signed_at = EXCLUDED.signed_at,
          metadata_json = EXCLUDED.metadata_json;
        """
        run_psql(sql)


def derive_design_package(
    *,
    package_path: Path,
    schema_path: Path | None = None,
    project_slug: str | None = None,
    project_name: str | None = None,
    repo_root: Path | None = None,
    dry_run: bool = False,
) -> DerivedDesignPackageResult:
    resolved_package_path = package_path.expanduser().resolve()
    resolved_schema_path = _resolve_stage1_schema_path(schema_path)
    package = validate_stage1_design_package(resolved_package_path, resolved_schema_path)
    ctx = package['authority_context']
    resolved_project_slug = project_slug or ctx.get('project_slug') or ctx.get('project_id')
    if not resolved_project_slug:
        raise RuntimeError('stage1 design package must provide authority_context.project_slug or project_id')
    resolved_project_name = project_name or _project_name_from_slug(resolved_project_slug)

    if dry_run:
        return DerivedDesignPackageResult(
            project_slug=resolved_project_slug,
            package_id=package['package_id'],
            package_path=str(resolved_package_path),
            schema_path=str(resolved_schema_path),
            authority_version=ctx['authority_version'],
            project_id=None,
            authority_version_id=None,
            spec_fragment_id=None,
            implementation_target_id=None,
            component_id=None,
            work_item_id=None,
            design_package_id=None,
            dry_run=True,
        )

    project_id = _ensure_project(
        slug=resolved_project_slug,
        name=resolved_project_name,
        repo_url=_git_remote_url(repo_root),
    )
    role_ids = _ensure_roles(project_id=project_id, signoff=package.get('signoff') or {})
    authority_version_id = _ensure_authority_version(
        project_id=project_id,
        version_label=ctx['authority_version'],
        package_path=resolved_package_path,
        repo_root=repo_root,
    )
    spec_fragment_id = _ensure_spec_fragment(project_id=project_id, package=package)
    implementation_target_id = _ensure_implementation_target(spec_fragment_id=spec_fragment_id, package=package)
    component_id = _ensure_component(project_id=project_id, package=package)
    work_item_id = _ensure_work_item(
        project_id=project_id,
        authority_version_id=authority_version_id,
        spec_fragment_id=spec_fragment_id,
        implementation_target_id=implementation_target_id,
        package=package,
    )
    design_package_id = _ensure_design_package(
        project_id=project_id,
        work_item_id=work_item_id,
        spec_fragment_id=spec_fragment_id,
        implementation_target_id=implementation_target_id,
        authority_version_id=authority_version_id,
        component_id=component_id,
        package_path=resolved_package_path,
        package=package,
        created_by_role_id=role_ids.get('Architect'),
    )
    _ensure_signoffs(
        design_package_id=design_package_id,
        project_id=project_id,
        signoff=package.get('signoff') or {},
    )
    return DerivedDesignPackageResult(
        project_slug=resolved_project_slug,
        package_id=package['package_id'],
        package_path=str(resolved_package_path),
        schema_path=str(resolved_schema_path),
        authority_version=ctx['authority_version'],
        project_id=project_id,
        authority_version_id=authority_version_id,
        spec_fragment_id=spec_fragment_id,
        implementation_target_id=implementation_target_id,
        component_id=component_id,
        work_item_id=work_item_id,
        design_package_id=design_package_id,
        dry_run=False,
    )

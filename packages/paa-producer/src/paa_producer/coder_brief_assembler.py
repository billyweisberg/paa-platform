"""Producer-side draft coder-brief assembly for Stage 1 design packages."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

from paa_core.db import query_rows, sql_literal

from paa_producer.derivation_readiness import evaluate_derivation_readiness

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover - dependency guard
    Draft202012Validator = None

DEFAULT_CODER_BRIEF_SCHEMA_CANDIDATES = (
    Path('/Users/billyweisberg/Repos/billyweisberg/paa-platform/schemas/derivation/coder_run_brief.schema.json'),
    Path('/Users/billyweisberg/Repos/Individual-Centricity/appdev/docs/architecture/tom-baby7-fractal-core/handoff-schemas/coder_run_brief.schema.json'),
)


@dataclass(frozen=True)
class AssembledCoderBriefResult:
    project_slug: str
    package_id: str
    brief_id: str
    package_path: str
    schema_path: str
    output_path: str | None
    coder_run_brief_id: str
    design_package_id: str
    work_item_id: str
    authority_state: str
    readiness_class: str
    persisted: bool


def _require_jsonschema() -> None:
    if Draft202012Validator is None:
        raise RuntimeError('jsonschema is required for assemble-coder-brief; install jsonschema in the producer environment')


def _resolve_coder_brief_schema_path(explicit: Path | None = None) -> Path:
    candidates = [explicit] if explicit else []
    candidates.extend(DEFAULT_CODER_BRIEF_SCHEMA_CANDIDATES)
    for candidate in candidates:
        if candidate is None:
            continue
        path = candidate.expanduser().resolve()
        if path.exists():
            return path
    looked = [str(c) for c in candidates if c is not None]
    raise FileNotFoundError(
        'No coder_run_brief schema found. Provide --schema-path or install the schema at one of: ' + ', '.join(looked)
    )


def _slugify(value: str) -> str:
    chars = []
    for ch in value.lower():
        if ch.isalnum():
            chars.append(ch)
        else:
            chars.append('-')
    slug = ''.join(chars)
    while '--' in slug:
        slug = slug.replace('--', '-')
    return slug.strip('-')


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _validate_brief(brief: dict[str, Any], schema_path: Path) -> None:
    _require_jsonschema()
    schema = _load_json(schema_path)
    Draft202012Validator(schema).validate(brief)


def _query_single_row(sql: str) -> list[str] | None:
    rows = query_rows(sql)
    return rows[0] if rows else None


def _query_scalar(sql: str) -> str | None:
    row = _query_single_row(sql)
    return row[0] if row else None


def _load_design_package_json(design_package_id: str) -> dict[str, Any]:
    sql = f"SELECT package_json::text FROM paa.design_packages WHERE design_package_id = {sql_literal(design_package_id)}::uuid LIMIT 1;"
    value = _query_scalar(sql)
    if not value:
        raise RuntimeError(f'No design package JSON found for {design_package_id}')
    return json.loads(value)


def _architect_role_id(project_slug: str) -> str | None:
    sql = f"""
    SELECT r.role_id::text
    FROM paa.roles r
    JOIN paa.projects p ON p.project_id = r.project_id
    WHERE p.slug = {sql_literal(project_slug)}
      AND r.name = 'Architect'
    LIMIT 1;
    """
    return _query_scalar(sql)


def _existing_brief_for_design_package(design_package_id: str) -> tuple[str, str] | None:
    sql = f"""
    SELECT coder_run_brief_id::text, coalesce(brief_id_external, '')
    FROM paa.coder_run_briefs
    WHERE generated_from_json->>'design_package_id' = {sql_literal(design_package_id)}
    ORDER BY created_at DESC
    LIMIT 1;
    """
    row = _query_single_row(sql)
    if row is None:
        return None
    return row[0], row[1]


def _derive_component_aspects(component_assignment: dict[str, Any], target_mappings: set[tuple[str, str]]) -> list[str]:
    aspects: list[str] = []
    if ('interfaces', 'service_interface') in target_mappings:
        aspects.append('interfaces')
    if ('functions', 'service_implementation') in target_mappings:
        aspects.append('functions')
    if any(str(path).endswith('/models.py') for path in component_assignment.get('target_modules', [])):
        aspects.append('data_contract')
    if ('verification_surfaces', 'test_module') in target_mappings:
        aspects.append('tests')
    if not aspects:
        aspects.append('functions')
    return aspects


def _derive_forbidden_surfaces(package: dict[str, Any]) -> list[str]:
    forbidden: list[str] = []
    forbidden_shortcuts = (package.get('architectural_authority_constraints') or {}).get('forbidden_dependency_shortcuts') or []
    out_of_scope = (package.get('spec_fragment') or {}).get('out_of_scope_delta_families') or []
    baseline = (package.get('implementation_target') or {}).get('protected_baseline') or []

    if any('ComponentDesignRepository' in item or 'direct database calls' in item for item in forbidden_shortcuts):
        forbidden.append('packages/paa-core/src/paa_core/repositories/component_design/postgres.py')
    if 'workflow-lifecycle-implementation' in out_of_scope:
        forbidden.append('packages/paa-core/src/paa_core/services/workflow_lifecycle/')
    if 'execution-package-resolution-implementation' in out_of_scope:
        forbidden.append('packages/paa-core/src/paa_core/services/execution_package_resolution/')
    if 'producer-derivation-orchestration' in out_of_scope:
        forbidden.append('packages/paa-producer/src/paa_producer/authority_runtime.py')
    if 'runtime-adoption' in out_of_scope:
        forbidden.append('packages/paa-consumer/src/paa_consumer/')
    if 'repository-sql-expansion' in out_of_scope or any('No workflow, runtime-event, or repository-schema ownership is redefined' in item for item in baseline):
        forbidden.append('migrations/postgres/')
    return forbidden


def _derive_collaboration_context(package: dict[str, Any]) -> dict[str, Any]:
    supporting_components = (package.get('component_model_slice') or {}).get('supporting_components') or []
    repository_callers = [name for name in supporting_components if name.endswith('Repository')]
    logger_callers = [name for name in supporting_components if 'Logger' in name]
    pattern_name = 'repository-backed domain planning service' if repository_callers else 'domain planning service'
    callers = [name for name in supporting_components if name.endswith('Service') or 'host' in name.lower() or 'Orchestration' in name]
    callees = repository_callers + logger_callers
    return {
        'pattern_name': pattern_name,
        'collaborating_components': supporting_components,
        'callers': callers,
        'callees': callees,
        'event_emitters': [],
        'event_consumers': [],
    }


def _derive_dependency_contract(package: dict[str, Any], collaboration_context: dict[str, Any]) -> dict[str, Any]:
    supporting_components = (package.get('component_model_slice') or {}).get('supporting_components') or []
    deps = [name for name in supporting_components if name.endswith('Repository') or 'Logger' in name]
    forbidden = (package.get('architectural_authority_constraints') or {}).get('forbidden_dependency_shortcuts') or []
    runtime_inputs = [
        'component identity',
        'component element records',
        'allowed realization type mappings',
        'current realization instances',
    ]
    if 'Brief Assembly Service' in collaboration_context.get('callers', []):
        runtime_inputs.append('optional coder brief realization target context')
    return {
        'dependencies_to_inject': deps,
        'runtime_inputs': runtime_inputs,
        'configuration_inputs': ['repository wiring', 'logging wiring'],
        'forbidden_hidden_dependencies': forbidden,
    }


def _derive_behavioral_contract(package: dict[str, Any]) -> dict[str, Any]:
    requirements = (package.get('requirement_set') or {}).get('requirements') or []
    decisions = (package.get('design_decision_set') or {}).get('design_decisions') or []
    protected = (package.get('product_and_source_basis') or {}).get('protected_product_truths') or []
    canonical = (package.get('spec_fragment') or {}).get('canonical_statement')
    behavior = [canonical] if canonical else []
    behavior.extend(requirements)
    invariants = protected or [
        'The slice stays within the approved package boundary.',
    ]
    return {
        'behavior_to_add_or_change': behavior,
        'invariants_to_preserve': invariants,
        'edge_cases': decisions,
        'error_conditions': [
            'Repository lookup fails or returns ambiguous component identity.',
            'Controlled target taxonomy needed for planning is missing.',
            'Required persisted slice records are unavailable during draft assembly.',
        ],
    }


def _derive_test_contract(package: dict[str, Any], primary_surfaces: list[str]) -> dict[str, Any]:
    target = package.get('implementation_target') or {}
    tests_to_add = [surface for surface in primary_surfaces if 'test' in surface.lower()]
    component_slug = _slugify((package.get('component_model_slice') or {}).get('primary_component') or 'component')
    tests_to_run = [
        f"PYTHONPATH=packages/paa-core/src python -m unittest discover -s tests/unit -p 'test_{component_slug.replace('-', '_')}*.py'"
    ]
    artifacts_expected = []
    if any(surface.endswith('contracts.py') for surface in primary_surfaces):
        artifacts_expected.append('service interface contract')
    if any(surface.endswith('models.py') for surface in primary_surfaces):
        artifacts_expected.append('service planning models')
    if any(surface.endswith('default.py') for surface in primary_surfaces):
        artifacts_expected.append('default service implementation')
    if tests_to_add:
        artifacts_expected.append('unit tests')
    return {
        'tests_to_run': tests_to_run,
        'tests_to_add_or_update': tests_to_add,
        'protected_baseline_checks': target.get('protected_baseline') or [],
        'artifacts_expected': artifacts_expected,
    }


def _derive_execution_prerequisites(readiness: dict[str, Any], package: dict[str, Any], primary_surfaces: list[str]) -> dict[str, Any]:
    notes = []
    notes.append('Stage 1 package materialized and passed derivation-readiness evaluation.')
    notes.extend((package.get('implementation_target') or {}).get('pre_handoff_scope_checks') or [])
    return {
        'prerequisite_briefs': [],
        'blocking_dependency_edges': [],
        'parallel_safe_with': [],
        'shared_surface_conflicts': [str(Path(surface).parent) for surface in primary_surfaces if '/services/' in surface][:1],
        'sequencing_notes': notes,
    }


def _derive_execution_readiness(readiness: dict[str, Any]) -> dict[str, Any]:
    checks = readiness['checks']
    passing_dependency_checks = []
    for check in checks:
        if check['status'] == 'pass' and check['check_id'] in {
            'package_materialized_in_db',
            'required_db_bindings_present',
            'required_signoffs_approved_in_db',
            'service_slice_realization_types_present',
            'service_slice_element_mappings_present',
        }:
            passing_dependency_checks.append({
                'dependency_edge_id': check['check_id'],
                'status': 'implementation_ready',
                'notes': check['message'],
            })
    return {
        'readiness_class': readiness['readiness_class'],
        'dependency_readiness': passing_dependency_checks,
        'blocking_causes': readiness['blockers'],
        'parallel_group_id': None,
        'recommended_next_owner': 'Authority Architect' if readiness['ready'] else 'Architect',
        'readiness_snapshot_source': 'paa-producer evaluate-derivation-readiness',
    }


def _load_target_model_mappings() -> set[tuple[str, str]]:
    sql = """
    SELECT cet.element_key, cert.realization_key
    FROM paa.component_element_type_realization_types m
    JOIN paa.component_element_types cet
      ON cet.component_element_type_id = m.component_element_type_id
    JOIN paa.component_element_realization_types cert
      ON cert.component_element_realization_type_id = m.component_element_realization_type_id;
    """
    return {(row[0], row[1]) for row in query_rows(sql)}


def _build_brief(
    *,
    package: dict[str, Any],
    readiness: dict[str, Any],
    existing_brief_id: str | None,
) -> dict[str, Any]:
    ctx = package['authority_context']
    spec_fragment = package['spec_fragment']
    target = package['implementation_target']
    component_slice = package['component_model_slice']
    primary_component = component_slice['primary_component']
    node = next(
        (node for node in (package.get('dependency_graph_slice') or {}).get('nodes', []) if node.get('component_name') == primary_component),
        {},
    )
    primary_surfaces = (package.get('component_surfaces') or {}).get('primary_surfaces') or target.get('expected_touch_surfaces') or []
    target_mappings = _load_target_model_mappings()
    brief_id = existing_brief_id or (
        f"{readiness['project_slug']}-coder-{ctx['authority_version']}-{_slugify(ctx['task_id'])}-draft"
    )
    collaboration = _derive_collaboration_context(package)
    component_assignment = {
        'component_name': primary_component,
        'component_role': node.get('component_role') or primary_component,
        'system_layer': node.get('system_layer') or 'domain-services',
        'tier': node.get('tier') or 'runtime',
        'component_aspects': _derive_component_aspects({'target_modules': primary_surfaces}, target_mappings),
        'target_modules': primary_surfaces,
    }
    brief = {
        'brief_id': brief_id,
        'schema_type': 'coder_run_brief',
        'schema_version': '1.1.0',
        'project': readiness['project_slug'],
        'authority_context': {
            'authority_version': ctx['authority_version'],
            'milestone_id': ctx.get('milestone_id'),
            'phase_id': ctx.get('phase_id'),
            'task_id': ctx.get('task_id'),
            'issue_number': ctx.get('issue_number'),
            'pr_number': None,
        },
        'slice_scope_ref': {
            'slice_name': spec_fragment.get('spec_fragment_title', '').lower(),
            'authorized_delta_family': spec_fragment.get('authorized_delta_family'),
            'out_of_scope_delta_families': spec_fragment.get('out_of_scope_delta_families') or [],
        },
        'component_assignment': component_assignment,
        'architecture_constraints': {
            'required_architecture_seams': (package.get('architectural_authority_constraints') or {}).get('required_architecture_seams') or [],
            'target_module_boundaries': (package.get('architectural_authority_constraints') or {}).get('target_module_boundaries') or [],
            'allowed_edit_surfaces': primary_surfaces,
            'forbidden_edit_surfaces': _derive_forbidden_surfaces(package),
            'forbidden_module_growth_patterns': (package.get('architectural_authority_constraints') or {}).get('forbidden_module_growth_patterns') or [],
        },
        'collaboration_context': collaboration,
        'execution_prerequisites': _derive_execution_prerequisites(readiness, package, primary_surfaces),
        'dependency_contract': _derive_dependency_contract(package, collaboration),
        'behavioral_contract': _derive_behavioral_contract(package),
        'test_contract': _derive_test_contract(package, primary_surfaces),
        'execution_readiness': _derive_execution_readiness(readiness),
        'change_budget': {
            'max_responsibility_expansion': (package.get('architectural_authority_constraints') or {}).get('max_responsibility_expansion'),
            'expected_touch_surfaces': target.get('expected_touch_surfaces') or [],
            'pre_handoff_scope_checks': target.get('pre_handoff_scope_checks') or [],
        },
        'anti_goals': {
            'anti_goals': (package.get('architectural_authority_constraints') or {}).get('architectural_anti_goals') or [],
            'common_failure_modes': (package.get('architectural_authority_constraints') or {}).get('forbidden_module_growth_patterns') or [],
        },
    }
    return brief


def _upsert_coder_brief(*, readiness: dict[str, Any], brief: dict[str, Any], output_path: Path | None) -> str:
    role_id = _architect_role_id(readiness['project_slug'])
    design_package_id = readiness['design_package_id']
    existing = _existing_brief_for_design_package(design_package_id)
    coder_run_brief_id = existing[0] if existing else None
    brief_id_external = existing[1] if existing and existing[1] else brief['brief_id']
    brief['brief_id'] = brief_id_external
    output_literal = sql_literal(str(output_path)) if output_path else 'NULL'
    sql = f"""
    WITH existing AS (
      SELECT coder_run_brief_id
      FROM paa.coder_run_briefs
      WHERE generated_from_json->>'design_package_id' = {sql_literal(design_package_id)}
      ORDER BY created_at DESC
      LIMIT 1
    ), updated AS (
      UPDATE paa.coder_run_briefs cb
      SET
        work_item_id = {sql_literal(readiness['work_item_id'])}::uuid,
        spec_fragment_id = {sql_literal(readiness['spec_fragment_id'])}::uuid,
        implementation_target_id = {sql_literal(readiness['implementation_target_id'])}::uuid,
        authority_version_id = {sql_literal(readiness['authority_version_id'])}::uuid,
        primary_component_id = {sql_literal(readiness['component_id'])}::uuid,
        brief_id_external = {sql_literal(brief_id_external)},
        schema_version = {sql_literal(brief['schema_version'])},
        status = 'draft'::paa.coder_brief_status,
        slice_scope_ref_json = {sql_literal(json.dumps(brief['slice_scope_ref']))}::jsonb,
        component_assignment_json = {sql_literal(json.dumps(brief['component_assignment']))}::jsonb,
        architecture_constraints_json = {sql_literal(json.dumps(brief['architecture_constraints']))}::jsonb,
        collaboration_context_json = {sql_literal(json.dumps(brief['collaboration_context']))}::jsonb,
        dependency_contract_json = {sql_literal(json.dumps(brief['dependency_contract']))}::jsonb,
        behavioral_contract_json = {sql_literal(json.dumps(brief['behavioral_contract']))}::jsonb,
        test_contract_json = {sql_literal(json.dumps(brief['test_contract']))}::jsonb,
        change_budget_json = {sql_literal(json.dumps(brief['change_budget']))}::jsonb,
        anti_goals_json = {sql_literal(json.dumps(brief['anti_goals']))}::jsonb,
        brief_json = {sql_literal(json.dumps(brief))}::jsonb,
        generated_from_json = {sql_literal(json.dumps({
            'design_package_id': design_package_id,
            'design_package_id_external': readiness['package_id'],
            'readiness_class': readiness['readiness_class'],
            'assembler': 'paa-producer assemble-coder-brief',
            'source_design_package_artifact': readiness['package_path'],
        }))}::jsonb,
        metadata_json = {sql_literal(json.dumps({
            'output_path': str(output_path) if output_path else None,
            'evaluation_mode': readiness['evaluation_mode'],
        }))}::jsonb,
        created_by_role_id = {sql_literal(role_id)}::uuid,
        authority_state = 'draft_brief'::paa.coder_brief_authority_state,
        authority_state_updated_at = now(),
        updated_at = now()
      FROM existing
      WHERE cb.coder_run_brief_id = existing.coder_run_brief_id
      RETURNING cb.coder_run_brief_id
    ), inserted AS (
      INSERT INTO paa.coder_run_briefs (
        project_id, work_item_id, spec_fragment_id, implementation_target_id, authority_version_id, primary_component_id,
        brief_id_external, schema_version, status, slice_scope_ref_json, component_assignment_json, architecture_constraints_json,
        collaboration_context_json, dependency_contract_json, behavioral_contract_json, test_contract_json, change_budget_json,
        anti_goals_json, brief_json, generated_from_json, metadata_json, created_by_role_id,
        authority_state, authority_state_updated_at
      )
      SELECT
        p.project_id,
        {sql_literal(readiness['work_item_id'])}::uuid,
        {sql_literal(readiness['spec_fragment_id'])}::uuid,
        {sql_literal(readiness['implementation_target_id'])}::uuid,
        {sql_literal(readiness['authority_version_id'])}::uuid,
        {sql_literal(readiness['component_id'])}::uuid,
        {sql_literal(brief_id_external)},
        {sql_literal(brief['schema_version'])},
        'draft'::paa.coder_brief_status,
        {sql_literal(json.dumps(brief['slice_scope_ref']))}::jsonb,
        {sql_literal(json.dumps(brief['component_assignment']))}::jsonb,
        {sql_literal(json.dumps(brief['architecture_constraints']))}::jsonb,
        {sql_literal(json.dumps(brief['collaboration_context']))}::jsonb,
        {sql_literal(json.dumps(brief['dependency_contract']))}::jsonb,
        {sql_literal(json.dumps(brief['behavioral_contract']))}::jsonb,
        {sql_literal(json.dumps(brief['test_contract']))}::jsonb,
        {sql_literal(json.dumps(brief['change_budget']))}::jsonb,
        {sql_literal(json.dumps(brief['anti_goals']))}::jsonb,
        {sql_literal(json.dumps(brief))}::jsonb,
        {sql_literal(json.dumps({
            'design_package_id': design_package_id,
            'design_package_id_external': readiness['package_id'],
            'readiness_class': readiness['readiness_class'],
            'assembler': 'paa-producer assemble-coder-brief',
            'source_design_package_artifact': readiness['package_path'],
        }))}::jsonb,
        {sql_literal(json.dumps({
            'output_path': str(output_path) if output_path else None,
            'evaluation_mode': readiness['evaluation_mode'],
        }))}::jsonb,
        {sql_literal(role_id)}::uuid,
        'draft_brief'::paa.coder_brief_authority_state,
        now()
      FROM paa.projects p
      WHERE p.slug = {sql_literal(readiness['project_slug'])}
        AND NOT EXISTS (SELECT 1 FROM existing)
      RETURNING coder_run_brief_id
    ), resolved AS (
      SELECT coder_run_brief_id FROM updated
      UNION ALL
      SELECT coder_run_brief_id FROM inserted
      LIMIT 1
    ), event_insert AS (
      INSERT INTO paa.coder_brief_authority_events (
        project_id, work_item_id, coder_run_brief_id, from_state, to_state, transition_kind, actor_role_id, actor_name, notes, evidence_json
      )
      SELECT
        p.project_id,
        {sql_literal(readiness['work_item_id'])}::uuid,
        r.coder_run_brief_id,
        NULL,
        'draft_brief'::paa.coder_brief_authority_state,
        'derive_draft'::paa.coder_brief_authority_transition_kind,
        {sql_literal(role_id)}::uuid,
        'Billy Weisberg - Architect',
        'Draft coder brief assembled by paa-producer assemble-coder-brief.',
        jsonb_build_object(
          'design_package_id', {sql_literal(design_package_id)},
          'package_id_external', {sql_literal(readiness['package_id'])},
          'output_path', {output_literal}
        )
      FROM resolved r
      JOIN paa.projects p ON p.slug = {sql_literal(readiness['project_slug'])}
      WHERE NOT EXISTS (
        SELECT 1
        FROM paa.coder_brief_authority_events e
        WHERE e.coder_run_brief_id = r.coder_run_brief_id
          AND e.transition_kind = 'derive_draft'::paa.coder_brief_authority_transition_kind
      )
      RETURNING coder_brief_authority_event_id
    )
    SELECT coder_run_brief_id::text FROM resolved;
    """
    result = _query_scalar(sql)
    if not result:
        raise RuntimeError('failed to persist coder brief')
    return result


def assemble_coder_brief(
    *,
    package_path: Path,
    package_schema_path: Path | None = None,
    brief_schema_path: Path | None = None,
    project_slug: str | None = None,
    output_path: Path | None = None,
    persist_db: bool = True,
) -> AssembledCoderBriefResult:
    readiness = asdict(
        evaluate_derivation_readiness(
            package_path=package_path,
            schema_path=package_schema_path,
            project_slug=project_slug,
        )
    )
    if not readiness['ready']:
        raise RuntimeError('derivation readiness failed; resolve blockers before assembling a coder brief')

    package = _load_design_package_json(readiness['design_package_id'])
    existing = _existing_brief_for_design_package(readiness['design_package_id'])
    brief = _build_brief(package=package, readiness=readiness, existing_brief_id=existing[1] if existing else None)
    resolved_brief_schema = _resolve_coder_brief_schema_path(brief_schema_path)
    _validate_brief(brief, resolved_brief_schema)

    resolved_output_path = output_path.expanduser().resolve() if output_path else None
    if resolved_output_path is not None:
        resolved_output_path.parent.mkdir(parents=True, exist_ok=True)
        resolved_output_path.write_text(json.dumps(brief, indent=2) + '\n')

    coder_run_brief_id = existing[0] if existing else ''
    if persist_db:
        coder_run_brief_id = _upsert_coder_brief(readiness=readiness, brief=brief, output_path=resolved_output_path)

    return AssembledCoderBriefResult(
        project_slug=readiness['project_slug'],
        package_id=readiness['package_id'],
        brief_id=brief['brief_id'],
        package_path=readiness['package_path'],
        schema_path=str(resolved_brief_schema),
        output_path=str(resolved_output_path) if resolved_output_path else None,
        coder_run_brief_id=coder_run_brief_id,
        design_package_id=readiness['design_package_id'],
        work_item_id=readiness['work_item_id'],
        authority_state='draft_brief',
        readiness_class=readiness['readiness_class'],
        persisted=persist_db,
    )

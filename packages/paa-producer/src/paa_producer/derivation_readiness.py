"""Producer-side derivation-readiness evaluation for Stage 1 design packages."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from paa_core.db import query_rows, sql_literal

from paa_producer.design_package_deriver import _resolve_stage1_schema_path, validate_stage1_design_package


SIGNOFF_KEY_TO_ROLE = {
    'architect': 'Architect',
    'product_owner': 'Product Owner',
    'project_designer': 'Project Designer',
    'techlead': 'TechLead',
}

SERVICE_SLICE_REQUIRED_REALIZATION_TYPES = (
    'service_interface',
    'service_implementation',
    'test_module',
    'package_export',
)

SERVICE_SLICE_REQUIRED_ELEMENT_MAPPINGS = (
    ('interfaces', 'service_interface'),
    ('functions', 'service_implementation'),
    ('verification_surfaces', 'test_module'),
    ('interfaces', 'package_export'),
)


@dataclass(frozen=True)
class ReadinessCheck:
    check_id: str
    status: str
    severity: str
    message: str
    evidence: dict[str, Any]


@dataclass(frozen=True)
class DerivationReadinessResult:
    project_slug: str
    package_id: str
    package_path: str
    schema_path: str
    design_package_id: str | None
    work_item_id: str | None
    authority_version_id: str | None
    spec_fragment_id: str | None
    implementation_target_id: str | None
    component_id: str | None
    primary_component_name: str | None
    readiness_class: str
    ready: bool
    blockers: list[str]
    warnings: list[str]
    checks: list[dict[str, Any]]
    recommendations: list[str]
    evaluation_mode: str


def _check(*, check_id: str, passed: bool, message: str, evidence: dict[str, Any], severity: str = 'blocker') -> ReadinessCheck:
    return ReadinessCheck(
        check_id=check_id,
        status='pass' if passed else 'fail',
        severity=severity,
        message=message,
        evidence=evidence,
    )


def _required_signoff_roles(package: dict[str, Any]) -> list[str]:
    required = {'Architect'}
    if package.get('product_and_source_basis') or package.get('requirement_set'):
        required.add('Product Owner')
    if package.get('component_model_slice') or package.get('dependency_graph_slice'):
        required.add('Project Designer')
    target = package.get('implementation_target') or {}
    if target.get('expected_touch_surfaces') or target.get('pre_handoff_scope_checks') or target.get('risk_level'):
        required.add('TechLead')
    return sorted(required)


def _artifact_signoff_roles(package: dict[str, Any]) -> set[str]:
    signoff = package.get('signoff') or {}
    roles: set[str] = set()
    for key, role_name in SIGNOFF_KEY_TO_ROLE.items():
        if signoff.get(key):
            roles.add(role_name)
    return roles


def _query_single_row(sql: str) -> list[str] | None:
    rows = query_rows(sql)
    return rows[0] if rows else None


def _load_design_package_binding(project_slug: str, package_id: str) -> dict[str, Any] | None:
    sql = f"""
    SELECT
      dp.design_package_id,
      dp.work_item_id,
      dp.spec_fragment_id,
      dp.implementation_target_id,
      dp.authority_version_id,
      dp.primary_component_id,
      dp.status::text,
      coalesce(wi.status::text, ''),
      coalesce(c.name, ''),
      coalesce(av.version_label, ''),
      coalesce(sf.delta_family, ''),
      coalesce(dp.package_json::text, '{{}}')
    FROM paa.design_packages dp
    JOIN paa.projects p ON p.project_id = dp.project_id
    LEFT JOIN paa.work_items wi ON wi.work_item_id = dp.work_item_id
    LEFT JOIN paa.components c ON c.component_id = dp.primary_component_id
    LEFT JOIN paa.authority_versions av ON av.authority_version_id = dp.authority_version_id
    LEFT JOIN paa.spec_fragments sf ON sf.spec_fragment_id = dp.spec_fragment_id
    WHERE p.slug = {sql_literal(project_slug)}
      AND dp.package_id_external = {sql_literal(package_id)}
    ORDER BY dp.created_at DESC
    LIMIT 1;
    """
    row = _query_single_row(sql)
    if row is None:
        return None
    return {
        'design_package_id': row[0],
        'work_item_id': row[1],
        'spec_fragment_id': row[2],
        'implementation_target_id': row[3],
        'authority_version_id': row[4],
        'component_id': row[5],
        'design_package_status': row[6],
        'work_item_status': row[7] or None,
        'primary_component_name': row[8] or None,
        'authority_version': row[9] or None,
        'delta_family': row[10] or None,
        'package_json': row[11],
    }


def _load_signoff_rows(design_package_id: str) -> dict[str, dict[str, Any]]:
    sql = f"""
    SELECT r.name, s.signoff_status, coalesce(s.signer_name, ''), coalesce(s.notes, '')
    FROM paa.design_package_signoffs s
    JOIN paa.roles r ON r.role_id = s.role_id
    WHERE s.design_package_id = {sql_literal(design_package_id)}::uuid
    ORDER BY r.sort_order, r.name;
    """
    rows = {}
    for role_name, signoff_status, signer_name, notes in query_rows(sql):
        rows[role_name] = {
            'signoff_status': signoff_status,
            'signer_name': signer_name or None,
            'notes': notes or None,
        }
    return rows


def _load_realization_type_keys() -> set[str]:
    sql = "SELECT realization_key FROM paa.component_element_realization_types ORDER BY sort_order, realization_key;"
    return {row[0] for row in query_rows(sql)}


def _load_element_realization_mappings() -> set[tuple[str, str]]:
    sql = """
    SELECT cet.element_key, cert.realization_key
    FROM paa.component_element_type_realization_types m
    JOIN paa.component_element_types cet
      ON cet.component_element_type_id = m.component_element_type_id
    JOIN paa.component_element_realization_types cert
      ON cert.component_element_realization_type_id = m.component_element_realization_type_id;
    """
    return {(row[0], row[1]) for row in query_rows(sql)}


def _has_brief_lifecycle_support() -> bool:
    sql = """
    SELECT
      EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'paa'
          AND table_name = 'coder_run_briefs'
          AND column_name = 'authority_state'
      )::text,
      EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'paa'
          AND table_name = 'coder_run_briefs'
          AND column_name = 'packet_ready_at'
      )::text,
      EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'paa'
          AND table_name = 'coder_brief_authority_events'
      )::text;
    """
    row = _query_single_row(sql)
    if row is None:
        return False
    return all(value in {'t', 'true', 'True'} for value in row)


def _target_model_checks(package: dict[str, Any]) -> list[ReadinessCheck]:
    fragment_kind = (package.get('spec_fragment') or {}).get('fragment_kind')
    if fragment_kind != 'service-implementation':
        return []

    available_types = _load_realization_type_keys()
    mappings = _load_element_realization_mappings()

    missing_types = sorted(set(SERVICE_SLICE_REQUIRED_REALIZATION_TYPES) - available_types)
    missing_mappings = sorted(set(SERVICE_SLICE_REQUIRED_ELEMENT_MAPPINGS) - mappings)

    return [
        _check(
            check_id='service_slice_realization_types_present',
            passed=not missing_types,
            message='Service-oriented realization types required for derivation are present.' if not missing_types else 'Required service-oriented realization types are missing.',
            evidence={
                'required_realization_types': list(SERVICE_SLICE_REQUIRED_REALIZATION_TYPES),
                'missing_realization_types': missing_types,
            },
        ),
        _check(
            check_id='service_slice_element_mappings_present',
            passed=not missing_mappings,
            message='Required component-element to realization mappings are present.' if not missing_mappings else 'Required component-element to realization mappings are missing.',
            evidence={
                'required_mappings': [list(pair) for pair in SERVICE_SLICE_REQUIRED_ELEMENT_MAPPINGS],
                'missing_mappings': [list(pair) for pair in missing_mappings],
            },
        ),
    ]


def evaluate_derivation_readiness(
    *,
    package_path: Path,
    schema_path: Path | None = None,
    project_slug: str | None = None,
) -> DerivationReadinessResult:
    resolved_package_path = package_path.expanduser().resolve()
    resolved_schema_path = _resolve_stage1_schema_path(schema_path)
    package = validate_stage1_design_package(resolved_package_path, resolved_schema_path)

    ctx = package['authority_context']
    resolved_project_slug = project_slug or ctx.get('project_slug') or ctx.get('project_id')
    if not resolved_project_slug:
        raise RuntimeError('stage1 design package must provide authority_context.project_slug or project_id')

    checks: list[ReadinessCheck] = []

    checks.append(_check(
        check_id='package_status_approved_for_derivation',
        passed=package.get('status') == 'approved_for_derivation',
        message='Stage 1 package status is approved_for_derivation.' if package.get('status') == 'approved_for_derivation' else 'Stage 1 package status is not approved_for_derivation.',
        evidence={'package_status': package.get('status')},
    ))

    primary_component = (package.get('component_model_slice') or {}).get('primary_component')
    checks.append(_check(
        check_id='primary_component_assigned',
        passed=bool(primary_component),
        message='Exactly one primary component is assigned.' if primary_component else 'Primary component assignment is missing.',
        evidence={'primary_component': primary_component},
    ))

    expected_touch_surfaces = (package.get('implementation_target') or {}).get('expected_touch_surfaces') or []
    checks.append(_check(
        check_id='expected_touch_surfaces_named',
        passed=bool(expected_touch_surfaces),
        message='Expected touch surfaces are named.' if expected_touch_surfaces else 'Expected touch surfaces are missing.',
        evidence={'expected_touch_surfaces': expected_touch_surfaces},
    ))

    out_of_scope = (package.get('spec_fragment') or {}).get('out_of_scope_delta_families') or []
    checks.append(_check(
        check_id='out_of_scope_delta_families_named',
        passed=bool(out_of_scope),
        message='Out-of-scope delta families are named.' if out_of_scope else 'Out-of-scope delta families are missing.',
        evidence={'out_of_scope_delta_families': out_of_scope},
    ))

    primary_surfaces = (package.get('component_surfaces') or {}).get('primary_surfaces') or []
    checks.append(_check(
        check_id='component_surfaces_mapped',
        passed=bool(primary_surfaces),
        message='Primary component surfaces are mapped to concrete files.' if primary_surfaces else 'Primary component surfaces are not mapped.',
        evidence={'primary_surfaces': primary_surfaces},
    ))

    architecture_seams = (package.get('architectural_authority_constraints') or {}).get('required_architecture_seams') or []
    checks.append(_check(
        check_id='architecture_seams_explicit',
        passed=bool(architecture_seams),
        message='Required architecture seams are explicit.' if architecture_seams else 'Required architecture seams are missing.',
        evidence={'required_architecture_seams': architecture_seams},
    ))

    protected_baseline = (package.get('implementation_target') or {}).get('protected_baseline') or []
    checks.append(_check(
        check_id='protected_baseline_named',
        passed=bool(protected_baseline),
        message='Protected baseline checks are named.' if protected_baseline else 'Protected baseline checks are missing.',
        evidence={'protected_baseline': protected_baseline},
    ))

    required_roles = _required_signoff_roles(package)
    artifact_roles = _artifact_signoff_roles(package)
    missing_artifact_roles = sorted(set(required_roles) - artifact_roles)
    checks.append(_check(
        check_id='required_signoff_roles_declared',
        passed=not missing_artifact_roles,
        message='All required signoff roles are declared in the package artifact.' if not missing_artifact_roles else 'The package artifact is missing required signoff role declarations.',
        evidence={
            'required_signoff_roles': required_roles,
            'declared_signoff_roles': sorted(artifact_roles),
            'missing_signoff_roles': missing_artifact_roles,
        },
    ))

    binding = _load_design_package_binding(resolved_project_slug, package['package_id'])
    checks.append(_check(
        check_id='package_materialized_in_db',
        passed=binding is not None,
        message='Stage 1 package is materialized in DB.' if binding is not None else 'Stage 1 package is not materialized in DB.',
        evidence={'project_slug': resolved_project_slug, 'package_id': package['package_id']},
    ))

    signoff_rows: dict[str, dict[str, Any]] = {}
    if binding is not None:
        checks.append(_check(
            check_id='package_db_status_matches',
            passed=binding['design_package_status'] == package.get('status'),
            message='Persisted package status matches the artifact.' if binding['design_package_status'] == package.get('status') else 'Persisted package status does not match the artifact.',
            evidence={'artifact_status': package.get('status'), 'db_status': binding['design_package_status']},
        ))
        checks.append(_check(
            check_id='required_db_bindings_present',
            passed=all(binding[key] for key in ('work_item_id', 'authority_version_id', 'spec_fragment_id', 'implementation_target_id', 'component_id')),
            message='All required persisted slice bindings are present.' if all(binding[key] for key in ('work_item_id', 'authority_version_id', 'spec_fragment_id', 'implementation_target_id', 'component_id')) else 'One or more required persisted slice bindings are missing.',
            evidence={key: binding[key] for key in ('work_item_id', 'authority_version_id', 'spec_fragment_id', 'implementation_target_id', 'component_id')},
        ))
        checks.append(_check(
            check_id='primary_component_alignment',
            passed=binding['primary_component_name'] == primary_component,
            message='Persisted primary component matches the artifact.' if binding['primary_component_name'] == primary_component else 'Persisted primary component does not match the artifact.',
            evidence={'artifact_primary_component': primary_component, 'db_primary_component': binding['primary_component_name']},
        ))
        checks.append(_check(
            check_id='work_item_authorized',
            passed=binding['work_item_status'] == 'authorized',
            message='Persisted work item is authorized.' if binding['work_item_status'] == 'authorized' else 'Persisted work item is not in authorized state.',
            evidence={'work_item_status': binding['work_item_status']},
        ))
        signoff_rows = _load_signoff_rows(binding['design_package_id'])
        missing_approved_roles = sorted(
            role for role in required_roles if signoff_rows.get(role, {}).get('signoff_status') != 'approved'
        )
        checks.append(_check(
            check_id='required_signoffs_approved_in_db',
            passed=not missing_approved_roles,
            message='All required signoffs are approved in DB.' if not missing_approved_roles else 'One or more required signoffs are not approved in DB.',
            evidence={
                'required_signoff_roles': required_roles,
                'db_signoffs': signoff_rows,
                'missing_approved_roles': missing_approved_roles,
            },
        ))

    checks.extend(_target_model_checks(package))

    checks.append(_check(
        check_id='brief_authority_lifecycle_support_present',
        passed=_has_brief_lifecycle_support(),
        message='Brief authority lifecycle support is present in DB.' if _has_brief_lifecycle_support() else 'Brief authority lifecycle support is missing in DB.',
        evidence={'required_support': ['coder_run_briefs.authority_state', 'coder_run_briefs.packet_ready_at', 'paa.coder_brief_authority_events']},
    ))

    blocker_messages = [check.message for check in checks if check.status == 'fail' and check.severity == 'blocker']
    warning_messages = [check.message for check in checks if check.status == 'fail' and check.severity == 'warning']

    readiness_class = 'derivation_ready' if not blocker_messages else 'not_derivation_ready'
    recommendations: list[str] = []
    if blocker_messages:
        recommendations.append('Resolve failed derivation-entry checks before assembling or approving a coder brief.')
    if any(check.check_id == 'package_materialized_in_db' and check.status == 'fail' for check in checks):
        recommendations.append('Run paa-producer derive-design-package for this slice before continuing derivation.')
    if any(check.check_id.startswith('service_slice_') and check.status == 'fail' for check in checks):
        recommendations.append('Extend or repair the service-oriented target taxonomy before deriving service-slice brief targets.')
    if any(check.check_id == 'required_signoffs_approved_in_db' and check.status == 'fail' for check in checks):
        recommendations.append('Complete or repair required design-package signoffs before moving to brief assembly.')
    if not recommendations:
        recommendations.append('Slice is structurally ready for the next producer-side derivation step.')

    return DerivationReadinessResult(
        project_slug=resolved_project_slug,
        package_id=package['package_id'],
        package_path=str(resolved_package_path),
        schema_path=str(resolved_schema_path),
        design_package_id=binding['design_package_id'] if binding else None,
        work_item_id=binding['work_item_id'] if binding else None,
        authority_version_id=binding['authority_version_id'] if binding else None,
        spec_fragment_id=binding['spec_fragment_id'] if binding else None,
        implementation_target_id=binding['implementation_target_id'] if binding else None,
        component_id=binding['component_id'] if binding else None,
        primary_component_name=primary_component,
        readiness_class=readiness_class,
        ready=not blocker_messages,
        blockers=blocker_messages,
        warnings=warning_messages,
        checks=[asdict(check) for check in checks],
        recommendations=recommendations,
        evaluation_mode='evaluation_only',
    )

"""Generic producer-side component-spec materialization."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from paa_core.db import run_psql, sql_literal
from paa_core.governance.component_spec_materialization import (
    ComponentSpecMaterializationSeed,
    extract_component_spec_materialization_seed,
)
from paa_core.repositories.component_design import (
    ComponentElementRealizationUpsertSpec,
    ComponentElementUpsertSpec,
    PostgresComponentDesignRepository,
)
from paa_core.repositories.implementation_plan import (
    ImplementationPlanActivityDependencyUpsertSpec,
    ImplementationPlanActivityUpsertSpec,
    ImplementationPlanRecord,
    ImplementationPlanUpsertSpec,
    PostgresImplementationPlanRepository,
)

DEFAULT_PROJECT_SLUG = 'paa-platform'
DEFAULT_ANCHOR_DESIGN_PACKAGE_EXTERNAL = 'paa-stage1-2026-05-16-component-design-planning-service'
DEFAULT_ANCHOR_CONSUMER_CONTEXT_KEY = 'python'

_ELEMENT_TYPE_KEY_BY_KIND = {
    'interface': 'interfaces',
    'dto': 'data_contract',
    'implementation': 'functions',
    'verification-surface': 'verification_surfaces',
}

_ACTIVITY_KIND_BY_SPEC_KIND = {
    'contract-authoring': 'artifact_construction',
    'dto-materialization': 'artifact_construction',
    'service-implementation': 'artifact_construction',
    'verification': 'verification',
}

_SEQUENCING_REQUIREMENT_BY_SPEC_KIND = {
    'hard': 'must_precede',
}

_DEPENDENCY_STRENGTH_BY_SPEC_KIND = {
    'hard': 'hard',
}


@dataclass(frozen=True)
class MaterializedComponentSpecResult:
    source_path: str
    project_id: str
    design_package_id: str
    component_id: str
    implementation_plan_id: str
    plan_id_external: str
    consumer_context_key: str
    component_element_keys: tuple[str, ...]
    realization_keys: tuple[str, ...]
    activity_keys: tuple[str, ...]


def _query_scalar(sql: str) -> str:
    output = run_psql(sql)
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f'Expected scalar value from SQL, got empty output.\nSQL:\n{sql}')
    return lines[0]


def _query_optional_scalar(sql: str) -> str | None:
    output = run_psql(sql)
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    return lines[0] if lines else None


def _ensure_component_row(project_id: str, seed: ComponentSpecMaterializationSeed) -> str:
    identity = seed.component_identity
    metadata = json.dumps(
        {
            'source': 'component spec materialization',
            'governed_component_name': identity.component_name,
            'doc_source_path': seed.source_path,
            'code_metadata_binding': True,
        },
        sort_keys=True,
    )
    sql = f"""
INSERT INTO paa.components (
  project_id, name, role, system_layer, tier, description, status, metadata_json
)
VALUES (
  {sql_literal(project_id)}::uuid,
  {sql_literal(identity.component_name)},
  {sql_literal(f'{identity.component_name} materialized from governed component spec')},
  {sql_literal(identity.system_layer)}::paa.system_layer,
  {sql_literal(identity.tier)}::paa.component_tier,
  {sql_literal(f'Materialized from governed component spec: {Path(seed.source_path).name}.')},
  {sql_literal(identity.status)}::paa.component_status,
  {sql_literal(metadata)}::jsonb
)
ON CONFLICT (project_id, name) DO UPDATE SET
  role = EXCLUDED.role,
  system_layer = EXCLUDED.system_layer,
  tier = EXCLUDED.tier,
  description = EXCLUDED.description,
  status = EXCLUDED.status,
  metadata_json = paa.components.metadata_json || EXCLUDED.metadata_json,
  updated_at = now();
"""
    run_psql(sql)
    return _query_scalar(
        f"SELECT component_id::text FROM paa.components WHERE project_id = {sql_literal(project_id)}::uuid AND name = {sql_literal(identity.component_name)} LIMIT 1;"
    )


def _element_id(component_id: str, element_key: str) -> str:
    return _query_scalar(
        f"SELECT component_element_id::text FROM paa.component_elements WHERE component_id = {sql_literal(component_id)}::uuid AND element_key = {sql_literal(element_key)} LIMIT 1;"
    )


def _realization_id(component_id: str, realization_key: str) -> str:
    return _query_scalar(
        f"SELECT component_element_realization_id::text FROM paa.component_element_realizations WHERE component_id = {sql_literal(component_id)}::uuid AND realization_key = {sql_literal(realization_key)} LIMIT 1;"
    )


def _anchor_plan(design_package_id: str, project_id: str, consumer_context_key: str) -> ImplementationPlanRecord:
    plan_repo = PostgresImplementationPlanRepository()
    record = plan_repo.get_implementation_plan_for_design_package(design_package_id, consumer_context_key)
    if record is not None:
        return record
    implementation_plan_id = _query_scalar(
        f"SELECT implementation_plan_id::text FROM paa.implementation_plans WHERE project_id = {sql_literal(project_id)}::uuid AND design_package_id = {sql_literal(design_package_id)}::uuid ORDER BY created_at ASC LIMIT 1;"
    )
    fallback_record = plan_repo.get_implementation_plan(implementation_plan_id)
    if fallback_record is None:
        raise RuntimeError('Failed to resolve anchor implementation plan record.')
    return fallback_record


def _clear_existing_plan_activity_truth(plan_id: str) -> None:
    for statement in (
        f"DELETE FROM paa.implementation_plan_activity_dependencies WHERE implementation_plan_id = {sql_literal(plan_id)}::uuid;",
        f"DELETE FROM paa.implementation_plan_activities WHERE implementation_plan_id = {sql_literal(plan_id)}::uuid;",
    ):
        run_psql(statement)


def _target_module(target_path: str) -> str:
    return Path(target_path).name


def materialize_component_spec(
    *,
    spec_path: Path,
    project_slug: str = DEFAULT_PROJECT_SLUG,
    anchor_design_package_external: str = DEFAULT_ANCHOR_DESIGN_PACKAGE_EXTERNAL,
    anchor_consumer_context_key: str = DEFAULT_ANCHOR_CONSUMER_CONTEXT_KEY,
) -> MaterializedComponentSpecResult:
    seed = extract_component_spec_materialization_seed(spec_path)
    component_repo = PostgresComponentDesignRepository()
    plan_repo = PostgresImplementationPlanRepository()

    project_id = _query_scalar(
        f"SELECT project_id::text FROM paa.projects WHERE slug = {sql_literal(project_slug)} LIMIT 1;"
    )
    design_package_id = _query_scalar(
        f"SELECT design_package_id::text FROM paa.design_packages WHERE package_id_external = {sql_literal(anchor_design_package_external)} LIMIT 1;"
    )
    anchor_plan = _anchor_plan(design_package_id, project_id, anchor_consumer_context_key)
    component_id = _ensure_component_row(project_id, seed)

    existing_plan_id = _query_optional_scalar(
        f"SELECT implementation_plan_id::text FROM paa.implementation_plans WHERE plan_id_external = {sql_literal(seed.plan_seed.plan_name)} LIMIT 1;"
    )
    if existing_plan_id is not None:
        _clear_existing_plan_activity_truth(existing_plan_id)

    for element in seed.component_elements:
        component_repo.upsert_component_element(
            ComponentElementUpsertSpec(
                project_id=project_id,
                component_id=component_id,
                element_type_key=_ELEMENT_TYPE_KEY_BY_KIND[element.element_kind],
                element_key=element.element_name,
                title=element.element_name.replace('_', ' ').title(),
                definition={
                    'description': element.description,
                    'owned_by_component': element.owned_by_component,
                    'materialized_from_component_spec': True,
                },
                metadata={
                    'component_name': seed.component_identity.component_name,
                    'element_kind': element.element_kind,
                    'source_path': seed.source_path,
                },
            )
        )

    element_ids = {
        element.element_name: _element_id(component_id, element.element_name)
        for element in seed.component_elements
    }

    for sequence_order, realization in enumerate(seed.realizations, start=10):
        component_repo.upsert_component_element_realization(
            ComponentElementRealizationUpsertSpec(
                project_id=project_id,
                component_id=component_id,
                component_element_id=element_ids[realization.element_name],
                realization_type_key=realization.realization_kind,
                realization_key=realization.realization_key,
                title=realization.element_name.replace('_', ' ').title(),
                status='planned',
                sequence_order=sequence_order,
                artifact_ref={'module_path': realization.artifact_target},
                definition={
                    'artifact_kind': realization.artifact_kind,
                    'verification_role': realization.verification_role,
                },
                metadata={
                    'component_name': seed.component_identity.component_name,
                    'source_path': seed.source_path,
                },
            )
        )

    realization_ids = {
        (realization.element_name, realization.realization_kind): _realization_id(component_id, realization.realization_key)
        for realization in seed.realizations
    }

    verification_targets = [surface.artifact_target for surface in seed.verification_surfaces if surface.required_for_acceptance]
    artifact_targets = [realization.artifact_target for realization in seed.realizations]

    plan_repo.upsert_implementation_plan(
        ImplementationPlanUpsertSpec(
            project_id=project_id,
            design_package_id=design_package_id,
            plan_id_external=seed.plan_seed.plan_name,
            consumer_context_key=seed.plan_seed.consumer_context_key,
            plan_title=f"{seed.component_identity.component_name} component-spec materialization proof slice",
            plan_kind='implementation_slice',
            status='draft',
            authority_state=seed.plan_seed.plan_status,
            work_item_id=anchor_plan.work_item_id,
            spec_fragment_id=anchor_plan.spec_fragment_id,
            implementation_target_id=anchor_plan.implementation_target_id,
            authority_version_id=anchor_plan.authority_version_id,
            primary_component_id=component_id,
            plan={
                'component_name': seed.component_identity.component_name,
                'materialization_source': 'component_spec_tables',
                'source_path': seed.source_path,
                'anchor_plan_id': anchor_plan.implementation_plan_id,
            },
            build_sequence={'activity_keys': [activity.activity_key for activity in seed.activity_seeds]},
            touch_surfaces={'modules': artifact_targets},
            protected_constraints={'forbid': ['ad hoc materializer vocabulary aliasing']},
            verification_plan={
                'surface_refs': verification_targets,
                'required_surface_count': len(verification_targets),
            },
            provenance={
                'source': 'paa-producer materialize-component-spec',
                'source_component_spec': seed.source_path,
                'anchor_design_package_external': anchor_design_package_external,
                'anchor_plan_id': anchor_plan.implementation_plan_id,
            },
            metadata={
                'governed_component_name': seed.component_identity.component_name,
                'component_spec_materialization': True,
            },
        )
    )

    plan_record = plan_repo.get_implementation_plan_for_design_package(
        design_package_id,
        seed.plan_seed.consumer_context_key,
    )
    if plan_record is None:
        raise RuntimeError('Failed to resolve materialized component-spec implementation plan.')

    for activity in seed.activity_seeds:
        matching_realization = next(
            realization
            for realization in seed.realizations
            if realization.element_name == activity.element_name and realization.realization_kind == activity.realization_kind
        )
        plan_repo.upsert_implementation_plan_activity(
            ImplementationPlanActivityUpsertSpec(
                implementation_plan_id=plan_record.implementation_plan_id,
                activity_key=activity.activity_key,
                activity_title=activity.activity_name,
                activity_kind=_ACTIVITY_KIND_BY_SPEC_KIND[activity.activity_kind],
                activity_state='planned',
                sequence_order=activity.sequence,
                component_element_id=element_ids[activity.element_name],
                component_element_realization_id=realization_ids[(activity.element_name, activity.realization_kind)],
                target_path=matching_realization.artifact_target,
                target_module=_target_module(matching_realization.artifact_target),
                planned_artifact_type_key=matching_realization.realization_kind,
                metadata={
                    'component_name': seed.component_identity.component_name,
                    'done_definition': activity.done_definition,
                    'source_path': seed.source_path,
                },
            )
        )

    for dependency in seed.activity_dependencies:
        plan_repo.upsert_implementation_plan_activity_dependency(
            ImplementationPlanActivityDependencyUpsertSpec(
                implementation_plan_id=plan_record.implementation_plan_id,
                predecessor_activity_key=dependency.depends_on_activity_key,
                successor_activity_key=dependency.activity_key,
                sequencing_requirement=_SEQUENCING_REQUIREMENT_BY_SPEC_KIND[dependency.dependency_kind],
                dependency_strength=_DEPENDENCY_STRENGTH_BY_SPEC_KIND[dependency.dependency_kind],
                notes='Materialized from governed component-spec activity dependency table.',
                metadata={
                    'component_name': seed.component_identity.component_name,
                    'source_path': seed.source_path,
                },
            )
        )

    return MaterializedComponentSpecResult(
        source_path=seed.source_path,
        project_id=project_id,
        design_package_id=design_package_id,
        component_id=component_id,
        implementation_plan_id=plan_record.implementation_plan_id,
        plan_id_external=plan_record.plan_id_external,
        consumer_context_key=plan_record.consumer_context_key,
        component_element_keys=tuple(element.element_name for element in seed.component_elements),
        realization_keys=tuple(realization.realization_key for realization in seed.realizations),
        activity_keys=tuple(activity.activity_key for activity in seed.activity_seeds),
    )

"""Producer-side implementation-plan derivation and persistence."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

from paa_core.db import query_rows, sql_literal
from paa_core.repositories.component_design import (
    ComponentElementRealizationUpsertSpec,
    ComponentElementUpsertSpec,
    PostgresComponentDesignRepository,
)
from paa_core.repositories.implementation_plan import PostgresImplementationPlanRepository, ImplementationPlanUpsertSpec
from paa_core.services.implementation_plan_derivation import (
    DefaultImplementationPlanDerivationService,
    ImplementationPlanActivityBlueprint,
    ImplementationPlanDerivationRequest,
    ImplementationPlanVerificationSurfaceDraft,
)
from paa_producer.brief_target_author import _target_blueprints, _element_by_key, _realization_by_key
from paa_producer.derivation_readiness import evaluate_derivation_readiness
from paa_producer.design_package_deriver import _resolve_stage1_schema_path, validate_stage1_design_package


@dataclass(frozen=True)
class DerivedImplementationPlanResult:
    project_slug: str
    package_id: str
    package_path: str
    design_package_id: str
    implementation_plan_id: str
    plan_id_external: str
    consumer_context_key: str
    activity_count: int
    dependency_count: int
    verification_surface_count: int
    output_path: str | None
    persisted: bool


class _ServiceLogger:
    def info(self, event: str, **fields: object) -> None:
        return None

    def warning(self, event: str, **fields: object) -> None:
        return None


_ACTIVITY_KIND_BY_TARGET = {
    'service_interface': 'artifact_construction',
    'dto': 'artifact_construction',
    'service_implementation': 'artifact_construction',
    'test_module': 'verification',
    'package_export': 'delivery_preparation',
}


_ACTIVITY_KEY_BY_TARGET = {
    'service_interface': 'define-service-interface',
    'dto': 'define-planning-dtos',
    'service_implementation': 'implement-service-default',
    'test_module': 'prove-service-behavior',
    'package_export': 'export-service-package',
}


def _slugify(value: str) -> str:
    chars = []
    for ch in value.lower():
        chars.append(ch if ch.isalnum() else '-')
    slug = ''.join(chars)
    while '--' in slug:
        slug = slug.replace('--', '-')
    return slug.strip('-')


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _component_name(package: dict[str, Any]) -> str:
    return (package.get('component_model_slice') or {}).get('primary_component') or 'Component'


def _node_for_primary_component(package: dict[str, Any]) -> dict[str, Any]:
    name = _component_name(package)
    for node in (package.get('dependency_graph_slice') or {}).get('nodes') or []:
        if node.get('component_name') == name:
            return node
    return {}


def _surface_summary(package: dict[str, Any]) -> dict[str, Any]:
    target = package.get('implementation_target') or {}
    return {
        'expected_touch_surfaces': target.get('expected_touch_surfaces') or [],
        'protected_baseline': target.get('protected_baseline') or [],
        'pre_handoff_scope_checks': target.get('pre_handoff_scope_checks') or [],
    }


def _plan_id_external(package: dict[str, Any], consumer_context_key: str) -> str:
    fragment = package.get('spec_fragment') or {}
    fragment_id = fragment.get('spec_fragment_id') or package.get('package_id') or 'implementation-plan'
    return f"plan-{_slugify(fragment_id)}-{consumer_context_key}"


def _plan_title(package: dict[str, Any], consumer_context_key: str) -> str:
    title = (package.get('spec_fragment') or {}).get('spec_fragment_title') or 'Implementation Plan'
    return f'{title} ({consumer_context_key})'


def _query_scalar(sql: str) -> str | None:
    rows = query_rows(sql)
    return rows[0][0] if rows else None


def _project_id_for_slug(project_slug: str) -> str:
    project_id = _query_scalar(f"SELECT project_id::text FROM paa.projects WHERE slug = {sql_literal(project_slug)} LIMIT 1;")
    if not project_id:
        raise RuntimeError(f'No project_id found for project slug {project_slug!r}')
    return project_id


def _ensure_component_design_records(project_id: str, package: dict[str, Any], component_id: str) -> dict[str, tuple[str, str]]:
    repo = PostgresComponentDesignRepository()
    blueprints = _target_blueprints(package)
    for blueprint in blueprints:
        repo.upsert_component_element(
            ComponentElementUpsertSpec(
                project_id=project_id,
                component_id=component_id,
                element_type_key=blueprint.element_type_key,
                element_key=blueprint.element_key,
                title=blueprint.element_title,
                status=blueprint.element_status,
                definition=blueprint.element_definition,
                metadata={'source': 'paa-producer derive-implementation-plan'},
            )
        )
    elements = _element_by_key(repo.list_component_elements_for_component(component_id))
    for blueprint in blueprints:
        element = elements[blueprint.element_key]
        repo.upsert_component_element_realization(
            ComponentElementRealizationUpsertSpec(
                project_id=project_id,
                component_id=component_id,
                component_element_id=element.component_element_id,
                realization_type_key=blueprint.realization_type_key,
                realization_key=blueprint.realization_key,
                title=blueprint.realization_title,
                status=blueprint.realization_status,
                sequence_order=blueprint.realization_sequence_order,
                definition=blueprint.definition,
                artifact_ref=blueprint.artifact_ref,
                metadata={'source': 'paa-producer derive-implementation-plan'},
            )
        )
    result: dict[str, tuple[str, str]] = {}
    elements = _element_by_key(repo.list_component_elements_for_component(component_id))
    for blueprint in blueprints:
        realizations = _realization_by_key(repo.list_realizations_for_component_element(elements[blueprint.element_key].component_element_id))
        result[blueprint.realization_key] = (
            elements[blueprint.element_key].component_element_id,
            realizations[blueprint.realization_key].component_element_realization_id,
        )
    return result


def _activity_blueprints(package: dict[str, Any], component_id: str, project_id: str) -> tuple[ImplementationPlanActivityBlueprint, ...]:
    blueprints = _target_blueprints(package)
    ids_by_realization_key = _ensure_component_design_records(project_id, package, component_id)
    activity_blueprints: list[ImplementationPlanActivityBlueprint] = []
    activity_key_by_realization_key = {
        blueprint.realization_key: _ACTIVITY_KEY_BY_TARGET[blueprint.realization_type_key]
        for blueprint in blueprints
    }
    for blueprint in blueprints:
        element_id, realization_id = ids_by_realization_key[blueprint.realization_key]
        predecessor_keys: list[str] = []
        if blueprint.depends_on_realization_key:
            predecessor_keys.append(activity_key_by_realization_key[blueprint.depends_on_realization_key])
        activity_blueprints.append(
            ImplementationPlanActivityBlueprint(
                activity_key=activity_key_by_realization_key[blueprint.realization_key],
                activity_title=blueprint.realization_title,
                activity_kind=_ACTIVITY_KIND_BY_TARGET[blueprint.realization_type_key],
                sequence_order=blueprint.target_sequence_order,
                component_element_id=element_id,
                component_element_key=blueprint.element_key,
                component_element_realization_id=realization_id,
                code_artifact_target_key=blueprint.realization_type_key,
                target_path=blueprint.artifact_ref.get('module_path'),
                target_module=Path(blueprint.artifact_ref.get('module_path', '')).name or None,
                metadata={
                    'component_id': component_id,
                    'component_name': _component_name(package),
                    'component_element_key': blueprint.element_key,
                    'code_artifact_target_key': blueprint.realization_type_key,
                },
                predecessor_activity_keys=tuple(predecessor_keys),
            )
        )
    return tuple(activity_blueprints)


def _verification_surfaces(package: dict[str, Any]) -> tuple[ImplementationPlanVerificationSurfaceDraft, ...]:
    surfaces: list[ImplementationPlanVerificationSurfaceDraft] = []
    for blueprint in _target_blueprints(package):
        if blueprint.realization_type_key == 'test_module':
            surfaces.append(
                ImplementationPlanVerificationSurfaceDraft(
                    activity_key=_ACTIVITY_KEY_BY_TARGET[blueprint.realization_type_key],
                    surface_kind='unit_test',
                    surface_ref=blueprint.artifact_ref.get('module_path', ''),
                    required=True,
                    sequence_order=blueprint.target_sequence_order,
                    metadata={
                        'proof_slice': 'component_design_planning_service',
                        'component_name': _component_name(package),
                    },
                )
            )
    return tuple(surfaces)


def derive_implementation_plan(
    *,
    package_path: Path,
    package_schema_path: Path | None = None,
    project_slug: str | None = None,
    consumer_context_key: str = 'python',
    output_path: Path | None = None,
    persist_db: bool = True,
) -> DerivedImplementationPlanResult:
    readiness = asdict(
        evaluate_derivation_readiness(
            package_path=package_path,
            schema_path=package_schema_path,
            project_slug=project_slug,
        )
    )
    if not readiness['ready']:
        raise RuntimeError('derivation readiness failed; resolve blockers before deriving an implementation plan')

    package = validate_stage1_design_package(package_path.resolve(), _resolve_stage1_schema_path(package_schema_path))
    project_id = _project_id_for_slug(readiness['project_slug'])
    component_id = readiness['component_id']
    if not component_id:
        raise RuntimeError('implementation plan derivation requires a materialized primary component binding')

    activity_blueprints = _activity_blueprints(package, component_id, project_id)
    verification_surfaces = _verification_surfaces(package)
    surface_summary = _surface_summary(package)
    node = _node_for_primary_component(package)
    plan_spec = ImplementationPlanUpsertSpec(
        project_id=project_id,
        work_item_id=readiness['work_item_id'],
        design_package_id=readiness['design_package_id'],
        spec_fragment_id=readiness['spec_fragment_id'],
        implementation_target_id=readiness['implementation_target_id'],
        authority_version_id=readiness['authority_version_id'],
        primary_component_id=component_id,
        plan_id_external=_plan_id_external(package, consumer_context_key),
        consumer_context_key=consumer_context_key,
        plan_title=_plan_title(package, consumer_context_key),
        plan_kind='implementation_slice',
        plan={
            'component_name': _component_name(package),
            'component_role': node.get('component_role'),
            'authorized_delta_family': (package.get('spec_fragment') or {}).get('authorized_delta_family'),
        },
        build_sequence={
            'activity_keys': [item.activity_key for item in activity_blueprints],
            'ordered_artifact_targets': [item.code_artifact_target_key for item in activity_blueprints],
        },
        touch_surfaces=surface_summary['expected_touch_surfaces'],
        protected_constraints=surface_summary['protected_baseline'],
        verification_plan={
            'surface_refs': [item.surface_ref for item in verification_surfaces],
            'required_surface_count': len(verification_surfaces),
        },
        provenance={
            'source': 'paa-producer derive-implementation-plan',
            'design_package_path': str(package_path.resolve()),
            'package_id': package.get('package_id'),
        },
        metadata={
            'pre_handoff_scope_checks': surface_summary['pre_handoff_scope_checks'],
            'activity_bridge': 'component -> component element -> code artifact target',
        },
    )
    service = DefaultImplementationPlanDerivationService(
        repository=PostgresImplementationPlanRepository(),
        logger=_ServiceLogger(),
    )
    result = service.derive_plan(
        ImplementationPlanDerivationRequest(
            plan=plan_spec,
            activity_blueprints=activity_blueprints,
            verification_surfaces=verification_surfaces,
            persist=persist_db,
        )
    )

    resolved_output_path = output_path.expanduser().resolve() if output_path else None
    if resolved_output_path is not None:
        resolved_output_path.parent.mkdir(parents=True, exist_ok=True)
        resolved_output_path.write_text(
            json.dumps(
                {
                    'implementation_plan_id': result.plan_record.implementation_plan_id,
                    'plan_id_external': result.plan_record.plan_id_external,
                    'consumer_context_key': result.plan_record.consumer_context_key,
                    'plan_title': result.plan_record.plan_title,
                    'activity_specs': [
                        {
                            'activity_key': item.activity_key,
                            'activity_title': item.activity_title,
                            'activity_kind': item.activity_kind,
                            'sequence_order': item.sequence_order,
                            'code_artifact_target_key': item.planned_artifact_type_key,
                            'target_path': item.target_path,
                        }
                        for item in result.activity_specs
                    ],
                    'dependency_specs': [
                        {
                            'predecessor_activity_key': item.predecessor_activity_key,
                            'successor_activity_key': item.successor_activity_key,
                        }
                        for item in result.dependency_specs
                    ],
                    'verification_surfaces': [
                        {
                            'activity_key': item.activity_key,
                            'surface_kind': item.surface_kind,
                            'surface_ref': item.surface_ref,
                        }
                        for item in result.verification_surfaces
                    ],
                },
                indent=2,
            )
            + '\n'
        )

    return DerivedImplementationPlanResult(
        project_slug=readiness['project_slug'],
        package_id=readiness['package_id'],
        package_path=readiness['package_path'],
        design_package_id=readiness['design_package_id'],
        implementation_plan_id=result.plan_record.implementation_plan_id,
        plan_id_external=result.plan_record.plan_id_external,
        consumer_context_key=result.plan_record.consumer_context_key,
        activity_count=len(result.activity_specs),
        dependency_count=len(result.dependency_specs),
        verification_surface_count=len(result.verification_surfaces),
        output_path=str(resolved_output_path) if resolved_output_path else None,
        persisted=result.persisted,
    )

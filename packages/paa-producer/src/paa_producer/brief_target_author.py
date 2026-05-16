"""Producer-side authoring of coder-brief realization targets."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

from paa_core.db import query_rows, sql_literal
from paa_core.repositories.component_design import (
    BriefRealizationTargetUpsertSpec,
    ComponentElementRecord,
    ComponentElementRealizationRecord,
    ComponentElementRealizationUpsertSpec,
    ComponentElementUpsertSpec,
    PostgresComponentDesignRepository,
)
from paa_producer.coder_brief_assembler import assemble_coder_brief
from paa_producer.derivation_readiness import evaluate_derivation_readiness
from paa_producer.design_package_deriver import _resolve_stage1_schema_path, validate_stage1_design_package


@dataclass(frozen=True)
class TargetBlueprint:
    element_type_key: str
    element_key: str
    element_title: str
    element_definition: dict[str, Any]
    realization_type_key: str
    realization_key: str
    realization_title: str
    realization_sequence_order: int
    artifact_ref: dict[str, Any]
    definition: dict[str, Any]
    target_sequence_order: int
    target_notes: str
    target_contract: dict[str, Any]
    depends_on_realization_key: str | None = None
    element_status: str = 'active'
    realization_status: str = 'planned'
    target_intent: str = 'implement'


@dataclass(frozen=True)
class AuthoredBriefTargetsResult:
    project_slug: str
    package_id: str
    package_path: str
    design_package_id: str
    coder_run_brief_id: str
    brief_id: str
    component_id: str
    work_item_id: str
    readiness_class: str
    output_path: str | None
    component_element_keys: list[str]
    realization_keys: list[str]
    target_ids: list[str]
    target_count: int
    persisted: bool


def _slugify(value: str) -> str:
    chars = []
    for ch in value.lower():
        chars.append(ch if ch.isalnum() else '-')
    slug = ''.join(chars)
    while '--' in slug:
        slug = slug.replace('--', '-')
    return slug.strip('-')


def _surface_with_suffix(surfaces: list[str], suffix: str) -> str:
    for surface in surfaces:
        if surface.endswith(suffix):
            return surface
    raise RuntimeError(f'Required proof-slice surface ending with {suffix!r} is missing.')


def _target_blueprints(package: dict[str, Any]) -> list[TargetBlueprint]:
    component_name = (package.get('component_model_slice') or {}).get('primary_component') or 'component'
    component_slug = _slugify(component_name).replace('-', '_')
    surfaces = (package.get('implementation_target') or {}).get('expected_touch_surfaces') or []
    contract_module = _surface_with_suffix(surfaces, '/contracts.py')
    models_module = _surface_with_suffix(surfaces, '/models.py')
    default_module = _surface_with_suffix(surfaces, '/default.py')
    export_module = _surface_with_suffix(surfaces, '/__init__.py')
    test_module = _surface_with_suffix(surfaces, 'test_component_design_planning_service.py')

    return [
        TargetBlueprint(
            element_type_key='interfaces',
            element_key='interfaces',
            element_title='Service Interfaces',
            element_definition={
                'planning_role': 'define public service contract surfaces',
                'primary_surface': contract_module,
            },
            realization_type_key='service_interface',
            realization_key=f'{component_slug}_service_interface',
            realization_title=f'{component_name} Service Interface',
            realization_sequence_order=10,
            artifact_ref={'module_path': contract_module},
            definition={
                'artifact_kind': 'service_interface',
                'responsibilities': [
                    'define the service protocol',
                    'name the planning entrypoints',
                    'state command/query boundaries',
                ],
            },
            target_sequence_order=10,
            target_notes='Define the public service contract first so later targets implement against a stable seam.',
            target_contract={
                'module_path': contract_module,
                'artifact_kind': 'service_interface',
                'required_outputs': ['service protocol', 'public method signatures'],
            },
        ),
        TargetBlueprint(
            element_type_key='data_contract',
            element_key='data_contract',
            element_title='Service Data Contracts',
            element_definition={
                'planning_role': 'define planning DTOs and result shapes',
                'primary_surface': models_module,
            },
            realization_type_key='dto',
            realization_key=f'{component_slug}_planning_dto',
            realization_title=f'{component_name} Planning DTOs',
            realization_sequence_order=20,
            artifact_ref={'module_path': models_module},
            definition={
                'artifact_kind': 'dto',
                'responsibilities': [
                    'define service request/response DTOs',
                    'carry planning summary data without persistence concerns',
                ],
            },
            target_sequence_order=20,
            target_notes='Define planning data contracts before the service implementation binds behavior to them.',
            target_contract={
                'module_path': models_module,
                'artifact_kind': 'dto',
                'required_outputs': ['input dataclasses', 'result dataclasses'],
            },
            depends_on_realization_key=f'{component_slug}_service_interface',
        ),
        TargetBlueprint(
            element_type_key='functions',
            element_key='functions',
            element_title='Service Functions',
            element_definition={
                'planning_role': 'implement planning behavior',
                'primary_surface': default_module,
            },
            realization_type_key='service_implementation',
            realization_key=f'{component_slug}_service_implementation',
            realization_title=f'{component_name} Default Implementation',
            realization_sequence_order=30,
            artifact_ref={'module_path': default_module},
            definition={
                'artifact_kind': 'service_implementation',
                'responsibilities': [
                    'interpret repository-backed component design inputs',
                    'emit planning-ready outputs for downstream brief derivation',
                ],
            },
            target_sequence_order=30,
            target_notes='Implement the service after interface and DTO targets are settled.',
            target_contract={
                'module_path': default_module,
                'artifact_kind': 'service_implementation',
                'required_outputs': ['default service class', 'planning methods'],
                'forbidden_dependencies': [
                    'direct SQL',
                    'workflow lifecycle imports',
                    'execution package resolution imports',
                ],
            },
            depends_on_realization_key=f'{component_slug}_planning_dto',
        ),
        TargetBlueprint(
            element_type_key='verification_surfaces',
            element_key='verification_surfaces',
            element_title='Verification Surfaces',
            element_definition={
                'planning_role': 'prove service behavior with focused tests',
                'primary_surface': test_module,
            },
            realization_type_key='test_module',
            realization_key=f'{component_slug}_service_tests',
            realization_title=f'{component_name} Unit Tests',
            realization_sequence_order=40,
            artifact_ref={'module_path': test_module},
            definition={
                'artifact_kind': 'test_module',
                'responsibilities': [
                    'verify service behavior',
                    'protect repository boundary assumptions',
                ],
            },
            target_sequence_order=40,
            target_notes='Add focused unit tests after the service implementation target exists.',
            target_contract={
                'module_path': test_module,
                'artifact_kind': 'test_module',
                'required_outputs': ['unit tests covering planning scenarios'],
            },
            depends_on_realization_key=f'{component_slug}_service_implementation',
        ),
        TargetBlueprint(
            element_type_key='interfaces',
            element_key='interfaces',
            element_title='Service Interfaces',
            element_definition={
                'planning_role': 'export service entrypoints from package boundary',
                'primary_surface': export_module,
            },
            realization_type_key='package_export',
            realization_key=f'{component_slug}_package_export',
            realization_title=f'{component_name} Package Export',
            realization_sequence_order=50,
            artifact_ref={'module_path': export_module},
            definition={
                'artifact_kind': 'package_export',
                'responsibilities': [
                    'export service contract and default implementation',
                    'keep package boundary intentional and stable',
                ],
            },
            target_sequence_order=50,
            target_notes='Export the finalized service surface after implementation details exist.',
            target_contract={
                'module_path': export_module,
                'artifact_kind': 'package_export',
                'required_outputs': ['package exports for contract and default implementation'],
            },
            depends_on_realization_key=f'{component_slug}_service_implementation',
        ),
    ]


def _element_by_key(elements: list[ComponentElementRecord]) -> dict[str, ComponentElementRecord]:
    return {element.element_key: element for element in elements}


def _realization_by_key(realizations: list[ComponentElementRealizationRecord]) -> dict[str, ComponentElementRealizationRecord]:
    return {realization.realization_key: realization for realization in realizations}


def _brief_id_for_brief_row(coder_run_brief_id: str) -> str:
    rows = query_rows(
        f"SELECT coalesce(brief_id_external, '') FROM paa.coder_run_briefs WHERE coder_run_brief_id = {sql_literal(coder_run_brief_id)}::uuid LIMIT 1;"
    )
    if not rows:
        raise RuntimeError(f'No coder_run_brief row found for {coder_run_brief_id}')
    return rows[0][0]


def author_brief_targets(
    *,
    package_path: Path,
    package_schema_path: Path | None = None,
    brief_schema_path: Path | None = None,
    project_slug: str | None = None,
    output_path: Path | None = None,
    persist_db: bool = True,
) -> AuthoredBriefTargetsResult:
    resolved_package_path = package_path.expanduser().resolve()
    resolved_schema_path = (package_schema_path or _resolve_stage1_schema_path()).expanduser().resolve()
    package = validate_stage1_design_package(resolved_package_path, resolved_schema_path)
    readiness = evaluate_derivation_readiness(
        package_path=resolved_package_path,
        schema_path=resolved_schema_path,
        project_slug=project_slug,
    )
    if not readiness.ready:
        raise RuntimeError('Slice is not derivation-ready; run evaluate-derivation-readiness and resolve blockers first.')
    if not persist_db:
        raise RuntimeError('author-brief-targets currently requires DB persistence to materialize target state.')
    if not readiness.component_id or not readiness.design_package_id or not readiness.work_item_id:
        raise RuntimeError('Derivation-ready slice is missing persisted component, design package, or work item binding.')
    project_id = _project_id_for_slug(readiness.project_slug)

    brief_result = assemble_coder_brief(
        package_path=resolved_package_path,
        package_schema_path=resolved_schema_path,
        brief_schema_path=brief_schema_path,
        project_slug=project_slug,
        output_path=None,
        persist_db=True,
    )
    repo = PostgresComponentDesignRepository()
    target_blueprints = _target_blueprints(package)

    elements_by_key = _element_by_key(repo.list_component_elements_for_component(readiness.component_id))
    for blueprint in target_blueprints:
        repo.upsert_component_element(
            ComponentElementUpsertSpec(
                project_id=project_id,
                component_id=readiness.component_id,
                element_type_key=blueprint.element_type_key,
                element_key=blueprint.element_key,
                title=blueprint.element_title,
                status=blueprint.element_status,
                definition=blueprint.element_definition,
                provenance={
                    'source': 'paa-producer author-brief-targets',
                    'package_id': readiness.package_id,
                    'design_package_id': readiness.design_package_id,
                },
                metadata={
                    'proof_slice': 'component_design_planning_service',
                },
            )
        )
    elements_by_key = _element_by_key(repo.list_component_elements_for_component(readiness.component_id))

    realization_lookup: dict[str, ComponentElementRealizationRecord] = {}
    for blueprint in target_blueprints:
        element = elements_by_key[blueprint.element_key]
        repo.upsert_component_element_realization(
            ComponentElementRealizationUpsertSpec(
                project_id=project_id,
                component_id=readiness.component_id,
                component_element_id=element.component_element_id,
                realization_type_key=blueprint.realization_type_key,
                realization_key=blueprint.realization_key,
                title=blueprint.realization_title,
                status=blueprint.realization_status,
                sequence_order=blueprint.realization_sequence_order,
                definition=blueprint.definition,
                artifact_ref=blueprint.artifact_ref,
                provenance={
                    'source': 'paa-producer author-brief-targets',
                    'package_id': readiness.package_id,
                    'design_package_id': readiness.design_package_id,
                },
                metadata={
                    'proof_slice': 'component_design_planning_service',
                    'component_element_key': blueprint.element_key,
                },
            )
        )
        realizations = repo.list_realizations_for_component_element(element.component_element_id)
        realization_lookup[blueprint.realization_key] = _realization_by_key(realizations)[blueprint.realization_key]

    target_id_by_realization_key: dict[str, str] = {}
    for blueprint in target_blueprints:
        element = elements_by_key[blueprint.element_key]
        realization = realization_lookup[blueprint.realization_key]
        depends_on_target_id = None
        if blueprint.depends_on_realization_key:
            depends_on_target_id = target_id_by_realization_key[blueprint.depends_on_realization_key]
        repo.upsert_brief_realization_target(
            BriefRealizationTargetUpsertSpec(
                project_id=project_id,
                work_item_id=readiness.work_item_id,
                coder_run_brief_id=brief_result.coder_run_brief_id,
                component_id=readiness.component_id,
                component_element_id=element.component_element_id,
                component_element_realization_id=realization.component_element_realization_id,
                depends_on_target_id=depends_on_target_id,
                target_intent=blueprint.target_intent,
                sequence_order=blueprint.target_sequence_order,
                is_required=True,
                target_notes=blueprint.target_notes,
                target_contract=blueprint.target_contract,
                metadata={
                    'proof_slice': 'component_design_planning_service',
                    'realization_key': blueprint.realization_key,
                },
            )
        )
        brief_targets = repo.list_brief_realization_targets(brief_result.coder_run_brief_id)
        for brief_target in brief_targets:
            if brief_target.component_element_realization_id == realization.component_element_realization_id:
                target_id_by_realization_key[blueprint.realization_key] = brief_target.coder_brief_realization_target_id
                break
        else:
            raise RuntimeError(f'Failed to resolve brief target row for realization {blueprint.realization_key}')

    final_targets = repo.list_brief_realization_targets(brief_result.coder_run_brief_id)
    result = AuthoredBriefTargetsResult(
        project_slug=readiness.project_slug,
        package_id=readiness.package_id,
        package_path=str(resolved_package_path),
        design_package_id=readiness.design_package_id or brief_result.design_package_id,
        coder_run_brief_id=brief_result.coder_run_brief_id,
        brief_id=_brief_id_for_brief_row(brief_result.coder_run_brief_id),
        component_id=readiness.component_id,
        work_item_id=readiness.work_item_id,
        readiness_class=readiness.readiness_class,
        output_path=str(output_path.resolve()) if output_path else None,
        component_element_keys=sorted({blueprint.element_key for blueprint in target_blueprints}),
        realization_keys=[blueprint.realization_key for blueprint in target_blueprints],
        target_ids=[target_id_by_realization_key[blueprint.realization_key] for blueprint in target_blueprints],
        target_count=len(final_targets),
        persisted=True,
    )
    if output_path is not None:
        resolved_output_path = output_path.expanduser().resolve()
        resolved_output_path.write_text(json.dumps({
            **asdict(result),
            'targets': [asdict(target) for target in final_targets],
        }, indent=2) + '\n')
    return result


def _project_id_for_slug(project_slug: str) -> str:
    rows = query_rows(
        f"SELECT project_id::text FROM paa.projects WHERE slug = {sql_literal(project_slug)} LIMIT 1;"
    )
    if not rows:
        raise RuntimeError(f'No project found for slug {project_slug!r}')
    return rows[0][0]

#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
CORE_SRC = REPO_ROOT / "packages" / "paa-core" / "src"
if str(CORE_SRC) not in sys.path:
    sys.path.insert(0, str(CORE_SRC))

from paa_core.db import run_psql, sql_literal
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


ANCHOR_DESIGN_PACKAGE_EXTERNAL = "paa-stage1-2026-05-16-component-design-planning-service"
ANCHOR_CONSUMER_CONTEXT_KEY = "python"
PROJECT_SLUG = "paa-platform"
COMPONENT_NAME = "ExecutionPackageResolutionService"
PLAN_ID_EXTERNAL = "plan-materialize-execution-package-resolution-service-proof-python"
CONSUMER_CONTEXT_KEY = "governance-materialization-python-execution-package-resolution"


def _query_scalar(sql: str) -> str:
    output = run_psql(sql)
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"Expected scalar value from SQL, got empty output.\nSQL:\n{sql}")
    return lines[0]


def _ensure_component_row(project_id: str) -> str:
    metadata = json.dumps(
        {
            "source": "governance materialization proof",
            "governed_component_name": COMPONENT_NAME,
            "code_metadata_binding": True,
        },
        sort_keys=True,
    )
    sql = f"""
INSERT INTO paa.components (
  project_id, name, role, system_layer, tier, description, status, metadata_json
)
VALUES (
  {sql_literal(project_id)}::uuid,
  {sql_literal(COMPONENT_NAME)},
  {sql_literal('resolve execution-package context and report governed capability gaps')},
  'domain-services'::paa.system_layer,
  'runtime'::paa.component_tier,
  {sql_literal('Service boundary for execution-package context resolution and normalized view assembly.')},
  'active'::paa.component_status,
  {sql_literal(metadata)}::jsonb
)
ON CONFLICT (project_id, name) DO UPDATE SET
  role = EXCLUDED.role,
  system_layer = EXCLUDED.system_layer,
  tier = EXCLUDED.tier,
  description = EXCLUDED.description,
  metadata_json = paa.components.metadata_json || EXCLUDED.metadata_json,
  updated_at = now()
RETURNING component_id::text;
"""
    return _query_scalar(sql)


def _element_id(component_id: str, element_key: str) -> str:
    return _query_scalar(
        f"""
SELECT ce.component_element_id::text
FROM paa.component_elements ce
WHERE ce.component_id = {sql_literal(component_id)}::uuid
  AND ce.element_key = {sql_literal(element_key)}
LIMIT 1;
"""
    )


def _realization_id(component_id: str, realization_key: str) -> str:
    return _query_scalar(
        f"""
SELECT cer.component_element_realization_id::text
FROM paa.component_element_realizations cer
WHERE cer.component_id = {sql_literal(component_id)}::uuid
  AND cer.realization_key = {sql_literal(realization_key)}
LIMIT 1;
"""
    )


def _anchor_plan(design_package_id: str, project_id: str) -> ImplementationPlanRecord:
    plan_repo = PostgresImplementationPlanRepository()
    record = plan_repo.get_implementation_plan_for_design_package(
        design_package_id,
        ANCHOR_CONSUMER_CONTEXT_KEY,
    )
    if record is not None:
        return record

    fallback_sql = f"""
SELECT implementation_plan_id::text
FROM paa.implementation_plans
WHERE project_id = {sql_literal(project_id)}::uuid
  AND design_package_id = {sql_literal(design_package_id)}::uuid
ORDER BY created_at ASC
LIMIT 1;
"""
    implementation_plan_id = _query_scalar(fallback_sql)
    fallback_record = plan_repo.get_implementation_plan(implementation_plan_id)
    if fallback_record is None:
        raise RuntimeError("Failed to resolve anchor implementation plan record for service materialization proof.")
    return fallback_record


def main() -> int:
    component_repo = PostgresComponentDesignRepository()
    plan_repo = PostgresImplementationPlanRepository()

    project_id = _query_scalar(
        f"SELECT project_id::text FROM paa.projects WHERE slug = {sql_literal(PROJECT_SLUG)} LIMIT 1;"
    )
    design_package_id = _query_scalar(
        f"""
SELECT design_package_id::text
FROM paa.design_packages
WHERE package_id_external = {sql_literal(ANCHOR_DESIGN_PACKAGE_EXTERNAL)}
LIMIT 1;
"""
    )
    anchor_plan = _anchor_plan(design_package_id, project_id)
    component_id = _ensure_component_row(project_id)

    component_repo.upsert_component_element(
        ComponentElementUpsertSpec(
            project_id=project_id,
            component_id=component_id,
            element_type_key="interfaces",
            element_key="interfaces",
            title="Execution Resolution Service Interfaces",
            definition={
                "primary_surface": "packages/paa-core/src/paa_core/runtime/packets/execution_package_resolution/contracts.py",
                "responsibility": "define the service contract surface",
            },
            metadata={"component_name": COMPONENT_NAME},
        )
    )
    component_repo.upsert_component_element(
        ComponentElementUpsertSpec(
            project_id=project_id,
            component_id=component_id,
            element_type_key="data_contract",
            element_key="data_contract",
            title="Execution Resolution DTOs",
            definition={
                "primary_surface": "packages/paa-core/src/paa_core/runtime/packets/execution_package_resolution/models.py",
                "responsibility": "define normalized resolution request and view models",
            },
            metadata={"component_name": COMPONENT_NAME},
        )
    )
    component_repo.upsert_component_element(
        ComponentElementUpsertSpec(
            project_id=project_id,
            component_id=component_id,
            element_type_key="functions",
            element_key="functions",
            title="Execution Resolution Service Functions",
            definition={
                "primary_surface": "packages/paa-core/src/paa_core/runtime/packets/execution_package_resolution/default.py",
                "responsibility": "implement execution-context resolution behavior",
            },
            metadata={"component_name": COMPONENT_NAME},
        )
    )
    component_repo.upsert_component_element(
        ComponentElementUpsertSpec(
            project_id=project_id,
            component_id=component_id,
            element_type_key="verification_surfaces",
            element_key="verification_surfaces",
            title="Execution Resolution Verification Surfaces",
            definition={
                "primary_surface": "tests/unit/test_execution_package_resolution_service.py",
                "responsibility": "prove resolution behavior and capability-gap reporting",
            },
            metadata={"component_name": COMPONENT_NAME},
        )
    )

    interface_element_id = _element_id(component_id, "interfaces")
    dto_element_id = _element_id(component_id, "data_contract")
    functions_element_id = _element_id(component_id, "functions")
    verification_element_id = _element_id(component_id, "verification_surfaces")

    component_repo.upsert_component_element_realization(
        ComponentElementRealizationUpsertSpec(
            project_id=project_id,
            component_id=component_id,
            component_element_id=interface_element_id,
            realization_type_key="service_interface",
            realization_key="execution_package_resolution_service_interface",
            title="ExecutionPackageResolutionService Interface",
            status="planned",
            sequence_order=10,
            artifact_ref={"module_path": "packages/paa-core/src/paa_core/runtime/packets/execution_package_resolution/contracts.py"},
            definition={"artifact_kind": "service_interface"},
            metadata={"component_name": COMPONENT_NAME},
        )
    )
    component_repo.upsert_component_element_realization(
        ComponentElementRealizationUpsertSpec(
            project_id=project_id,
            component_id=component_id,
            component_element_id=dto_element_id,
            realization_type_key="dto",
            realization_key="execution_package_resolution_service_dto",
            title="Execution Package Resolution DTOs",
            status="planned",
            sequence_order=20,
            artifact_ref={"module_path": "packages/paa-core/src/paa_core/runtime/packets/execution_package_resolution/models.py"},
            definition={"artifact_kind": "dto"},
            metadata={"component_name": COMPONENT_NAME},
        )
    )
    component_repo.upsert_component_element_realization(
        ComponentElementRealizationUpsertSpec(
            project_id=project_id,
            component_id=component_id,
            component_element_id=functions_element_id,
            realization_type_key="service_implementation",
            realization_key="execution_package_resolution_service_implementation",
            title="DefaultExecutionPackageResolutionService",
            status="planned",
            sequence_order=30,
            artifact_ref={"module_path": "packages/paa-core/src/paa_core/runtime/packets/execution_package_resolution/default.py"},
            definition={"artifact_kind": "service_implementation"},
            metadata={"component_name": COMPONENT_NAME},
        )
    )
    component_repo.upsert_component_element_realization(
        ComponentElementRealizationUpsertSpec(
            project_id=project_id,
            component_id=component_id,
            component_element_id=verification_element_id,
            realization_type_key="test_module",
            realization_key="execution_package_resolution_service_tests",
            title="Execution Package Resolution Service Unit Tests",
            status="planned",
            sequence_order=40,
            artifact_ref={"module_path": "tests/unit/test_execution_package_resolution_service.py"},
            definition={"artifact_kind": "test_module"},
            metadata={"component_name": COMPONENT_NAME},
        )
    )

    interface_realization_id = _realization_id(component_id, "execution_package_resolution_service_interface")
    dto_realization_id = _realization_id(component_id, "execution_package_resolution_service_dto")
    implementation_realization_id = _realization_id(component_id, "execution_package_resolution_service_implementation")
    test_realization_id = _realization_id(component_id, "execution_package_resolution_service_tests")

    plan_repo.upsert_implementation_plan(
        ImplementationPlanUpsertSpec(
            project_id=project_id,
            design_package_id=design_package_id,
            plan_id_external=PLAN_ID_EXTERNAL,
            consumer_context_key=CONSUMER_CONTEXT_KEY,
            plan_title="ExecutionPackageResolutionService governed materialization proof slice",
            plan_kind="implementation_slice",
            status="draft",
            authority_state="draft_plan",
            work_item_id=anchor_plan.work_item_id,
            spec_fragment_id=anchor_plan.spec_fragment_id,
            implementation_target_id=anchor_plan.implementation_target_id,
            authority_version_id=anchor_plan.authority_version_id,
            primary_component_id=component_id,
            plan={
                "component_name": COMPONENT_NAME,
                "materialization_source": "governance proof materializer",
                "anchor_plan_id": anchor_plan.implementation_plan_id,
            },
            build_sequence={
                "activity_keys": [
                    "define-service-interface",
                    "define-resolution-dtos",
                    "implement-service-default",
                    "prove-service-behavior",
                ]
            },
            touch_surfaces={
                "modules": [
                    "packages/paa-core/src/paa_core/runtime/packets/execution_package_resolution/contracts.py",
                    "packages/paa-core/src/paa_core/runtime/packets/execution_package_resolution/models.py",
                    "packages/paa-core/src/paa_core/runtime/packets/execution_package_resolution/default.py",
                    "tests/unit/test_execution_package_resolution_service.py",
                ]
            },
            protected_constraints={
                "forbid": [
                    "install mutation",
                    "workflow ownership",
                    "queue orchestration",
                ]
            },
            verification_plan={
                "surface_refs": ["tests/unit/test_execution_package_resolution_service.py"],
                "required_surface_count": 1,
            },
            provenance={
                "source": "scripts/runtime/materialize_execution_package_resolution_service_component.py",
                "anchor_design_package_external": ANCHOR_DESIGN_PACKAGE_EXTERNAL,
                "anchor_plan_id": anchor_plan.implementation_plan_id,
            },
            metadata={"governed_component_name": COMPONENT_NAME, "proof_materialization": True},
        )
    )

    plan_record = plan_repo.get_implementation_plan_for_design_package(design_package_id, CONSUMER_CONTEXT_KEY)
    if plan_record is None:
        raise RuntimeError("Failed to resolve materialized execution-package resolution plan record.")

    plan_repo.upsert_implementation_plan_activity(
        ImplementationPlanActivityUpsertSpec(
            implementation_plan_id=plan_record.implementation_plan_id,
            activity_key="define-service-interface",
            activity_title="ExecutionPackageResolutionService Interface",
            activity_kind="artifact_construction",
            activity_state="planned",
            sequence_order=10,
            component_element_id=interface_element_id,
            component_element_realization_id=interface_realization_id,
            target_path="packages/paa-core/src/paa_core/runtime/packets/execution_package_resolution/contracts.py",
            target_module="contracts.py",
            planned_artifact_type_key="service_interface",
            metadata={"component_name": COMPONENT_NAME},
        )
    )
    plan_repo.upsert_implementation_plan_activity(
        ImplementationPlanActivityUpsertSpec(
            implementation_plan_id=plan_record.implementation_plan_id,
            activity_key="define-resolution-dtos",
            activity_title="Execution Package Resolution DTOs",
            activity_kind="artifact_construction",
            activity_state="planned",
            sequence_order=20,
            component_element_id=dto_element_id,
            component_element_realization_id=dto_realization_id,
            target_path="packages/paa-core/src/paa_core/runtime/packets/execution_package_resolution/models.py",
            target_module="models.py",
            planned_artifact_type_key="dto",
            metadata={"component_name": COMPONENT_NAME},
        )
    )
    plan_repo.upsert_implementation_plan_activity(
        ImplementationPlanActivityUpsertSpec(
            implementation_plan_id=plan_record.implementation_plan_id,
            activity_key="implement-service-default",
            activity_title="DefaultExecutionPackageResolutionService",
            activity_kind="artifact_construction",
            activity_state="planned",
            sequence_order=30,
            component_element_id=functions_element_id,
            component_element_realization_id=implementation_realization_id,
            target_path="packages/paa-core/src/paa_core/runtime/packets/execution_package_resolution/default.py",
            target_module="default.py",
            planned_artifact_type_key="service_implementation",
            metadata={"component_name": COMPONENT_NAME},
        )
    )
    plan_repo.upsert_implementation_plan_activity(
        ImplementationPlanActivityUpsertSpec(
            implementation_plan_id=plan_record.implementation_plan_id,
            activity_key="prove-service-behavior",
            activity_title="Execution Package Resolution Service Unit Tests",
            activity_kind="verification",
            activity_state="planned",
            sequence_order=40,
            component_element_id=verification_element_id,
            component_element_realization_id=test_realization_id,
            target_path="tests/unit/test_execution_package_resolution_service.py",
            target_module="test_execution_package_resolution_service.py",
            planned_artifact_type_key="test_module",
            metadata={"component_name": COMPONENT_NAME},
        )
    )
    plan_repo.upsert_implementation_plan_activity_dependency(
        ImplementationPlanActivityDependencyUpsertSpec(
            implementation_plan_id=plan_record.implementation_plan_id,
            predecessor_activity_key="define-service-interface",
            successor_activity_key="define-resolution-dtos",
            notes="DTO surface follows the contract boundary for the service.",
        )
    )
    plan_repo.upsert_implementation_plan_activity_dependency(
        ImplementationPlanActivityDependencyUpsertSpec(
            implementation_plan_id=plan_record.implementation_plan_id,
            predecessor_activity_key="define-resolution-dtos",
            successor_activity_key="implement-service-default",
            notes="Implementation follows the normalized request and resolution view models.",
        )
    )
    plan_repo.upsert_implementation_plan_activity_dependency(
        ImplementationPlanActivityDependencyUpsertSpec(
            implementation_plan_id=plan_record.implementation_plan_id,
            predecessor_activity_key="implement-service-default",
            successor_activity_key="prove-service-behavior",
            notes="Verification follows service implementation materialization.",
        )
    )

    output = {
        "project_id": project_id,
        "design_package_id": design_package_id,
        "component_id": component_id,
        "implementation_plan_id": plan_record.implementation_plan_id,
        "plan_id_external": plan_record.plan_id_external,
        "component_element_keys": ["interfaces", "data_contract", "functions", "verification_surfaces"],
        "realization_keys": [
            "execution_package_resolution_service_interface",
            "execution_package_resolution_service_dto",
            "execution_package_resolution_service_implementation",
            "execution_package_resolution_service_tests",
        ],
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

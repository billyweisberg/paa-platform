from __future__ import annotations

import unittest

from paa_core.governance.component_spec_materialization import (
    ComponentSpecExtractionError,
    extract_component_spec_materialization_seed,
)


WORKFLOW_SPEC_PATH = "/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-17-workflow-lifecycle-service-component-spec.md"
EXECUTION_SPEC_PATH = "/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-17-execution-package-resolution-service-component-spec.md"
IMPLEMENTATION_PLAN_REPOSITORY_SPEC_PATH = "/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-17-implementation-plan-repository-contract.md"


class ComponentSpecMaterializationTests(unittest.TestCase):
    def test_extracts_workflow_lifecycle_seed(self) -> None:
        seed = extract_component_spec_materialization_seed(WORKFLOW_SPEC_PATH)
        self.assertEqual(seed.component_identity.component_name, "WorkflowLifecycleService")
        self.assertEqual(seed.plan_seed.plan_name, "plan-materialize-workflow-lifecycle-service-proof-python")
        self.assertEqual(len(seed.component_elements), 4)
        self.assertEqual(len(seed.realizations), 5)
        self.assertEqual(len(seed.activity_seeds), 4)
        self.assertEqual(len(seed.activity_dependencies), 3)
        self.assertEqual(len(seed.verification_surfaces), 4)
        self.assertEqual(
            seed.realizations[0].realization_key,
            "workflow_lifecycle_service__workflow_transition_interface__service_interface",
        )


    def test_extracts_execution_package_resolution_seed(self) -> None:
        seed = extract_component_spec_materialization_seed(EXECUTION_SPEC_PATH)
        self.assertEqual(seed.component_identity.component_name, "ExecutionPackageResolutionService")
        self.assertEqual(seed.plan_seed.plan_name, "plan-materialize-execution-package-resolution-service-proof-python")
        self.assertEqual(len(seed.component_elements), 4)
        self.assertEqual(len(seed.realizations), 5)
        self.assertEqual(len(seed.activity_seeds), 4)
        self.assertEqual(len(seed.activity_dependencies), 3)
        self.assertEqual(len(seed.verification_surfaces), 4)


    def test_extracts_implementation_plan_repository_seed(self) -> None:
        seed = extract_component_spec_materialization_seed(IMPLEMENTATION_PLAN_REPOSITORY_SPEC_PATH)
        self.assertEqual(seed.component_identity.component_name, "ImplementationPlanRepository")
        self.assertEqual(seed.plan_seed.plan_name, "plan-materialize-implementation-plan-repository-proof-python")
        self.assertEqual(len(seed.component_elements), 4)
        self.assertEqual(len(seed.realizations), 5)
        self.assertEqual(len(seed.activity_seeds), 5)
        self.assertEqual(len(seed.activity_dependencies), 4)
        self.assertEqual(len(seed.verification_surfaces), 4)

    def test_fails_when_dependency_references_unknown_activity(self) -> None:
        from tempfile import NamedTemporaryFile

        with open(WORKFLOW_SPEC_PATH, "r", encoding="utf-8") as handle:
            content = handle.read().replace(
                "| workflow-default-service | workflow-decision-models | hard |",
                "| workflow-default-service | missing-activity | hard |",
            )
        with NamedTemporaryFile("w", suffix=".md", encoding="utf-8", delete=False) as handle:
            handle.write(content)
            broken_path = handle.name
        with self.assertRaises(ComponentSpecExtractionError):
            extract_component_spec_materialization_seed(broken_path)


if __name__ == "__main__":
    unittest.main()

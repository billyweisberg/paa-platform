from __future__ import annotations

import unittest

from paa_core.governance import GovernedComponentMetadata
from paa_core.governance.model_code_consistency import (
    ModelComponentTruthSnapshot,
    evaluate_model_code_consistency,
)


class ModelCodeConsistencyTests(unittest.TestCase):
    def test_consistency_report_is_clean_when_model_and_code_align(self) -> None:
        registry = {
            "WorkflowLifecycleService": GovernedComponentMetadata(
                name="WorkflowLifecycleService",
                kind="service",
                alignment="aligned",
                lifecycle_stage="build",
                owns=("workflow transition evaluation",),
                does_not_own=("queue transport",),
            )
        }
        model_truth = {
            "WorkflowLifecycleService": ModelComponentTruthSnapshot(
                component_name="WorkflowLifecycleService",
                component_count=1,
                component_ids=("component-1",),
                project_ids=("project-1",),
                element_count=2,
                realization_count=2,
                implementation_plan_activity_count=3,
            )
        }

        reports = evaluate_model_code_consistency(
            ["WorkflowLifecycleService"],
            component_registry=registry,
            model_truth=model_truth,
        )

        self.assertEqual(1, len(reports))
        report = reports[0]
        self.assertTrue(report.metadata_found)
        self.assertEqual((), report.blocking_gaps)

    def test_consistency_report_flags_missing_model_truth_and_metadata(self) -> None:
        reports = evaluate_model_code_consistency(
            ["MissingService"],
            component_registry={},
            model_truth={},
        )

        self.assertEqual(1, len(reports))
        report = reports[0]
        self.assertFalse(report.metadata_found)
        self.assertIn("missing_code_metadata", report.blocking_gaps)
        self.assertIn("missing_model_component", report.blocking_gaps)
        self.assertIn("missing_component_elements", report.blocking_gaps)
        self.assertIn("missing_component_realizations", report.blocking_gaps)
        self.assertIn("missing_implementation_plan_activities", report.blocking_gaps)

    def test_consistency_report_flags_ambiguous_component_rows(self) -> None:
        registry = {
            "ImplementationPlanRepository": GovernedComponentMetadata(
                name="ImplementationPlanRepository",
                kind="repository",
                alignment="aligned",
                lifecycle_stage="build",
                owns=("implementation-plan activity persistence",),
                does_not_own=("coder-brief assembly",),
            )
        }
        model_truth = {
            "ImplementationPlanRepository": ModelComponentTruthSnapshot(
                component_name="ImplementationPlanRepository",
                component_count=2,
                component_ids=("component-1", "component-2"),
                project_ids=("project-1", "project-2"),
                element_count=2,
                realization_count=2,
                implementation_plan_activity_count=2,
            )
        }

        reports = evaluate_model_code_consistency(
            ["ImplementationPlanRepository"],
            component_registry=registry,
            model_truth=model_truth,
        )

        self.assertIn("ambiguous_model_component", reports[0].blocking_gaps)


if __name__ == "__main__":
    unittest.main()

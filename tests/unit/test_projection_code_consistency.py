from __future__ import annotations

import unittest

from paa_core.governance.component_metadata import GovernedComponentMetadata
from paa_core.governance.projection_code_consistency import evaluate_projection_code_consistency


class ProjectionCodeConsistencyTest(unittest.TestCase):
    def test_reports_missing_projection_surface(self) -> None:
        reports = evaluate_projection_code_consistency(
            ["WorkflowLifecycleService"],
            projection_surface_present=False,
            projection_truth={"WorkflowLifecycleService": (0, ())},
            component_registry={
                "WorkflowLifecycleService": GovernedComponentMetadata(
                    name="WorkflowLifecycleService",
                    kind="service",
                    alignment="aligned",
                    lifecycle_stage="build",
                    owns=("workflow transition evaluation",),
                    does_not_own=("queue transport",),
                )
            },
        )
        self.assertEqual(len(reports), 1)
        self.assertIn("missing_project_delivery_projection_surface", reports[0].blocking_gaps)

    def test_reports_missing_projection_rows_when_surface_exists(self) -> None:
        reports = evaluate_projection_code_consistency(
            ["ExecutionPackageResolutionService"],
            projection_surface_present=True,
            projection_truth={"ExecutionPackageResolutionService": (0, ())},
            component_registry={
                "ExecutionPackageResolutionService": GovernedComponentMetadata(
                    name="ExecutionPackageResolutionService",
                    kind="service",
                    alignment="aligned",
                    lifecycle_stage="build",
                    owns=("execution-package context resolution",),
                    does_not_own=("install mutation",),
                )
            },
        )
        self.assertEqual(len(reports), 1)
        self.assertIn("missing_component_projection_rows", reports[0].blocking_gaps)

    def test_reports_clean_when_projection_rows_exist(self) -> None:
        reports = evaluate_projection_code_consistency(
            ["ImplementationPlanRepository"],
            projection_surface_present=True,
            projection_truth={"ImplementationPlanRepository": (1, ("plan-1",))},
            component_registry={
                "ImplementationPlanRepository": GovernedComponentMetadata(
                    name="ImplementationPlanRepository",
                    kind="repository",
                    alignment="aligned",
                    lifecycle_stage="build",
                    owns=("implementation-plan persistence reads and writes",),
                    does_not_own=("workflow truth",),
                )
            },
        )
        self.assertEqual(len(reports), 1)
        self.assertEqual(reports[0].blocking_gaps, ())
        self.assertEqual(reports[0].projected_row_count, 1)


if __name__ == "__main__":
    unittest.main()

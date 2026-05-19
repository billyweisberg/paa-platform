from __future__ import annotations

import unittest

from paa_core.governance.component_metadata import GovernedComponentMetadata
from paa_core.governance.runtime_evidence_model_consistency import (
    RuntimeEvidenceConsistencyComponentReport,
    evaluate_runtime_evidence_model_consistency,
)


class RuntimeEvidenceModelConsistencyTest(unittest.TestCase):
    def test_reports_missing_runtime_evidence(self) -> None:
        reports = evaluate_runtime_evidence_model_consistency(
            ["WorkflowLifecycleService"],
            runtime_truth={
                "WorkflowLifecycleService": RuntimeEvidenceConsistencyComponentReport(
                    component_name="WorkflowLifecycleService",
                    metadata_found=False,
                    metadata_kind=None,
                    implementation_plan_id="plan-1",
                    work_item_id="work-1",
                    workflow_state_count=0,
                    workflow_transition_count=0,
                    handoff_count=0,
                    automation_run_count=0,
                    execution_record_count=0,
                    blocking_gaps=(),
                )
            },
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
        self.assertIn("missing_workflow_state_evidence", reports[0].blocking_gaps)
        self.assertIn("missing_execution_record_evidence", reports[0].blocking_gaps)

    def test_reports_missing_plan_and_work_item_links(self) -> None:
        reports = evaluate_runtime_evidence_model_consistency(
            ["ExecutionPackageResolutionService"],
            runtime_truth={},
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
        self.assertIn("missing_component_plan_link", reports[0].blocking_gaps)
        self.assertIn("missing_component_work_item_link", reports[0].blocking_gaps)

    def test_reports_clean_when_runtime_evidence_exists(self) -> None:
        reports = evaluate_runtime_evidence_model_consistency(
            ["ImplementationPlanRepository"],
            runtime_truth={
                "ImplementationPlanRepository": RuntimeEvidenceConsistencyComponentReport(
                    component_name="ImplementationPlanRepository",
                    metadata_found=False,
                    metadata_kind=None,
                    implementation_plan_id="plan-1",
                    work_item_id="work-1",
                    workflow_state_count=1,
                    workflow_transition_count=2,
                    handoff_count=1,
                    automation_run_count=1,
                    execution_record_count=1,
                    blocking_gaps=(),
                )
            },
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


if __name__ == "__main__":
    unittest.main()

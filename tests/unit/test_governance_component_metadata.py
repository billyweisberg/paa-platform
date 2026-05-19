from __future__ import annotations

import unittest

from paa_core.governance import ALIGNMENT_STATES, COMPONENT_KINDS, GovernedComponentMetadata, LIFECYCLE_STAGES
from paa_core.governance.component_registry import COMPONENT_METADATA_BY_NAME, GOVERNED_COMPONENTS
from paa_core.repositories.implementation_plan import IMPLEMENTATION_PLAN_REPOSITORY_METADATA
from paa_core.services.execution_package_resolution import EXECUTION_PACKAGE_RESOLUTION_SERVICE_METADATA
from paa_core.services.workflow_lifecycle import WORKFLOW_LIFECYCLE_SERVICE_METADATA


class GovernanceComponentMetadataTests(unittest.TestCase):
    def test_metadata_exports_use_governed_shape(self) -> None:
        for metadata in (
            WORKFLOW_LIFECYCLE_SERVICE_METADATA,
            EXECUTION_PACKAGE_RESOLUTION_SERVICE_METADATA,
            IMPLEMENTATION_PLAN_REPOSITORY_METADATA,
        ):
            self.assertIsInstance(metadata, GovernedComponentMetadata)
            self.assertIn(metadata.kind, COMPONENT_KINDS)
            self.assertIn(metadata.alignment, ALIGNMENT_STATES)
            self.assertIn(metadata.lifecycle_stage, LIFECYCLE_STAGES)
            self.assertTrue(metadata.owns)
            self.assertTrue(metadata.does_not_own)

    def test_service_and_repository_kinds_are_distinct(self) -> None:
        self.assertEqual('service', WORKFLOW_LIFECYCLE_SERVICE_METADATA.kind)
        self.assertEqual('service', EXECUTION_PACKAGE_RESOLUTION_SERVICE_METADATA.kind)
        self.assertEqual('repository', IMPLEMENTATION_PLAN_REPOSITORY_METADATA.kind)

    def test_component_registry_maps_metadata_by_name(self) -> None:
        self.assertEqual(3, len(GOVERNED_COMPONENTS))
        self.assertIs(
            WORKFLOW_LIFECYCLE_SERVICE_METADATA,
            COMPONENT_METADATA_BY_NAME["WorkflowLifecycleService"],
        )
        self.assertIs(
            EXECUTION_PACKAGE_RESOLUTION_SERVICE_METADATA,
            COMPONENT_METADATA_BY_NAME["ExecutionPackageResolutionService"],
        )
        self.assertIs(
            IMPLEMENTATION_PLAN_REPOSITORY_METADATA,
            COMPONENT_METADATA_BY_NAME["ImplementationPlanRepository"],
        )


if __name__ == "__main__":
    unittest.main()

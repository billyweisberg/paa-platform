from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))
sys.path.insert(0, str(ROOT / 'packages' / 'paa-cli' / 'src'))

from paa_core.governance import ALIGNMENT_STATES, COMPONENT_KINDS, GovernedComponentMetadata, LIFECYCLE_STAGES
from paa_core.governance.component_registry import COMPONENT_METADATA_BY_NAME, GOVERNED_COMPONENTS
from paa_core.repositories.implementation_plan import IMPLEMENTATION_PLAN_REPOSITORY_METADATA
from paa_core.repositories.methodology_execution import METHODOLOGY_EXECUTION_REPOSITORY_METADATA
from paa_core.services.execution_package_resolution import EXECUTION_PACKAGE_RESOLUTION_SERVICE_METADATA
from paa_core.services.methodology_execution_preflight import (
    METHODOLOGY_EXECUTION_PREFLIGHT_SERVICE_METADATA,
)
from paa_core.services.methodology_execution_projection import (
    METHODOLOGY_EXECUTION_PROJECTION_SERVICE_METADATA,
)
from paa_core.services.methodology_execution_state import (
    METHODOLOGY_EXECUTION_STATE_SERVICE_METADATA,
)
from paa_core.services.workflow_lifecycle import WORKFLOW_LIFECYCLE_SERVICE_METADATA
from paa_core.services.techlead_worker import TECHLEAD_WORKER_SERVICE_METADATA
from paa_core.services.packet_context_assembly import PACKET_CONTEXT_ASSEMBLY_SERVICE_METADATA
from paa_core.services.dev_worker import DEV_WORKER_SERVICE_METADATA
from paa_core.services.qa_worker import QA_WORKER_SERVICE_METADATA
from paa_core.services.queue_packet_runtime_controller import QUEUE_PACKET_RUNTIME_CONTROLLER_METADATA
from paa_core.services.queue_claim_runtime import QUEUE_CLAIM_RUNTIME_SERVICE_METADATA
from paa_core.services.packet_reference_resolution import PACKET_REFERENCE_RESOLUTION_SERVICE_METADATA
from paa_cli import PAA_OPERATOR_CLI_METADATA


class GovernanceComponentMetadataTests(unittest.TestCase):
    def test_metadata_exports_use_governed_shape(self) -> None:
        for metadata in (
            WORKFLOW_LIFECYCLE_SERVICE_METADATA,
            EXECUTION_PACKAGE_RESOLUTION_SERVICE_METADATA,
            IMPLEMENTATION_PLAN_REPOSITORY_METADATA,
            METHODOLOGY_EXECUTION_REPOSITORY_METADATA,
            METHODOLOGY_EXECUTION_STATE_SERVICE_METADATA,
            METHODOLOGY_EXECUTION_PROJECTION_SERVICE_METADATA,
            METHODOLOGY_EXECUTION_PREFLIGHT_SERVICE_METADATA,
            TECHLEAD_WORKER_SERVICE_METADATA,
            PACKET_CONTEXT_ASSEMBLY_SERVICE_METADATA,
            DEV_WORKER_SERVICE_METADATA,
            QA_WORKER_SERVICE_METADATA,
            QUEUE_PACKET_RUNTIME_CONTROLLER_METADATA,
            QUEUE_CLAIM_RUNTIME_SERVICE_METADATA,
            PACKET_REFERENCE_RESOLUTION_SERVICE_METADATA,
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
        self.assertEqual('service', METHODOLOGY_EXECUTION_STATE_SERVICE_METADATA.kind)
        self.assertEqual('service', METHODOLOGY_EXECUTION_PROJECTION_SERVICE_METADATA.kind)
        self.assertEqual('service', METHODOLOGY_EXECUTION_PREFLIGHT_SERVICE_METADATA.kind)
        self.assertEqual('service', TECHLEAD_WORKER_SERVICE_METADATA.kind)
        self.assertEqual('service', PACKET_CONTEXT_ASSEMBLY_SERVICE_METADATA.kind)
        self.assertEqual('service', DEV_WORKER_SERVICE_METADATA.kind)
        self.assertEqual('service', QA_WORKER_SERVICE_METADATA.kind)
        self.assertEqual('service', QUEUE_PACKET_RUNTIME_CONTROLLER_METADATA.kind)
        self.assertEqual('service', QUEUE_CLAIM_RUNTIME_SERVICE_METADATA.kind)
        self.assertEqual('service', PACKET_REFERENCE_RESOLUTION_SERVICE_METADATA.kind)
        self.assertEqual('repository', IMPLEMENTATION_PLAN_REPOSITORY_METADATA.kind)
        self.assertEqual('repository', METHODOLOGY_EXECUTION_REPOSITORY_METADATA.kind)

    def test_component_registry_maps_metadata_by_name(self) -> None:
        self.assertGreaterEqual(len(GOVERNED_COMPONENTS), 6)
        self.assertIs(
            WORKFLOW_LIFECYCLE_SERVICE_METADATA,
            COMPONENT_METADATA_BY_NAME['WorkflowLifecycleService'],
        )
        self.assertIs(
            EXECUTION_PACKAGE_RESOLUTION_SERVICE_METADATA,
            COMPONENT_METADATA_BY_NAME['ExecutionPackageResolutionService'],
        )
        self.assertIs(
            IMPLEMENTATION_PLAN_REPOSITORY_METADATA,
            COMPONENT_METADATA_BY_NAME['ImplementationPlanRepository'],
        )
        self.assertIs(
            METHODOLOGY_EXECUTION_REPOSITORY_METADATA,
            COMPONENT_METADATA_BY_NAME['MethodologyExecutionRepository'],
        )
        self.assertIs(
            METHODOLOGY_EXECUTION_STATE_SERVICE_METADATA,
            COMPONENT_METADATA_BY_NAME['MethodologyExecutionStateService'],
        )
        self.assertIs(
            METHODOLOGY_EXECUTION_PROJECTION_SERVICE_METADATA,
            COMPONENT_METADATA_BY_NAME['MethodologyExecutionProjectionService'],
        )
        self.assertIs(
            METHODOLOGY_EXECUTION_PREFLIGHT_SERVICE_METADATA,
            COMPONENT_METADATA_BY_NAME['MethodologyExecutionPreflightService'],
        )
        self.assertIs(
            TECHLEAD_WORKER_SERVICE_METADATA,
            COMPONENT_METADATA_BY_NAME['TechLeadWorkerService'],
        )
        self.assertIs(
            PACKET_CONTEXT_ASSEMBLY_SERVICE_METADATA,
            COMPONENT_METADATA_BY_NAME['PacketContextAssemblyService'],
        )
        self.assertIs(
            DEV_WORKER_SERVICE_METADATA,
            COMPONENT_METADATA_BY_NAME['DevWorkerService'],
        )
        self.assertIs(
            QA_WORKER_SERVICE_METADATA,
            COMPONENT_METADATA_BY_NAME['QAWorkerService'],
        )
        self.assertIs(
            QUEUE_PACKET_RUNTIME_CONTROLLER_METADATA,
            COMPONENT_METADATA_BY_NAME['QueuePacketRuntimeController'],
        )
        self.assertIs(
            QUEUE_CLAIM_RUNTIME_SERVICE_METADATA,
            COMPONENT_METADATA_BY_NAME['QueueClaimRuntimeService'],
        )
        self.assertIs(
            PACKET_REFERENCE_RESOLUTION_SERVICE_METADATA,
            COMPONENT_METADATA_BY_NAME['PacketReferenceResolutionService'],
        )
        self.assertIs(
            PAA_OPERATOR_CLI_METADATA,
            COMPONENT_METADATA_BY_NAME['PAAOperatorCLI'],
        )


if __name__ == '__main__':
    unittest.main()

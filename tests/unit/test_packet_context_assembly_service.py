from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))

from paa_core.runtime.packets.execution_package_resolution import (
    ExecutionPackageCapabilitySummary,
    ExecutionPackageGap,
    ExecutionPackageResolutionView,
)
from paa_core.runtime.workflow.methodology_execution_projection import MethodologyExecutionStatusProjection
from paa_core.runtime.packets.context_assembly import (
    DefaultPacketContextAssemblyService,
    PACKET_CONTEXT_ASSEMBLY_SERVICE_METADATA,
    PacketContextAssemblyRequest,
)
from paa_core.runtime.packets.context_assembly.contracts import (
    PacketContextAssemblyService,
    PacketPayloadReader,
)


class _FakeProjectionService:
    def __init__(self, status_projection: MethodologyExecutionStatusProjection) -> None:
        self.status_projection = status_projection
        self.requested_execution_ids: list[str] = []

    def get_status_projection(self, methodology_execution_id: str) -> MethodologyExecutionStatusProjection:
        self.requested_execution_ids.append(methodology_execution_id)
        return self.status_projection


class _FakeExecutionPackageResolutionService:
    def __init__(self, view: ExecutionPackageResolutionView) -> None:
        self.view = view
        self.surface_requests: list[tuple[str, object | None]] = []

    def resolve_execution_context_for_surface(self, execution_surface_key: str, request=None) -> ExecutionPackageResolutionView:
        self.surface_requests.append((execution_surface_key, request))
        return self.view


class _FakePacketPayloadReader:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload
        self.paths: list[str] = []

    def read_packet_payload(self, packet_path: str) -> dict[str, object]:
        self.paths.append(packet_path)
        return self.payload


class PacketContextAssemblyServiceTests(unittest.TestCase):
    def test_metadata_is_published_for_governed_component(self) -> None:
        self.assertEqual(PACKET_CONTEXT_ASSEMBLY_SERVICE_METADATA.name, 'PacketContextAssemblyService')
        self.assertEqual(PACKET_CONTEXT_ASSEMBLY_SERVICE_METADATA.kind, 'service')

    def test_contract_protocol_exposes_runtime_service_methods(self) -> None:
        self.assertTrue(hasattr(PacketContextAssemblyService, 'assemble_packet_context'))
        self.assertTrue(hasattr(PacketContextAssemblyService, 'supports_packet_context'))

    def test_contract_protocol_exposes_required_collaborator_properties(self) -> None:
        self.assertTrue(hasattr(PacketContextAssemblyService, 'methodology_execution_repository'))
        self.assertTrue(hasattr(PacketContextAssemblyService, 'methodology_execution_projection_service'))
        self.assertTrue(hasattr(PacketContextAssemblyService, 'execution_package_resolution_service'))
        self.assertTrue(hasattr(PacketContextAssemblyService, 'packet_payload_reader'))
        self.assertTrue(hasattr(PacketContextAssemblyService, 'logger'))

    def test_packet_payload_reader_protocol_exposes_expected_loader(self) -> None:
        self.assertTrue(hasattr(PacketPayloadReader, 'read_packet_payload'))

    def test_assemble_packet_context_supports_worker_result_packet_for_techlead(self) -> None:
        projection_service = _FakeProjectionService(_status_projection())
        resolution_service = _FakeExecutionPackageResolutionService(_resolution_view())
        service = self._build_service(
            projection_service=projection_service,
            resolution_service=resolution_service,
        )

        result = service.assemble_packet_context(
            PacketContextAssemblyRequest(
                packet_schema_type='worker_result_packet',
                methodology_execution_id='exec-123',
                runtime_surface='techlead',
                packet_payload={'project_slug': 'paa-platform', 'issue_number': 42},
            )
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.methodology_execution_status.methodology_execution_id, 'exec-123')
        self.assertEqual(result.execution_package_resolution.execution_package_install_id, 'install-123')
        self.assertEqual(result.assembly_summary.context_kind, 'worker_result_review')
        self.assertEqual(result.assembly_summary.resolved_capabilities, ('packet-read', 'techlead-runtime'))
        self.assertEqual(projection_service.requested_execution_ids, ['exec-123'])
        self.assertEqual(resolution_service.surface_requests[0][0], 'techlead')

    def test_assemble_packet_context_loads_payload_from_reader_when_needed(self) -> None:
        payload_reader = _FakePacketPayloadReader({'project_slug': 'paa-platform'})
        service = self._build_service(payload_reader=payload_reader)

        result = service.assemble_packet_context(
            PacketContextAssemblyRequest(
                packet_schema_type='worker_result_packet',
                methodology_execution_id='exec-123',
                runtime_surface='techlead',
                packet_path='/tmp/packet.json',
            )
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.packet_payload, {'project_slug': 'paa-platform'})
        self.assertEqual(payload_reader.paths, ['/tmp/packet.json'])

    def test_assemble_packet_context_supports_techlead_assignment_packet_for_qa(self) -> None:
        projection_service = _FakeProjectionService(_status_projection())
        resolution_service = _FakeExecutionPackageResolutionService(_qa_resolution_view())
        service = self._build_service(
            projection_service=projection_service,
            resolution_service=resolution_service,
        )

        result = service.assemble_packet_context(
            PacketContextAssemblyRequest(
                packet_schema_type='techlead_assignment_packet',
                methodology_execution_id='exec-123',
                runtime_surface='qa',
                packet_payload={'project_slug': 'paa-platform', 'issue_number': 42},
            )
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.assembly_summary.context_kind, 'qa_assignment_execution')
        self.assertEqual(result.assembly_summary.required_capabilities, ('packet-read', 'qa-runtime'))
        self.assertEqual(result.assembly_summary.resolved_capabilities, ('packet-read', 'qa-runtime'))
        self.assertEqual(resolution_service.surface_requests[0][0], 'qa')

    def test_assemble_packet_context_supports_techlead_assignment_packet_for_dev(self) -> None:
        projection_service = _FakeProjectionService(_status_projection())
        resolution_service = _FakeExecutionPackageResolutionService(_dev_resolution_view())
        service = self._build_service(
            projection_service=projection_service,
            resolution_service=resolution_service,
        )

        result = service.assemble_packet_context(
            PacketContextAssemblyRequest(
                packet_schema_type='techlead_assignment_packet',
                methodology_execution_id='exec-123',
                runtime_surface='dev',
                packet_payload={'project_slug': 'paa-platform', 'issue_number': 42},
            )
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.assembly_summary.context_kind, 'dev_assignment_execution')
        self.assertEqual(result.assembly_summary.required_capabilities, ('packet-read', 'dev-runtime'))
        self.assertEqual(result.assembly_summary.resolved_capabilities, ('packet-read', 'dev-runtime'))
        self.assertEqual(resolution_service.surface_requests[0][0], 'dev')

    def test_assemble_packet_context_fails_closed_for_missing_execution_id(self) -> None:
        service = self._build_service()

        result = service.assemble_packet_context(
            PacketContextAssemblyRequest(
                packet_schema_type='worker_result_packet',
                runtime_surface='techlead',
                packet_payload={'project_slug': 'paa-platform'},
            )
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'missing_methodology_execution_id')
        self.assertEqual(result.assembly_summary.blocking_gaps, ('missing_methodology_execution_id',))

    def test_assemble_packet_context_fails_closed_for_missing_payload(self) -> None:
        service = self._build_service()

        result = service.assemble_packet_context(
            PacketContextAssemblyRequest(
                packet_schema_type='worker_result_packet',
                methodology_execution_id='exec-123',
                runtime_surface='techlead',
            )
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'missing_packet_payload')
        self.assertEqual(result.assembly_summary.blocking_gaps, ('missing_packet_payload',))

    def test_assemble_packet_context_fails_closed_for_unsupported_context(self) -> None:
        service = self._build_service()

        result = service.assemble_packet_context(
            PacketContextAssemblyRequest(
                packet_schema_type='qa_verification_packet',
                methodology_execution_id='exec-123',
                runtime_surface='qa',
                packet_payload={},
            )
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'unsupported_packet_context')
        self.assertEqual(result.assembly_summary.blocking_gaps, ('unsupported_packet_context',))

    def test_assemble_packet_context_fails_closed_when_execution_package_resolution_blocks(self) -> None:
        service = self._build_service(
            resolution_service=_FakeExecutionPackageResolutionService(_blocked_resolution_view()),
        )

        result = service.assemble_packet_context(
            PacketContextAssemblyRequest(
                packet_schema_type='worker_result_packet',
                methodology_execution_id='exec-123',
                runtime_surface='techlead',
                packet_payload={'project_slug': 'paa-platform', 'issue_number': 42},
            )
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'missing_active_install')
        self.assertEqual(result.assembly_summary.blocking_gaps, ('missing_active_install',))
        self.assertEqual(result.gaps[0].gap_key, 'missing_active_install')

    def _build_service(
        self,
        *,
        projection_service: _FakeProjectionService | None = None,
        resolution_service: _FakeExecutionPackageResolutionService | None = None,
        payload_reader: _FakePacketPayloadReader | None = None,
    ) -> DefaultPacketContextAssemblyService:
        projection_service = projection_service or _FakeProjectionService(_status_projection())
        resolution_service = resolution_service or _FakeExecutionPackageResolutionService(_resolution_view())
        logger = SimpleNamespace(info=lambda *args, **kwargs: None, warning=lambda *args, **kwargs: None)
        return DefaultPacketContextAssemblyService(
            methodology_execution_repository=SimpleNamespace(),
            methodology_execution_projection_service=projection_service,
            execution_package_resolution_service=resolution_service,
            packet_payload_reader=payload_reader,
            logger=logger,
        )


def _status_projection() -> MethodologyExecutionStatusProjection:
    return MethodologyExecutionStatusProjection(
        methodology_execution_id='exec-123',
        lane='component_realization',
        stage='slice_execution',
        step='techlead_worker_review_pending',
        status='active',
        current_owner_role='TechLead',
        next_action_key='review-worker-result',
        blocked_reason=None,
        component_id='component-123',
        design_package_id=None,
        implementation_plan_id='plan-123',
        coder_run_brief_id=None,
        packet_id='packet-123',
        workflow_state_id='workflow-123',
        active_authority_ref=None,
        active_artifact_ref=None,
        binding_refs=('implementation_plan:plan-123',),
        summary_text='TechLead is reviewing a worker result.',
    )


def _resolution_view() -> ExecutionPackageResolutionView:
    return ExecutionPackageResolutionView(
        execution_surface_key='techlead',
        execution_surface_type='worker_runtime',
        execution_package_install_id='install-123',
        package_name='paa-authority',
        package_version='1.0.0',
        authority_version_id='authority-123',
        active_overlay_keys=(),
        manifest_path='/runtime/manifest.json',
        package_metadata_path='/runtime/package-metadata.json',
        docs_root_path='/runtime/docs',
        artifacts_root_path='/runtime/artifacts',
        repo_root_path='/repo',
        runtime_root_path='/runtime',
        capability_summary=ExecutionPackageCapabilitySummary(
            allowed=True,
            missing_capabilities=(),
            blocking_reasons=(),
            satisfied_capabilities=('packet-read', 'techlead-runtime'),
            notes=(),
            metadata={},
        ),
        warnings=(),
        gaps=(),
        metadata={},
    )


def _blocked_resolution_view() -> ExecutionPackageResolutionView:
    return ExecutionPackageResolutionView(
        execution_surface_key='techlead',
        execution_surface_type='worker_runtime',
        execution_package_install_id=None,
        package_name=None,
        package_version=None,
        authority_version_id=None,
        active_overlay_keys=(),
        manifest_path=None,
        package_metadata_path=None,
        docs_root_path=None,
        artifacts_root_path=None,
        repo_root_path=None,
        runtime_root_path=None,
        capability_summary=ExecutionPackageCapabilitySummary(
            allowed=False,
            missing_capabilities=('packet-read',),
            blocking_reasons=('missing_active_install',),
            satisfied_capabilities=(),
            notes=(),
            metadata={},
        ),
        warnings=('No active install',),
        gaps=(
            ExecutionPackageGap(
                gap_code='missing_active_install',
                severity='blocker',
                execution_surface_key='techlead',
                execution_surface_type='worker_runtime',
                note='No active installed execution package could be resolved.',
                recommended_next_action='install execution package',
                metadata={},
            ),
        ),
        metadata={},
    )


def _qa_resolution_view() -> ExecutionPackageResolutionView:
    return ExecutionPackageResolutionView(
        execution_surface_key='qa',
        execution_surface_type='worker_runtime',
        execution_package_install_id='install-qa-123',
        package_name='paa-authority',
        package_version='1.0.0',
        authority_version_id='authority-123',
        active_overlay_keys=(),
        manifest_path='/runtime/manifest.json',
        package_metadata_path='/runtime/package-metadata.json',
        docs_root_path='/runtime/docs',
        artifacts_root_path='/runtime/artifacts',
        repo_root_path='/repo',
        runtime_root_path='/runtime',
        capability_summary=ExecutionPackageCapabilitySummary(
            allowed=True,
            missing_capabilities=(),
            blocking_reasons=(),
            satisfied_capabilities=('packet-read', 'qa-runtime'),
            notes=(),
            metadata={},
        ),
        warnings=(),
        gaps=(),
        metadata={},
    )


def _dev_resolution_view() -> ExecutionPackageResolutionView:
    return ExecutionPackageResolutionView(
        execution_surface_key='dev',
        execution_surface_type='worker_runtime',
        execution_package_install_id='install-dev-123',
        package_name='paa-authority',
        package_version='1.0.0',
        authority_version_id='authority-123',
        active_overlay_keys=(),
        manifest_path='/runtime/manifest.json',
        package_metadata_path='/runtime/package-metadata.json',
        docs_root_path='/runtime/docs',
        artifacts_root_path='/runtime/artifacts',
        repo_root_path='/repo',
        runtime_root_path='/runtime',
        capability_summary=ExecutionPackageCapabilitySummary(
            allowed=True,
            missing_capabilities=(),
            blocking_reasons=(),
            satisfied_capabilities=('packet-read', 'dev-runtime'),
            notes=(),
            metadata={},
        ),
        warnings=(),
        gaps=(),
        metadata={},
    )


if __name__ == '__main__':
    unittest.main()

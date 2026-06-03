from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))

from paa_core.services.dev_worker import (
    DEV_WORKER_SERVICE_METADATA,
    DefaultDevWorkerService,
    DevWorkerRequest,
)
from paa_core.runtime.workers.dev_worker.contracts import (
    DevExecutionRunner,
    DevWorkerService,
    WorkerResultPacketAssembler,
)
from paa_core.runtime.packets.execution_package_resolution import (
    ExecutionPackageCapabilitySummary,
    ExecutionPackageGap,
    ExecutionPackageResolutionView,
)
from paa_core.runtime.workflow.methodology_execution_projection import MethodologyExecutionStatusProjection
from paa_core.runtime.packets.context_assembly import DefaultPacketContextAssemblyService


class DevWorkerServiceContractTests(unittest.TestCase):
    def test_metadata_is_published_for_governed_component(self) -> None:
        self.assertEqual(DEV_WORKER_SERVICE_METADATA.name, 'DevWorkerService')
        self.assertEqual(DEV_WORKER_SERVICE_METADATA.kind, 'service')

    def test_contract_protocol_exposes_runtime_service_methods(self) -> None:
        self.assertTrue(hasattr(DevWorkerService, 'handle_packet'))
        self.assertTrue(hasattr(DevWorkerService, 'supports_packet_schema_type'))

    def test_contract_protocol_exposes_required_collaborator_properties(self) -> None:
        self.assertTrue(hasattr(DevWorkerService, 'packet_context_assembly_service'))
        self.assertTrue(hasattr(DevWorkerService, 'methodology_execution_state_service'))
        self.assertTrue(hasattr(DevWorkerService, 'methodology_execution_projection_service'))
        self.assertTrue(hasattr(DevWorkerService, 'execution_runner'))
        self.assertTrue(hasattr(DevWorkerService, 'worker_result_packet_assembler'))
        self.assertTrue(hasattr(DevWorkerService, 'logger'))

    def test_execution_runner_protocol_exposes_expected_run_method(self) -> None:
        self.assertTrue(hasattr(DevExecutionRunner, 'run_dev_execution'))

    def test_worker_result_packet_assembler_protocol_exposes_expected_assembler(self) -> None:
        self.assertTrue(hasattr(WorkerResultPacketAssembler, 'assemble_worker_result_packet'))


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


class _FakeExecutionRunner:
    def __init__(self, execution_result: object) -> None:
        self.execution_result = execution_result
        self.contexts: list[object] = []

    def run_dev_execution(self, context: object) -> object:
        self.contexts.append(context)
        return self.execution_result


class _FakeWorkerResultPacketAssembler:
    def __init__(self, packet_output: object) -> None:
        self.packet_output = packet_output
        self.execution_results: list[object] = []

    def assemble_worker_result_packet(self, execution_result: object) -> object:
        self.execution_results.append(execution_result)
        return self.packet_output


class DevWorkerServiceTests(unittest.TestCase):
    def test_handle_packet_supports_techlead_assignment_packet_dry_run(self) -> None:
        projection = _status_projection()
        packet_context_service = _packet_context_service(status_projection=projection)
        execution_runner = _FakeExecutionRunner({'status': 'ok', 'changed_files': ('file.py',)})
        packet_assembler = _FakeWorkerResultPacketAssembler('worker_result_packet ready')
        service = self._build_service(
            packet_context_service=packet_context_service,
            projection_service=_FakeProjectionService(projection),
            execution_runner=execution_runner,
            packet_assembler=packet_assembler,
        )

        result = service.handle_packet(
            DevWorkerRequest(
                packet_schema_type='techlead_assignment_packet',
                packet_message_id='msg-123',
                methodology_execution_id='exec-123',
                packet_payload={'project_slug': 'paa-platform', 'issue_number': 42},
            )
        )

        self.assertTrue(result.ok)
        self.assertTrue(result.dry_run)
        self.assertEqual(result.methodology_execution_id, 'exec-123')
        self.assertEqual(result.execution_summary.handler_key, 'dev-assignment-dry-run')
        self.assertTrue(result.execution_summary.packet_context_ok)
        self.assertEqual(result.current_execution_summary, projection)
        self.assertEqual(result.execution_result, {'status': 'ok', 'changed_files': ('file.py',)})
        self.assertEqual(result.normalized_packet_output_summary, 'worker_result_packet ready')
        self.assertEqual(len(execution_runner.contexts), 1)
        self.assertEqual(packet_assembler.execution_results, [{'status': 'ok', 'changed_files': ('file.py',)}])

    def test_handle_packet_fails_closed_for_unsupported_packet_schema_type(self) -> None:
        service = self._build_service()

        result = service.handle_packet(
            DevWorkerRequest(
                packet_schema_type='worker_result_packet',
                methodology_execution_id='exec-123',
            )
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'unsupported_packet_schema_type')
        self.assertEqual(result.execution_summary.handler_key, 'packet-classification')
        self.assertEqual(result.execution_summary.blocking_reasons, ('unsupported_packet_schema_type',))
        self.assertIsNone(result.packet_context_result)

    def test_handle_packet_fails_closed_for_live_mode(self) -> None:
        service = self._build_service()

        result = service.handle_packet(
            DevWorkerRequest(
                packet_schema_type='techlead_assignment_packet',
                methodology_execution_id='exec-123',
                runtime_mode='live',
            )
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'unsupported_runtime_mode')
        self.assertEqual(result.execution_summary.handler_key, 'runtime-mode-check')
        self.assertEqual(result.execution_summary.notes, ('fail-closed', 'dry-run-only'))
        self.assertFalse(result.dry_run)

    def test_handle_packet_fails_closed_when_packet_context_blocks(self) -> None:
        service = self._build_service(packet_context_service=_packet_context_service(block_resolution=True))

        result = service.handle_packet(
            DevWorkerRequest(
                packet_schema_type='techlead_assignment_packet',
                methodology_execution_id='exec-123',
                packet_payload={'project_slug': 'paa-platform', 'issue_number': 42},
            )
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'missing_active_install')
        self.assertEqual(result.execution_summary.handler_key, 'packet-context-assembly')
        self.assertEqual(result.execution_summary.blocking_reasons, ('missing_active_install',))
        self.assertIsNotNone(result.packet_context_result)

    def test_handle_packet_uses_context_summary_when_projection_matches(self) -> None:
        projection = _status_projection()
        runtime_projection_service = _FakeProjectionService(projection)
        packet_context_service = _packet_context_service(status_projection=projection)
        service = self._build_service(
            packet_context_service=packet_context_service,
            projection_service=runtime_projection_service,
        )

        result = service.handle_packet(
            DevWorkerRequest(
                packet_schema_type='techlead_assignment_packet',
                methodology_execution_id='exec-123',
                packet_payload={'project_slug': 'paa-platform', 'issue_number': 42},
            )
        )

        self.assertTrue(result.ok)
        self.assertEqual(runtime_projection_service.requested_execution_ids, [])

    def _build_service(
        self,
        *,
        packet_context_service: DefaultPacketContextAssemblyService | None = None,
        projection_service: _FakeProjectionService | None = None,
        execution_runner: _FakeExecutionRunner | None = None,
        packet_assembler: _FakeWorkerResultPacketAssembler | None = None,
    ) -> DefaultDevWorkerService:
        projection_service = projection_service or _FakeProjectionService(_status_projection())
        packet_context_service = packet_context_service or _packet_context_service(
            status_projection=projection_service.status_projection
        )
        execution_runner = execution_runner or _FakeExecutionRunner({'status': 'ok'})
        packet_assembler = packet_assembler or _FakeWorkerResultPacketAssembler('worker_result_packet ready')
        logger = SimpleNamespace(info=lambda *args, **kwargs: None, warning=lambda *args, **kwargs: None)
        unused = SimpleNamespace()
        return DefaultDevWorkerService(
            packet_context_assembly_service=packet_context_service,
            methodology_execution_state_service=unused,
            methodology_execution_projection_service=projection_service,
            execution_runner=execution_runner,
            worker_result_packet_assembler=packet_assembler,
            logger=logger,
        )


def _packet_context_service(
    *,
    status_projection: MethodologyExecutionStatusProjection | None = None,
    block_resolution: bool = False,
) -> DefaultPacketContextAssemblyService:
    status_projection = status_projection or _status_projection()
    projection_service = _FakeProjectionService(status_projection)
    resolution_service = _FakeExecutionPackageResolutionService(
        _blocked_resolution_view() if block_resolution else _resolution_view()
    )
    logger = SimpleNamespace(info=lambda *args, **kwargs: None, warning=lambda *args, **kwargs: None)
    return DefaultPacketContextAssemblyService(
        methodology_execution_repository=SimpleNamespace(),
        methodology_execution_projection_service=projection_service,
        execution_package_resolution_service=resolution_service,
        packet_payload_reader=None,
        logger=logger,
    )


def _status_projection() -> MethodologyExecutionStatusProjection:
    return MethodologyExecutionStatusProjection(
        methodology_execution_id='exec-123',
        lane='component_realization',
        stage='slice_execution',
        step='dev_assignment_ready',
        status='active',
        current_owner_role='Dev',
        next_action_key='run-assignment',
        blocked_reason=None,
        component_id='component-123',
        design_package_id=None,
        implementation_plan_id='plan-123',
        coder_run_brief_id='brief-123',
        packet_id='packet-123',
        workflow_state_id='workflow-123',
        active_authority_ref=None,
        active_artifact_ref=None,
        binding_refs=('implementation_plan:plan-123',),
        summary_text='Dev worker is ready to execute the assignment.',
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


if __name__ == '__main__':
    unittest.main()

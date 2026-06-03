from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))

from paa_core.runtime.workflow.methodology_execution_projection import MethodologyExecutionStatusProjection
from paa_core.runtime.packets.context_assembly import (
    PacketContextAssemblyRequest,
    PacketContextAssemblyResult,
    PacketContextAssemblySummary,
)
from paa_core.services.qa_worker import (
    DefaultQAWorkerService,
    QA_WORKER_SERVICE_METADATA,
    QAWorkerRequest,
)
from paa_core.runtime.workers.qa_worker.contracts import (
    QAVerificationPacketAssembler,
    QAVerificationRunner,
    QAWorkerService,
)


class QAWorkerServiceContractTests(unittest.TestCase):
    def test_metadata_is_published_for_governed_component(self) -> None:
        self.assertEqual(QA_WORKER_SERVICE_METADATA.name, 'QAWorkerService')
        self.assertEqual(QA_WORKER_SERVICE_METADATA.kind, 'service')

    def test_contract_protocol_exposes_runtime_service_methods(self) -> None:
        self.assertTrue(hasattr(QAWorkerService, 'handle_packet'))
        self.assertTrue(hasattr(QAWorkerService, 'supports_packet_schema_type'))

    def test_contract_protocol_exposes_required_collaborator_properties(self) -> None:
        self.assertTrue(hasattr(QAWorkerService, 'packet_context_assembly_service'))
        self.assertTrue(hasattr(QAWorkerService, 'methodology_execution_state_service'))
        self.assertTrue(hasattr(QAWorkerService, 'methodology_execution_projection_service'))
        self.assertTrue(hasattr(QAWorkerService, 'verification_runner'))
        self.assertTrue(hasattr(QAWorkerService, 'qa_verification_packet_assembler'))
        self.assertTrue(hasattr(QAWorkerService, 'logger'))

    def test_verification_runner_protocol_exposes_expected_run_method(self) -> None:
        self.assertTrue(hasattr(QAVerificationRunner, 'run_qa_verification'))

    def test_qa_verification_packet_assembler_protocol_exposes_expected_assembler(self) -> None:
        self.assertTrue(hasattr(QAVerificationPacketAssembler, 'assemble_qa_verification_packet'))


class _FakeProjectionService:
    def __init__(self, status_projection: MethodologyExecutionStatusProjection) -> None:
        self.status_projection = status_projection
        self.requested_execution_ids: list[str] = []

    def get_status_projection(self, methodology_execution_id: str) -> MethodologyExecutionStatusProjection:
        self.requested_execution_ids.append(methodology_execution_id)
        return self.status_projection


class _FakePacketContextAssemblyService:
    def __init__(self, result: PacketContextAssemblyResult) -> None:
        self.result = result
        self.requests: list[PacketContextAssemblyRequest] = []

    def assemble_packet_context(self, request: PacketContextAssemblyRequest) -> PacketContextAssemblyResult:
        self.requests.append(request)
        return self.result

    def supports_packet_context(self, packet_schema_type: str, runtime_surface: str) -> bool:
        return packet_schema_type == 'techlead_assignment_packet' and runtime_surface == 'qa'


class _FakeVerificationRunner:
    def __init__(self, verification_result: object) -> None:
        self.verification_result = verification_result
        self.contexts: list[object] = []

    def run_qa_verification(self, context: object) -> object:
        self.contexts.append(context)
        return self.verification_result


class _FakeQAVerificationPacketAssembler:
    def __init__(self, packet_output: object) -> None:
        self.packet_output = packet_output
        self.verification_results: list[object] = []

    def assemble_qa_verification_packet(self, verification_result: object) -> object:
        self.verification_results.append(verification_result)
        return self.packet_output


class QAWorkerServiceTests(unittest.TestCase):
    def test_handle_packet_supports_techlead_assignment_packet_dry_run(self) -> None:
        projection = _status_projection()
        packet_context_service = _packet_context_service(status_projection=projection)
        verification_runner = _FakeVerificationRunner({'verification_status': 'pass', 'findings': ()})
        packet_assembler = _FakeQAVerificationPacketAssembler('qa_verification_packet ready')
        service = self._build_service(
            packet_context_service=packet_context_service,
            projection_service=_FakeProjectionService(projection),
            verification_runner=verification_runner,
            packet_assembler=packet_assembler,
        )

        result = service.handle_packet(
            QAWorkerRequest(
                packet_schema_type='techlead_assignment_packet',
                packet_message_id='msg-123',
                methodology_execution_id='exec-123',
                packet_payload={'project_slug': 'paa-platform', 'issue_number': 42},
            )
        )

        self.assertTrue(result.ok)
        self.assertTrue(result.dry_run)
        self.assertEqual(result.methodology_execution_id, 'exec-123')
        self.assertEqual(result.verification_summary.handler_key, 'qa-verification-dry-run')
        self.assertTrue(result.verification_summary.packet_context_ok)
        self.assertEqual(result.current_execution_summary, projection)
        self.assertEqual(result.verification_result, {'verification_status': 'pass', 'findings': ()})
        self.assertEqual(result.normalized_packet_output_summary, 'qa_verification_packet ready')
        self.assertEqual(len(verification_runner.contexts), 1)
        self.assertEqual(packet_assembler.verification_results, [{'verification_status': 'pass', 'findings': ()}])

    def test_handle_packet_fails_closed_for_unsupported_packet_schema_type(self) -> None:
        service = self._build_service()

        result = service.handle_packet(
            QAWorkerRequest(
                packet_schema_type='worker_result_packet',
                methodology_execution_id='exec-123',
            )
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'unsupported_packet_schema_type')
        self.assertEqual(result.verification_summary.handler_key, 'packet-classification')
        self.assertEqual(result.verification_summary.blocking_reasons, ('unsupported_packet_schema_type',))
        self.assertIsNone(result.packet_context_result)

    def test_handle_packet_fails_closed_for_live_mode(self) -> None:
        service = self._build_service()

        result = service.handle_packet(
            QAWorkerRequest(
                packet_schema_type='techlead_assignment_packet',
                methodology_execution_id='exec-123',
                runtime_mode='live',
            )
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'unsupported_runtime_mode')
        self.assertEqual(result.verification_summary.handler_key, 'runtime-mode-check')
        self.assertEqual(result.verification_summary.notes, ('fail-closed', 'dry-run-only'))
        self.assertFalse(result.dry_run)

    def test_handle_packet_fails_closed_when_packet_context_blocks(self) -> None:
        service = self._build_service(packet_context_service=_packet_context_service(blocked=True))

        result = service.handle_packet(
            QAWorkerRequest(
                packet_schema_type='techlead_assignment_packet',
                methodology_execution_id='exec-123',
                packet_payload={'project_slug': 'paa-platform', 'issue_number': 42},
            )
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'unsupported_packet_context')
        self.assertEqual(result.verification_summary.handler_key, 'packet-context-assembly')
        self.assertEqual(result.verification_summary.blocking_reasons, ('unsupported_packet_context',))
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
            QAWorkerRequest(
                packet_schema_type='techlead_assignment_packet',
                methodology_execution_id='exec-123',
                packet_payload={'project_slug': 'paa-platform', 'issue_number': 42},
            )
        )

        self.assertTrue(result.ok)
        self.assertEqual(runtime_projection_service.requested_execution_ids, [])

    def test_handle_packet_reports_non_string_packet_output_with_normalized_summary(self) -> None:
        service = self._build_service(
            packet_assembler=_FakeQAVerificationPacketAssembler({'schema_type': 'qa_verification_packet'}),
        )

        result = service.handle_packet(
            QAWorkerRequest(
                packet_schema_type='techlead_assignment_packet',
                methodology_execution_id='exec-123',
                packet_payload={'project_slug': 'paa-platform', 'issue_number': 42},
            )
        )

        self.assertTrue(result.ok)
        self.assertIn('prepared as dict', result.normalized_packet_output_summary or '')

    def _build_service(
        self,
        *,
        packet_context_service: _FakePacketContextAssemblyService | None = None,
        projection_service: _FakeProjectionService | None = None,
        verification_runner: _FakeVerificationRunner | None = None,
        packet_assembler: _FakeQAVerificationPacketAssembler | None = None,
    ) -> DefaultQAWorkerService:
        projection_service = projection_service or _FakeProjectionService(_status_projection())
        packet_context_service = packet_context_service or _packet_context_service(
            status_projection=projection_service.status_projection
        )
        verification_runner = verification_runner or _FakeVerificationRunner({'verification_status': 'pass'})
        packet_assembler = packet_assembler or _FakeQAVerificationPacketAssembler('qa_verification_packet ready')
        logger = SimpleNamespace(info=lambda *args, **kwargs: None, warning=lambda *args, **kwargs: None)
        unused = SimpleNamespace()
        return DefaultQAWorkerService(
            packet_context_assembly_service=packet_context_service,
            methodology_execution_state_service=unused,
            methodology_execution_projection_service=projection_service,
            verification_runner=verification_runner,
            qa_verification_packet_assembler=packet_assembler,
            logger=logger,
        )


def _packet_context_service(
    *,
    status_projection: MethodologyExecutionStatusProjection | None = None,
    blocked: bool = False,
) -> _FakePacketContextAssemblyService:
    status_projection = status_projection or _status_projection()
    request = PacketContextAssemblyRequest(
        packet_schema_type='techlead_assignment_packet',
        methodology_execution_id='exec-123',
        runtime_surface='qa',
        packet_payload={'project_slug': 'paa-platform', 'issue_number': 42},
    )
    if blocked:
        result = PacketContextAssemblyResult(
            request=request,
            methodology_execution_status=status_projection,
            execution_package_resolution=None,
            packet_payload=request.packet_payload,
            assembly_summary=PacketContextAssemblySummary(
                packet_schema_type='techlead_assignment_packet',
                runtime_surface='qa',
                methodology_execution_id='exec-123',
                execution_package_id=None,
                context_kind='qa_assignment_execution',
                assembly_supported=False,
                required_capabilities=('packet-read', 'qa-runtime'),
                resolved_capabilities=(),
                blocking_gaps=('unsupported_packet_context',),
                notes=('fail-closed',),
            ),
            gaps=(),
            ok=False,
            reason='unsupported_packet_context',
            details='The provided QA packet context is unsupported in this blocked test path.',
        )
        return _FakePacketContextAssemblyService(result)

    result = PacketContextAssemblyResult(
        request=request,
        methodology_execution_status=status_projection,
        execution_package_resolution=None,
        packet_payload=request.packet_payload,
        assembly_summary=PacketContextAssemblySummary(
            packet_schema_type='techlead_assignment_packet',
            runtime_surface='qa',
            methodology_execution_id='exec-123',
            execution_package_id='install-123',
            context_kind='qa_assignment_execution',
            assembly_supported=True,
            required_capabilities=('packet-read', 'qa-runtime'),
            resolved_capabilities=('packet-read', 'qa-runtime'),
            blocking_gaps=(),
            notes=('dry-run-supported',),
        ),
        gaps=(),
        ok=True,
    )
    return _FakePacketContextAssemblyService(result)


def _status_projection() -> MethodologyExecutionStatusProjection:
    return MethodologyExecutionStatusProjection(
        methodology_execution_id='exec-123',
        lane='component_realization',
        stage='slice_execution',
        step='qa_verification_ready',
        status='active',
        current_owner_role='QA',
        next_action_key='verify-assignment',
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
        summary_text='QA worker is ready to verify the assignment.',
    )


if __name__ == '__main__':
    unittest.main()

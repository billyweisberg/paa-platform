from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))

from paa_core.runtime.hosts.dev import DevRuntimeHost, _WorkerResultPublisher
from paa_core.runtime.workers.dev_worker import DevWorkerExecutionSummary, DevWorkerRequest, DevWorkerResult
from paa_core.runtime.packets.reference_resolution import (
    PacketReferenceResolutionRequest,
    PacketReferenceResolutionResult,
    PacketReferenceResolutionSummary,
)
from paa_core.runtime.orchestration.queue_claim_runtime import (
    QueueClaimRuntimeRequest,
    QueueClaimRuntimeResult,
    QueuePacketClaimSummary,
    QueuePacketPreviewSummary,
)


class _FakeQueueClaimRuntimeService:
    def __init__(self, result: QueueClaimRuntimeResult) -> None:
        self.result = result
        self.calls: list[QueueClaimRuntimeRequest] = []

    def assemble_queue_intake(self, request: QueueClaimRuntimeRequest) -> QueueClaimRuntimeResult:
        self.calls.append(request)
        return self.result


class _FakePacketReferenceResolutionService:
    def __init__(self, result: PacketReferenceResolutionResult) -> None:
        self.result = result
        self.calls: list[PacketReferenceResolutionRequest] = []

    def resolve_packet_reference(self, request: PacketReferenceResolutionRequest) -> PacketReferenceResolutionResult:
        self.calls.append(request)
        return self.result


class _FakeDevWorkerService:
    def __init__(self, result: DevWorkerResult) -> None:
        self.result = result
        self.calls: list[DevWorkerRequest] = []

    def handle_packet(self, request: DevWorkerRequest) -> DevWorkerResult:
        self.calls.append(request)
        return self.result


class _FakeWorkerResultPublisher:
    def __init__(self, result: dict[str, object] | None = None) -> None:
        self.result = result if result is not None else {'ok': True, 'message_id': 'dev-1', 'resolved_queue': 'paa-techlead'}
        self.calls: list[dict[str, object]] = []

    def publish_worker_result(
        self,
        *,
        worker_result,
        source_packet_message_id: str | None,
        source_packet_path: str | None,
    ) -> dict[str, object] | None:
        self.calls.append(
            {
                'worker_result': worker_result,
                'source_packet_message_id': source_packet_message_id,
                'source_packet_path': source_packet_path,
            }
        )
        return self.result


class _FakeQueueClaimLifecycleAdapter:
    def __init__(self) -> None:
        self.acks: list[str] = []
        self.requeues: list[str] = []

    def acknowledge_claim(self, claim_id: str) -> dict[str, object]:
        self.acks.append(claim_id)
        return {'ok': True, 'claim_id': claim_id, 'status': 'done'}

    def requeue_claim(self, claim_id: str) -> dict[str, object]:
        self.requeues.append(claim_id)
        return {'ok': True, 'claim_id': claim_id, 'status': 'requeued'}


class DevRuntimeHostTests(unittest.TestCase):
    def test_run_once_claims_resolves_and_executes_one_packet(self) -> None:
        claim_result = QueueClaimRuntimeResult(
            request=QueueClaimRuntimeRequest(queue_name='paa-dev', intake_mode='claim_next'),
            preview_summary=QueuePacketPreviewSummary(
                queue_name='paa-dev',
                packet_message_id='msg-dev-1',
                packet_schema_type='techlead_assignment_packet',
                packet_reference='msg-dev-1',
                preview_supported=True,
                claim_supported=True,
                blocking_reasons=(),
                notes=('preview',),
            ),
            claim_summary=QueuePacketClaimSummary(
                queue_name='paa-dev',
                claim_id='claim-dev-1',
                claimant_name='Dev Agent',
                packet_message_id='msg-dev-1',
                packet_reference='msg-dev-1',
                claim_supported=True,
                blocking_reasons=(),
                notes=('claimed',),
            ),
            normalized_packet_envelope={'packet_message_id': 'msg-dev-1', 'packet_schema_type': 'techlead_assignment_packet', 'packet_reference': 'msg-dev-1'},
            normalized_packet_payload=None,
            ok=True,
            metadata={'claim': True},
        )
        resolution_result = PacketReferenceResolutionResult(
            request=PacketReferenceResolutionRequest(packet_message_id='msg-dev-1'),
            resolution_summary=PacketReferenceResolutionSummary(
                resolution_source='message-id',
                packet_message_id='msg-dev-1',
                packet_schema_type='techlead_assignment_packet',
                queue_name='paa-dev',
                packet_reference='msg-dev-1',
                resolved_packet_path='/tmp/dev-assignment.json',
                resolution_supported=True,
                blocking_reasons=(),
                notes=('message-id', 'resolved-artifact-path'),
            ),
            normalized_packet_payload={'methodology_execution_id': 'exec-dev-1', 'issue_number': 6},
            ok=True,
            metadata={'resolution': True},
        )
        worker_result = DevWorkerResult(
            request=DevWorkerRequest(packet_schema_type='techlead_assignment_packet'),
            methodology_execution_id='exec-dev-1',
            current_execution_summary=None,
            packet_context_result=None,
            execution_summary=DevWorkerExecutionSummary(
                handler_key='dev-assignment-dry-run',
                packet_schema_type='techlead_assignment_packet',
                runtime_mode='dry_run',
                execution_supported=True,
                execution_runner_used='Runner',
                packet_context_required=True,
                packet_context_ok=True,
                worker_result_packet_required=True,
                methodology_transition_required=False,
                blocking_reasons=(),
                notes=('dry-run-only',),
            ),
            execution_result={'worker_result_type': 'implemented_ready_for_qa'},
            methodology_transition_result=None,
            normalized_packet_output_summary='worker_result_packet ready',
            ok=True,
            metadata={'execution': True},
        )
        host = DevRuntimeHost(
            queue_name='paa-dev',
            queue_claim_runtime_service=_FakeQueueClaimRuntimeService(claim_result),
            queue_claim_lifecycle_adapter=_FakeQueueClaimLifecycleAdapter(),
            packet_reference_resolution_service=_FakePacketReferenceResolutionService(resolution_result),
            dev_worker_service=_FakeDevWorkerService(worker_result),
            worker_result_publisher=None,
            actor_name='Dev Agent',
            host_name='dev-runtime-host',
        )

        result = host.run_once(intake_mode='claim_next')

        self.assertTrue(result.ok)
        self.assertEqual(result.claim_id, 'claim-dev-1')
        self.assertEqual(result.packet_message_id, 'msg-dev-1')
        self.assertEqual(result.packet_path, '/tmp/dev-assignment.json')

    def test_run_once_claim_next_can_emit_worker_result_after_success(self) -> None:
        claim_result = QueueClaimRuntimeResult(
            request=QueueClaimRuntimeRequest(queue_name='paa-dev', intake_mode='claim_next'),
            preview_summary=None,
            claim_summary=QueuePacketClaimSummary(
                queue_name='paa-dev',
                claim_id='claim-dev-2',
                claimant_name='Dev Agent',
                packet_message_id='msg-dev-2',
                packet_reference='msg-dev-2',
                claim_supported=True,
                blocking_reasons=(),
                notes=('claimed',),
            ),
            normalized_packet_envelope={'packet_message_id': 'msg-dev-2', 'packet_schema_type': 'techlead_assignment_packet', 'packet_reference': 'msg-dev-2'},
            normalized_packet_payload=None,
            ok=True,
            metadata={'claim': True},
        )
        resolution_result = PacketReferenceResolutionResult(
            request=PacketReferenceResolutionRequest(packet_message_id='msg-dev-2'),
            resolution_summary=PacketReferenceResolutionSummary(
                resolution_source='message-id',
                packet_message_id='msg-dev-2',
                packet_schema_type='techlead_assignment_packet',
                queue_name='paa-dev',
                packet_reference='msg-dev-2',
                resolved_packet_path='/tmp/dev-assignment.json',
                resolution_supported=True,
                blocking_reasons=(),
                notes=('message-id',),
            ),
            normalized_packet_payload={'methodology_execution_id': 'exec-dev-2', 'issue_number': 6},
            ok=True,
            metadata=None,
        )
        worker_result = DevWorkerResult(
            request=DevWorkerRequest(packet_schema_type='techlead_assignment_packet'),
            methodology_execution_id='exec-dev-2',
            current_execution_summary=None,
            packet_context_result=None,
            execution_summary=DevWorkerExecutionSummary(
                handler_key='dev-assignment-dry-run',
                packet_schema_type='techlead_assignment_packet',
                runtime_mode='dry_run',
                execution_supported=True,
                execution_runner_used='Runner',
                packet_context_required=True,
                packet_context_ok=True,
                worker_result_packet_required=True,
                methodology_transition_required=False,
                blocking_reasons=(),
                notes=('dry-run-only',),
            ),
            execution_result={'worker_result_type': 'implemented_ready_for_qa'},
            methodology_transition_result=None,
            normalized_packet_output_summary='worker_result_packet ready',
            ok=True,
            metadata=None,
        )
        publisher = _FakeWorkerResultPublisher()
        lifecycle = _FakeQueueClaimLifecycleAdapter()
        host = DevRuntimeHost(
            queue_name='paa-dev',
            queue_claim_runtime_service=_FakeQueueClaimRuntimeService(claim_result),
            queue_claim_lifecycle_adapter=lifecycle,
            packet_reference_resolution_service=_FakePacketReferenceResolutionService(resolution_result),
            dev_worker_service=_FakeDevWorkerService(worker_result),
            worker_result_publisher=publisher,
            actor_name='Dev Agent',
            host_name='dev-runtime-host',
        )

        result = host.run_once(intake_mode='claim_next', emit_worker_result=True)

        self.assertTrue(result.ok)
        self.assertEqual(result.emitted_worker_result, {'ok': True, 'message_id': 'dev-1', 'resolved_queue': 'paa-techlead'})
        self.assertEqual(len(publisher.calls), 1)
        self.assertEqual(lifecycle.acks, ['claim-dev-2'])

    def test_run_once_requeues_claim_when_execution_fails(self) -> None:
        claim_result = QueueClaimRuntimeResult(
            request=QueueClaimRuntimeRequest(queue_name='paa-dev', intake_mode='claim_next'),
            preview_summary=None,
            claim_summary=QueuePacketClaimSummary(
                queue_name='paa-dev',
                claim_id='claim-dev-fail-1',
                claimant_name='Dev Agent',
                packet_message_id='msg-dev-fail-1',
                packet_reference='msg-dev-fail-1',
                claim_supported=True,
                blocking_reasons=(),
                notes=('claimed',),
            ),
            normalized_packet_envelope={'packet_message_id': 'msg-dev-fail-1', 'packet_schema_type': 'techlead_assignment_packet', 'packet_reference': 'msg-dev-fail-1'},
            normalized_packet_payload=None,
            ok=True,
            metadata={'claim': True},
        )
        resolution_result = PacketReferenceResolutionResult(
            request=PacketReferenceResolutionRequest(packet_message_id='msg-dev-fail-1'),
            resolution_summary=PacketReferenceResolutionSummary(
                resolution_source='message-id',
                packet_message_id='msg-dev-fail-1',
                packet_schema_type='techlead_assignment_packet',
                queue_name='paa-dev',
                packet_reference='msg-dev-fail-1',
                resolved_packet_path='/tmp/dev-assignment.json',
                resolution_supported=True,
                blocking_reasons=(),
                notes=('message-id',),
            ),
            normalized_packet_payload={'methodology_execution_id': 'exec-dev-fail-1', 'issue_number': 6},
            ok=True,
            metadata=None,
        )
        worker_result = DevWorkerResult(
            request=DevWorkerRequest(packet_schema_type='techlead_assignment_packet'),
            methodology_execution_id='exec-dev-fail-1',
            current_execution_summary=None,
            packet_context_result=None,
            execution_summary=DevWorkerExecutionSummary(
                handler_key='dev-assignment-dry-run',
                packet_schema_type='techlead_assignment_packet',
                runtime_mode='dry_run',
                execution_supported=False,
                execution_runner_used='Runner',
                packet_context_required=True,
                packet_context_ok=True,
                worker_result_packet_required=True,
                methodology_transition_required=False,
                blocking_reasons=('blocked',),
                notes=('dry-run-only',),
            ),
            execution_result=None,
            methodology_transition_result=None,
            normalized_packet_output_summary=None,
            ok=False,
            reason='blocked',
            details='Execution blocked.',
            metadata=None,
        )
        lifecycle = _FakeQueueClaimLifecycleAdapter()
        host = DevRuntimeHost(
            queue_name='paa-dev',
            queue_claim_runtime_service=_FakeQueueClaimRuntimeService(claim_result),
            queue_claim_lifecycle_adapter=lifecycle,
            packet_reference_resolution_service=_FakePacketReferenceResolutionService(resolution_result),
            dev_worker_service=_FakeDevWorkerService(worker_result),
            worker_result_publisher=None,
            actor_name='Dev Agent',
            host_name='dev-runtime-host',
        )

        result = host.run_once(intake_mode='claim_next')

        self.assertFalse(result.ok)
        self.assertEqual(lifecycle.requeues, ['claim-dev-fail-1'])

    def test_worker_result_publisher_message_ids_are_unique_per_run(self) -> None:
        publisher = _WorkerResultPublisher(
            repo_root=ROOT,
            project_slug='paa-platform',
            github_repo='billyweisberg/paa-platform',
        )

        first = publisher._build_message_id(issue_number=6, worker_result_type='implemented_ready_for_qa')
        second = publisher._build_message_id(issue_number=6, worker_result_type='implemented_ready_for_qa')

        self.assertNotEqual(first, second)
        self.assertRegex(
            first,
            r'^paa-dev-\d{8}T\d{6}Z-issue6-implemented-ready-for-qa-[0-9a-f]{8}$',
        )


if __name__ == '__main__':
    unittest.main()

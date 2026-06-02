from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))
sys.path.insert(0, str(ROOT / 'packages' / 'paa-consumer' / 'src'))

from paa_consumer.hosts.qa_runtime import QARuntimeHost, _QAVerificationPublisher
from paa_core.services.packet_reference_resolution import (
    PacketReferenceResolutionRequest,
    PacketReferenceResolutionResult,
    PacketReferenceResolutionSummary,
)
from paa_core.services.qa_worker import QAWorkerRequest, QAWorkerResult, QAWorkerVerificationSummary
from paa_core.services.queue_claim_runtime import (
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


class _FakeQAWorkerService:
    def __init__(self, result: QAWorkerResult) -> None:
        self.result = result
        self.calls: list[QAWorkerRequest] = []

    def handle_packet(self, request: QAWorkerRequest) -> QAWorkerResult:
        self.calls.append(request)
        return self.result


class _FakeVerificationPublisher:
    def __init__(self, result: dict[str, object] | None = None) -> None:
        self.result = result if result is not None else {'ok': True, 'message_id': 'qa-1', 'resolved_queue': 'paa-techlead'}
        self.calls: list[dict[str, object]] = []

    def publish_verification_result(
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


class QARuntimeHostTests(unittest.TestCase):
    def test_run_once_claims_resolves_and_verifies_one_packet(self) -> None:
        claim_result = QueueClaimRuntimeResult(
            request=QueueClaimRuntimeRequest(queue_name='paa-qa', intake_mode='claim_next'),
            preview_summary=QueuePacketPreviewSummary(
                queue_name='paa-qa',
                packet_message_id='msg-qa-1',
                packet_schema_type='techlead_assignment_packet',
                packet_reference='msg-qa-1',
                preview_supported=True,
                claim_supported=True,
                blocking_reasons=(),
                notes=('preview',),
            ),
            claim_summary=QueuePacketClaimSummary(
                queue_name='paa-qa',
                claim_id='claim-qa-1',
                claimant_name='QA Agent',
                packet_message_id='msg-qa-1',
                packet_reference='msg-qa-1',
                claim_supported=True,
                blocking_reasons=(),
                notes=('claimed',),
            ),
            normalized_packet_envelope={'packet_message_id': 'msg-qa-1', 'packet_schema_type': 'techlead_assignment_packet', 'packet_reference': 'msg-qa-1'},
            normalized_packet_payload=None,
            ok=True,
            metadata={'claim': True},
        )
        resolution_result = PacketReferenceResolutionResult(
            request=PacketReferenceResolutionRequest(packet_message_id='msg-qa-1'),
            resolution_summary=PacketReferenceResolutionSummary(
                resolution_source='message-id',
                packet_message_id='msg-qa-1',
                packet_schema_type='techlead_assignment_packet',
                queue_name='paa-qa',
                packet_reference='msg-qa-1',
                resolved_packet_path='/tmp/techlead-assignment.json',
                resolution_supported=True,
                blocking_reasons=(),
                notes=('message-id', 'resolved-artifact-path'),
            ),
            normalized_packet_payload={'methodology_execution_id': 'exec-qa-1', 'issue_number': 6},
            ok=True,
            metadata={'resolution': True},
        )
        worker_request = QAWorkerRequest(packet_schema_type='techlead_assignment_packet')
        worker_result = QAWorkerResult(
            request=worker_request,
            methodology_execution_id='exec-qa-1',
            current_execution_summary=None,
            packet_context_result=None,
            verification_summary=QAWorkerVerificationSummary(
                handler_key='qa-verification-dry-run',
                packet_schema_type='techlead_assignment_packet',
                runtime_mode='dry_run',
                verification_supported=True,
                verification_runner_used='Runner',
                packet_context_required=True,
                packet_context_ok=True,
                qa_verification_packet_required=True,
                methodology_transition_required=False,
                blocking_reasons=(),
                notes=('dry-run-only',),
            ),
            verification_result={'verification_status': 'pass'},
            methodology_transition_result=None,
            normalized_packet_output_summary='qa_verification_packet ready',
            ok=True,
            metadata={'verification': True},
        )
        host = QARuntimeHost(
            queue_name='paa-qa',
            queue_claim_runtime_service=_FakeQueueClaimRuntimeService(claim_result),
            queue_claim_lifecycle_adapter=_FakeQueueClaimLifecycleAdapter(),
            packet_reference_resolution_service=_FakePacketReferenceResolutionService(resolution_result),
            qa_worker_service=_FakeQAWorkerService(worker_result),
            verification_publisher=None,
            actor_name='QA Agent',
            host_name='qa-runtime-host',
        )

        result = host.run_once(intake_mode='claim_next')

        self.assertTrue(result.ok)
        self.assertEqual(result.claim_id, 'claim-qa-1')
        self.assertEqual(result.packet_message_id, 'msg-qa-1')
        self.assertEqual(result.packet_path, '/tmp/techlead-assignment.json')

    def test_run_once_claim_next_can_emit_verification_after_success(self) -> None:
        claim_result = QueueClaimRuntimeResult(
            request=QueueClaimRuntimeRequest(queue_name='paa-qa', intake_mode='claim_next'),
            preview_summary=None,
            claim_summary=QueuePacketClaimSummary(
                queue_name='paa-qa',
                claim_id='claim-qa-2',
                claimant_name='QA Agent',
                packet_message_id='msg-qa-2',
                packet_reference='msg-qa-2',
                claim_supported=True,
                blocking_reasons=(),
                notes=('claimed',),
            ),
            normalized_packet_envelope={'packet_message_id': 'msg-qa-2', 'packet_schema_type': 'techlead_assignment_packet', 'packet_reference': 'msg-qa-2'},
            normalized_packet_payload=None,
            ok=True,
            metadata={'claim': True},
        )
        resolution_result = PacketReferenceResolutionResult(
            request=PacketReferenceResolutionRequest(packet_message_id='msg-qa-2'),
            resolution_summary=PacketReferenceResolutionSummary(
                resolution_source='message-id',
                packet_message_id='msg-qa-2',
                packet_schema_type='techlead_assignment_packet',
                queue_name='paa-qa',
                packet_reference='msg-qa-2',
                resolved_packet_path='/tmp/techlead-assignment.json',
                resolution_supported=True,
                blocking_reasons=(),
                notes=('message-id',),
            ),
            normalized_packet_payload={'methodology_execution_id': 'exec-qa-2', 'issue_number': 6},
            ok=True,
            metadata=None,
        )
        worker_result = QAWorkerResult(
            request=QAWorkerRequest(packet_schema_type='techlead_assignment_packet'),
            methodology_execution_id='exec-qa-2',
            current_execution_summary=None,
            packet_context_result=None,
            verification_summary=QAWorkerVerificationSummary(
                handler_key='qa-verification-dry-run',
                packet_schema_type='techlead_assignment_packet',
                runtime_mode='dry_run',
                verification_supported=True,
                verification_runner_used='Runner',
                packet_context_required=True,
                packet_context_ok=True,
                qa_verification_packet_required=True,
                methodology_transition_required=False,
                blocking_reasons=(),
                notes=('dry-run-only',),
            ),
            verification_result={'verification_status': 'pass'},
            methodology_transition_result=None,
            normalized_packet_output_summary='qa_verification_packet ready',
            ok=True,
            metadata=None,
        )
        publisher = _FakeVerificationPublisher()
        lifecycle = _FakeQueueClaimLifecycleAdapter()
        host = QARuntimeHost(
            queue_name='paa-qa',
            queue_claim_runtime_service=_FakeQueueClaimRuntimeService(claim_result),
            queue_claim_lifecycle_adapter=lifecycle,
            packet_reference_resolution_service=_FakePacketReferenceResolutionService(resolution_result),
            qa_worker_service=_FakeQAWorkerService(worker_result),
            verification_publisher=publisher,
            actor_name='QA Agent',
            host_name='qa-runtime-host',
        )

        result = host.run_once(intake_mode='claim_next', emit_verification=True)

        self.assertTrue(result.ok)
        self.assertEqual(result.emitted_verification, {'ok': True, 'message_id': 'qa-1', 'resolved_queue': 'paa-techlead'})
        self.assertEqual(len(publisher.calls), 1)
        self.assertEqual(lifecycle.acks, ['claim-qa-2'])

    def test_run_once_requeues_claim_when_verification_fails(self) -> None:
        claim_result = QueueClaimRuntimeResult(
            request=QueueClaimRuntimeRequest(queue_name='paa-qa', intake_mode='claim_next'),
            preview_summary=None,
            claim_summary=QueuePacketClaimSummary(
                queue_name='paa-qa',
                claim_id='claim-qa-fail-1',
                claimant_name='QA Agent',
                packet_message_id='msg-qa-fail-1',
                packet_reference='msg-qa-fail-1',
                claim_supported=True,
                blocking_reasons=(),
                notes=('claimed',),
            ),
            normalized_packet_envelope={'packet_message_id': 'msg-qa-fail-1', 'packet_schema_type': 'techlead_assignment_packet', 'packet_reference': 'msg-qa-fail-1'},
            normalized_packet_payload=None,
            ok=True,
            metadata={'claim': True},
        )
        resolution_result = PacketReferenceResolutionResult(
            request=PacketReferenceResolutionRequest(packet_message_id='msg-qa-fail-1'),
            resolution_summary=PacketReferenceResolutionSummary(
                resolution_source='message-id',
                packet_message_id='msg-qa-fail-1',
                packet_schema_type='techlead_assignment_packet',
                queue_name='paa-qa',
                packet_reference='msg-qa-fail-1',
                resolved_packet_path='/tmp/techlead-assignment.json',
                resolution_supported=True,
                blocking_reasons=(),
                notes=('message-id',),
            ),
            normalized_packet_payload={'methodology_execution_id': 'exec-qa-fail-1', 'issue_number': 6},
            ok=True,
            metadata=None,
        )
        worker_result = QAWorkerResult(
            request=QAWorkerRequest(packet_schema_type='techlead_assignment_packet'),
            methodology_execution_id='exec-qa-fail-1',
            current_execution_summary=None,
            packet_context_result=None,
            verification_summary=QAWorkerVerificationSummary(
                handler_key='qa-verification-dry-run',
                packet_schema_type='techlead_assignment_packet',
                runtime_mode='dry_run',
                verification_supported=False,
                verification_runner_used='Runner',
                packet_context_required=True,
                packet_context_ok=True,
                qa_verification_packet_required=True,
                methodology_transition_required=False,
                blocking_reasons=('blocked',),
                notes=('dry-run-only',),
            ),
            verification_result=None,
            methodology_transition_result=None,
            normalized_packet_output_summary=None,
            ok=False,
            reason='blocked',
            details='Verification blocked.',
            metadata=None,
        )
        lifecycle = _FakeQueueClaimLifecycleAdapter()
        host = QARuntimeHost(
            queue_name='paa-qa',
            queue_claim_runtime_service=_FakeQueueClaimRuntimeService(claim_result),
            queue_claim_lifecycle_adapter=lifecycle,
            packet_reference_resolution_service=_FakePacketReferenceResolutionService(resolution_result),
            qa_worker_service=_FakeQAWorkerService(worker_result),
            verification_publisher=None,
            actor_name='QA Agent',
            host_name='qa-runtime-host',
        )

        result = host.run_once(intake_mode='claim_next')

        self.assertFalse(result.ok)
        self.assertEqual(lifecycle.requeues, ['claim-qa-fail-1'])

    def test_verification_publisher_message_ids_are_unique_per_run(self) -> None:
        publisher = _QAVerificationPublisher(
            repo_root=ROOT,
            project_slug='paa-platform',
            github_repo='billyweisberg/paa-platform',
        )

        first = publisher._build_message_id(issue_number=6, verification_status='pass')
        second = publisher._build_message_id(issue_number=6, verification_status='pass')

        self.assertNotEqual(first, second)
        self.assertRegex(
            first,
            r'^paa-qa-\d{8}T\d{6}Z-issue6-pass-[0-9a-f]{8}$',
        )


if __name__ == '__main__':
    unittest.main()

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))

from paa_core.runtime.hosts.techlead import TechLeadRuntimeHost, _TechLeadAssignmentPublisher
from paa_core.services.queue_claim_runtime import QueueClaimRuntimeResult, QueuePacketClaimSummary, QueuePacketPreviewSummary, QueueClaimRuntimeRequest
from paa_core.services.packet_reference_resolution import PacketReferenceResolutionResult, PacketReferenceResolutionSummary, PacketReferenceResolutionRequest
from paa_core.services.queue_packet_runtime_controller import QueuePacketDispatchSummary, QueuePacketRuntimeRequest, QueuePacketRuntimeResult
from paa_core.services.techlead_worker import TechLeadWorkerDispatchSummary, TechLeadWorkerRequest, TechLeadWorkerResult


class _FakeQueueClaimRuntimeService:
    def __init__(self, result: QueueClaimRuntimeResult | None = None, results: list[QueueClaimRuntimeResult] | None = None) -> None:
        self.result = result
        self.results = list(results or [])
        self.calls: list[QueueClaimRuntimeRequest] = []

    def assemble_queue_intake(self, request: QueueClaimRuntimeRequest) -> QueueClaimRuntimeResult:
        self.calls.append(request)
        if self.results:
            return self.results.pop(0)
        if self.result is None:
            raise AssertionError('No fake queue claim result configured.')
        return self.result


class _FakePacketReferenceResolutionService:
    def __init__(self, result: PacketReferenceResolutionResult) -> None:
        self.result = result
        self.calls: list[PacketReferenceResolutionRequest] = []

    def resolve_packet_reference(self, request: PacketReferenceResolutionRequest) -> PacketReferenceResolutionResult:
        self.calls.append(request)
        return self.result


class _FakeQueuePacketRuntimeController:
    def __init__(self, result: QueuePacketRuntimeResult) -> None:
        self.result = result
        self.calls: list[QueuePacketRuntimeRequest] = []

    def handle_packet(self, request: QueuePacketRuntimeRequest) -> QueuePacketRuntimeResult:
        self.calls.append(request)
        return self.result


class _FakeAssignmentPublisher:
    def __init__(self, result: dict[str, object] | None = None) -> None:
        self.result = result if result is not None else {'ok': True, 'message_id': 'assign-1', 'resolved_queue': 'paa-qa'}
        self.calls: list[dict[str, object]] = []

    def publish_next_assignment(
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


class _FakeWorkflowTransitionAdapter:
    def __init__(
        self,
        *,
        return_result: dict[str, object] | None = None,
        assignment_result: dict[str, object] | None = None,
    ) -> None:
        self.return_result = return_result if return_result is not None else {'ok': True, 'workflow_stage': 'techlead_worker_review_pending'}
        self.assignment_result = assignment_result if assignment_result is not None else {'ok': True, 'workflow_stage': 'qa_execution_in_progress'}
        self.return_calls: list[dict[str, object]] = []
        self.assignment_calls: list[dict[str, object]] = []

    def apply_return_transition(
        self,
        *,
        packet_path: str | None,
        packet_message_id: str | None,
        packet_schema_type: str | None,
    ) -> dict[str, object]:
        self.return_calls.append(
            {
                'packet_path': packet_path,
                'packet_message_id': packet_message_id,
                'packet_schema_type': packet_schema_type,
            }
        )
        return self.return_result

    def record_assignment_emitted(
        self,
        *,
        source_packet_message_id: str | None,
        source_packet_schema_type: str | None,
        source_claim_id: str | None,
        emitted_assignment: dict[str, object],
    ) -> dict[str, object]:
        self.assignment_calls.append(
            {
                'source_packet_message_id': source_packet_message_id,
                'source_packet_schema_type': source_packet_schema_type,
                'source_claim_id': source_claim_id,
                'emitted_assignment': emitted_assignment,
            }
        )
        return self.assignment_result


class TechLeadRuntimeHostTests(unittest.TestCase):
    def test_run_once_claims_resolves_and_dispatches_one_packet(self) -> None:
        claim_result = QueueClaimRuntimeResult(
            request=QueueClaimRuntimeRequest(queue_name='paa-techlead', intake_mode='claim_next'),
            preview_summary=QueuePacketPreviewSummary(
                queue_name='paa-techlead',
                packet_message_id='msg-1',
                packet_schema_type='worker_result_packet',
                packet_reference='msg-1',
                preview_supported=True,
                claim_supported=True,
                blocking_reasons=(),
                notes=('claimed-preview',),
            ),
            claim_summary=QueuePacketClaimSummary(
                queue_name='paa-techlead',
                claim_id='claim-1',
                claimant_name='TechLead Agent',
                packet_message_id='msg-1',
                packet_reference='msg-1',
                claim_supported=True,
                blocking_reasons=(),
                notes=('claimed',),
            ),
            normalized_packet_envelope={'packet_message_id': 'msg-1', 'packet_schema_type': 'worker_result_packet', 'packet_reference': 'msg-1'},
            normalized_packet_payload=None,
            ok=True,
            metadata={'claim': True},
        )
        resolution_result = PacketReferenceResolutionResult(
            request=PacketReferenceResolutionRequest(packet_message_id='msg-1'),
            resolution_summary=PacketReferenceResolutionSummary(
                resolution_source='message-id',
                packet_message_id='msg-1',
                packet_schema_type='worker_result_packet',
                queue_name='paa-techlead',
                packet_reference='msg-1',
                resolved_packet_path='/tmp/worker-result.json',
                resolution_supported=True,
                blocking_reasons=(),
                notes=('message-id', 'resolved-artifact-path'),
            ),
            normalized_packet_payload={'methodology_execution_id': 'exec-1'},
            ok=True,
            metadata={'resolution': True},
        )
        dispatch_result = QueuePacketRuntimeResult(
            request=QueuePacketRuntimeRequest(
                queue_name='paa-techlead',
                packet_schema_type='worker_result_packet',
                packet_message_id='msg-1',
                packet_path='/tmp/worker-result.json',
                packet_payload={'methodology_execution_id': 'exec-1'},
            ),
            dispatch_summary=QueuePacketDispatchSummary(
                handler_key='techlead-worker-dispatch',
                packet_schema_type='worker_result_packet',
                target_worker_host='TechLeadWorkerService',
                dispatch_supported=True,
                queue_side_effect_required=False,
                ack_required=False,
                blocking_reasons=(),
                notes=('dry-run-only',),
            ),
            selected_worker_result=None,
            normalized_queue_side_effect_summary='Dry run only.',
            ok=True,
            metadata={'dispatch': True},
        )
        host = TechLeadRuntimeHost(
            queue_name='paa-techlead',
            queue_claim_runtime_service=_FakeQueueClaimRuntimeService(claim_result),
            queue_claim_lifecycle_adapter=_FakeQueueClaimLifecycleAdapter(),
            packet_reference_resolution_service=_FakePacketReferenceResolutionService(resolution_result),
            queue_packet_runtime_controller=_FakeQueuePacketRuntimeController(dispatch_result),
            assignment_publisher=None,
            workflow_transition_adapter=None,
            actor_name='TechLead Agent',
            host_name='techlead-runtime-host',
        )

        result = host.run_once(intake_mode='claim_next')

        self.assertTrue(result.ok)
        self.assertEqual(result.claim_id, 'claim-1')
        self.assertEqual(result.packet_message_id, 'msg-1')
        self.assertEqual(result.target_worker_host, 'TechLeadWorkerService')
        self.assertEqual(result.packet_path, '/tmp/worker-result.json')

    def test_run_loop_skips_duplicate_preview_head(self) -> None:
        claim_result = QueueClaimRuntimeResult(
            request=QueueClaimRuntimeRequest(queue_name='paa-techlead', intake_mode='preview'),
            preview_summary=QueuePacketPreviewSummary(
                queue_name='paa-techlead',
                packet_message_id='msg-1',
                packet_schema_type='worker_result_packet',
                packet_reference='msg-1',
                preview_supported=True,
                claim_supported=True,
                blocking_reasons=(),
                notes=('preview',),
            ),
            claim_summary=None,
            normalized_packet_envelope={'packet_message_id': 'msg-1'},
            normalized_packet_payload=None,
            ok=False,
            reason='missing_packet_payload',
            details='Pointer-only preview.',
            metadata=None,
        )
        host = TechLeadRuntimeHost(
            queue_name='paa-techlead',
            queue_claim_runtime_service=_FakeQueueClaimRuntimeService(claim_result),
            queue_claim_lifecycle_adapter=_FakeQueueClaimLifecycleAdapter(),
            packet_reference_resolution_service=_FakePacketReferenceResolutionService(
                PacketReferenceResolutionResult(
                    request=PacketReferenceResolutionRequest(packet_message_id='msg-1'),
                    resolution_summary=PacketReferenceResolutionSummary(
                        resolution_source='message-id',
                        packet_message_id='msg-1',
                        packet_schema_type='worker_result_packet',
                        queue_name='paa-techlead',
                        packet_reference='msg-1',
                        resolved_packet_path=None,
                        resolution_supported=False,
                        blocking_reasons=('pointer-only',),
                        notes=('pointer-only',),
                    ),
                    normalized_packet_payload=None,
                    ok=False,
                    reason='pointer-only',
                    details='No artifact path yet.',
                    metadata=None,
                )
            ),
            queue_packet_runtime_controller=_FakeQueuePacketRuntimeController(
                QueuePacketRuntimeResult(
                    request=QueuePacketRuntimeRequest(queue_name='paa-techlead', packet_schema_type='worker_result_packet'),
                    dispatch_summary=QueuePacketDispatchSummary(
                        handler_key='noop',
                        packet_schema_type='worker_result_packet',
                        target_worker_host=None,
                        dispatch_supported=False,
                        queue_side_effect_required=False,
                        ack_required=False,
                        blocking_reasons=('noop',),
                        notes=(),
                    ),
                    selected_worker_result=None,
                    normalized_queue_side_effect_summary=None,
                    ok=False,
                )
            ),
            assignment_publisher=None,
            workflow_transition_adapter=None,
            actor_name='TechLead Agent',
            host_name='techlead-runtime-host',
        )

        summary = host.run_loop(intake_mode='preview', max_iterations=2, poll_interval_seconds=0.0)

        self.assertEqual(summary['iteration_count'], 2)
        self.assertEqual(summary['iterations'][1]['reason'], 'duplicate_preview_head')
        self.assertTrue(summary['iterations'][1]['skipped'])

    def test_run_once_claim_next_can_emit_next_assignment_after_successful_dispatch(self) -> None:
        claim_result = QueueClaimRuntimeResult(
            request=QueueClaimRuntimeRequest(queue_name='paa-techlead', intake_mode='claim_next'),
            preview_summary=QueuePacketPreviewSummary(
                queue_name='paa-techlead',
                packet_message_id='msg-1',
                packet_schema_type='worker_result_packet',
                packet_reference='msg-1',
                preview_supported=True,
                claim_supported=True,
                blocking_reasons=(),
                notes=('claimed-preview',),
            ),
            claim_summary=QueuePacketClaimSummary(
                queue_name='paa-techlead',
                claim_id='claim-1',
                claimant_name='TechLead Agent',
                packet_message_id='msg-1',
                packet_reference='msg-1',
                claim_supported=True,
                blocking_reasons=(),
                notes=('claimed',),
            ),
            normalized_packet_envelope={'packet_message_id': 'msg-1', 'packet_schema_type': 'worker_result_packet', 'packet_reference': 'msg-1'},
            normalized_packet_payload=None,
            ok=True,
            metadata={'claim': True},
        )
        resolution_result = PacketReferenceResolutionResult(
            request=PacketReferenceResolutionRequest(packet_message_id='msg-1'),
            resolution_summary=PacketReferenceResolutionSummary(
                resolution_source='message-id',
                packet_message_id='msg-1',
                packet_schema_type='worker_result_packet',
                queue_name='paa-techlead',
                packet_reference='msg-1',
                resolved_packet_path='/tmp/worker-result.json',
                resolution_supported=True,
                blocking_reasons=(),
                notes=('message-id', 'resolved-artifact-path'),
            ),
            normalized_packet_payload={'methodology_execution_id': 'exec-1'},
            ok=True,
            metadata={'resolution': True},
        )
        worker_result = TechLeadWorkerResult(
            request=TechLeadWorkerRequest(
                packet_schema_type='worker_result_packet',
                packet_payload={'issue_number': 6},
            ),
            methodology_execution_id='exec-1',
            current_execution_summary=None,
            dispatch_summary=TechLeadWorkerDispatchSummary(
                handler_key='techlead-worker-dispatch',
                packet_schema_type='worker_result_packet',
                decision_service_used='worker-review-routing',
                decision_supported=True,
                recommended_next_action='assign_qa',
                recommended_target_role='QA',
                packet_emission_required=True,
                methodology_transition_required=False,
                blocking_reasons=(),
                notes=(),
            ),
            worker_review_routing_result=SimpleNamespace(
                summary=SimpleNamespace(review_summary='Route implementation to QA.'),
                recommended_actions=('assign_qa',),
            ),
            assignment_decision_result=None,
            methodology_transition_result=None,
            normalized_packet_output_summary=None,
            ok=True,
        )
        dispatch_result = QueuePacketRuntimeResult(
            request=QueuePacketRuntimeRequest(
                queue_name='paa-techlead',
                packet_schema_type='worker_result_packet',
                packet_message_id='msg-1',
                packet_path='/tmp/worker-result.json',
                packet_payload={'methodology_execution_id': 'exec-1'},
            ),
            dispatch_summary=QueuePacketDispatchSummary(
                handler_key='techlead-worker-dispatch',
                packet_schema_type='worker_result_packet',
                target_worker_host='TechLeadWorkerService',
                dispatch_supported=True,
                queue_side_effect_required=False,
                ack_required=False,
                blocking_reasons=(),
                notes=('dry-run-only',),
            ),
            selected_worker_result=worker_result,
            normalized_queue_side_effect_summary='Dry run only.',
            ok=True,
            metadata={'dispatch': True},
        )
        publisher = _FakeAssignmentPublisher()
        lifecycle = _FakeQueueClaimLifecycleAdapter()
        workflow = _FakeWorkflowTransitionAdapter()
        host = TechLeadRuntimeHost(
            queue_name='paa-techlead',
            queue_claim_runtime_service=_FakeQueueClaimRuntimeService(claim_result),
            queue_claim_lifecycle_adapter=lifecycle,
            packet_reference_resolution_service=_FakePacketReferenceResolutionService(resolution_result),
            queue_packet_runtime_controller=_FakeQueuePacketRuntimeController(dispatch_result),
            assignment_publisher=publisher,
            workflow_transition_adapter=workflow,
            actor_name='TechLead Agent',
            host_name='techlead-runtime-host',
        )

        result = host.run_once(intake_mode='claim_next', emit_next_assignment=True)

        self.assertTrue(result.ok)
        self.assertEqual(result.emitted_assignment['message_id'], 'assign-1')
        self.assertEqual(len(publisher.calls), 1)
        self.assertEqual(workflow.return_calls[0]['packet_schema_type'], 'worker_result_packet')
        self.assertEqual(workflow.assignment_calls[0]['source_claim_id'], 'claim-1')
        self.assertEqual(lifecycle.acks, ['claim-1'])

    def test_run_once_can_emit_dev_assignment_from_techlead_decision_packet(self) -> None:
        claim_result = QueueClaimRuntimeResult(
            request=QueueClaimRuntimeRequest(queue_name='paa-techlead', intake_mode='claim_next'),
            preview_summary=QueuePacketPreviewSummary(
                queue_name='paa-techlead',
                packet_message_id='msg-decision-1',
                packet_schema_type='techlead_decision_packet',
                packet_reference='msg-decision-1',
                preview_supported=True,
                claim_supported=True,
                blocking_reasons=(),
                notes=('claimed-preview',),
            ),
            claim_summary=QueuePacketClaimSummary(
                queue_name='paa-techlead',
                claim_id='claim-decision-1',
                claimant_name='TechLead Agent',
                packet_message_id='msg-decision-1',
                packet_reference='msg-decision-1',
                claim_supported=True,
                blocking_reasons=(),
                notes=('claimed',),
            ),
            normalized_packet_envelope={
                'packet_message_id': 'msg-decision-1',
                'packet_schema_type': 'techlead_decision_packet',
                'packet_reference': 'msg-decision-1',
            },
            normalized_packet_payload=None,
            ok=True,
            metadata={'claim': True},
        )
        resolution_result = PacketReferenceResolutionResult(
            request=PacketReferenceResolutionRequest(packet_message_id='msg-decision-1'),
            resolution_summary=PacketReferenceResolutionSummary(
                resolution_source='message-id',
                packet_message_id='msg-decision-1',
                packet_schema_type='techlead_decision_packet',
                queue_name='paa-techlead',
                packet_reference='msg-decision-1',
                resolved_packet_path='/tmp/techlead-decision.json',
                resolution_supported=True,
                blocking_reasons=(),
                notes=('message-id', 'resolved-artifact-path'),
            ),
            normalized_packet_payload={'methodology_execution_id': 'exec-1'},
            ok=True,
            metadata={'resolution': True},
        )
        worker_result = TechLeadWorkerResult(
            request=TechLeadWorkerRequest(
                packet_schema_type='techlead_decision_packet',
                packet_payload={'issue_number': 6, 'target_role': 'Dev'},
            ),
            methodology_execution_id='exec-1',
            current_execution_summary=None,
            dispatch_summary=TechLeadWorkerDispatchSummary(
                handler_key='techlead-worker-dispatch',
                packet_schema_type='techlead_decision_packet',
                decision_service_used='assignment',
                decision_supported=True,
                recommended_next_action='assign_dev',
                recommended_target_role='Dev',
                packet_emission_required=True,
                methodology_transition_required=False,
                blocking_reasons=(),
                notes=(),
            ),
            worker_review_routing_result=None,
            assignment_decision_result=SimpleNamespace(
                summary=SimpleNamespace(
                    assignment_type='implement_authorized_slice',
                    assignment_summary='Assign Dev to implement the authorized slice.',
                    allowed_result_types=('implemented_ready_for_qa', 'blocked'),
                ),
            ),
            methodology_transition_result=None,
            normalized_packet_output_summary=None,
            ok=True,
        )
        dispatch_result = QueuePacketRuntimeResult(
            request=QueuePacketRuntimeRequest(
                queue_name='paa-techlead',
                packet_schema_type='techlead_decision_packet',
                packet_message_id='msg-decision-1',
                packet_path='/tmp/techlead-decision.json',
                packet_payload={'methodology_execution_id': 'exec-1'},
            ),
            dispatch_summary=QueuePacketDispatchSummary(
                handler_key='techlead-worker-dispatch',
                packet_schema_type='techlead_decision_packet',
                target_worker_host='TechLeadWorkerService',
                dispatch_supported=True,
                queue_side_effect_required=False,
                ack_required=False,
                blocking_reasons=(),
                notes=('dry-run-only',),
            ),
            selected_worker_result=worker_result,
            normalized_queue_side_effect_summary='Dry run only.',
            ok=True,
            metadata={'dispatch': True},
        )
        publisher = _FakeAssignmentPublisher(result={'ok': True, 'message_id': 'assign-dev-1', 'resolved_queue': 'paa-dev'})
        lifecycle = _FakeQueueClaimLifecycleAdapter()
        workflow = _FakeWorkflowTransitionAdapter(
            assignment_result={'ok': True, 'workflow_stage': 'worker_execution_in_progress'}
        )
        host = TechLeadRuntimeHost(
            queue_name='paa-techlead',
            queue_claim_runtime_service=_FakeQueueClaimRuntimeService(claim_result),
            queue_claim_lifecycle_adapter=lifecycle,
            packet_reference_resolution_service=_FakePacketReferenceResolutionService(resolution_result),
            queue_packet_runtime_controller=_FakeQueuePacketRuntimeController(dispatch_result),
            assignment_publisher=publisher,
            workflow_transition_adapter=workflow,
            actor_name='TechLead Agent',
            host_name='techlead-runtime-host',
        )

        result = host.run_once(intake_mode='claim_next', emit_next_assignment=True)

        self.assertTrue(result.ok)
        self.assertEqual(result.emitted_assignment['message_id'], 'assign-dev-1')
        self.assertEqual(len(publisher.calls), 1)
        self.assertEqual(workflow.assignment_calls[0]['source_packet_schema_type'], 'techlead_decision_packet')
        self.assertEqual(lifecycle.acks, ['claim-decision-1'])

    def test_run_once_claims_and_dispatches_returned_qa_verification_packet(self) -> None:
        claim_result = QueueClaimRuntimeResult(
            request=QueueClaimRuntimeRequest(queue_name='paa-techlead', intake_mode='claim_next'),
            preview_summary=None,
            claim_summary=QueuePacketClaimSummary(
                queue_name='paa-techlead',
                claim_id='claim-qa-return-1',
                claimant_name='TechLead Agent',
                packet_message_id='msg-qa-return-1',
                packet_reference='msg-qa-return-1',
                claim_supported=True,
                blocking_reasons=(),
                notes=('claimed',),
            ),
            normalized_packet_envelope={
                'packet_message_id': 'msg-qa-return-1',
                'packet_schema_type': 'qa_verification_packet',
                'packet_reference': 'msg-qa-return-1',
            },
            normalized_packet_payload=None,
            ok=True,
            metadata={'claim': True},
        )
        resolution_result = PacketReferenceResolutionResult(
            request=PacketReferenceResolutionRequest(packet_message_id='msg-qa-return-1'),
            resolution_summary=PacketReferenceResolutionSummary(
                resolution_source='message-id',
                packet_message_id='msg-qa-return-1',
                packet_schema_type='qa_verification_packet',
                queue_name='paa-techlead',
                packet_reference='msg-qa-return-1',
                resolved_packet_path='/tmp/qa-verification.json',
                resolution_supported=True,
                blocking_reasons=(),
                notes=('message-id', 'resolved-artifact-path'),
            ),
            normalized_packet_payload={
                'methodology_execution_id': 'exec-qa-return-1',
                'project_slug': 'paa-platform',
                'issue_number': 42,
                'workflow_stage': 'techlead_qa_review_pending',
                'verification_status': 'pass',
            },
            ok=True,
            metadata={'resolution': True},
        )
        dispatch_result = QueuePacketRuntimeResult(
            request=QueuePacketRuntimeRequest(
                queue_name='paa-techlead',
                packet_schema_type='qa_verification_packet',
                packet_message_id='msg-qa-return-1',
                packet_path='/tmp/qa-verification.json',
                packet_payload={'methodology_execution_id': 'exec-qa-return-1'},
            ),
            dispatch_summary=QueuePacketDispatchSummary(
                handler_key='qa-verification-acceptance',
                packet_schema_type='qa_verification_packet',
                target_worker_host='TechLeadWorkerService',
                dispatch_supported=True,
                queue_side_effect_required=False,
                ack_required=False,
                blocking_reasons=(),
                notes=('dry-run-only',),
            ),
            selected_worker_result=None,
            normalized_queue_side_effect_summary='Dry run only.',
            ok=True,
            metadata={'dispatch': True},
        )
        controller = _FakeQueuePacketRuntimeController(dispatch_result)
        workflow = _FakeWorkflowTransitionAdapter(
            return_result={'ok': True, 'workflow_stage': 'techlead_qa_review_pending'}
        )
        host = TechLeadRuntimeHost(
            queue_name='paa-techlead',
            queue_claim_runtime_service=_FakeQueueClaimRuntimeService(claim_result),
            queue_claim_lifecycle_adapter=_FakeQueueClaimLifecycleAdapter(),
            packet_reference_resolution_service=_FakePacketReferenceResolutionService(resolution_result),
            queue_packet_runtime_controller=controller,
            assignment_publisher=None,
            workflow_transition_adapter=workflow,
            actor_name='TechLead Agent',
            host_name='techlead-runtime-host',
        )

        result = host.run_once(intake_mode='claim_next')

        self.assertTrue(result.ok)
        self.assertEqual(controller.calls[0].packet_schema_type, 'qa_verification_packet')
        self.assertEqual(result.packet_path, '/tmp/qa-verification.json')
        self.assertEqual(workflow.return_calls[0]['packet_schema_type'], 'qa_verification_packet')

    def test_assignment_publisher_message_ids_are_unique_per_run(self) -> None:
        publisher = _TechLeadAssignmentPublisher(
            repo_root=ROOT,
            project_slug='paa-platform',
            github_repo='billyweisberg/paa-platform',
        )

        first = publisher._build_message_id(issue_number=6, assignment_type='verify_authorized_slice')
        second = publisher._build_message_id(issue_number=6, assignment_type='verify_authorized_slice')

        self.assertNotEqual(first, second)
        self.assertRegex(
            first,
            r'^paa-techlead-\d{8}T\d{6}Z-issue6-verify-authorized-slice-[0-9a-f]{8}$',
        )

    def test_run_once_retries_claim_next_when_queue_packet_is_temporarily_missing(self) -> None:
        missing_result = QueueClaimRuntimeResult(
            request=QueueClaimRuntimeRequest(queue_name='paa-techlead', intake_mode='claim_next'),
            preview_summary=None,
            claim_summary=None,
            normalized_packet_envelope=None,
            normalized_packet_payload=None,
            ok=False,
            reason='missing_queue_packet',
            details='No queue packet yet.',
            metadata={'service_component': 'QueueClaimRuntimeService'},
        )
        found_result = QueueClaimRuntimeResult(
            request=QueueClaimRuntimeRequest(queue_name='paa-techlead', intake_mode='claim_next'),
            preview_summary=QueuePacketPreviewSummary(
                queue_name='paa-techlead',
                packet_message_id='msg-2',
                packet_schema_type='worker_result_packet',
                packet_reference='msg-2',
                preview_supported=True,
                claim_supported=True,
                blocking_reasons=(),
                notes=('claimed-preview',),
            ),
            claim_summary=QueuePacketClaimSummary(
                queue_name='paa-techlead',
                claim_id='claim-2',
                claimant_name='TechLead Agent',
                packet_message_id='msg-2',
                packet_reference='msg-2',
                claim_supported=True,
                blocking_reasons=(),
                notes=('claimed',),
            ),
            normalized_packet_envelope={'packet_message_id': 'msg-2', 'packet_schema_type': 'worker_result_packet', 'packet_reference': 'msg-2'},
            normalized_packet_payload=None,
            ok=True,
            metadata={'claim': True},
        )
        resolution_result = PacketReferenceResolutionResult(
            request=PacketReferenceResolutionRequest(packet_message_id='msg-2'),
            resolution_summary=PacketReferenceResolutionSummary(
                resolution_source='message-id',
                packet_message_id='msg-2',
                packet_schema_type='worker_result_packet',
                queue_name='paa-techlead',
                packet_reference='msg-2',
                resolved_packet_path='/tmp/worker-result-2.json',
                resolution_supported=True,
                blocking_reasons=(),
                notes=('message-id',),
            ),
            normalized_packet_payload={'methodology_execution_id': 'exec-2'},
            ok=True,
            metadata={'resolution': True},
        )
        dispatch_result = QueuePacketRuntimeResult(
            request=QueuePacketRuntimeRequest(
                queue_name='paa-techlead',
                packet_schema_type='worker_result_packet',
                packet_message_id='msg-2',
                packet_path='/tmp/worker-result-2.json',
                packet_payload={'methodology_execution_id': 'exec-2'},
            ),
            dispatch_summary=QueuePacketDispatchSummary(
                handler_key='techlead-worker-dispatch',
                packet_schema_type='worker_result_packet',
                target_worker_host='TechLeadWorkerService',
                dispatch_supported=True,
                queue_side_effect_required=False,
                ack_required=False,
                blocking_reasons=(),
                notes=('dry-run-only',),
            ),
            selected_worker_result=None,
            normalized_queue_side_effect_summary='Dry run only.',
            ok=True,
            metadata={'dispatch': True},
        )
        host = TechLeadRuntimeHost(
            queue_name='paa-techlead',
            queue_claim_runtime_service=_FakeQueueClaimRuntimeService(results=[missing_result, found_result]),
            queue_claim_lifecycle_adapter=_FakeQueueClaimLifecycleAdapter(),
            packet_reference_resolution_service=_FakePacketReferenceResolutionService(resolution_result),
            queue_packet_runtime_controller=_FakeQueuePacketRuntimeController(dispatch_result),
            assignment_publisher=None,
            workflow_transition_adapter=None,
            actor_name='TechLead Agent',
            host_name='techlead-runtime-host',
        )

        with patch('paa_core.runtime.hosts.techlead.time.sleep'):
            result = host.run_once(intake_mode='claim_next')

        self.assertTrue(result.ok)
        self.assertEqual(result.packet_message_id, 'msg-2')

    def test_run_once_requeues_claim_when_resolution_fails(self) -> None:
        claim_result = QueueClaimRuntimeResult(
            request=QueueClaimRuntimeRequest(queue_name='paa-techlead', intake_mode='claim_next'),
            preview_summary=None,
            claim_summary=QueuePacketClaimSummary(
                queue_name='paa-techlead',
                claim_id='claim-fail-1',
                claimant_name='TechLead Agent',
                packet_message_id='msg-fail-1',
                packet_reference='msg-fail-1',
                claim_supported=True,
                blocking_reasons=(),
                notes=('claimed',),
            ),
            normalized_packet_envelope={'packet_message_id': 'msg-fail-1', 'packet_schema_type': 'worker_result_packet', 'packet_reference': 'msg-fail-1'},
            normalized_packet_payload=None,
            ok=True,
            metadata={'claim': True},
        )
        resolution_result = PacketReferenceResolutionResult(
            request=PacketReferenceResolutionRequest(packet_message_id='msg-fail-1'),
            resolution_summary=PacketReferenceResolutionSummary(
                resolution_source='message-id',
                packet_message_id='msg-fail-1',
                packet_schema_type='worker_result_packet',
                queue_name='paa-techlead',
                packet_reference='msg-fail-1',
                resolved_packet_path=None,
                resolution_supported=False,
                blocking_reasons=('unresolved_packet_reference',),
                notes=('fail-closed',),
            ),
            normalized_packet_payload=None,
            ok=False,
            reason='unresolved_packet_reference',
            details='Missing packet artifact.',
            metadata=None,
        )
        lifecycle = _FakeQueueClaimLifecycleAdapter()
        host = TechLeadRuntimeHost(
            queue_name='paa-techlead',
            queue_claim_runtime_service=_FakeQueueClaimRuntimeService(claim_result),
            queue_claim_lifecycle_adapter=lifecycle,
            packet_reference_resolution_service=_FakePacketReferenceResolutionService(resolution_result),
            queue_packet_runtime_controller=_FakeQueuePacketRuntimeController(
                QueuePacketRuntimeResult(
                    request=QueuePacketRuntimeRequest(queue_name='paa-techlead', packet_schema_type='worker_result_packet'),
                    dispatch_summary=QueuePacketDispatchSummary(
                        handler_key='noop',
                        packet_schema_type='worker_result_packet',
                        target_worker_host=None,
                        dispatch_supported=False,
                        queue_side_effect_required=False,
                        ack_required=False,
                        blocking_reasons=('noop',),
                        notes=(),
                    ),
                    selected_worker_result=None,
                    normalized_queue_side_effect_summary=None,
                    ok=False,
                )
            ),
            assignment_publisher=None,
            workflow_transition_adapter=None,
            actor_name='TechLead Agent',
            host_name='techlead-runtime-host',
        )

        result = host.run_once(intake_mode='claim_next')

        self.assertFalse(result.ok)
        self.assertEqual(lifecycle.requeues, ['claim-fail-1'])

    def test_run_once_requeues_claim_when_return_transition_fails(self) -> None:
        claim_result = QueueClaimRuntimeResult(
            request=QueueClaimRuntimeRequest(queue_name='paa-techlead', intake_mode='claim_next'),
            preview_summary=None,
            claim_summary=QueuePacketClaimSummary(
                queue_name='paa-techlead',
                claim_id='claim-transition-fail-1',
                claimant_name='TechLead Agent',
                packet_message_id='msg-transition-fail-1',
                packet_reference='msg-transition-fail-1',
                claim_supported=True,
                blocking_reasons=(),
                notes=('claimed',),
            ),
            normalized_packet_envelope={'packet_message_id': 'msg-transition-fail-1', 'packet_schema_type': 'worker_result_packet', 'packet_reference': 'msg-transition-fail-1'},
            normalized_packet_payload=None,
            ok=True,
            metadata={'claim': True},
        )
        resolution_result = PacketReferenceResolutionResult(
            request=PacketReferenceResolutionRequest(packet_message_id='msg-transition-fail-1'),
            resolution_summary=PacketReferenceResolutionSummary(
                resolution_source='message-id',
                packet_message_id='msg-transition-fail-1',
                packet_schema_type='worker_result_packet',
                queue_name='paa-techlead',
                packet_reference='msg-transition-fail-1',
                resolved_packet_path='/tmp/worker-result-transition-fail.json',
                resolution_supported=True,
                blocking_reasons=(),
                notes=('message-id',),
            ),
            normalized_packet_payload={'methodology_execution_id': 'exec-transition-fail-1'},
            ok=True,
            metadata={'resolution': True},
        )
        dispatch_result = QueuePacketRuntimeResult(
            request=QueuePacketRuntimeRequest(
                queue_name='paa-techlead',
                packet_schema_type='worker_result_packet',
                packet_message_id='msg-transition-fail-1',
                packet_path='/tmp/worker-result-transition-fail.json',
                packet_payload={'methodology_execution_id': 'exec-transition-fail-1'},
            ),
            dispatch_summary=QueuePacketDispatchSummary(
                handler_key='techlead-worker-dispatch',
                packet_schema_type='worker_result_packet',
                target_worker_host='TechLeadWorkerService',
                dispatch_supported=True,
                queue_side_effect_required=False,
                ack_required=False,
                blocking_reasons=(),
                notes=('dry-run-only',),
            ),
            selected_worker_result=None,
            normalized_queue_side_effect_summary='Dry run only.',
            ok=True,
            metadata={'dispatch': True},
        )
        lifecycle = _FakeQueueClaimLifecycleAdapter()
        workflow = _FakeWorkflowTransitionAdapter(
            return_result={'ok': False, 'reason': 'workflow_transition_rejected', 'blocking_reasons': ('invalid_stage',)}
        )
        host = TechLeadRuntimeHost(
            queue_name='paa-techlead',
            queue_claim_runtime_service=_FakeQueueClaimRuntimeService(claim_result),
            queue_claim_lifecycle_adapter=lifecycle,
            packet_reference_resolution_service=_FakePacketReferenceResolutionService(resolution_result),
            queue_packet_runtime_controller=_FakeQueuePacketRuntimeController(dispatch_result),
            assignment_publisher=None,
            workflow_transition_adapter=workflow,
            actor_name='TechLead Agent',
            host_name='techlead-runtime-host',
        )

        result = host.run_once(intake_mode='claim_next')

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'workflow_transition_rejected')
        self.assertEqual(lifecycle.requeues, ['claim-transition-fail-1'])


if __name__ == '__main__':
    unittest.main()

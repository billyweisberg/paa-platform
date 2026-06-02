from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))

from paa_core.services.queue_packet_runtime_controller import (
    DefaultQueuePacketRuntimeController,
    QUEUE_PACKET_RUNTIME_CONTROLLER_METADATA,
    QueuePacketRuntimeRequest,
)
from paa_core.services.queue_packet_runtime_controller.contracts import (
    QueuePacketDeliveryAdapter,
    QueuePacketReader,
    QueuePacketRuntimeController,
)
from paa_core.services.techlead_worker import (
    TechLeadWorkerDispatchSummary,
    TechLeadWorkerRequest,
    TechLeadWorkerResult,
)


class QueuePacketRuntimeControllerContractTests(unittest.TestCase):
    def test_metadata_is_published_for_governed_component(self) -> None:
        self.assertEqual(QUEUE_PACKET_RUNTIME_CONTROLLER_METADATA.name, 'QueuePacketRuntimeController')
        self.assertEqual(QUEUE_PACKET_RUNTIME_CONTROLLER_METADATA.kind, 'service')

    def test_contract_protocol_exposes_runtime_controller_methods(self) -> None:
        self.assertTrue(hasattr(QueuePacketRuntimeController, 'handle_packet'))
        self.assertTrue(hasattr(QueuePacketRuntimeController, 'supports_packet_schema_type'))

    def test_contract_protocol_exposes_required_collaborator_properties(self) -> None:
        self.assertTrue(hasattr(QueuePacketRuntimeController, 'techlead_worker_service'))
        self.assertTrue(hasattr(QueuePacketRuntimeController, 'dev_worker_service'))
        self.assertTrue(hasattr(QueuePacketRuntimeController, 'qa_worker_service'))
        self.assertTrue(hasattr(QueuePacketRuntimeController, 'queue_packet_reader'))
        self.assertTrue(hasattr(QueuePacketRuntimeController, 'queue_packet_delivery_adapter'))
        self.assertTrue(hasattr(QueuePacketRuntimeController, 'logger'))

    def test_queue_packet_reader_protocol_exposes_expected_loader(self) -> None:
        self.assertTrue(hasattr(QueuePacketReader, 'read_packet'))

    def test_queue_packet_delivery_adapter_protocol_exposes_send_and_ack(self) -> None:
        self.assertTrue(hasattr(QueuePacketDeliveryAdapter, 'send_packet'))
        self.assertTrue(hasattr(QueuePacketDeliveryAdapter, 'acknowledge_packet'))


class _FakeTechLeadWorkerService:
    def __init__(self, result: TechLeadWorkerResult) -> None:
        self.result = result
        self.requests: list[TechLeadWorkerRequest] = []

    def handle_packet(self, request: TechLeadWorkerRequest) -> TechLeadWorkerResult:
        self.requests.append(request)
        return self.result

    def supports_packet_schema_type(self, packet_schema_type: str) -> bool:
        return packet_schema_type in {'worker_result_packet', 'qa_verification_packet'}


class _FakeQueuePacketReader:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload
        self.packet_paths: list[str] = []

    def read_packet(self, packet_reference: object) -> object:
        self.packet_paths.append(str(packet_reference))
        return self.payload


class QueuePacketRuntimeControllerTests(unittest.TestCase):
    def test_handle_packet_routes_supported_worker_result_packet_to_techlead_service(self) -> None:
        techlead_service = _FakeTechLeadWorkerService(_techlead_worker_result(ok=True))
        service = self._build_service(techlead_worker_service=techlead_service)

        result = service.handle_packet(
            QueuePacketRuntimeRequest(
                queue_name='fractal-core-architecture',
                packet_schema_type='worker_result_packet',
                packet_message_id='msg-123',
                packet_payload={
                    'methodology_execution_id': 'exec-123',
                    'project_slug': 'paa-platform',
                    'issue_number': 42,
                },
            )
        )

        self.assertTrue(result.ok)
        self.assertTrue(result.dry_run)
        self.assertEqual(result.dispatch_summary.handler_key, 'techlead-worker-dispatch')
        self.assertEqual(result.dispatch_summary.target_worker_host, 'TechLeadWorkerService')
        self.assertEqual(result.selected_worker_result, techlead_service.result)
        self.assertEqual(
            result.normalized_queue_side_effect_summary,
            'Dry run only: no queue send or ack side effects executed.',
        )
        self.assertEqual(len(techlead_service.requests), 1)
        self.assertEqual(techlead_service.requests[0].methodology_execution_id, 'exec-123')

    def test_handle_packet_returns_blocked_dispatch_when_techlead_worker_blocks(self) -> None:
        techlead_service = _FakeTechLeadWorkerService(_techlead_worker_result(ok=False))
        service = self._build_service(techlead_worker_service=techlead_service)

        result = service.handle_packet(
            QueuePacketRuntimeRequest(
                queue_name='fractal-core-architecture',
                packet_schema_type='worker_result_packet',
                packet_payload={
                    'methodology_execution_id': 'exec-123',
                    'project_slug': 'paa-platform',
                    'issue_number': 42,
                },
            )
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'techlead-routing-blocked')
        self.assertEqual(result.dispatch_summary.handler_key, 'techlead-worker-dispatch')
        self.assertEqual(result.dispatch_summary.target_worker_host, 'TechLeadWorkerService')
        self.assertEqual(
            result.normalized_queue_side_effect_summary,
            'Dry run only: queue side effects suppressed because dispatch did not succeed.',
        )
        self.assertEqual(result.dispatch_summary.blocking_reasons, ('techlead-routing-blocked',))

    def test_handle_packet_loads_payload_from_queue_packet_reader(self) -> None:
        techlead_service = _FakeTechLeadWorkerService(_techlead_worker_result(ok=True))
        queue_reader = _FakeQueuePacketReader(
            {
                'methodology_execution_id': 'exec-456',
                'project_slug': 'paa-platform',
                'issue_number': 77,
            }
        )
        service = self._build_service(
            techlead_worker_service=techlead_service,
            queue_packet_reader=queue_reader,
        )

        result = service.handle_packet(
            QueuePacketRuntimeRequest(
                queue_name='fractal-core-architecture',
                packet_schema_type='worker_result_packet',
                packet_path='packets/result-packet.json',
            )
        )

        self.assertTrue(result.ok)
        self.assertEqual(queue_reader.packet_paths, ['packets/result-packet.json'])
        self.assertEqual(techlead_service.requests[0].methodology_execution_id, 'exec-456')

    def test_handle_packet_routes_supported_qa_verification_packet_to_techlead_service(self) -> None:
        techlead_service = _FakeTechLeadWorkerService(
            _techlead_worker_result(ok=True, packet_schema_type='qa_verification_packet')
        )
        service = self._build_service(techlead_worker_service=techlead_service)

        result = service.handle_packet(
            QueuePacketRuntimeRequest(
                queue_name='paa-techlead',
                packet_schema_type='qa_verification_packet',
                packet_message_id='msg-qa-1',
                packet_payload={
                    'methodology_execution_id': 'exec-qa-1',
                    'project_slug': 'paa-platform',
                    'issue_number': 42,
                    'verification_status': 'pass',
                },
            )
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.dispatch_summary.target_worker_host, 'TechLeadWorkerService')
        self.assertEqual(techlead_service.requests[0].packet_schema_type, 'qa_verification_packet')

    def test_handle_packet_fails_closed_for_unsupported_packet_schema_type(self) -> None:
        service = self._build_service()

        result = service.handle_packet(
            QueuePacketRuntimeRequest(
                queue_name='fractal-core-architecture',
                packet_schema_type='techlead_assignment_packet',
            )
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'unsupported_packet_schema_type')
        self.assertEqual(result.dispatch_summary.handler_key, 'packet-classification')
        self.assertEqual(result.dispatch_summary.blocking_reasons, ('unsupported_packet_schema_type',))
        self.assertIsNone(result.selected_worker_result)

    def test_handle_packet_fails_closed_for_live_mode(self) -> None:
        service = self._build_service()

        result = service.handle_packet(
            QueuePacketRuntimeRequest(
                queue_name='fractal-core-architecture',
                packet_schema_type='worker_result_packet',
                runtime_mode='live',
            )
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'unsupported_runtime_mode')
        self.assertEqual(result.dispatch_summary.handler_key, 'runtime-mode-check')
        self.assertEqual(result.dispatch_summary.notes, ('fail-closed', 'dry-run-only'))
        self.assertFalse(result.dry_run)

    def test_handle_packet_fails_closed_when_payload_is_missing(self) -> None:
        service = self._build_service()

        result = service.handle_packet(
            QueuePacketRuntimeRequest(
                queue_name='fractal-core-architecture',
                packet_schema_type='worker_result_packet',
            )
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'missing_packet_payload')
        self.assertEqual(result.dispatch_summary.handler_key, 'packet-payload-resolution')
        self.assertEqual(result.dispatch_summary.blocking_reasons, ('missing_packet_payload',))

    def _build_service(
        self,
        *,
        techlead_worker_service: _FakeTechLeadWorkerService | None = None,
        queue_packet_reader: _FakeQueuePacketReader | None = None,
    ) -> DefaultQueuePacketRuntimeController:
        techlead_worker_service = techlead_worker_service or _FakeTechLeadWorkerService(
            _techlead_worker_result(ok=True)
        )
        unused = SimpleNamespace()
        logger = SimpleNamespace(info=lambda *args, **kwargs: None, warning=lambda *args, **kwargs: None)
        return DefaultQueuePacketRuntimeController(
            techlead_worker_service=techlead_worker_service,
            dev_worker_service=unused,
            qa_worker_service=unused,
            queue_packet_reader=queue_packet_reader,
            queue_packet_delivery_adapter=None,
            logger=logger,
        )


def _techlead_worker_result(*, ok: bool, packet_schema_type: str = 'worker_result_packet') -> TechLeadWorkerResult:
    dispatch_summary = TechLeadWorkerDispatchSummary(
        handler_key='worker-review-routing' if packet_schema_type == 'worker_result_packet' else 'qa-verification-acceptance',
        packet_schema_type=packet_schema_type,
        decision_service_used='TechLeadWorkerReviewRoutingService',
        decision_supported=ok,
        recommended_next_action='assign-dev' if ok and packet_schema_type == 'worker_result_packet' else ('close_slice' if ok else None),
        recommended_target_role='Dev' if ok and packet_schema_type == 'worker_result_packet' else ('TechLead' if ok else None),
        packet_emission_required=False,
        methodology_transition_required=False,
        blocking_reasons=() if ok else ('techlead-routing-blocked',),
        notes=('dry-run-only',),
    )
    return TechLeadWorkerResult(
        request=TechLeadWorkerRequest(
            packet_schema_type=packet_schema_type,
            methodology_execution_id='exec-123',
        ),
        methodology_execution_id='exec-123',
        current_execution_summary=None,
        dispatch_summary=dispatch_summary,
        worker_review_routing_result=None,
        methodology_transition_result=None,
        normalized_packet_output_summary='Dry run only: would emit the next packet.',
        ok=ok,
        reason=None if ok else 'techlead-routing-blocked',
        details=None if ok else 'Routing failed.',
        dry_run=True,
    )


if __name__ == '__main__':
    unittest.main()

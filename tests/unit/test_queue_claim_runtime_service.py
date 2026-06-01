from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))

from paa_core.services.queue_claim_runtime import (
    DefaultQueueClaimRuntimeService,
    QUEUE_CLAIM_RUNTIME_SERVICE_METADATA,
    QueueClaimRuntimeRequest,
)
from paa_core.services.queue_claim_runtime.contracts import (
    PacketEnvelopeValidator,
    QueueClaimRuntimeService,
    QueueClaimStateAdapter,
    QueueTransportAdapter,
)


class QueueClaimRuntimeServiceContractTests(unittest.TestCase):
    def test_metadata_is_published_for_governed_component(self) -> None:
        self.assertEqual(QUEUE_CLAIM_RUNTIME_SERVICE_METADATA.name, 'QueueClaimRuntimeService')
        self.assertEqual(QUEUE_CLAIM_RUNTIME_SERVICE_METADATA.kind, 'service')

    def test_contract_protocol_exposes_runtime_methods(self) -> None:
        self.assertTrue(hasattr(QueueClaimRuntimeService, 'assemble_queue_intake'))
        self.assertTrue(hasattr(QueueClaimRuntimeService, 'supports_intake_mode'))

    def test_contract_protocol_exposes_required_collaborator_properties(self) -> None:
        self.assertTrue(hasattr(QueueClaimRuntimeService, 'queue_transport_adapter'))
        self.assertTrue(hasattr(QueueClaimRuntimeService, 'queue_claim_state_adapter'))
        self.assertTrue(hasattr(QueueClaimRuntimeService, 'packet_envelope_validator'))
        self.assertTrue(hasattr(QueueClaimRuntimeService, 'logger'))

    def test_queue_transport_adapter_protocol_exposes_preview_and_claim(self) -> None:
        self.assertTrue(hasattr(QueueTransportAdapter, 'preview_queue'))
        self.assertTrue(hasattr(QueueTransportAdapter, 'claim_next_packet'))

    def test_claim_state_and_packet_validator_protocols_expose_expected_methods(self) -> None:
        self.assertTrue(hasattr(QueueClaimStateAdapter, 'record_claim'))
        self.assertTrue(hasattr(PacketEnvelopeValidator, 'validate_packet_envelope'))


class _FakeQueueTransportAdapter:
    def __init__(self, *, preview_result: object = None, claim_result: object = None) -> None:
        self.preview_result = preview_result
        self.claim_result = claim_result
        self.preview_calls: list[tuple[str, int]] = []
        self.claim_calls: list[tuple[str, str | None]] = []

    def preview_queue(self, queue_name: str, *, limit: int = 1) -> object:
        self.preview_calls.append((queue_name, limit))
        return self.preview_result

    def claim_next_packet(self, queue_name: str, *, claimant_name: str | None = None) -> object:
        self.claim_calls.append((queue_name, claimant_name))
        return self.claim_result


class _FakePacketEnvelopeValidator:
    def __init__(self, result: object = None) -> None:
        self.result = {'ok': True} if result is None else result
        self.calls: list[object] = []

    def validate_packet_envelope(self, packet: object) -> object:
        self.calls.append(packet)
        return self.result


class _FakeQueueClaimStateAdapter:
    def __init__(self, result: object = None) -> None:
        self.result = {'claim_id': 'claim-1'} if result is None else result
        self.calls: list[object] = []

    def record_claim(self, claim_record: object) -> object:
        self.calls.append(claim_record)
        return self.result


class QueueClaimRuntimeServiceTests(unittest.TestCase):
    def test_assemble_queue_intake_supports_preview_path(self) -> None:
        packet = {
            'packet_message_id': 'msg-1',
            'packet_schema_type': 'worker_result_packet',
            'packet_payload': {'methodology_execution_id': 'exec-1'},
        }
        service = self._build_service(preview_result=packet)

        result = service.assemble_queue_intake(
            QueueClaimRuntimeRequest(
                queue_name='fractal-core-architecture',
                intake_mode='preview',
            )
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.preview_summary.packet_message_id, 'msg-1')
        self.assertEqual(result.normalized_packet_payload, {'methodology_execution_id': 'exec-1'})
        self.assertIsNone(result.claim_summary)

    def test_assemble_queue_intake_supports_claim_next_path(self) -> None:
        packet = {
            'packet_message_id': 'msg-2',
            'packet_schema_type': 'worker_result_packet',
            'packet_payload': {'methodology_execution_id': 'exec-2'},
        }
        claim_state = _FakeQueueClaimStateAdapter({'claim_id': 'claim-99'})
        service = self._build_service(claim_result=packet, claim_state_adapter=claim_state)

        result = service.assemble_queue_intake(
            QueueClaimRuntimeRequest(
                queue_name='fractal-core-architecture',
                intake_mode='claim_next',
                claimant_name='techlead',
            )
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.claim_summary.claim_id, 'claim-99')
        self.assertEqual(claim_state.calls[0]['packet_message_id'], 'msg-2')
        self.assertEqual(result.normalized_packet_payload, {'methodology_execution_id': 'exec-2'})

    def test_assemble_queue_intake_fails_closed_for_unsupported_intake_mode(self) -> None:
        service = self._build_service()

        result = service.assemble_queue_intake(
            QueueClaimRuntimeRequest(
                queue_name='fractal-core-architecture',
                intake_mode='ack',
            )
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'unsupported_intake_mode')
        self.assertEqual(result.preview_summary.blocking_reasons, ('unsupported_intake_mode',))

    def test_assemble_queue_intake_fails_closed_for_missing_claimant_name(self) -> None:
        service = self._build_service()

        result = service.assemble_queue_intake(
            QueueClaimRuntimeRequest(
                queue_name='fractal-core-architecture',
                intake_mode='claim_next',
            )
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'missing_claimant_name')
        self.assertEqual(result.claim_summary.blocking_reasons, ('missing_claimant_name',))

    def test_assemble_queue_intake_fails_closed_for_invalid_packet_envelope(self) -> None:
        packet = {
            'packet_message_id': 'msg-3',
            'packet_schema_type': 'worker_result_packet',
            'packet_payload': {'methodology_execution_id': 'exec-3'},
        }
        service = self._build_service(preview_result=packet, validator_result={'ok': False})

        result = service.assemble_queue_intake(
            QueueClaimRuntimeRequest(
                queue_name='fractal-core-architecture',
                intake_mode='preview',
            )
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'invalid_packet_envelope')
        self.assertEqual(result.preview_summary.blocking_reasons, ('invalid_packet_envelope',))

    def test_assemble_queue_intake_fails_closed_for_unsupported_queue_name(self) -> None:
        service = self._build_service()

        result = service.assemble_queue_intake(
            QueueClaimRuntimeRequest(
                queue_name='fractal-core-python',
                intake_mode='preview',
            )
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'unsupported_queue_name')
        self.assertEqual(result.preview_summary.blocking_reasons, ('unsupported_queue_name',))

    def test_assemble_queue_intake_fails_closed_for_missing_queue_packet(self) -> None:
        service = self._build_service(preview_result=None)

        result = service.assemble_queue_intake(
            QueueClaimRuntimeRequest(
                queue_name='fractal-core-architecture',
                intake_mode='preview',
            )
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'missing_queue_packet')
        self.assertEqual(result.preview_summary.blocking_reasons, ('missing_queue_packet',))

    def test_assemble_queue_intake_fails_closed_for_unsupported_packet_schema_type(self) -> None:
        packet = {
            'packet_message_id': 'msg-4',
            'packet_schema_type': 'qa_verification_packet',
            'packet_payload': {'verification_status': 'pass'},
        }
        service = self._build_service(preview_result=packet)

        result = service.assemble_queue_intake(
            QueueClaimRuntimeRequest(
                queue_name='fractal-core-architecture',
                intake_mode='preview',
            )
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'unsupported_packet_schema_type')
        self.assertEqual(result.preview_summary.blocking_reasons, ('unsupported_packet_schema_type',))

    def _build_service(
        self,
        *,
        preview_result: object = None,
        claim_result: object = None,
        validator_result: object = None,
        claim_state_adapter: _FakeQueueClaimStateAdapter | None = None,
    ) -> DefaultQueueClaimRuntimeService:
        transport = _FakeQueueTransportAdapter(preview_result=preview_result, claim_result=claim_result)
        validator = _FakePacketEnvelopeValidator(validator_result)
        logger = SimpleNamespace(info=lambda *args, **kwargs: None, warning=lambda *args, **kwargs: None)
        return DefaultQueueClaimRuntimeService(
            queue_transport_adapter=transport,
            packet_envelope_validator=validator,
            queue_claim_state_adapter=claim_state_adapter,
            logger=logger,
        )


if __name__ == '__main__':
    unittest.main()

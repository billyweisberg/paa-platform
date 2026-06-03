from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))

from paa_core.runtime.packets.reference_resolution import (
    DefaultPacketReferenceResolutionService,
    PACKET_REFERENCE_RESOLUTION_SERVICE_METADATA,
    PacketReferenceResolutionRequest,
)
from paa_core.runtime.packets.reference_resolution.contracts import (
    PacketArtifactReader,
    PacketReferenceResolutionService,
    RuntimePathAdapter,
)
from paa_core.repositories.runtime_event import AutomationRunRecord, QueueMessageRecord


class PacketReferenceResolutionServiceContractTests(unittest.TestCase):
    def test_metadata_is_published_for_governed_component(self) -> None:
        self.assertEqual(PACKET_REFERENCE_RESOLUTION_SERVICE_METADATA.name, 'PacketReferenceResolutionService')
        self.assertEqual(PACKET_REFERENCE_RESOLUTION_SERVICE_METADATA.kind, 'service')

    def test_contract_protocol_exposes_runtime_methods(self) -> None:
        self.assertTrue(hasattr(PacketReferenceResolutionService, 'resolve_packet_reference'))
        self.assertTrue(hasattr(PacketReferenceResolutionService, 'supports_packet_schema_type'))

    def test_contract_protocol_exposes_required_collaborator_properties(self) -> None:
        self.assertTrue(hasattr(PacketReferenceResolutionService, 'runtime_event_repository'))
        self.assertTrue(hasattr(PacketReferenceResolutionService, 'packet_artifact_reader'))
        self.assertTrue(hasattr(PacketReferenceResolutionService, 'runtime_path_adapter'))
        self.assertTrue(hasattr(PacketReferenceResolutionService, 'logger'))

    def test_optional_adapter_protocols_expose_expected_methods(self) -> None:
        self.assertTrue(hasattr(PacketArtifactReader, 'read_packet_payload'))
        self.assertTrue(hasattr(RuntimePathAdapter, 'resolve_packet_path'))


class _FakeRuntimeEventRepository:
    def __init__(
        self,
        *,
        queue_message: QueueMessageRecord | None = None,
        automation_run: AutomationRunRecord | None = None,
    ) -> None:
        self.queue_message = queue_message
        self.automation_run = automation_run
        self.message_id_calls: list[str] = []
        self.automation_message_id_calls: list[str] = []

    def get_queue_message_by_external(self, message_id_external: str):
        self.message_id_calls.append(message_id_external)
        return self.queue_message

    def get_latest_automation_run_for_message_id(self, message_id_external: str):
        self.automation_message_id_calls.append(message_id_external)
        return self.automation_run


class _FakePacketArtifactReader:
    def __init__(self, payload: dict[str, object] | None = None) -> None:
        self.payload = payload if payload is not None else {'methodology_execution_id': 'exec-1'}
        self.calls: list[str] = []

    def read_packet_payload(self, packet_path: str) -> dict[str, object]:
        self.calls.append(packet_path)
        return self.payload


class _FakeRuntimePathAdapter:
    def __init__(self, resolved_path: str | None = None) -> None:
        self.resolved_path = resolved_path
        self.calls: list[str] = []

    def resolve_packet_path(self, packet_reference: str) -> str | None:
        self.calls.append(packet_reference)
        return self.resolved_path


class PacketReferenceResolutionServiceTests(unittest.TestCase):
    def test_resolve_packet_reference_supports_message_id_lookup_with_artifact_path_resolution(self) -> None:
        reader = _FakePacketArtifactReader({'methodology_execution_id': 'exec-1', 'source_packet_path': '/tmp/worker-result.json'})
        service = self._build_service(
            queue_message=QueueMessageRecord(
                queue_message_id='queue-message-1',
                handoff_id='handoff-1',
                queue_name='fractal-core-architecture',
                schema_type='worker_result_packet',
                message_id_external='msg-1',
                correlation_key='corr-1',
                payload={},
                status='sent',
                sent_at=None,
                claimed_at=None,
                acknowledged_at=None,
                metadata={},
                created_at=None,
                updated_at=None,
            ),
            automation_run=AutomationRunRecord(
                automation_run_id='automation-run-1',
                agent_id='agent-1',
                work_item_id='work-item-1',
                handoff_id='handoff-1',
                trigger_type='packet_compilation:worker_result_packet',
                status='completed',
                started_at=None,
                finished_at=None,
                summary='Compiled worker result packet.',
                artifacts={
                    'message_id': 'msg-1',
                    'packet_output_path': '/tmp/worker-result.json',
                },
                created_at=None,
                updated_at=None,
            ),
            packet_artifact_reader=reader,
        )

        result = service.resolve_packet_reference(
            PacketReferenceResolutionRequest(
                packet_message_id='msg-1',
                queue_name='fractal-core-architecture',
                packet_schema_type='worker_result_packet',
            )
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.resolution_summary.resolution_source, 'message-id')
        self.assertEqual(result.resolution_summary.packet_reference, 'msg-1')
        self.assertEqual(result.resolution_summary.resolved_packet_path, '/tmp/worker-result.json')
        self.assertEqual(result.normalized_packet_payload, {'methodology_execution_id': 'exec-1', 'source_packet_path': '/tmp/worker-result.json'})
        self.assertEqual(reader.calls, ['/tmp/worker-result.json'])

    def test_resolve_packet_reference_supports_packet_path_with_payload_reader(self) -> None:
        reader = _FakePacketArtifactReader({'methodology_execution_id': 'exec-2'})
        service = self._build_service(packet_artifact_reader=reader)

        result = service.resolve_packet_reference(
            PacketReferenceResolutionRequest(
                packet_path='packets/worker-result.json',
                packet_schema_type='worker_result_packet',
            )
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.resolution_summary.resolved_packet_path, 'packets/worker-result.json')
        self.assertEqual(result.normalized_packet_payload, {'methodology_execution_id': 'exec-2'})
        self.assertEqual(reader.calls, ['packets/worker-result.json'])

    def test_resolve_packet_reference_supports_techlead_assignment_packet_path(self) -> None:
        reader = _FakePacketArtifactReader({'methodology_execution_id': 'exec-qa-1'})
        service = self._build_service(packet_artifact_reader=reader)

        result = service.resolve_packet_reference(
            PacketReferenceResolutionRequest(
                packet_path='packets/techlead-assignment.json',
                packet_schema_type='techlead_assignment_packet',
            )
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.resolution_summary.resolved_packet_path, 'packets/techlead-assignment.json')
        self.assertEqual(result.normalized_packet_payload, {'methodology_execution_id': 'exec-qa-1'})
        self.assertEqual(reader.calls, ['packets/techlead-assignment.json'])

    def test_resolve_packet_reference_supports_runtime_packet_reference_resolution(self) -> None:
        reader = _FakePacketArtifactReader({'methodology_execution_id': 'exec-3'})
        runtime_path_adapter = _FakeRuntimePathAdapter('packets/runtime-worker-result.json')
        service = self._build_service(
            packet_artifact_reader=reader,
            runtime_path_adapter=runtime_path_adapter,
        )

        result = service.resolve_packet_reference(
            PacketReferenceResolutionRequest(
                packet_reference='runtime:worker-result:msg-3',
                packet_schema_type='worker_result_packet',
            )
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.resolution_summary.resolution_source, 'packet-reference')
        self.assertEqual(result.resolution_summary.resolved_packet_path, 'packets/runtime-worker-result.json')
        self.assertEqual(reader.calls, ['packets/runtime-worker-result.json'])

    def test_resolve_packet_reference_fails_closed_for_unresolved_message_id(self) -> None:
        service = self._build_service()

        result = service.resolve_packet_reference(
            PacketReferenceResolutionRequest(
                packet_message_id='missing-msg',
                packet_schema_type='worker_result_packet',
            )
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'unresolved_packet_message_id')
        self.assertEqual(result.resolution_summary.blocking_reasons, ('unresolved_packet_message_id',))

    def test_resolve_packet_reference_fails_closed_for_queue_name_mismatch(self) -> None:
        service = self._build_service(
            queue_message=QueueMessageRecord(
                queue_message_id='queue-message-2',
                handoff_id='handoff-2',
                queue_name='fractal-core-python',
                schema_type='worker_result_packet',
                message_id_external='msg-2',
                correlation_key='corr-2',
                payload={},
                status='sent',
                sent_at=None,
                claimed_at=None,
                acknowledged_at=None,
                metadata={},
                created_at=None,
                updated_at=None,
            )
        )

        result = service.resolve_packet_reference(
            PacketReferenceResolutionRequest(
                packet_message_id='msg-2',
                queue_name='fractal-core-architecture',
                packet_schema_type='worker_result_packet',
            )
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'queue_name_mismatch')
        self.assertEqual(result.resolution_summary.blocking_reasons, ('queue_name_mismatch',))

    def test_resolve_packet_reference_fails_closed_for_unsupported_packet_schema_type(self) -> None:
        service = self._build_service()

        result = service.resolve_packet_reference(
            PacketReferenceResolutionRequest(
                packet_path='packets/qa.json',
                packet_schema_type='architect_cycle_packet',
            )
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'unsupported_packet_schema_type')
        self.assertEqual(result.resolution_summary.blocking_reasons, ('unsupported_packet_schema_type',))

    def test_resolve_packet_reference_fails_closed_for_missing_identity(self) -> None:
        service = self._build_service()

        result = service.resolve_packet_reference(PacketReferenceResolutionRequest())

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'missing_packet_reference_identity')

    def test_resolve_packet_reference_fails_closed_for_unresolved_runtime_reference(self) -> None:
        service = self._build_service(runtime_path_adapter=_FakeRuntimePathAdapter(None))

        result = service.resolve_packet_reference(
            PacketReferenceResolutionRequest(
                packet_reference='runtime:worker-result:missing',
                packet_schema_type='worker_result_packet',
            )
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'unresolved_packet_reference')
        self.assertEqual(result.resolution_summary.blocking_reasons, ('unresolved_packet_reference',))

    def _build_service(
        self,
        *,
        queue_message: QueueMessageRecord | None = None,
        automation_run: AutomationRunRecord | None = None,
        packet_artifact_reader: _FakePacketArtifactReader | None = None,
        runtime_path_adapter: _FakeRuntimePathAdapter | None = None,
    ) -> DefaultPacketReferenceResolutionService:
        return DefaultPacketReferenceResolutionService(
            runtime_event_repository=_FakeRuntimeEventRepository(
                queue_message=queue_message,
                automation_run=automation_run,
            ),
            packet_artifact_reader=packet_artifact_reader,
            runtime_path_adapter=runtime_path_adapter,
        )


if __name__ == '__main__':
    unittest.main()

from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))

from paa_core.services.queue_packet_runtime_controller import (
    QueuePacketDispatchSummary,
    QueuePacketRuntimeRequest,
    QueuePacketRuntimeResult,
)


class QueuePacketRuntimeControllerModelTests(unittest.TestCase):
    def test_request_defaults_to_dry_run_mode(self) -> None:
        request = QueuePacketRuntimeRequest(
            queue_name='fractal-core-architecture',
            packet_schema_type='worker_result_packet',
        )

        self.assertEqual(request.runtime_mode, 'dry_run')
        self.assertIsNone(request.packet_message_id)

    def test_dispatch_summary_captures_first_runtime_controller_slice_shape(self) -> None:
        summary = QueuePacketDispatchSummary(
            handler_key='techlead-worker-result-dry-run',
            packet_schema_type='worker_result_packet',
            target_worker_host='TechLeadWorkerService',
            dispatch_supported=True,
            queue_side_effect_required=False,
            ack_required=False,
            blocking_reasons=(),
            notes=('dry-run only',),
        )

        self.assertTrue(summary.dispatch_supported)
        self.assertEqual(summary.target_worker_host, 'TechLeadWorkerService')
        self.assertEqual(summary.notes, ('dry-run only',))

    def test_result_supports_typed_runtime_controller_outcome(self) -> None:
        request = QueuePacketRuntimeRequest(
            queue_name='fractal-core-architecture',
            packet_schema_type='worker_result_packet',
            packet_message_id='msg-123',
        )
        summary = QueuePacketDispatchSummary(
            handler_key='techlead-worker-result-dry-run',
            packet_schema_type='worker_result_packet',
            target_worker_host='TechLeadWorkerService',
            dispatch_supported=True,
            queue_side_effect_required=False,
            ack_required=False,
            blocking_reasons=(),
            notes=(),
        )

        result = QueuePacketRuntimeResult(
            request=request,
            dispatch_summary=summary,
            selected_worker_result=None,
            normalized_queue_side_effect_summary='no queue side effects in dry-run mode',
            ok=True,
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.request.packet_message_id, 'msg-123')
        self.assertEqual(
            result.normalized_queue_side_effect_summary,
            'no queue side effects in dry-run mode',
        )


if __name__ == '__main__':
    unittest.main()

from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))

from paa_core.runtime.orchestration.queue_claim_runtime import (
    QueueClaimRuntimeRequest,
    QueueClaimRuntimeResult,
    QueuePacketClaimSummary,
    QueuePacketPreviewSummary,
)


class QueueClaimRuntimeServiceModelTests(unittest.TestCase):
    def test_request_model_captures_supported_queue_intake_slice(self) -> None:
        request = QueueClaimRuntimeRequest(
            queue_name='paa-techlead',
            intake_mode='preview',
            packet_schema_type='worker_result_packet',
            claimant_name='techlead',
            host_name='local-runtime',
            metadata={'source': 'cli'},
        )

        self.assertEqual(request.queue_name, 'paa-techlead')
        self.assertEqual(request.intake_mode, 'preview')
        self.assertEqual(request.packet_schema_type, 'worker_result_packet')
        self.assertEqual(request.metadata, {'source': 'cli'})

    def test_preview_and_claim_summary_models_capture_stable_intake_state(self) -> None:
        preview = QueuePacketPreviewSummary(
            queue_name='paa-techlead',
            packet_message_id='msg-1',
            packet_schema_type='worker_result_packet',
            packet_reference='packets/worker-result.json',
            preview_supported=True,
            claim_supported=True,
            blocking_reasons=(),
            notes=('preview',),
        )
        claim = QueuePacketClaimSummary(
            queue_name='paa-techlead',
            claim_id='claim-1',
            claimant_name='techlead',
            packet_message_id='msg-1',
            packet_reference='packets/worker-result.json',
            claim_supported=True,
            blocking_reasons=(),
            notes=('claimed',),
        )

        self.assertTrue(preview.preview_supported)
        self.assertTrue(preview.claim_supported)
        self.assertEqual(claim.claim_id, 'claim-1')
        self.assertEqual(claim.notes, ('claimed',))

    def test_result_model_captures_normalized_payload_and_failure_state(self) -> None:
        request = QueueClaimRuntimeRequest(
            queue_name='paa-techlead',
            intake_mode='claim_next',
        )
        preview = QueuePacketPreviewSummary(
            queue_name='paa-techlead',
            packet_message_id=None,
            packet_schema_type=None,
            packet_reference=None,
            preview_supported=False,
            claim_supported=False,
            blocking_reasons=('missing_packet',),
            notes=('fail-closed',),
        )
        result = QueueClaimRuntimeResult(
            request=request,
            preview_summary=preview,
            claim_summary=None,
            normalized_packet_envelope={'packet_reference': 'packets/worker-result.json'},
            normalized_packet_payload=None,
            ok=False,
            reason='missing_packet',
            details='No queue packet available for preview or claim.',
            metadata={'queue_depth': 0},
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'missing_packet')
        self.assertEqual(result.metadata, {'queue_depth': 0})


if __name__ == '__main__':
    unittest.main()

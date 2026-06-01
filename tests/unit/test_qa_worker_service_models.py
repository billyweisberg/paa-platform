from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))

from paa_core.services.qa_worker import (
    QAWorkerRequest,
    QAWorkerResult,
    QAWorkerVerificationSummary,
)


class QAWorkerServiceModelTests(unittest.TestCase):
    def test_request_defaults_to_dry_run_mode(self) -> None:
        request = QAWorkerRequest(packet_schema_type='qa_verification_packet')

        self.assertEqual(request.runtime_mode, 'dry_run')
        self.assertIsNone(request.methodology_execution_id)

    def test_verification_summary_captures_first_runtime_slice_shape(self) -> None:
        summary = QAWorkerVerificationSummary(
            handler_key='qa-verification-dry-run',
            packet_schema_type='qa_verification_packet',
            runtime_mode='dry_run',
            verification_supported=True,
            verification_runner_used='StubQAVerificationRunner',
            packet_context_required=True,
            packet_context_ok=True,
            qa_verification_packet_required=True,
            methodology_transition_required=False,
            blocking_reasons=(),
            notes=('assembled packet context',),
        )

        self.assertTrue(summary.verification_supported)
        self.assertTrue(summary.packet_context_ok)
        self.assertEqual(summary.notes, ('assembled packet context',))

    def test_result_supports_typed_runtime_host_outcome(self) -> None:
        request = QAWorkerRequest(
            packet_schema_type='qa_verification_packet',
            methodology_execution_id='exec-123',
        )
        summary = QAWorkerVerificationSummary(
            handler_key='qa-verification-dry-run',
            packet_schema_type='qa_verification_packet',
            runtime_mode='dry_run',
            verification_supported=True,
            verification_runner_used='StubQAVerificationRunner',
            packet_context_required=True,
            packet_context_ok=True,
            qa_verification_packet_required=True,
            methodology_transition_required=False,
            blocking_reasons=(),
            notes=(),
        )

        result = QAWorkerResult(
            request=request,
            methodology_execution_id='exec-123',
            current_execution_summary=None,
            packet_context_result=None,
            verification_summary=summary,
            verification_result={'verification_status': 'pass'},
            methodology_transition_result=None,
            normalized_packet_output_summary='qa_verification_packet ready',
            ok=True,
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.methodology_execution_id, 'exec-123')
        self.assertEqual(result.normalized_packet_output_summary, 'qa_verification_packet ready')


if __name__ == '__main__':
    unittest.main()

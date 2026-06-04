from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))

from paa_core.runtime.workers.dev_worker import (
    DevWorkerExecutionSummary,
    DevWorkerRequest,
    DevWorkerResult,
)


class DevWorkerServiceModelTests(unittest.TestCase):
    def test_request_defaults_to_dry_run_mode(self) -> None:
        request = DevWorkerRequest(packet_schema_type='techlead_assignment_packet')

        self.assertEqual(request.runtime_mode, 'dry_run')
        self.assertIsNone(request.methodology_execution_id)

    def test_execution_summary_captures_first_runtime_slice_shape(self) -> None:
        summary = DevWorkerExecutionSummary(
            handler_key='dev-assignment-dry-run',
            packet_schema_type='techlead_assignment_packet',
            runtime_mode='dry_run',
            execution_supported=True,
            execution_runner_used='StubDevExecutionRunner',
            packet_context_required=True,
            packet_context_ok=True,
            worker_result_packet_required=True,
            methodology_transition_required=False,
            blocking_reasons=(),
            notes=('assembled packet context',),
        )

        self.assertTrue(summary.execution_supported)
        self.assertTrue(summary.packet_context_ok)
        self.assertEqual(summary.notes, ('assembled packet context',))

    def test_result_supports_typed_runtime_host_outcome(self) -> None:
        request = DevWorkerRequest(
            packet_schema_type='techlead_assignment_packet',
            methodology_execution_id='exec-123',
        )
        summary = DevWorkerExecutionSummary(
            handler_key='dev-assignment-dry-run',
            packet_schema_type='techlead_assignment_packet',
            runtime_mode='dry_run',
            execution_supported=True,
            execution_runner_used='StubDevExecutionRunner',
            packet_context_required=True,
            packet_context_ok=True,
            worker_result_packet_required=True,
            methodology_transition_required=False,
            blocking_reasons=(),
            notes=(),
        )

        result = DevWorkerResult(
            request=request,
            methodology_execution_id='exec-123',
            current_execution_summary=None,
            packet_context_result=None,
            execution_summary=summary,
            execution_result={'status': 'ok'},
            methodology_transition_result=None,
            normalized_packet_output_summary='worker_result_packet ready',
            ok=True,
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.methodology_execution_id, 'exec-123')
        self.assertEqual(result.normalized_packet_output_summary, 'worker_result_packet ready')


if __name__ == '__main__':
    unittest.main()

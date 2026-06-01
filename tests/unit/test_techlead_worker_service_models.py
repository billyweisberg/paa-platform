from __future__ import annotations

import sys
from pathlib import Path
import unittest
from typing import get_type_hints

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))

from paa_core.services.techlead_worker import (
    TechLeadWorkerDispatchSummary,
    TechLeadWorkerRequest,
    TechLeadWorkerResult,
)
from paa_core.services.techlead_worker.contracts import TechLeadWorkerService


class TechLeadWorkerServiceModelsTests(unittest.TestCase):
    def test_request_carries_supported_first_slice_fields(self) -> None:
        request = TechLeadWorkerRequest(
            packet_schema_type='worker_result_packet',
            packet_message_id='msg-123',
            methodology_execution_id='exec-123',
            runtime_mode='dry_run',
        )

        self.assertEqual(request.packet_schema_type, 'worker_result_packet')
        self.assertEqual(request.packet_message_id, 'msg-123')
        self.assertEqual(request.methodology_execution_id, 'exec-123')
        self.assertEqual(request.runtime_mode, 'dry_run')

    def test_dispatch_summary_carries_routing_and_transition_flags(self) -> None:
        summary = TechLeadWorkerDispatchSummary(
            handler_key='worker-review-routing',
            packet_schema_type='worker_result_packet',
            decision_service_used='TechLeadWorkerReviewRoutingService',
            decision_supported=True,
            recommended_next_action='assign-qa',
            recommended_target_role='qa',
            packet_emission_required=False,
            methodology_transition_required=False,
            blocking_reasons=(),
            notes=('dry-run only',),
        )

        self.assertEqual(summary.handler_key, 'worker-review-routing')
        self.assertEqual(summary.recommended_target_role, 'qa')
        self.assertFalse(summary.packet_emission_required)
        self.assertEqual(summary.notes, ('dry-run only',))

    def test_result_wraps_typed_request_and_dispatch_summary(self) -> None:
        request = TechLeadWorkerRequest(packet_schema_type='worker_result_packet')
        dispatch_summary = TechLeadWorkerDispatchSummary(
            handler_key='worker-review-routing',
            packet_schema_type='worker_result_packet',
            decision_service_used='TechLeadWorkerReviewRoutingService',
            decision_supported=True,
            recommended_next_action='assign-qa',
            recommended_target_role='qa',
            packet_emission_required=False,
            methodology_transition_required=False,
            blocking_reasons=(),
            notes=(),
        )
        result = TechLeadWorkerResult(
            request=request,
            methodology_execution_id='exec-123',
            current_execution_summary=None,
            dispatch_summary=dispatch_summary,
            worker_review_routing_result=None,
            methodology_transition_result=None,
            normalized_packet_output_summary=None,
            ok=True,
        )

        self.assertIs(result.request, request)
        self.assertIs(result.dispatch_summary, dispatch_summary)
        self.assertTrue(result.ok)
        self.assertTrue(result.dry_run)

    def test_contract_now_uses_typed_request_and_result(self) -> None:
        annotations = get_type_hints(TechLeadWorkerService.handle_packet)

        self.assertEqual(annotations['request'].__name__, 'TechLeadWorkerRequest')
        self.assertEqual(annotations['return'].__name__, 'TechLeadWorkerResult')


if __name__ == '__main__':
    unittest.main()

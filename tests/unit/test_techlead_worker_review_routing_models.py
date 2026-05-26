from __future__ import annotations

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'packages' / 'paa-core' / 'src'))

from paa_core.services.techlead_worker_review_routing import (
    TechLeadWorkerReviewRoutingRequest,
    TechLeadWorkerReviewRoutingResult,
    TechLeadWorkerReviewRoutingSummary,
)


class TechLeadWorkerReviewRoutingModelsTests(unittest.TestCase):
    def test_request_carries_worker_result_review_inputs(self) -> None:
        request = TechLeadWorkerReviewRoutingRequest(
            project_slug='paa-platform',
            issue_number=123,
            pr_number=456,
            workflow_stage='techlead_worker_review_pending',
            worker_role='Python Dev',
            worker_result_type='implemented_ready_for_qa',
            source_packet_schema_type='worker_result_packet',
            source_packet_message_id='msg-123',
            metadata={'source': 'unit-test'},
        )
        self.assertEqual(request.project_slug, 'paa-platform')
        self.assertEqual(request.issue_number, 123)
        self.assertEqual(request.pr_number, 456)
        self.assertEqual(request.worker_role, 'Python Dev')
        self.assertEqual(request.worker_result_type, 'implemented_ready_for_qa')

    def test_result_carries_structured_review_routing_summary(self) -> None:
        summary = TechLeadWorkerReviewRoutingSummary(
            decision_supported=True,
            recommended_next_decision='assign_qa',
            recommended_target_role='QA',
            qa_assignment_allowed=True,
            review_summary='Worker result is ready for QA verification.',
            blocking_reasons=(),
            notes=('narrow-slice',),
        )
        result = TechLeadWorkerReviewRoutingResult(
            project_slug='paa-platform',
            issue_number=123,
            pr_number=456,
            workflow_stage='techlead_worker_review_pending',
            worker_role='Python Dev',
            worker_result_type='implemented_ready_for_qa',
            source_packet_schema_type='worker_result_packet',
            source_packet_message_id='msg-123',
            summary=summary,
            ok=True,
            recommended_actions=('assign_qa',),
            unattended_safe=True,
            metadata={'source': 'unit-test'},
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.summary.recommended_next_decision, 'assign_qa')
        self.assertEqual(result.summary.recommended_target_role, 'QA')
        self.assertEqual(result.source_packet_message_id, 'msg-123')
        self.assertEqual(result.recommended_actions, ('assign_qa',))


if __name__ == '__main__':
    unittest.main()

from __future__ import annotations

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'packages' / 'paa-core' / 'src'))

from paa_core.services.techlead_delivery_review_decision.models import (
    TechLeadDeliveryReviewDecisionRequest,
    TechLeadDeliveryReviewDecisionResult,
    TechLeadDeliveryReviewDecisionSummary,
)


class TechLeadDeliveryReviewDecisionModelsTests(unittest.TestCase):
    def test_request_model_preserves_delivery_review_context_fields(self) -> None:
        request = TechLeadDeliveryReviewDecisionRequest(
            project_slug='paa-platform',
            issue_number=42,
            issue_url='https://example.test/issues/42',
            pr_number=77,
            pr_url='https://example.test/pulls/77',
            workflow_stage='techlead_delivery_review_pending',
            delivery_review_result_type='ready_for_dev',
            recommended_action_name='assign_worker',
            recommended_target_role='Python Dev',
            recommended_reason='Slice is implementation-ready.',
            resolved_team_worker_key='python',
            resolved_team_worker_display_name='Python Dev',
            source_packet_schema_type='delivery_review_packet',
            source_packet_message_id='msg-123',
            source_packet_path='handoff/packet.json',
            branch_name='issue-42',
            metadata={'source_queue_name': 'fractal-core-architecture'},
        )

        self.assertEqual(request.issue_number, 42)
        self.assertEqual(request.delivery_review_result_type, 'ready_for_dev')
        self.assertEqual(request.resolved_team_worker_key, 'python')
        self.assertEqual(request.branch_name, 'issue-42')

    def test_result_model_wraps_structured_summary(self) -> None:
        summary = TechLeadDeliveryReviewDecisionSummary(
            decision_supported=True,
            recommended_next_decision='assign_worker',
            recommended_target_role='Python Dev',
            assignment_allowed=True,
            delivery_review_summary='Delivery review is ready for Python Dev.',
            blocking_reasons=(),
            notes=('ready-for-dev',),
        )
        result = TechLeadDeliveryReviewDecisionResult(
            project_slug='paa-platform',
            issue_number=42,
            issue_url='https://example.test/issues/42',
            pr_number=77,
            pr_url='https://example.test/pulls/77',
            workflow_stage='techlead_delivery_review_pending',
            delivery_review_result_type='ready_for_dev',
            recommended_action_name='assign_worker',
            recommended_target_role='Python Dev',
            resolved_team_worker_key='python',
            resolved_team_worker_display_name='Python Dev',
            source_packet_schema_type='delivery_review_packet',
            source_packet_message_id='msg-123',
            source_packet_path='handoff/packet.json',
            branch_name='issue-42',
            summary=summary,
            ok=True,
            recommended_actions=('assign_worker',),
            unattended_safe=True,
            metadata={'delivery_mode': 'ready_for_dev'},
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.summary.recommended_next_decision, 'assign_worker')
        self.assertEqual(result.recommended_actions, ('assign_worker',))
        self.assertTrue(result.unattended_safe)


if __name__ == '__main__':
    unittest.main()

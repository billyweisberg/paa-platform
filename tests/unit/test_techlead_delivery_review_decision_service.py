from __future__ import annotations

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'packages' / 'paa-core' / 'src'))

from paa_core.services.techlead_delivery_review_decision import (
    DefaultTechLeadDeliveryReviewDecisionService,
)
from paa_core.services.techlead_delivery_review_decision.models import (
    TechLeadDeliveryReviewDecisionRequest,
)


class TechLeadDeliveryReviewDecisionServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = DefaultTechLeadDeliveryReviewDecisionService()

    def test_ready_for_dev_assign_worker_returns_supported_decision(self) -> None:
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
            recommended_reason='Delivery Architect cleared the slice for implementation.',
            resolved_team_worker_key='python',
            resolved_team_worker_display_name='Python Dev',
            source_packet_schema_type='delivery_review_packet',
            source_packet_message_id='msg-123',
            source_packet_path='handoff/packet.json',
            branch_name='issue-42',
        )

        result = self.service.derive_delivery_review_decision(request)

        self.assertTrue(result.ok)
        self.assertTrue(result.summary.decision_supported)
        self.assertEqual(result.summary.recommended_next_decision, 'assign_worker')
        self.assertEqual(result.summary.recommended_target_role, 'Python Dev')
        self.assertTrue(result.summary.assignment_allowed)
        self.assertEqual(result.recommended_actions, ('assign_worker',))
        self.assertTrue(result.unattended_safe)

    def test_missing_issue_number_fails_closed(self) -> None:
        request = TechLeadDeliveryReviewDecisionRequest(
            project_slug='paa-platform',
            issue_number=0,
            workflow_stage='techlead_delivery_review_pending',
            delivery_review_result_type='ready_for_dev',
            recommended_action_name='assign_worker',
            resolved_team_worker_key='python',
            resolved_team_worker_display_name='Python Dev',
        )

        result = self.service.derive_delivery_review_decision(request)

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'missing_issue_number')

    def test_missing_workflow_stage_fails_closed(self) -> None:
        request = TechLeadDeliveryReviewDecisionRequest(
            project_slug='paa-platform',
            issue_number=42,
            workflow_stage='',
            delivery_review_result_type='ready_for_dev',
            recommended_action_name='assign_worker',
            resolved_team_worker_key='python',
            resolved_team_worker_display_name='Python Dev',
        )

        result = self.service.derive_delivery_review_decision(request)

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'missing_workflow_stage')

    def test_unsupported_result_type_fails_closed(self) -> None:
        request = TechLeadDeliveryReviewDecisionRequest(
            project_slug='paa-platform',
            issue_number=42,
            workflow_stage='techlead_delivery_review_pending',
            delivery_review_result_type='narrow_scope',
            recommended_action_name='assign_worker',
            resolved_team_worker_key='python',
            resolved_team_worker_display_name='Python Dev',
        )

        result = self.service.derive_delivery_review_decision(request)

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'unsupported_delivery_review_decision')

    def test_ready_for_dev_without_assign_worker_fails_closed(self) -> None:
        request = TechLeadDeliveryReviewDecisionRequest(
            project_slug='paa-platform',
            issue_number=42,
            workflow_stage='techlead_delivery_review_pending',
            delivery_review_result_type='ready_for_dev',
            recommended_action_name='pause_slice',
            resolved_team_worker_key='python',
            resolved_team_worker_display_name='Python Dev',
        )

        result = self.service.derive_delivery_review_decision(request)

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'delivery_review_ready_for_dev_without_assign_worker')

    def test_ready_for_dev_without_supported_worker_resolution_fails_closed(self) -> None:
        request = TechLeadDeliveryReviewDecisionRequest(
            project_slug='paa-platform',
            issue_number=42,
            workflow_stage='techlead_delivery_review_pending',
            delivery_review_result_type='ready_for_dev',
            recommended_action_name='assign_worker',
            recommended_target_role='Unknown Worker',
            resolved_team_worker_key=None,
            resolved_team_worker_display_name=None,
        )

        result = self.service.derive_delivery_review_decision(request)

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'delivery_review_ready_for_dev_target_not_supported')

    def test_supports_delivery_review_decision_is_narrow(self) -> None:
        self.assertTrue(
            self.service.supports_delivery_review_decision(
                'techlead_delivery_review_pending',
                'ready_for_dev',
            )
        )
        self.assertFalse(
            self.service.supports_delivery_review_decision(
                'techlead_delivery_review_pending',
                'request_reset',
            )
        )
        self.assertFalse(
            self.service.supports_delivery_review_decision(
                'techlead_worker_review_pending',
                'ready_for_dev',
            )
        )


if __name__ == '__main__':
    unittest.main()

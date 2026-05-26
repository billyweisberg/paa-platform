from __future__ import annotations

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'packages' / 'paa-core' / 'src'))

from paa_core.services.techlead_worker_review_routing import (
    DefaultTechLeadWorkerReviewRoutingService,
    TechLeadWorkerReviewRoutingRequest,
)


class TechLeadWorkerReviewRoutingServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = DefaultTechLeadWorkerReviewRoutingService()

    def test_implemented_ready_for_qa_recommends_assign_qa(self) -> None:
        request = TechLeadWorkerReviewRoutingRequest(
            project_slug='paa-platform',
            issue_number=123,
            pr_number=456,
            workflow_stage='techlead_worker_review_pending',
            worker_role='Python Dev',
            worker_result_type='implemented_ready_for_qa',
            source_packet_schema_type='worker_result_packet',
            source_packet_message_id='msg-123',
        )

        result = self.service.derive_worker_review_routing(request)

        self.assertTrue(result.ok)
        self.assertTrue(result.summary.decision_supported)
        self.assertEqual(result.summary.recommended_next_decision, 'assign_qa')
        self.assertEqual(result.summary.recommended_target_role, 'QA')
        self.assertTrue(result.summary.qa_assignment_allowed)
        self.assertEqual(result.source_packet_message_id, 'msg-123')
        self.assertEqual(result.recommended_actions, ('assign_qa',))
        self.assertTrue(result.unattended_safe)

    def test_blocked_recommends_return_to_delivery_architect(self) -> None:
        request = TechLeadWorkerReviewRoutingRequest(
            project_slug='paa-platform',
            issue_number=123,
            workflow_stage='techlead_dev_review_pending',
            worker_role='Python Dev',
            worker_result_type='blocked',
        )

        result = self.service.derive_worker_review_routing(request)

        self.assertTrue(result.ok)
        self.assertEqual(result.summary.recommended_next_decision, 'return_to_delivery_architect')
        self.assertEqual(result.summary.recommended_target_role, 'Delivery Architect')
        self.assertFalse(result.summary.qa_assignment_allowed)

    def test_scope_change_recommends_architect_escalation(self) -> None:
        request = TechLeadWorkerReviewRoutingRequest(
            project_slug='paa-platform',
            issue_number=123,
            workflow_stage='techlead_dev_review_pending',
            worker_role='Python Dev',
            worker_result_type='cannot_complete_without_scope_change',
        )

        result = self.service.derive_worker_review_routing(request)

        self.assertTrue(result.ok)
        self.assertEqual(result.summary.recommended_next_decision, 'escalate_to_authority_architect')
        self.assertEqual(result.summary.recommended_target_role, 'Architect')

    def test_needs_clarification_recommends_return_to_delivery_architect(self) -> None:
        request = TechLeadWorkerReviewRoutingRequest(
            project_slug='paa-platform',
            issue_number=123,
            workflow_stage='techlead_worker_review_pending',
            worker_role='Python Dev',
            worker_result_type='needs_clarification',
        )

        result = self.service.derive_worker_review_routing(request)

        self.assertTrue(result.ok)
        self.assertEqual(result.summary.recommended_next_decision, 'return_to_delivery_architect')
        self.assertEqual(result.summary.recommended_target_role, 'Delivery Architect')
        self.assertFalse(result.summary.qa_assignment_allowed)

    def test_superseded_by_branch_reset_recommends_reset_branch(self) -> None:
        request = TechLeadWorkerReviewRoutingRequest(
            project_slug='paa-platform',
            issue_number=123,
            workflow_stage='techlead_worker_review_pending',
            worker_role='Python Dev',
            worker_result_type='superseded_by_branch_reset',
        )

        result = self.service.derive_worker_review_routing(request)

        self.assertTrue(result.ok)
        self.assertEqual(result.summary.recommended_next_decision, 'reset_branch')
        self.assertEqual(result.summary.recommended_target_role, 'Python Dev')
        self.assertFalse(result.summary.qa_assignment_allowed)

    def test_missing_issue_number_fails_closed(self) -> None:
        request = TechLeadWorkerReviewRoutingRequest(
            project_slug='paa-platform',
            issue_number=0,
            workflow_stage='techlead_worker_review_pending',
            worker_role='Python Dev',
            worker_result_type='implemented_ready_for_qa',
        )

        result = self.service.derive_worker_review_routing(request)

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'missing_issue_number')
        self.assertEqual(result.summary.blocking_reasons, ('missing_issue_number',))
        self.assertFalse(result.unattended_safe)

    def test_missing_workflow_stage_fails_closed(self) -> None:
        request = TechLeadWorkerReviewRoutingRequest(
            project_slug='paa-platform',
            issue_number=123,
            workflow_stage='',
            worker_role='Python Dev',
            worker_result_type='implemented_ready_for_qa',
        )

        result = self.service.derive_worker_review_routing(request)

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'missing_workflow_stage')
        self.assertEqual(result.summary.blocking_reasons, ('missing_workflow_stage',))

    def test_missing_worker_role_fails_closed(self) -> None:
        request = TechLeadWorkerReviewRoutingRequest(
            project_slug='paa-platform',
            issue_number=123,
            workflow_stage='techlead_worker_review_pending',
            worker_role='',
            worker_result_type='implemented_ready_for_qa',
        )

        result = self.service.derive_worker_review_routing(request)

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'missing_worker_role')
        self.assertEqual(result.summary.blocking_reasons, ('missing_worker_role',))

    def test_missing_worker_result_type_fails_closed(self) -> None:
        request = TechLeadWorkerReviewRoutingRequest(
            project_slug='paa-platform',
            issue_number=123,
            workflow_stage='techlead_worker_review_pending',
            worker_role='Python Dev',
            worker_result_type='',
        )

        result = self.service.derive_worker_review_routing(request)

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'missing_worker_result_type')
        self.assertEqual(result.summary.blocking_reasons, ('missing_worker_result_type',))

    def test_unsupported_result_type_fails_closed(self) -> None:
        request = TechLeadWorkerReviewRoutingRequest(
            project_slug='paa-platform',
            issue_number=123,
            workflow_stage='techlead_worker_review_pending',
            worker_role='Python Dev',
            worker_result_type='unknown_result_type',
        )

        result = self.service.derive_worker_review_routing(request)

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'unsupported_worker_review_routing')
        self.assertEqual(result.summary.blocking_reasons, ('unsupported_worker_review_routing',))
        self.assertIsNone(result.recommended_actions)
        self.assertFalse(result.unattended_safe)

    def test_supports_worker_review_routing_requires_supported_stage_and_result(self) -> None:
        self.assertTrue(
            self.service.supports_worker_review_routing(
                'techlead_worker_review_pending',
                'implemented_ready_for_qa',
            )
        )
        self.assertFalse(
            self.service.supports_worker_review_routing(
                'techlead_delivery_review_pending',
                'implemented_ready_for_qa',
            )
        )
        self.assertFalse(
            self.service.supports_worker_review_routing(
                'techlead_worker_review_pending',
                'unknown_result_type',
            )
        )


if __name__ == '__main__':
    unittest.main()

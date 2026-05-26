from __future__ import annotations

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'packages' / 'paa-core' / 'src'))

from paa_core.services.techlead_assignment_decision import (
    DefaultTechLeadAssignmentDecisionService,
    TechLeadAssignmentDecisionRequest,
)


class TechLeadAssignmentDecisionServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = DefaultTechLeadAssignmentDecisionService()

    def test_explicit_team_worker_assignment_is_supported(self) -> None:
        request = TechLeadAssignmentDecisionRequest(
            project_slug='paa-platform',
            issue_number=123,
            workflow_stage='worker_execution_in_progress',
            explicit_target_role='python-dev',
            recommended_actions=('route-to-python',),
        )

        result = self.service.derive_assignment_decision(request)

        self.assertTrue(result.ok)
        self.assertTrue(result.summary.decision_supported)
        self.assertEqual(result.summary.target_role, 'Python Dev')
        self.assertEqual(result.summary.target_role_cli, 'python')
        self.assertEqual(result.summary.assignment_type, 'implement_authorized_slice')
        self.assertEqual(
            result.summary.allowed_result_types,
            ('implemented_ready_for_qa', 'blocked', 'needs_clarification'),
        )
        self.assertEqual(result.recommended_actions, ('route-to-python',))
        self.assertTrue(result.unattended_safe)

    def test_worker_review_ready_stage_routes_to_qa(self) -> None:
        request = TechLeadAssignmentDecisionRequest(
            project_slug='paa-platform',
            issue_number=123,
            workflow_stage='techlead_worker_review_pending',
            source_packet_schema_type='worker_result_packet',
            source_packet_message_id='msg-123',
            source_packet_queue_name='fractal-core-python',
            source_packet_path='/tmp/worker-result.json',
        )

        result = self.service.derive_assignment_decision(request)

        self.assertTrue(result.ok)
        self.assertEqual(result.summary.target_role, 'QA')
        self.assertEqual(result.summary.target_role_cli, 'qa')
        self.assertEqual(result.summary.assignment_type, 'verify_authorized_slice')
        self.assertEqual(result.source_packet_message_id, 'msg-123')
        self.assertEqual(result.source_packet_queue_name, 'fractal-core-python')
        self.assertEqual(result.source_packet_path, '/tmp/worker-result.json')

    def test_unsupported_stage_fails_closed(self) -> None:
        request = TechLeadAssignmentDecisionRequest(
            project_slug='paa-platform',
            issue_number=123,
            workflow_stage='techlead_delivery_review_pending',
        )

        result = self.service.derive_assignment_decision(request)

        self.assertFalse(result.ok)
        self.assertFalse(result.summary.decision_supported)
        self.assertEqual(result.reason, 'no_supported_emission_available')
        self.assertEqual(result.summary.blocking_reasons, ('unsupported_workflow_stage',))
        self.assertFalse(result.unattended_safe)

    def test_supports_assignment_for_stage_requires_qa_ready_packet_family(self) -> None:
        self.assertTrue(
            self.service.supports_assignment_for_stage(
                'techlead_dev_review_pending',
                'slice_result_packet',
            )
        )
        self.assertFalse(
            self.service.supports_assignment_for_stage(
                'techlead_dev_review_pending',
                'qa_verification_packet',
            )
        )

    def test_missing_issue_number_fails_closed(self) -> None:
        request = TechLeadAssignmentDecisionRequest(
            project_slug='paa-platform',
            issue_number=0,
            workflow_stage='techlead_worker_review_pending',
        )

        result = self.service.derive_assignment_decision(request)

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'missing_issue_number')
        self.assertEqual(result.summary.blocking_reasons, ('missing_issue_number',))

    def test_missing_workflow_stage_fails_closed(self) -> None:
        request = TechLeadAssignmentDecisionRequest(
            project_slug='paa-platform',
            issue_number=123,
            workflow_stage='',
        )

        result = self.service.derive_assignment_decision(request)

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'missing_workflow_stage')
        self.assertEqual(result.summary.blocking_reasons, ('missing_workflow_stage',))

    def test_unsupported_explicit_target_role_fails_closed(self) -> None:
        request = TechLeadAssignmentDecisionRequest(
            project_slug='paa-platform',
            issue_number=123,
            workflow_stage='worker_execution_in_progress',
            explicit_target_role='rust-dev',
        )

        result = self.service.derive_assignment_decision(request)

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'explicit_target_role_not_supported')
        self.assertEqual(result.summary.blocking_reasons, ('unsupported_explicit_target_role',))

    def test_qa_ready_stage_requires_supported_source_packet_family(self) -> None:
        request = TechLeadAssignmentDecisionRequest(
            project_slug='paa-platform',
            issue_number=123,
            workflow_stage='techlead_dev_review_pending',
            source_packet_schema_type='qa_verification_packet',
        )

        result = self.service.derive_assignment_decision(request)

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'no_supported_emission_available')


if __name__ == '__main__':
    unittest.main()

from __future__ import annotations

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'packages' / 'paa-core' / 'src'))

from paa_core.services.techlead_acceptance_decision.default import (
    DefaultTechLeadAcceptanceDecisionService,
)
from paa_core.services.techlead_acceptance_decision.models import (
    TechLeadAcceptanceDecisionRequest,
)


class TechLeadAcceptanceDecisionServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = DefaultTechLeadAcceptanceDecisionService()

    def test_pass_live_delivery_recommends_prepare_merge(self) -> None:
        request = TechLeadAcceptanceDecisionRequest(
            project_slug='paa-platform',
            issue_number=42,
            pr_number=77,
            workflow_stage='techlead_qa_review_pending',
            qa_result_type='pass',
            source_packet_schema_type='qa_verification_packet',
            source_packet_message_id='msg-123',
            merge_state={'merge_ready': True},
            metadata={'execution_mode': 'live_delivery'},
        )

        result = self.service.derive_acceptance_decision(request)

        self.assertTrue(result.ok)
        self.assertTrue(result.summary.decision_supported)
        self.assertEqual(result.summary.recommended_next_decision, 'prepare_merge')
        self.assertTrue(result.summary.acceptance_allowed)
        self.assertFalse(result.summary.closeout_allowed)
        self.assertEqual(result.recommended_actions, ('prepare_merge',))
        self.assertEqual(result.source_packet_schema_type, 'qa_verification_packet')
        self.assertEqual(result.source_packet_message_id, 'msg-123')
        self.assertTrue(result.unattended_safe)
        self.assertEqual(result.metadata['execution_mode'], 'live_delivery')
        self.assertTrue(result.metadata['merge_ready'])

    def test_pass_proof_only_recommends_close_slice(self) -> None:
        request = TechLeadAcceptanceDecisionRequest(
            project_slug='paa-platform',
            issue_number=42,
            workflow_stage='techlead_qa_review_pending',
            qa_result_type='pass',
            source_packet_schema_type='qa_verification_packet',
            metadata={'execution_mode': 'proof_only'},
        )

        result = self.service.derive_acceptance_decision(request)

        self.assertTrue(result.ok)
        self.assertEqual(result.summary.recommended_next_decision, 'close_slice')
        self.assertTrue(result.summary.acceptance_allowed)
        self.assertTrue(result.summary.closeout_allowed)
        self.assertEqual(result.recommended_actions, ('close_slice',))
        self.assertEqual(result.metadata['execution_mode'], 'proof_only')
        self.assertIsNone(result.metadata['merge_ready'])

    def test_live_delivery_requires_merge_ready(self) -> None:
        request = TechLeadAcceptanceDecisionRequest(
            project_slug='paa-platform',
            issue_number=42,
            workflow_stage='techlead_qa_review_pending',
            qa_result_type='pass',
            source_packet_schema_type='qa_verification_packet',
            merge_state={'merge_ready': False},
            metadata={'execution_mode': 'live_delivery'},
        )

        result = self.service.derive_acceptance_decision(request)

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'merge_not_ready_for_live_acceptance')
        self.assertEqual(result.summary.blocking_reasons, ('merge_not_ready',))
        self.assertFalse(result.unattended_safe)

    def test_unsupported_qa_result_fails_closed(self) -> None:
        request = TechLeadAcceptanceDecisionRequest(
            project_slug='paa-platform',
            issue_number=42,
            workflow_stage='techlead_qa_review_pending',
            qa_result_type='needs_human_review',
            source_packet_schema_type='qa_verification_packet',
        )

        result = self.service.derive_acceptance_decision(request)

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'unsupported_acceptance_decision')
        self.assertEqual(result.summary.decision_summary, 'No supported acceptance decision is available for this slice.')

    def test_missing_issue_number_fails_closed(self) -> None:
        request = TechLeadAcceptanceDecisionRequest(
            project_slug='paa-platform',
            issue_number=0,
            workflow_stage='techlead_qa_review_pending',
            qa_result_type='pass',
        )

        result = self.service.derive_acceptance_decision(request)

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'missing_issue_number')

    def test_missing_workflow_stage_fails_closed(self) -> None:
        request = TechLeadAcceptanceDecisionRequest(
            project_slug='paa-platform',
            issue_number=42,
            workflow_stage='',
            qa_result_type='pass',
        )

        result = self.service.derive_acceptance_decision(request)

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'missing_workflow_stage')

    def test_missing_qa_result_type_fails_closed(self) -> None:
        request = TechLeadAcceptanceDecisionRequest(
            project_slug='paa-platform',
            issue_number=42,
            workflow_stage='techlead_qa_review_pending',
            qa_result_type='',
        )

        result = self.service.derive_acceptance_decision(request)

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'missing_qa_result_type')

    def test_unsupported_source_schema_fails_closed(self) -> None:
        request = TechLeadAcceptanceDecisionRequest(
            project_slug='paa-platform',
            issue_number=42,
            workflow_stage='techlead_qa_review_pending',
            qa_result_type='pass',
            source_packet_schema_type='worker_result_packet',
        )

        result = self.service.derive_acceptance_decision(request)

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'unsupported_source_packet_schema')

    def test_supports_acceptance_decision_is_limited_to_first_slice(self) -> None:
        self.assertTrue(self.service.supports_acceptance_decision('techlead_qa_review_pending', 'pass'))
        self.assertTrue(self.service.supports_acceptance_decision('techlead_qa_review_pending'))
        self.assertFalse(self.service.supports_acceptance_decision('techlead_worker_review_pending', 'pass'))
        self.assertFalse(self.service.supports_acceptance_decision('techlead_qa_review_pending', 'needs_human_review'))


if __name__ == '__main__':
    unittest.main()

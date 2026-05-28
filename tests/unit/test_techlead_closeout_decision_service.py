from __future__ import annotations

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'packages' / 'paa-core' / 'src'))

from paa_core.services.techlead_closeout_decision import (
    DefaultTechLeadCloseoutDecisionService,
)
from paa_core.services.techlead_closeout_decision.models import (
    TechLeadCloseoutDecisionRequest,
)


class TechLeadCloseoutDecisionServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = DefaultTechLeadCloseoutDecisionService()

    def test_proof_only_closeout_returns_supported_decision(self) -> None:
        request = TechLeadCloseoutDecisionRequest(
            project_slug='paa-platform',
            issue_number=42,
            issue_url='https://example.test/issues/42',
            pr_number=77,
            pr_url='https://example.test/pulls/77',
            workflow_stage='proof_only_closed',
            decision_type='proof_only_closed',
            proof_only_mode=True,
            source_packet_schema_type='qa_verification_packet',
            source_packet_message_id='msg-123',
            source_packet_path='handoff/packet.json',
            branch_name='issue-42-python',
            canonical_branch='issue-42',
        )

        result = self.service.derive_closeout_decision(request)

        self.assertTrue(result.ok)
        self.assertTrue(result.summary.decision_supported)
        self.assertEqual(result.summary.recommended_next_decision, 'proof_only_close_slice')
        self.assertEqual(result.summary.recommended_target_role, 'TechLead')
        self.assertTrue(result.summary.closeout_allowed)
        self.assertEqual(result.recommended_actions, ('proof_only_close_slice',))
        self.assertTrue(result.unattended_safe)


    def test_supported_result_uses_default_proof_only_summary(self) -> None:
        request = TechLeadCloseoutDecisionRequest(
            project_slug='paa-platform',
            issue_number=42,
            workflow_stage='proof_only_closed',
            decision_type='proof_only_closed',
            proof_only_mode=True,
            source_packet_schema_type='qa_verification_packet',
            source_packet_path='handoff/packet.json',
        )

        result = self.service.derive_closeout_decision(request)

        self.assertTrue(result.ok)
        self.assertIn('issue #42', result.summary.closeout_decision_summary)
        self.assertEqual(result.summary.notes, ('proof-only-closeout', 'qa-pass'))

    def test_missing_issue_number_fails_closed(self) -> None:
        request = TechLeadCloseoutDecisionRequest(
            project_slug='paa-platform',
            issue_number=0,
            workflow_stage='proof_only_closed',
            decision_type='proof_only_closed',
            proof_only_mode=True,
            source_packet_schema_type='qa_verification_packet',
            source_packet_path='handoff/packet.json',
        )

        result = self.service.derive_closeout_decision(request)

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'missing_issue_number')

    def test_missing_workflow_stage_fails_closed(self) -> None:
        request = TechLeadCloseoutDecisionRequest(
            project_slug='paa-platform',
            issue_number=42,
            workflow_stage='',
            decision_type='proof_only_closed',
            proof_only_mode=True,
            source_packet_schema_type='qa_verification_packet',
            source_packet_path='handoff/packet.json',
        )

        result = self.service.derive_closeout_decision(request)

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'missing_workflow_stage')

    def test_missing_decision_type_fails_closed(self) -> None:
        request = TechLeadCloseoutDecisionRequest(
            project_slug='paa-platform',
            issue_number=42,
            workflow_stage='proof_only_closed',
            decision_type='',
            proof_only_mode=True,
            source_packet_schema_type='qa_verification_packet',
            source_packet_path='handoff/packet.json',
        )

        result = self.service.derive_closeout_decision(request)

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'missing_decision_type')

    def test_unsupported_source_schema_fails_closed(self) -> None:
        request = TechLeadCloseoutDecisionRequest(
            project_slug='paa-platform',
            issue_number=42,
            workflow_stage='proof_only_closed',
            decision_type='proof_only_closed',
            proof_only_mode=True,
            source_packet_schema_type='delivery_review_packet',
            source_packet_path='handoff/packet.json',
        )

        result = self.service.derive_closeout_decision(request)

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'unsupported_source_packet_schema')

    def test_proof_only_mode_required_fails_closed(self) -> None:
        request = TechLeadCloseoutDecisionRequest(
            project_slug='paa-platform',
            issue_number=42,
            workflow_stage='proof_only_closed',
            decision_type='proof_only_closed',
            proof_only_mode=False,
            source_packet_schema_type='qa_verification_packet',
            source_packet_path='handoff/packet.json',
        )

        result = self.service.derive_closeout_decision(request)

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'proof_only_mode_required')

    def test_missing_source_packet_fails_closed(self) -> None:
        request = TechLeadCloseoutDecisionRequest(
            project_slug='paa-platform',
            issue_number=42,
            workflow_stage='proof_only_closed',
            decision_type='proof_only_closed',
            proof_only_mode=True,
            source_packet_schema_type=None,
            source_packet_path=None,
        )

        result = self.service.derive_closeout_decision(request)

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'missing_source_packet')

    def test_unsupported_combination_fails_closed(self) -> None:
        request = TechLeadCloseoutDecisionRequest(
            project_slug='paa-platform',
            issue_number=42,
            workflow_stage='closed',
            decision_type='closed',
            proof_only_mode=True,
            source_packet_schema_type='qa_verification_packet',
            source_packet_path='handoff/packet.json',
        )

        result = self.service.derive_closeout_decision(request)

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'unsupported_closeout_decision')

    def test_supported_result_carries_source_packet_and_metadata(self) -> None:
        request = TechLeadCloseoutDecisionRequest(
            project_slug='paa-platform',
            issue_number=42,
            issue_url='https://example.test/issues/42',
            pr_number=77,
            pr_url='https://example.test/pulls/77',
            workflow_stage='proof_only_closed',
            decision_type='proof_only_closed',
            proof_only_mode=True,
            source_packet_schema_type='qa_verification_packet',
            source_packet_message_id='msg-123',
            source_packet_path='handoff/packet.json',
            branch_name='issue-42-python',
            canonical_branch='issue-42',
            metadata={'source_queue_name': 'fractal-core-qa'},
        )

        result = self.service.derive_closeout_decision(request)

        self.assertTrue(result.ok)
        self.assertEqual(result.source_packet_schema_type, 'qa_verification_packet')
        self.assertEqual(result.source_packet_message_id, 'msg-123')
        self.assertEqual(result.source_packet_path, 'handoff/packet.json')
        self.assertEqual(result.branch_name, 'issue-42-python')
        self.assertEqual(result.canonical_branch, 'issue-42')
        self.assertEqual(result.metadata['source_queue_name'], 'fractal-core-qa')
        self.assertEqual(result.metadata['service_component'], 'TechLeadCloseoutDecisionService')
        self.assertTrue(result.metadata['source_packet_present'])
        self.assertTrue(result.metadata['proof_only_mode'])
        self.assertTrue(result.metadata['canonical_branch_supplied'])

    def test_rejected_result_carries_blocking_reasons_and_rejection_timestamp(self) -> None:
        request = TechLeadCloseoutDecisionRequest(
            project_slug='paa-platform',
            issue_number=42,
            workflow_stage='closed',
            decision_type='closed',
            proof_only_mode=True,
            source_packet_schema_type='qa_verification_packet',
            source_packet_path='handoff/packet.json',
        )

        result = self.service.derive_closeout_decision(request)

        self.assertFalse(result.ok)
        self.assertEqual(result.summary.blocking_reasons, ('unsupported_closeout_decision',))
        self.assertEqual(result.summary.notes, ('fail-closed',))
        self.assertIn('rejected_at', result.metadata)

    def test_supports_closeout_decision_is_narrow(self) -> None:
        self.assertTrue(
            self.service.supports_closeout_decision(
                'proof_only_closed',
                'proof_only_closed',
                True,
            )
        )
        self.assertFalse(
            self.service.supports_closeout_decision(
                'proof_only_closed',
                'proof_only_closed',
                False,
            )
        )
        self.assertFalse(
            self.service.supports_closeout_decision(
                'closed',
                'closed',
                True,
            )
        )


if __name__ == '__main__':
    unittest.main()

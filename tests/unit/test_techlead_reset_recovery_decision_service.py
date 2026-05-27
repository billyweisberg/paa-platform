from __future__ import annotations

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'packages' / 'paa-core' / 'src'))

from paa_core.services.techlead_reset_recovery_decision import (
    DefaultTechLeadResetRecoveryDecisionService,
)
from paa_core.services.techlead_reset_recovery_decision.models import (
    TechLeadResetRecoveryDecisionRequest,
)


class TechLeadResetRecoveryDecisionServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = DefaultTechLeadResetRecoveryDecisionService()

    def test_reset_required_stage_returns_supported_decision(self) -> None:
        request = TechLeadResetRecoveryDecisionRequest(
            project_slug='paa-platform',
            issue_number=42,
            issue_url='https://example.test/issues/42',
            pr_number=77,
            pr_url='https://example.test/pulls/77',
            workflow_stage='dev_reset_required',
            lineage_state='reset_required',
            reset_escalation_type='reset_branch_required',
            reset_escalation_summary='Repeated scope failure requires a branch reset.',
            source_packet_schema_type='qa_verification_packet',
            source_packet_message_id='msg-123',
            source_packet_path='handoff/packet.json',
            branch_name='issue-42-python',
        )

        result = self.service.derive_reset_recovery_decision(request)

        self.assertTrue(result.ok)
        self.assertTrue(result.summary.decision_supported)
        self.assertEqual(result.summary.recommended_next_decision, 'reset_branch')
        self.assertEqual(result.summary.recommended_target_role, 'Python Dev')
        self.assertTrue(result.summary.reset_allowed)
        self.assertEqual(result.recommended_actions, ('reset_branch',))
        self.assertFalse(result.unattended_safe)

    def test_lineage_state_only_returns_supported_decision(self) -> None:
        request = TechLeadResetRecoveryDecisionRequest(
            project_slug='paa-platform',
            issue_number=42,
            workflow_stage='worker_execution_in_progress',
            lineage_state='reset_required',
        )

        result = self.service.derive_reset_recovery_decision(request)

        self.assertTrue(result.ok)
        self.assertEqual(result.summary.recommended_next_decision, 'reset_branch')

    def test_reset_escalation_only_returns_supported_decision(self) -> None:
        request = TechLeadResetRecoveryDecisionRequest(
            project_slug='paa-platform',
            issue_number=42,
            workflow_stage='worker_execution_in_progress',
            lineage_state='',
            reset_escalation_type='reset_branch_recommended',
            reset_escalation_summary='Architect should record a reset-branch recovery decision.',
        )

        result = self.service.derive_reset_recovery_decision(request)

        self.assertTrue(result.ok)
        self.assertEqual(result.summary.recommended_next_decision, 'reset_branch')
        self.assertEqual(
            result.summary.reset_recovery_summary,
            'Architect should record a reset-branch recovery decision.',
        )

    def test_missing_issue_number_fails_closed(self) -> None:
        request = TechLeadResetRecoveryDecisionRequest(
            project_slug='paa-platform',
            issue_number=0,
            workflow_stage='dev_reset_required',
            lineage_state='reset_required',
        )

        result = self.service.derive_reset_recovery_decision(request)

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'missing_issue_number')

    def test_missing_workflow_stage_fails_closed_without_escalation_signal(self) -> None:
        request = TechLeadResetRecoveryDecisionRequest(
            project_slug='paa-platform',
            issue_number=42,
            workflow_stage='',
            lineage_state='',
            reset_escalation_type=None,
        )

        result = self.service.derive_reset_recovery_decision(request)

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'missing_workflow_stage')

    def test_missing_reset_signal_fails_closed(self) -> None:
        request = TechLeadResetRecoveryDecisionRequest(
            project_slug='paa-platform',
            issue_number=42,
            workflow_stage='worker_execution_in_progress',
            lineage_state='',
            reset_escalation_type=None,
        )

        result = self.service.derive_reset_recovery_decision(request)

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'missing_reset_recovery_signal')

    def test_unsupported_combination_fails_closed(self) -> None:
        request = TechLeadResetRecoveryDecisionRequest(
            project_slug='paa-platform',
            issue_number=42,
            workflow_stage='qa_verification_complete',
            lineage_state='active',
            reset_escalation_type='manual_note',
        )

        result = self.service.derive_reset_recovery_decision(request)

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'unsupported_reset_recovery_decision')

    def test_supported_result_carries_source_packet_and_metadata(self) -> None:
        request = TechLeadResetRecoveryDecisionRequest(
            project_slug='paa-platform',
            issue_number=42,
            issue_url='https://example.test/issues/42',
            pr_number=77,
            pr_url='https://example.test/pulls/77',
            workflow_stage='dev_reset_required',
            lineage_state='reset_required',
            reset_escalation_type='reset_branch_required',
            reset_escalation_summary='Repeated scope failure requires a branch reset.',
            reset_escalation_details={'architect_comment_at': '2026-05-27T00:00:00Z'},
            source_packet_schema_type='qa_verification_packet',
            source_packet_message_id='msg-123',
            source_packet_path='handoff/packet.json',
            branch_name='issue-42-python',
            metadata={'source_queue_name': 'fractal-core-qa'},
        )

        result = self.service.derive_reset_recovery_decision(request)

        self.assertTrue(result.ok)
        self.assertEqual(result.source_packet_schema_type, 'qa_verification_packet')
        self.assertEqual(result.source_packet_message_id, 'msg-123')
        self.assertEqual(result.source_packet_path, 'handoff/packet.json')
        self.assertEqual(result.branch_name, 'issue-42-python')
        self.assertEqual(result.metadata['source_queue_name'], 'fractal-core-qa')
        self.assertEqual(result.metadata['service_component'], 'TechLeadResetRecoveryDecisionService')
        self.assertTrue(result.metadata['source_packet_present'])
        self.assertTrue(result.metadata['reset_escalation_details_supplied'])

    def test_rejected_result_carries_blocking_reasons_and_rejection_timestamp(self) -> None:
        request = TechLeadResetRecoveryDecisionRequest(
            project_slug='paa-platform',
            issue_number=42,
            workflow_stage='qa_verification_complete',
            lineage_state='active',
            reset_escalation_type='manual_note',
        )

        result = self.service.derive_reset_recovery_decision(request)

        self.assertFalse(result.ok)
        self.assertEqual(
            result.summary.blocking_reasons,
            ('unsupported_reset_recovery_decision',),
        )
        self.assertEqual(result.summary.notes, ('fail-closed',))
        self.assertIn('rejected_at', result.metadata)

    def test_supports_reset_recovery_decision_is_narrow(self) -> None:
        self.assertTrue(
            self.service.supports_reset_recovery_decision(
                'dev_reset_required',
                None,
                None,
            )
        )
        self.assertTrue(
            self.service.supports_reset_recovery_decision(
                'worker_execution_in_progress',
                'reset_required',
                None,
            )
        )
        self.assertTrue(
            self.service.supports_reset_recovery_decision(
                'worker_execution_in_progress',
                None,
                'reset_branch_recommended',
            )
        )
        self.assertFalse(
            self.service.supports_reset_recovery_decision(
                'qa_verification_complete',
                'active',
                'manual_note',
            )
        )


if __name__ == '__main__':
    unittest.main()

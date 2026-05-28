from __future__ import annotations

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'packages' / 'paa-core' / 'src'))

from paa_core.services.techlead_lineage_decision import (
    DefaultTechLeadLineageDecisionService,
)
from paa_core.services.techlead_lineage_decision.models import (
    TechLeadLineageDecisionRequest,
)


class TechLeadLineageDecisionServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = DefaultTechLeadLineageDecisionService()

    def test_superseded_lineage_state_returns_supported_decision(self) -> None:
        request = TechLeadLineageDecisionRequest(
            project_slug='paa-platform',
            issue_number=42,
            issue_url='https://example.test/issues/42',
            pr_number=77,
            pr_url='https://example.test/pulls/77',
            workflow_stage='techlead_qa_review_pending',
            lineage_state='superseded',
            superseded_escalation_type='qa_escalation_superseded',
            superseded_escalation_summary='A newer Python rework superseded the earlier QA escalation.',
            source_packet_schema_type='qa_verification_packet',
            source_packet_message_id='msg-123',
            source_packet_path='handoff/packet.json',
            branch_name='issue-42-python',
            superseded_branch='issue-42-python-old',
        )

        result = self.service.derive_lineage_decision(request)

        self.assertTrue(result.ok)
        self.assertTrue(result.summary.decision_supported)
        self.assertEqual(result.summary.recommended_next_decision, 'supersede_branch_lineage')
        self.assertEqual(result.summary.recommended_target_role, 'TechLead')
        self.assertTrue(result.summary.supersede_allowed)
        self.assertEqual(result.recommended_actions, ('supersede_branch_lineage',))
        self.assertFalse(result.unattended_safe)

    def test_superseded_escalation_only_returns_supported_decision(self) -> None:
        request = TechLeadLineageDecisionRequest(
            project_slug='paa-platform',
            issue_number=42,
            workflow_stage='worker_execution_in_progress',
            lineage_state='',
            superseded_escalation_type='qa_escalation_superseded',
            superseded_escalation_summary='Earlier QA packet is superseded by newer work.',
        )

        result = self.service.derive_lineage_decision(request)

        self.assertTrue(result.ok)
        self.assertEqual(result.summary.recommended_next_decision, 'supersede_branch_lineage')
        self.assertEqual(result.summary.lineage_decision_summary, 'Earlier QA packet is superseded by newer work.')

    def test_supported_stage_with_superseded_escalation_returns_supported_decision(self) -> None:
        request = TechLeadLineageDecisionRequest(
            project_slug='paa-platform',
            issue_number=42,
            workflow_stage='qa_pending',
            lineage_state='',
            superseded_escalation_type='qa_escalation_superseded',
        )

        result = self.service.derive_lineage_decision(request)

        self.assertTrue(result.ok)
        self.assertEqual(result.summary.recommended_target_role, 'TechLead')


    def test_supported_result_uses_default_summary_when_escalation_summary_missing(self) -> None:
        request = TechLeadLineageDecisionRequest(
            project_slug='paa-platform',
            issue_number=42,
            workflow_stage='techlead_qa_review_pending',
            lineage_state='superseded',
            superseded_escalation_type='qa_escalation_superseded',
        )

        result = self.service.derive_lineage_decision(request)

        self.assertTrue(result.ok)
        self.assertIn('issue #42', result.summary.lineage_decision_summary)
        self.assertEqual(result.summary.notes, ('superseded-lineage',))

    def test_missing_issue_number_fails_closed(self) -> None:
        request = TechLeadLineageDecisionRequest(
            project_slug='paa-platform',
            issue_number=0,
            workflow_stage='techlead_qa_review_pending',
            lineage_state='superseded',
        )

        result = self.service.derive_lineage_decision(request)

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'missing_issue_number')

    def test_missing_workflow_stage_fails_closed(self) -> None:
        request = TechLeadLineageDecisionRequest(
            project_slug='paa-platform',
            issue_number=42,
            workflow_stage='',
            lineage_state='superseded',
        )

        result = self.service.derive_lineage_decision(request)

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'missing_workflow_stage')

    def test_missing_lineage_signal_fails_closed(self) -> None:
        request = TechLeadLineageDecisionRequest(
            project_slug='paa-platform',
            issue_number=42,
            workflow_stage='techlead_qa_review_pending',
            lineage_state='',
            superseded_escalation_type=None,
        )

        result = self.service.derive_lineage_decision(request)

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'missing_lineage_signal')

    def test_unsupported_combination_fails_closed(self) -> None:
        request = TechLeadLineageDecisionRequest(
            project_slug='paa-platform',
            issue_number=42,
            workflow_stage='qa_verification_complete',
            lineage_state='active',
            superseded_escalation_type='manual_note',
        )

        result = self.service.derive_lineage_decision(request)

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'unsupported_lineage_decision')

    def test_supported_result_carries_source_packet_and_metadata(self) -> None:
        request = TechLeadLineageDecisionRequest(
            project_slug='paa-platform',
            issue_number=42,
            issue_url='https://example.test/issues/42',
            pr_number=77,
            pr_url='https://example.test/pulls/77',
            workflow_stage='techlead_qa_review_pending',
            lineage_state='superseded',
            superseded_escalation_type='qa_escalation_superseded',
            superseded_escalation_summary='A newer Python rework superseded the earlier QA escalation.',
            superseded_escalation_details={'superseded_qa_packet_id': 'msg-old'},
            source_packet_schema_type='qa_verification_packet',
            source_packet_message_id='msg-123',
            source_packet_path='handoff/packet.json',
            branch_name='issue-42-python',
            superseded_branch='issue-42-python-old',
            metadata={'source_queue_name': 'fractal-core-qa'},
        )

        result = self.service.derive_lineage_decision(request)

        self.assertTrue(result.ok)
        self.assertEqual(result.source_packet_schema_type, 'qa_verification_packet')
        self.assertEqual(result.source_packet_message_id, 'msg-123')
        self.assertEqual(result.source_packet_path, 'handoff/packet.json')
        self.assertEqual(result.branch_name, 'issue-42-python')
        self.assertEqual(result.superseded_branch, 'issue-42-python-old')
        self.assertEqual(result.metadata['source_queue_name'], 'fractal-core-qa')
        self.assertEqual(result.metadata['service_component'], 'TechLeadLineageDecisionService')
        self.assertTrue(result.metadata['source_packet_present'])
        self.assertTrue(result.metadata['superseded_branch_present'])
        self.assertTrue(result.metadata['superseded_escalation_details_supplied'])

    def test_rejected_result_carries_blocking_reasons_and_rejection_timestamp(self) -> None:
        request = TechLeadLineageDecisionRequest(
            project_slug='paa-platform',
            issue_number=42,
            workflow_stage='qa_verification_complete',
            lineage_state='active',
            superseded_escalation_type='manual_note',
        )

        result = self.service.derive_lineage_decision(request)

        self.assertFalse(result.ok)
        self.assertEqual(
            result.summary.blocking_reasons,
            ('unsupported_lineage_decision',),
        )
        self.assertEqual(result.summary.notes, ('fail-closed',))
        self.assertIn('rejected_at', result.metadata)

    def test_supports_lineage_decision_is_narrow(self) -> None:
        self.assertTrue(
            self.service.supports_lineage_decision(
                'techlead_qa_review_pending',
                'superseded',
                None,
            )
        )
        self.assertTrue(
            self.service.supports_lineage_decision(
                'worker_execution_in_progress',
                None,
                'qa_escalation_superseded',
            )
        )
        self.assertTrue(
            self.service.supports_lineage_decision(
                'qa_pending',
                None,
                'qa_escalation_superseded',
            )
        )
        self.assertFalse(
            self.service.supports_lineage_decision(
                'qa_verification_complete',
                'active',
                'manual_note',
            )
        )


if __name__ == '__main__':
    unittest.main()

from __future__ import annotations

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'packages' / 'paa-core' / 'src'))

from paa_core.services.techlead_lineage_decision.models import (
    TechLeadLineageDecisionRequest,
    TechLeadLineageDecisionResult,
    TechLeadLineageDecisionSummary,
)


class TechLeadLineageDecisionModelsTests(unittest.TestCase):
    def test_request_model_preserves_superseded_lineage_context_fields(self) -> None:
        request = TechLeadLineageDecisionRequest(
            project_slug='paa-platform',
            issue_number=42,
            issue_url='https://example.test/issues/42',
            pr_number=77,
            pr_url='https://example.test/pulls/77',
            workflow_stage='techlead_qa_review_pending',
            lineage_state='superseded',
            superseded_escalation_type='qa_escalation_superseded',
            superseded_escalation_summary='A newer Python rework superseded the prior QA escalation.',
            superseded_escalation_details={'superseded_qa_packet_id': 'msg-old'},
            source_packet_schema_type='qa_verification_packet',
            source_packet_message_id='msg-123',
            source_packet_path='handoff/packet.json',
            branch_name='issue-42-python',
            superseded_branch='issue-42-python-old',
            metadata={'source_queue_name': 'fractal-core-qa'},
        )

        self.assertEqual(request.issue_number, 42)
        self.assertEqual(request.lineage_state, 'superseded')
        self.assertEqual(request.superseded_escalation_type, 'qa_escalation_superseded')
        self.assertEqual(request.superseded_branch, 'issue-42-python-old')

    def test_result_model_wraps_structured_summary(self) -> None:
        summary = TechLeadLineageDecisionSummary(
            decision_supported=True,
            recommended_next_decision='supersede_branch_lineage',
            recommended_target_role='TechLead',
            supersede_allowed=True,
            lineage_decision_summary='The earlier QA escalation has been superseded by a newer branch lineage.',
            blocking_reasons=(),
            notes=('superseded-lineage',),
        )
        result = TechLeadLineageDecisionResult(
            project_slug='paa-platform',
            issue_number=42,
            issue_url='https://example.test/issues/42',
            pr_number=77,
            pr_url='https://example.test/pulls/77',
            workflow_stage='techlead_qa_review_pending',
            lineage_state='superseded',
            superseded_escalation_type='qa_escalation_superseded',
            source_packet_schema_type='qa_verification_packet',
            source_packet_message_id='msg-123',
            source_packet_path='handoff/packet.json',
            branch_name='issue-42-python',
            superseded_branch='issue-42-python-old',
            summary=summary,
            ok=True,
            recommended_actions=('supersede_branch_lineage',),
            unattended_safe=False,
            metadata={'closeout_mode': 'superseded-lineage'},
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.summary.recommended_next_decision, 'supersede_branch_lineage')
        self.assertEqual(result.recommended_actions, ('supersede_branch_lineage',))
        self.assertFalse(result.unattended_safe)


if __name__ == '__main__':
    unittest.main()

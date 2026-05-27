from __future__ import annotations

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'packages' / 'paa-core' / 'src'))

from paa_core.services.techlead_acceptance_decision.models import (
    TechLeadAcceptanceDecisionRequest,
    TechLeadAcceptanceDecisionResult,
    TechLeadAcceptanceDecisionSummary,
)


class TechLeadAcceptanceDecisionModelsTests(unittest.TestCase):
    def test_request_model_preserves_acceptance_context_fields(self) -> None:
        request = TechLeadAcceptanceDecisionRequest(
            project_slug='paa-platform',
            issue_number=42,
            pr_number=77,
            workflow_stage='qa_verification_complete',
            qa_result_type='pass',
            source_packet_schema_type='qa_verification_packet',
            source_packet_message_id='msg-123',
            merge_state={'merge_ready': True},
            acceptance_event_state={'event': 'qa_passed'},
            metadata={'source_queue_name': 'fractal-core-qa'},
        )

        self.assertEqual(request.issue_number, 42)
        self.assertEqual(request.qa_result_type, 'pass')
        self.assertEqual(request.merge_state, {'merge_ready': True})
        self.assertEqual(request.acceptance_event_state, {'event': 'qa_passed'})

    def test_result_model_wraps_structured_summary(self) -> None:
        summary = TechLeadAcceptanceDecisionSummary(
            decision_supported=True,
            recommended_next_decision='prepare_merge',
            acceptance_allowed=True,
            closeout_allowed=False,
            decision_summary='QA pass supports merge preparation.',
            blocking_reasons=(),
            notes=('ready-for-merge',),
        )
        result = TechLeadAcceptanceDecisionResult(
            project_slug='paa-platform',
            issue_number=42,
            pr_number=77,
            workflow_stage='qa_verification_complete',
            qa_result_type='pass',
            source_packet_schema_type='qa_verification_packet',
            source_packet_message_id='msg-123',
            summary=summary,
            ok=True,
            recommended_actions=('prepare_merge',),
            unattended_safe=True,
            metadata={'closeout_mode': 'merge'},
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.summary.recommended_next_decision, 'prepare_merge')
        self.assertEqual(result.recommended_actions, ('prepare_merge',))
        self.assertTrue(result.unattended_safe)


if __name__ == '__main__':
    unittest.main()

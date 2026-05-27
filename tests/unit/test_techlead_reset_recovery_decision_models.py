from __future__ import annotations

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'packages' / 'paa-core' / 'src'))

from paa_core.services.techlead_reset_recovery_decision.models import (
    TechLeadResetRecoveryDecisionRequest,
    TechLeadResetRecoveryDecisionResult,
    TechLeadResetRecoveryDecisionSummary,
)


class TechLeadResetRecoveryDecisionModelsTests(unittest.TestCase):
    def test_request_model_preserves_reset_recovery_context_fields(self) -> None:
        request = TechLeadResetRecoveryDecisionRequest(
            project_slug='paa-platform',
            issue_number=42,
            issue_url='https://example.test/issues/42',
            pr_number=77,
            pr_url='https://example.test/pulls/77',
            workflow_stage='dev_reset_required',
            lineage_state='reset_required',
            reset_escalation_type='reset_branch_required',
            reset_escalation_summary='Repeated scope failure requires branch reset.',
            reset_escalation_details={'architect_comment_at': '2026-05-27T00:00:00Z'},
            source_packet_schema_type='qa_verification_packet',
            source_packet_message_id='msg-123',
            source_packet_path='handoff/packet.json',
            branch_name='issue-42-python',
            metadata={'source_queue_name': 'fractal-core-qa'},
        )

        self.assertEqual(request.issue_number, 42)
        self.assertEqual(request.lineage_state, 'reset_required')
        self.assertEqual(request.reset_escalation_type, 'reset_branch_required')
        self.assertEqual(request.branch_name, 'issue-42-python')

    def test_result_model_wraps_structured_summary(self) -> None:
        summary = TechLeadResetRecoveryDecisionSummary(
            decision_supported=True,
            recommended_next_decision='reset_branch',
            recommended_target_role='Python Dev',
            reset_allowed=True,
            reset_recovery_summary='Reset branch recovery is required for Python Dev.',
            blocking_reasons=(),
            notes=('reset-required',),
        )
        result = TechLeadResetRecoveryDecisionResult(
            project_slug='paa-platform',
            issue_number=42,
            issue_url='https://example.test/issues/42',
            pr_number=77,
            pr_url='https://example.test/pulls/77',
            workflow_stage='dev_reset_required',
            lineage_state='reset_required',
            reset_escalation_type='reset_branch_required',
            source_packet_schema_type='qa_verification_packet',
            source_packet_message_id='msg-123',
            source_packet_path='handoff/packet.json',
            branch_name='issue-42-python',
            summary=summary,
            ok=True,
            recommended_actions=('reset_branch',),
            unattended_safe=False,
            metadata={'closeout_mode': 'reset-recovery'},
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.summary.recommended_next_decision, 'reset_branch')
        self.assertEqual(result.recommended_actions, ('reset_branch',))
        self.assertFalse(result.unattended_safe)


if __name__ == '__main__':
    unittest.main()

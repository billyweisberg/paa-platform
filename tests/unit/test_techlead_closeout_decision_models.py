from __future__ import annotations

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'packages' / 'paa-core' / 'src'))

from paa_core.services.techlead_closeout_decision.models import (
    TechLeadCloseoutDecisionRequest,
    TechLeadCloseoutDecisionResult,
    TechLeadCloseoutDecisionSummary,
)


class TechLeadCloseoutDecisionModelsTests(unittest.TestCase):
    def test_request_model_preserves_proof_only_closeout_context_fields(self) -> None:
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

        self.assertEqual(request.issue_number, 42)
        self.assertEqual(request.workflow_stage, 'proof_only_closed')
        self.assertEqual(request.decision_type, 'proof_only_closed')
        self.assertTrue(request.proof_only_mode)
        self.assertEqual(request.canonical_branch, 'issue-42')

    def test_result_model_wraps_structured_summary(self) -> None:
        summary = TechLeadCloseoutDecisionSummary(
            decision_supported=True,
            recommended_next_decision='proof_only_close_slice',
            recommended_target_role='TechLead',
            closeout_allowed=True,
            closeout_decision_summary='Proof-only QA closeout can be recorded without merge side effects.',
            blocking_reasons=(),
            notes=('proof-only-closeout',),
        )
        result = TechLeadCloseoutDecisionResult(
            project_slug='paa-platform',
            issue_number=42,
            issue_url='https://example.test/issues/42',
            pr_number=77,
            pr_url='https://example.test/pulls/77',
            workflow_stage='proof_only_closed',
            decision_type='proof_only_closed',
            source_packet_schema_type='qa_verification_packet',
            source_packet_message_id='msg-123',
            source_packet_path='handoff/packet.json',
            branch_name='issue-42-python',
            canonical_branch='issue-42',
            summary=summary,
            ok=True,
            recommended_actions=('proof_only_close_slice',),
            unattended_safe=True,
            metadata={'closeout_mode': 'proof_only'},
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.summary.recommended_next_decision, 'proof_only_close_slice')
        self.assertEqual(result.recommended_actions, ('proof_only_close_slice',))
        self.assertTrue(result.unattended_safe)


if __name__ == '__main__':
    unittest.main()

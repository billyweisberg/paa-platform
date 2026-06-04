import json
import unittest
from pathlib import Path
from unittest.mock import patch

from paa_core.producer.brief_reviewer import _review_checks, review_coder_brief, BriefContext


REPO_ROOT = Path('/Users/billyweisberg/Repos/billyweisberg/paa-platform')
OUTPUT_PATH = REPO_ROOT / '.codex-work' / 'brief-reviewer-tests' / 'brief-review-approval.json'


class BriefReviewerTests(unittest.TestCase):
    def test_review_checks_require_targets_for_approval(self):
        context = BriefContext(
            coder_run_brief_id='brief',
            project_id='project',
            project_slug='paa-platform',
            work_item_id='work-item',
            authority_state='draft_brief',
            status='draft',
            brief_id='brief-id',
            approval_json={},
            packet_preparation_json={},
            readiness_class='derivation_ready',
            target_count=0,
        )
        checks = _review_checks(context, 'approve')
        failed_ids = {check.check_id for check in checks if check.status == 'fail'}
        self.assertIn('targets_materialized', failed_ids)

    def test_reapprove_existing_approved_brief_is_noop(self):
        context = BriefContext(
            coder_run_brief_id='brief',
            project_id='project',
            project_slug='paa-platform',
            work_item_id='work-item',
            authority_state='approved_brief',
            status='approved',
            brief_id='brief-id',
            approval_json={'current_state': 'approved_brief'},
            packet_preparation_json={},
            readiness_class='derivation_ready',
            target_count=5,
        )
        with patch('paa_core.producer.brief_reviewer._resolve_brief_context', return_value=context):
            result = review_coder_brief(coder_run_brief_id='brief', decision='approve')
        self.assertFalse(result.transition_applied)
        self.assertEqual(result.authority_state, 'approved_brief')

    def test_review_coder_brief_approve_writes_output(self):
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_PATH.unlink(missing_ok=True)
        context = BriefContext(
            coder_run_brief_id='brief',
            project_id='project',
            project_slug='paa-platform',
            work_item_id='work-item',
            authority_state='approved_brief',
            status='approved',
            brief_id='brief-id',
            approval_json={'current_state': 'approved_brief'},
            packet_preparation_json={},
            readiness_class='derivation_ready',
            target_count=5,
        )
        with patch('paa_core.producer.brief_reviewer._resolve_brief_context', return_value=context):
            result = review_coder_brief(
                coder_run_brief_id='brief',
                decision='approve',
                review_summary='Proof slice approved after target authoring validation.',
                notes='Approved through producer-side governed review flow.',
                output_path=OUTPUT_PATH,
            )
        self.assertFalse(result.transition_applied)
        self.assertEqual(result.authority_state, 'approved_brief')
        self.assertTrue(OUTPUT_PATH.exists())
        payload = json.loads(OUTPUT_PATH.read_text())
        self.assertEqual(payload['decision'], 'approve')
        self.assertEqual(payload['authority_state'], 'approved_brief')
        OUTPUT_PATH.unlink(missing_ok=True)


if __name__ == '__main__':
    unittest.main()

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from paa_consumer import techlead


class TechLeadSelfHostedTests(unittest.TestCase):
    def test_repo_auth_current_uses_dynamic_installed_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            manifest_dir = repo_root / '.project' / 'data' / 'paa' / 'authority' / 'current' / 'authority'
            manifest_dir.mkdir(parents=True, exist_ok=True)
            manifest_path = manifest_dir / 'paa-platform-authority.json'
            manifest_path.write_text(json.dumps({'project': {'repo': 'billyweisberg/paa-platform'}}))

            resolved = techlead.repo_auth_current(repo_root)

            self.assertEqual(resolved, manifest_path)

    def test_github_state_falls_back_to_packet_context(self):
        packet = {
            'github_context': {
                'repo': 'billyweisberg/paa-platform',
                'issue_number': 9002,
                'pr_number': 9001,
                'branch': 'system-design-1',
                'links': [
                    'https://example.invalid/paa/proof/pull/9001',
                    'https://example.invalid/paa/proof/issues/9002',
                ],
            },
            'payload': {
                'accepted_pr': {
                    'number': 9001,
                    'url': 'https://example.invalid/paa/proof/pull/9001',
                },
                'next_issue': {
                    'number': 9002,
                    'url': 'https://example.invalid/paa/proof/issues/9002',
                },
            },
        }

        with patch('paa_consumer.techlead.run_json', side_effect=RuntimeError('gh unavailable')):
            issue, pr = techlead.github_state(
                9002,
                'billyweisberg/paa-platform',
                fallback_pr_number=9001,
                fallback_task={'title': 'Proof Slice Task'},
                fallback_packet=packet,
            )

        self.assertEqual(issue['number'], 9002)
        self.assertEqual(issue['title'], 'Proof Slice Task')
        self.assertEqual(issue['url'], 'https://example.invalid/paa/proof/issues/9002')
        self.assertIsNotNone(pr)
        self.assertEqual(pr['number'], 9001)
        self.assertEqual(pr['headRefName'], 'system-design-1')
        self.assertEqual(pr['url'], 'https://example.invalid/paa/proof/pull/9001')

    def test_closeout_qa_pass_uses_proof_only_terminal_path(self):
        qa_packet = {
            'message_id': 'qa-proof-1',
            'verification_status': 'pass',
            'path': '/tmp/qa-proof-1.json',
            'pr_number': 9001,
            'created_at': '2026-05-17T00:00:00Z',
            'recommended_action': {'merge_recommendation': 'do_not_merge_proof_slice'},
        }
        persisted = {}

        def _capture_persist(*args, **kwargs):
            persisted['decision'] = kwargs.get('decision')
            persisted['decision_notes'] = kwargs.get('decision_notes')
            persisted['metadata_extra'] = kwargs.get('metadata_extra')

        with patch('paa_consumer.techlead.load_design_package', return_value={'authority_context': {'execution_mode': 'proof_only'}}), \
             patch('paa_consumer.techlead.latest_qa_packet', return_value=qa_packet), \
             patch('paa_consumer.techlead.queue_state', return_value={'fractal-core-architecture': {'preview': []}}), \
             patch('paa_consumer.techlead.latest_packet_preview', return_value={'github_context': {'repo': 'billyweisberg/paa-platform'}}), \
             patch('paa_consumer.techlead.github_state', return_value=({'state': 'OPEN', 'closedAt': None}, {'number': 9001, 'state': 'OPEN', 'mergedAt': None, 'url': 'https://example.invalid/pull/9001'})), \
             patch('paa_consumer.techlead.persist_techlead_acceptance_event', side_effect=_capture_persist), \
             patch('paa_consumer.techlead.emit_decision', return_value={'ok': True, 'message_id': 'decision-proof-1', 'sent': False}):
            args = type('Args', (), {
                'repo_root': Path('/tmp/proof-repo'),
                'project_slug': 'paa-platform',
                'package_id_external': 'paa-stage1-2026-05-16-component-design-planning-service',
                'brief_id_external': 'paa-coder-2026-05-16-component-design-planning-service-governed-draft',
                'issue_number': 9002,
                'send_decision': False,
                'ack_qa_packet': False,
                'claimed_by': 'test-proof-closeout',
                'canonical_branch': 'main',
                'role_branch': 'issue-9002-qa',
                'worktree_hint': '.codex-work/worktrees/paa/issue-9002-qa',
                'output': None,
                'review_output': None,
                'db_container': 'db',
                'db_name': 'paa_dev',
                'db_user': 'mmuser',
            })()
            result = techlead.closeout_qa_pass(args)

        self.assertTrue(result['ok'])
        self.assertEqual(result['execution_mode'], 'proof_only')
        self.assertEqual(result['closeout_mode'], 'proof_only')
        self.assertEqual(persisted['decision'], 'proof_only_closed')
        self.assertTrue(persisted['metadata_extra']['proof_only_closeout'])
        self.assertEqual(persisted['metadata_extra']['closeout_mode'], 'proof_only')


if __name__ == '__main__':
    unittest.main()

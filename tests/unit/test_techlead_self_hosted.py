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


if __name__ == '__main__':
    unittest.main()

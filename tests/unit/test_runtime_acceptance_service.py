from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))

from paa_core.runtime.bridges.acceptance import (
    DefaultRuntimeAcceptanceService,
    RuntimeAcceptanceRequest,
)


class RuntimeAcceptanceServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path('/tmp/paa-acceptance-test')
        self.qa_packet = {
            'message_id': 'qa-pass-1',
            'verification_status': 'pass',
            'pr_number': 11,
            'recommended_action': {'merge_recommendation': 'accept_and_merge'},
        }
        self.github_states = [
            (
                {'state': 'OPEN', 'closedAt': None},
                {'number': 11, 'state': 'OPEN', 'mergedAt': None, 'url': 'https://example.test/pulls/11'},
            ),
            (
                {'state': 'OPEN', 'closedAt': None},
                {'number': 11, 'state': 'OPEN', 'mergedAt': None, 'url': 'https://example.test/pulls/11'},
            ),
            (
                {'state': 'CLOSED', 'closedAt': '2026-06-02T00:00:00Z'},
                {'number': 11, 'state': 'MERGED', 'mergedAt': '2026-06-02T00:00:00Z', 'url': 'https://example.test/pulls/11'},
            ),
        ]
        self.merge_calls: list[tuple[int, str, str]] = []
        self.close_calls: list[tuple[int, str, str]] = []
        self.closeout_calls: list[dict[str, object]] = []

        def _github_state_loader(*args, **kwargs):
            return self.github_states.pop(0)

        def _merge_state_loader(pr_number: int, github_repo: str):
            return {
                'number': pr_number,
                'state': 'OPEN',
                'isDraft': False,
                'mergeStateStatus': 'CLEAN',
                'mergedAt': None,
                'statusCheckRollup': [],
                'url': 'https://example.test/pulls/11',
            }

        def _merge_pr(pr_number: int, github_repo: str, merge_method: str):
            self.merge_calls.append((pr_number, github_repo, merge_method))
            return {'ok': True, 'stdout': 'merged', 'stderr': ''}

        def _close_issue(issue_number: int, github_repo: str, comment: str):
            self.close_calls.append((issue_number, github_repo, comment))
            return {'ok': True, 'stdout': 'closed', 'stderr': ''}

        def _closeout_runner(payload):
            self.closeout_calls.append(payload)
            return {'ok': True, 'decision': {'ok': True}}

        self.service = DefaultRuntimeAcceptanceService(
            github_state_loader=_github_state_loader,
            merge_state_loader=_merge_state_loader,
            merge_pr=_merge_pr,
            close_issue=_close_issue,
            closeout_runner=_closeout_runner,
            fallback_packet_loader=lambda repo_root, issue_number: {'message_id': 'fallback-1'},
            github_repo_resolver=lambda repo_root: 'billyweisberg/paa-platform',
            ci_status_deriver=lambda pr: 'green',
            qa_packet_loader=lambda issue_number, reports_dir: self.qa_packet,
            reports_dir_resolver=lambda repo_root: repo_root / '.project' / 'data' / 'paa' / 'reports',
        )

    def test_rejects_non_passing_qa_packet(self) -> None:
        self.qa_packet['verification_status'] = 'fail'

        result = self.service.accept_and_merge_qa_pass(
            RuntimeAcceptanceRequest(
                repo_root=self.repo_root,
                issue_number=6,
                package_id_external='pkg-1',
                brief_id_external='brief-1',
                project_slug='paa-platform',
            )
        )

        self.assertFalse(result['ok'])
        self.assertEqual(result['reason'], 'qa_packet_not_pass')

    def test_rejects_non_merge_recommendation(self) -> None:
        self.qa_packet['recommended_action'] = {'merge_recommendation': 'changes_requested'}

        result = self.service.accept_and_merge_qa_pass(
            RuntimeAcceptanceRequest(
                repo_root=self.repo_root,
                issue_number=6,
                package_id_external='pkg-1',
                brief_id_external='brief-1',
                project_slug='paa-platform',
            )
        )

        self.assertFalse(result['ok'])
        self.assertEqual(result['reason'], 'qa_packet_not_accept_and_merge')

    def test_merges_closes_issue_and_runs_closeout(self) -> None:
        result = self.service.accept_and_merge_qa_pass(
            RuntimeAcceptanceRequest(
                repo_root=self.repo_root,
                issue_number=6,
                package_id_external='pkg-1',
                brief_id_external='brief-1',
                project_slug='paa-platform',
                merge_method='squash',
                issue_close_comment='done',
                canonical_branch='issue-6',
                role_branch='issue-6-dev',
                worktree_hint='issue-6-dev',
            )
        )

        self.assertTrue(result['ok'])
        self.assertEqual(self.merge_calls, [(11, 'billyweisberg/paa-platform', 'squash')])
        self.assertEqual(self.close_calls, [(6, 'billyweisberg/paa-platform', 'done')])
        self.assertEqual(len(self.closeout_calls), 1)
        self.assertEqual(self.closeout_calls[0]['issue_number'], 6)
        self.assertTrue(self.closeout_calls[0]['send_decision'])
        self.assertTrue(self.closeout_calls[0]['ack_qa_packet'])
        self.assertEqual(result['github_state_after_merge']['issue_state'], 'CLOSED')
        self.assertEqual(result['github_state_after_merge']['pr_state'], 'MERGED')


if __name__ == '__main__':
    unittest.main()

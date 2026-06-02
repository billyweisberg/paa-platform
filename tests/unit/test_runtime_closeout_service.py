from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))

from paa_core.services.runtime_closeout import (
    DefaultRuntimeCloseoutService,
    RuntimeQaCloseoutRequest,
)


class _StubQueueAdmin:
    def __init__(self) -> None:
        self.claimed = []
        self.acked = []
        self._preview_messages = []
        self._claim_results = []

    def set_preview_messages(self, messages):
        self._preview_messages = list(messages)

    def set_claim_results(self, results):
        self._claim_results = list(results)

    def check(self, *, repo_root: Path, queue: str, preview: int = 0):
        message_id = self._preview_messages.pop(0) if self._preview_messages else None
        preview_rows = []
        if message_id is not None:
            preview_rows.append({'payload_preview': {'message_id': message_id}})
        return {'queue': queue, 'preview': preview_rows}

    def claim_next(self, *, repo_root: Path, queue: str, claimed_by: str = 'paa'):
        self.claimed.append((queue, claimed_by))
        return self._claim_results.pop(0), 0

    def ack(self, *, repo_root: Path, claim_id: str):
        self.acked.append(claim_id)
        return {'ok': True, 'claim_id': claim_id, 'status': 'done'}


class RuntimeCloseoutServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.queue_admin = _StubQueueAdmin()
        self.persist_calls = []
        self.emit_calls = []

        def _persist(*args, **kwargs):
            self.persist_calls.append((args, kwargs))
            return None

        def _emit(payload):
            self.emit_calls.append(payload)
            return {
                'ok': True,
                'message_id': 'decision-1',
                'sent': payload['send'],
            }

        self.service = DefaultRuntimeCloseoutService(
            queue_admin_service=self.queue_admin,
            acceptance_event_persister=_persist,
            decision_emitter=_emit,
        )
        self.repo_root = Path('/tmp/paa-closeout-test')
        self.qa_packet = {
            'message_id': 'qa-pass-1',
            'verification_status': 'pass',
            'pr_number': 11,
            'path': '/tmp/qa-pass-1.json',
        }
        self.issue_full = {'state': 'OPEN', 'closedAt': None}
        self.pr_full = {'number': 11, 'state': 'OPEN', 'mergedAt': None}

    def test_live_closeout_requires_merged_or_closed(self) -> None:
        result = self.service.closeout_qa_pass(
            RuntimeQaCloseoutRequest(
                repo_root=self.repo_root,
                issue_number=6,
                execution_mode='live_delivery',
                qa_packet=self.qa_packet,
                issue_full=self.issue_full,
                pr_full=self.pr_full,
                package_id_external='pkg-1',
                brief_id_external='brief-1',
                project_slug='paa-platform',
                architecture_queue='paa-techlead',
            )
        )

        self.assertFalse(result['ok'])
        self.assertEqual(result['reason'], 'slice_not_merged_or_closed')

    def test_proof_only_closeout_persists_and_acks_packets(self) -> None:
        self.queue_admin.set_preview_messages(['qa-pass-1', 'decision-1'])
        self.queue_admin.set_claim_results([
            {'ok': True, 'claim_id': 'claim-qa', 'message_id': 'qa-pass-1'},
            {'ok': True, 'claim_id': 'claim-decision', 'message_id': 'decision-1'},
        ])
        result = self.service.closeout_qa_pass(
            RuntimeQaCloseoutRequest(
                repo_root=self.repo_root,
                issue_number=6,
                execution_mode='proof_only',
                qa_packet=self.qa_packet,
                issue_full=self.issue_full,
                pr_full=self.pr_full,
                package_id_external='pkg-1',
                brief_id_external='brief-1',
                project_slug='paa-platform',
                architecture_queue='paa-techlead',
                send_decision=True,
                ack_qa_packet=True,
                claimed_by='techlead-closeout',
            )
        )

        self.assertTrue(result['ok'])
        self.assertEqual(result['closeout_mode'], 'proof_only')
        self.assertEqual(len(self.persist_calls), 1)
        self.assertEqual(len(self.emit_calls), 1)
        self.assertEqual(self.queue_admin.claimed, [
            ('paa-techlead', 'techlead-closeout'),
            ('paa-techlead', 'techlead-closeout-decision'),
        ])
        self.assertEqual(self.queue_admin.acked, ['claim-qa', 'claim-decision'])
        self.assertEqual(result['qa_ack']['claim_id'], 'claim-qa')
        self.assertEqual(result['decision_ack']['claim_id'], 'claim-decision')


if __name__ == '__main__':
    unittest.main()

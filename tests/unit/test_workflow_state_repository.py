from __future__ import annotations

import sys
from pathlib import Path
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'packages' / 'paa-core' / 'src'))

from paa_core.repositories.workflow_state import (  # noqa: E402
    PostgresWorkflowStateRepository,
    WorkflowStateUpsertSpec,
    WorkflowTransitionAppendSpec,
)


class WorkflowStateRepositoryTests(unittest.TestCase):
    def test_get_workflow_state_for_work_item_parses_row(self) -> None:
        repo = PostgresWorkflowStateRepository()
        output = {"workflow_state_id":"ws-1","project_id":"proj-1","work_item_id":"work-1","authority_version_id":"auth-1","design_package_id":"pkg-1","coder_run_brief_id":"brief-1","workflow_stage":"qa_assignment_pending","current_owner_role_id":"role-qa","lineage_state":"awaiting_result","blocking_reason_code":None,"blocking_reason_text":None,"terminal_decision":"none","state_consistency":"consistent","current_issue_number":42,"current_pr_number":43,"canonical_branch":"main","active_role_branch":"issue-42-qa","active_handoff_id":"handoff-1","active_queue_message_id":"qm-1","active_message_id_external":"msg-1","active_assignment_role_id":"role-qa","active_result_role_id":None,"active_queue_claim_id":"claim-1","state_entered_at":"2026-05-17T12:00:00+00:00","last_transition_at":"2026-05-17T12:10:00+00:00","closed_at":None,"metadata":{"proof":True},"created_at":"2026-05-17T12:00:00+00:00","updated_at":"2026-05-17T12:10:00+00:00"}
        with patch('paa_core.repositories.workflow_state.postgres.query_json_rows', return_value=[output]):
            row = repo.get_workflow_state_for_work_item('work-1')

        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row.workflow_stage, 'qa_assignment_pending')
        self.assertEqual(row.current_issue_number, 42)
        self.assertEqual(row.metadata, {'proof': True})

    def test_list_workflow_transitions_for_work_item_parses_rows(self) -> None:
        repo = PostgresWorkflowStateRepository()
        output = [{
            "workflow_transition_id":"wt-1","workflow_state_id":"ws-1","project_id":"proj-1","work_item_id":"work-1","transition_type":"assignment_emitted","transition_status":"applied","from_workflow_stage":"worker_assignment_pending","to_workflow_stage":"worker_execution_in_progress","from_owner_role_id":"role-techlead","to_owner_role_id":"role-worker","reason_code":None,"reason_text":"Assigned to worker","source_handoff_id":"handoff-1","source_queue_message_id":"qm-1","source_queue_claim_id":None,"source_message_id_external":"msg-1","source_packet_schema_type":"techlead_assignment_packet","source_role_id":"role-techlead","source_transition_input_id":None,"result_handoff_id":None,"result_queue_message_id":None,"result_queue_claim_id":None,"result_message_id_external":None,"result_packet_schema_type":None,"result_role_id":None,"performed_by_role_id":"role-techlead","performed_by_agent_id":"agent-1","automation_run_id":"run-1","error_code":None,"error_details":None,"transition_requested_at":"2026-05-17T12:00:00+00:00","transition_applied_at":"2026-05-17T12:00:01+00:00","metadata":{"phase":"assign"},"created_at":"2026-05-17T12:00:01+00:00"
        }]
        with patch('paa_core.repositories.workflow_state.postgres.query_json_rows', return_value=output):
            rows = repo.list_workflow_transitions_for_work_item('work-1')

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].transition_type, 'assignment_emitted')
        self.assertEqual(rows[0].metadata, {'phase': 'assign'})

    def test_get_active_queue_claim_for_message_parses_row(self) -> None:
        repo = PostgresWorkflowStateRepository()
        output = {"queue_claim_id":"claim-1","queue_message_id":"qm-1","handoff_id":"handoff-1","project_id":"proj-1","work_item_id":"work-1","claimed_by_role_id":"role-worker","claimed_by_agent_id":"agent-1","claim_attempt_source":"role_preflight","claim_status":"active","ack_outcome":"none","release_reason_code":None,"release_reason_text":None,"claimed_at":"2026-05-17T12:05:00+00:00","lease_expires_at":"2026-05-17T12:10:00+00:00","released_at":None,"acked_at":None,"metadata":{"queue":"python"},"created_at":"2026-05-17T12:05:00+00:00"}
        with patch('paa_core.repositories.workflow_state.postgres.query_json_rows', return_value=[output]):
            row = repo.get_active_queue_claim_for_message('qm-1')

        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row.claim_status, 'active')
        self.assertEqual(row.metadata, {'queue': 'python'})

    def test_upsert_workflow_state_emits_upsert_sql(self) -> None:
        repo = PostgresWorkflowStateRepository()
        spec = WorkflowStateUpsertSpec(
            project_id='11111111-1111-1111-1111-111111111111',
            work_item_id='22222222-2222-2222-2222-222222222222',
            authority_version_id='33333333-3333-3333-3333-333333333333',
            design_package_id='44444444-4444-4444-4444-444444444444',
            coder_run_brief_id='55555555-5555-5555-5555-555555555555',
            workflow_stage='worker_execution_in_progress',
            current_owner_role_id='66666666-6666-6666-6666-666666666666',
            lineage_state='active',
            current_issue_number=42,
            canonical_branch='main',
            metadata={'proof': True},
        )
        with patch('paa_core.repositories.workflow_state.postgres.run_psql', return_value='') as mock_run:
            repo.upsert_workflow_state(spec)

        sql = mock_run.call_args.args[0]
        self.assertIn('INSERT INTO paa.workflow_states', sql)
        self.assertIn('worker_execution_in_progress', sql)
        self.assertIn('ON CONFLICT (work_item_id) DO UPDATE', sql)
        self.assertIn('updated_at = now()', sql)

    def test_append_workflow_transition_emits_insert_sql(self) -> None:
        repo = PostgresWorkflowStateRepository()
        spec = WorkflowTransitionAppendSpec(
            workflow_state_id='11111111-1111-1111-1111-111111111111',
            project_id='22222222-2222-2222-2222-222222222222',
            work_item_id='33333333-3333-3333-3333-333333333333',
            transition_type='worker_result_returned',
            transition_status='applied',
            from_workflow_stage='worker_execution_in_progress',
            to_workflow_stage='techlead_worker_review_pending',
            source_queue_message_id='44444444-4444-4444-4444-444444444444',
            source_packet_schema_type='worker_result_packet',
            performed_by_role_id='55555555-5555-5555-5555-555555555555',
            performed_by_agent_id='66666666-6666-6666-6666-666666666666',
            metadata={'bridge': 'runtime->workflow'},
        )
        with patch('paa_core.repositories.workflow_state.postgres.run_psql', return_value='') as mock_run:
            repo.append_workflow_transition(spec)

        sql = mock_run.call_args.args[0]
        self.assertIn('INSERT INTO paa.workflow_transitions', sql)
        self.assertIn('worker_result_returned', sql)
        self.assertIn('techlead_worker_review_pending', sql)


if __name__ == '__main__':
    unittest.main()

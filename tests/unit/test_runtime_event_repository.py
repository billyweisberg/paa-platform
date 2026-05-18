from __future__ import annotations

import sys
from pathlib import Path
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'packages' / 'paa-core' / 'src'))

from paa_core.repositories.runtime_event import PostgresRuntimeEventRepository  # noqa: E402


class RuntimeEventRepositoryTests(unittest.TestCase):
    def test_get_queue_message_by_external_parses_payload(self) -> None:
        repo = PostgresRuntimeEventRepository()
        output = '{"queue_message_id":"qm-1","handoff_id":"handoff-1","queue_name":"fractal-core-python","schema_type":"architect_cycle_packet","message_id_external":"msg-1","correlation_key":"corr-1","payload":{"schema_type":"architect_cycle_packet"},"status":"sent","sent_at":"2026-05-17T12:00:00+00:00","claimed_at":null,"acknowledged_at":null,"metadata":{"source":"test"},"created_at":"2026-05-17T12:00:00+00:00","updated_at":"2026-05-17T12:00:00+00:00"}'
        with patch('paa_core.repositories.runtime_event.postgres.run_psql', return_value=output):
            row = repo.get_queue_message_by_external('msg-1')

        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row.schema_type, 'architect_cycle_packet')
        self.assertEqual(row.payload, {'schema_type': 'architect_cycle_packet'})

    def test_get_automation_run_parses_artifacts(self) -> None:
        repo = PostgresRuntimeEventRepository()
        output = '{"automation_run_id":"run-1","agent_id":"agent-1","work_item_id":"work-1","handoff_id":"handoff-1","trigger_type":"queue_dispatch","status":"completed","started_at":"2026-05-17T12:00:00+00:00","finished_at":"2026-05-17T12:03:00+00:00","summary":"Completed dispatch","artifacts":{"queue":"fractal-core-python"},"created_at":"2026-05-17T12:00:00+00:00","updated_at":"2026-05-17T12:03:00+00:00"}'
        with patch('paa_core.repositories.runtime_event.postgres.run_psql', return_value=output):
            row = repo.get_automation_run('run-1')

        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row.status, 'completed')
        self.assertEqual(row.artifacts, {'queue': 'fractal-core-python'})

    def test_list_transition_inputs_for_work_item_parses_rows(self) -> None:
        repo = PostgresRuntimeEventRepository()
        output = '{"transition_input_id":"ti-1","project_id":"proj-1","work_item_id":"work-1","workflow_state_id":"ws-1","workflow_transition_id":"wt-1","automation_run_id":"run-1","input_type":"queue_packet","input_schema_type":"worker_result_packet","input_source_surface":"consumer_queue","input_key":"msg-1","input_hash":"hash-1","source_queue_message_id":"qm-1","source_handoff_id":"handoff-1","source_message_id_external":"msg-1","source_report_path":null,"payload":{"verification_status":"pass"},"content_summary":{"summary":"Worker result"},"schema_version":"1.0","captured_at":"2026-05-17T12:00:00+00:00","metadata":{"bridge":"worker"},"created_at":"2026-05-17T12:00:00+00:00"}'
        with patch('paa_core.repositories.runtime_event.postgres.run_psql', return_value=output):
            rows = repo.list_transition_inputs_for_work_item('work-1')

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].input_type, 'queue_packet')
        self.assertEqual(rows[0].payload, {'verification_status': 'pass'})

    def test_list_automation_run_events_parses_rows(self) -> None:
        repo = PostgresRuntimeEventRepository()
        output = '{"automation_run_event_id":"evt-1","automation_run_id":"run-1","project_id":"proj-1","work_item_id":"work-1","workflow_state_id":"ws-1","workflow_transition_id":"wt-1","event_type":"packet_emitted","event_status":"completed","event_phase":"handoff","event_reason_code":null,"event_reason_text":null,"role_id":"role-1","agent_id":"agent-1","handoff_id":"handoff-1","queue_message_id":"qm-1","queue_claim_id":"claim-1","message_id_external":"msg-1","event_summary":{"step":"emit"},"evidence_ref":null,"raw_log_pointer":null,"event_recorded_at":"2026-05-17T12:01:00+00:00","metadata":{"queue":"python"},"created_at":"2026-05-17T12:01:00+00:00"}'
        with patch('paa_core.repositories.runtime_event.postgres.run_psql', return_value=output):
            rows = repo.list_automation_run_events('run-1')

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].event_type, 'packet_emitted')
        self.assertEqual(rows[0].event_summary, {'step': 'emit'})

    def test_list_acceptance_events_for_work_item_parses_rows(self) -> None:
        repo = PostgresRuntimeEventRepository()
        output = '{"acceptance_event_id":"ae-1","project_id":"proj-1","work_item_id":"work-1","handoff_id":"handoff-1","accepted_by_agent_id":"agent-1","accepted_by_role_id":"role-1","decision":"accepted","notes":"Approved","merge_commit_sha":"abc123","metadata":{"closeout_mode":"live"},"created_at":"2026-05-17T12:05:00+00:00"}'
        with patch('paa_core.repositories.runtime_event.postgres.run_psql', return_value=output):
            rows = repo.list_acceptance_events_for_work_item('work-1')

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].decision, 'accepted')
        self.assertEqual(rows[0].metadata, {'closeout_mode': 'live'})


if __name__ == '__main__':
    unittest.main()

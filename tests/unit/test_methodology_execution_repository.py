from __future__ import annotations

import sys
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))

from paa_core.repositories.methodology_execution import (
    MethodologyExecutionBindingEntrySpec,
    MethodologyExecutionBindingReplaceSpec,
    MethodologyExecutionEventAppendSpec,
    MethodologyExecutionUpsertSpec,
    PostgresMethodologyExecutionRepository,
)


class MethodologyExecutionRepositoryTests(unittest.TestCase):
    def test_get_methodology_execution_parses_root_row(self) -> None:
        repo = PostgresMethodologyExecutionRepository()
        output = '{"methodology_execution_id":"exec-1","project_id":"proj-1","work_item_id":"work-1","lane":"component_realization","stage":"slice_execution","step":"derive_next_activity_bundle","status":"active","current_owner_role":"architect","next_action_key":"implement-postgres","blocked_reason":null,"component_id":"component-1","design_package_id":"design-1","implementation_plan_id":"plan-1","coder_run_brief_id":null,"packet_id":null,"workflow_state_id":"workflow-1","active_authority_ref":"docs/spec.md","active_artifact_ref":"contracts.py","metadata":{"priority":"high"},"created_at":"2026-05-30T12:00:00+00:00","updated_at":"2026-05-30T12:05:00+00:00"}'
        with patch('paa_core.repositories.methodology_execution.postgres.run_psql', return_value=output):
            row = repo.get_methodology_execution('exec-1')

        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row.lane, 'component_realization')
        self.assertEqual(row.metadata, {'priority': 'high'})

    def test_find_methodology_execution_by_primary_ref_filters_component_anchor(self) -> None:
        repo = PostgresMethodologyExecutionRepository()
        output = '{"methodology_execution_id":"exec-1","project_id":"proj-1","work_item_id":"work-1","lane":"authority_derivation","stage":"design","step":"author_component_spec","status":"active","current_owner_role":"architect","next_action_key":"materialize_component_spec","blocked_reason":null,"component_id":"component-1","design_package_id":null,"implementation_plan_id":null,"coder_run_brief_id":null,"packet_id":null,"workflow_state_id":null,"active_authority_ref":null,"active_artifact_ref":null,"metadata":{},"created_at":null,"updated_at":null}'
        with patch('paa_core.repositories.methodology_execution.postgres.run_psql', return_value=output) as mock_run:
            row = repo.find_methodology_execution_by_primary_ref('proj-1', 'work-1', 'component-1')

        self.assertIsNotNone(row)
        self.assertIn("me.component_id = 'component-1'::uuid", mock_run.call_args.args[0])

    def test_list_events_and_bindings_parse_history_rows(self) -> None:
        repo = PostgresMethodologyExecutionRepository()
        event_output = '{"methodology_execution_event_id":"event-1","methodology_execution_id":"exec-1","from_lane":"design","to_lane":"component_realization","from_stage":"design","to_stage":"component_materialization","from_step":"author_component_spec","to_step":"materialize_component_spec","from_status":"active","to_status":"active","transition_kind":"advance","actor_role_id":"architect","actor_name":"Authority Architect","notes":"advance","evidence":{"component_id":"component-1"},"created_at":"2026-05-30T12:10:00+00:00"}'
        binding_output = '{"methodology_execution_binding_id":"binding-1","methodology_execution_id":"exec-1","binding_kind":"implementation_plan","bound_record_id":"plan-1","bound_record_key":"plan-materialize","bound_record_ref":"implementation_plan:plan-1","is_primary":true,"notes":"current plan","metadata":{"source":"materializer"},"created_at":"2026-05-30T12:10:00+00:00","updated_at":"2026-05-30T12:11:00+00:00"}'
        with patch('paa_core.repositories.methodology_execution.postgres.run_psql', side_effect=[event_output, binding_output]):
            events = repo.list_methodology_execution_events('exec-1')
            bindings = repo.list_methodology_execution_bindings('exec-1')

        self.assertEqual(events[0].transition_kind, 'advance')
        self.assertTrue(bindings[0].is_primary)
        self.assertEqual(bindings[0].bound_record_ref, 'implementation_plan:plan-1')

    def test_load_projection_inputs_stitches_root_history_and_bindings(self) -> None:
        repo = PostgresMethodologyExecutionRepository()
        execution_output = '{"methodology_execution_id":"exec-1","project_id":"proj-1","work_item_id":"work-1","lane":"runtime_execution","stage":"verification","step":"await_result","status":"waiting","current_owner_role":"qa","next_action_key":"qa-review","blocked_reason":null,"component_id":null,"design_package_id":null,"implementation_plan_id":null,"coder_run_brief_id":"brief-1","packet_id":"packet-1","workflow_state_id":"workflow-1","active_authority_ref":null,"active_artifact_ref":null,"metadata":{},"created_at":null,"updated_at":null}'
        event_output = '{"methodology_execution_event_id":"event-1","methodology_execution_id":"exec-1","from_lane":null,"to_lane":"runtime_execution","from_stage":null,"to_stage":"verification","from_step":null,"to_step":"await_result","from_status":null,"to_status":"waiting","transition_kind":"enter_stage","actor_role_id":null,"actor_name":null,"notes":null,"evidence":{},"created_at":null}'
        binding_output = '{"methodology_execution_binding_id":"binding-1","methodology_execution_id":"exec-1","binding_kind":"packet","bound_record_id":"packet-1","bound_record_key":null,"bound_record_ref":"packet:packet-1","is_primary":true,"notes":null,"metadata":{},"created_at":null,"updated_at":null}'
        with patch('paa_core.repositories.methodology_execution.postgres.run_psql', side_effect=[execution_output, event_output, binding_output]):
            projection = repo.load_methodology_execution_projection_inputs('exec-1')

        self.assertEqual(projection.execution.methodology_execution_id, 'exec-1')
        self.assertEqual(len(projection.events), 1)
        self.assertEqual(projection.bindings[0].binding_kind, 'packet')
        self.assertEqual(projection.related_records, {})


    def test_projection_inputs_fail_closed_when_execution_is_missing(self) -> None:
        repo = PostgresMethodologyExecutionRepository()
        with patch('paa_core.repositories.methodology_execution.postgres.run_psql', return_value=''):
            with self.assertRaises(LookupError):
                repo.load_methodology_execution_projection_inputs('missing-exec')

    def test_upsert_methodology_execution_emits_upsert_sql(self) -> None:
        repo = PostgresMethodologyExecutionRepository()
        spec = MethodologyExecutionUpsertSpec(
            methodology_execution_id='11111111-1111-1111-1111-111111111111',
            project_id='22222222-2222-2222-2222-222222222222',
            work_item_id='33333333-3333-3333-3333-333333333333',
            lane='component_realization',
            stage='slice_execution',
            step='implement_adapter',
            status='active',
            current_owner_role='architect',
            next_action_key='run_validation',
            implementation_plan_id='44444444-4444-4444-4444-444444444444',
            metadata={'source': 'test'},
        )
        with patch('paa_core.repositories.methodology_execution.postgres.run_psql', return_value='') as mock_run:
            repo.upsert_methodology_execution(spec)

        sql = mock_run.call_args.args[0]
        self.assertIn('INSERT INTO paa.methodology_executions', sql)
        self.assertIn("'component_realization'::paa.methodology_lane", sql)
        self.assertIn('ON CONFLICT (methodology_execution_id) DO UPDATE', sql)

    def test_append_event_and_replace_bindings_emit_expected_sql(self) -> None:
        repo = PostgresMethodologyExecutionRepository()
        append_spec = MethodologyExecutionEventAppendSpec(
            methodology_execution_id='11111111-1111-1111-1111-111111111111',
            to_lane='component_realization',
            to_stage='slice_execution',
            to_step='implement_adapter',
            to_status='active',
            transition_kind='advance',
            evidence={'component_id': 'component-1'},
        )
        replace_spec = MethodologyExecutionBindingReplaceSpec(
            methodology_execution_id='11111111-1111-1111-1111-111111111111',
            replace_scope='replace_kind',
            bindings=(
                MethodologyExecutionBindingEntrySpec(
                    binding_kind='implementation_plan',
                    bound_record_id='22222222-2222-2222-2222-222222222222',
                    bound_record_ref='implementation_plan:plan-1',
                    is_primary=True,
                ),
            ),
        )
        with patch('paa_core.repositories.methodology_execution.postgres.run_psql', return_value='') as mock_run:
            repo.append_methodology_execution_event(append_spec)
        event_sql = mock_run.call_args.args[0]
        self.assertIn('INSERT INTO paa.methodology_execution_events', event_sql)
        self.assertIn("'advance'::paa.methodology_transition_kind", event_sql)

        with patch('paa_core.repositories.methodology_execution.postgres.run_psql', return_value='') as mock_run:
            repo.replace_methodology_execution_bindings(replace_spec)
        calls = [call.args[0] for call in mock_run.call_args_list]
        self.assertIn('DELETE FROM paa.methodology_execution_bindings', calls[0])
        self.assertIn("binding_kind IN ('implementation_plan')", calls[0])
        self.assertIn('INSERT INTO paa.methodology_execution_bindings', calls[1])


if __name__ == '__main__':
    unittest.main()

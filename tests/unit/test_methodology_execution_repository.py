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
        row_payload = {
            'methodology_execution_id': 'exec-1',
            'project_id': 'proj-1',
            'work_item_id': 'work-1',
            'lane': 'component_realization',
            'stage': 'slice_execution',
            'step': 'derive_next_activity_bundle',
            'status': 'active',
            'current_owner_role': 'architect',
            'next_action_key': 'implement-postgres',
            'blocked_reason': None,
            'component_id': 'component-1',
            'design_package_id': 'design-1',
            'implementation_plan_id': 'plan-1',
            'coder_run_brief_id': None,
            'packet_id': None,
            'workflow_state_id': 'workflow-1',
            'active_authority_ref': 'docs/spec.md',
            'active_artifact_ref': 'contracts.py',
            'metadata': {'priority': 'high'},
            'created_at': '2026-05-30T12:00:00+00:00',
            'updated_at': '2026-05-30T12:05:00+00:00',
        }
        with patch(
            'paa_core.repositories.methodology_execution.postgres.query_json_rows',
            return_value=[row_payload],
        ):
            row = repo.get_methodology_execution('exec-1')

        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row.lane, 'component_realization')
        self.assertEqual(row.metadata, {'priority': 'high'})

    def test_get_methodology_execution_returns_none_when_missing(self) -> None:
        repo = PostgresMethodologyExecutionRepository()
        with patch('paa_core.repositories.methodology_execution.postgres.query_json_rows', return_value=[]):
            row = repo.get_methodology_execution('missing-exec')

        self.assertIsNone(row)

    def test_find_methodology_execution_by_primary_ref_filters_component_anchor(self) -> None:
        repo = PostgresMethodologyExecutionRepository()
        with patch(
            'paa_core.repositories.methodology_execution.postgres.query_json_rows',
            return_value=[self._execution_row('exec-1')],
        ) as mock_query:
            row = repo.find_methodology_execution_by_primary_ref(
                '11111111-1111-1111-1111-111111111111',
                '22222222-2222-2222-2222-222222222222',
                '33333333-3333-3333-3333-333333333333',
            )

        self.assertIsNotNone(row)
        sql = mock_query.call_args.args[0]
        self.assertIn("me.component_id = '33333333-3333-3333-3333-333333333333'::uuid", sql)
        self.assertIn(
            'ORDER BY me.updated_at DESC, me.created_at DESC, me.methodology_execution_id DESC',
            sql,
        )
        self.assertIn('LIMIT 1', sql)

    def test_find_methodology_execution_by_primary_ref_supports_null_component_anchor(self) -> None:
        repo = PostgresMethodologyExecutionRepository()
        with patch(
            'paa_core.repositories.methodology_execution.postgres.query_json_rows',
            return_value=[self._execution_row('exec-1', component_id=None)],
        ) as mock_query:
            row = repo.find_methodology_execution_by_primary_ref(
                '11111111-1111-1111-1111-111111111111',
                '22222222-2222-2222-2222-222222222222',
                None,
            )

        self.assertIsNotNone(row)
        self.assertIn('me.component_id IS NULL', mock_query.call_args.args[0])

    def test_find_methodology_execution_by_primary_ref_returns_none_when_missing(self) -> None:
        repo = PostgresMethodologyExecutionRepository()
        with patch('paa_core.repositories.methodology_execution.postgres.query_json_rows', return_value=[]):
            row = repo.find_methodology_execution_by_primary_ref(
                '11111111-1111-1111-1111-111111111111',
                '22222222-2222-2222-2222-222222222222',
            )

        self.assertIsNone(row)

    def test_list_events_parse_history_rows_and_use_stable_ordering(self) -> None:
        repo = PostgresMethodologyExecutionRepository()
        event_rows = [
            {
                'methodology_execution_event_id': 'event-1',
                'methodology_execution_id': 'exec-1',
                'from_lane': 'design',
                'to_lane': 'component_realization',
                'from_stage': 'component_design',
                'to_stage': 'slice_execution',
                'from_step': 'author_component_spec',
                'to_step': 'materialize_component_spec',
                'from_status': 'active',
                'to_status': 'active',
                'transition_kind': 'manual_update',
                'actor_role_id': 'architect',
                'actor_name': 'Authority Architect',
                'notes': 'advance',
                'evidence': {'component_id': 'component-1'},
                'created_at': '2026-05-30T12:10:00+00:00',
            },
        ]
        with patch(
            'paa_core.repositories.methodology_execution.postgres.query_json_rows',
            return_value=event_rows,
        ) as mock_query:
            events = repo.list_methodology_execution_events('exec-1')

        self.assertEqual(events[0].transition_kind, 'manual_update')
        self.assertEqual(events[0].evidence, {'component_id': 'component-1'})
        self.assertIn(
            'ORDER BY mee.created_at, mee.methodology_execution_event_id',
            mock_query.call_args.args[0],
        )

    def test_list_bindings_parse_rows_and_use_stable_ordering(self) -> None:
        repo = PostgresMethodologyExecutionRepository()
        binding_rows = [
            {
                'methodology_execution_binding_id': 'binding-1',
                'methodology_execution_id': 'exec-1',
                'binding_kind': 'implementation_plan',
                'bound_record_id': 'plan-1',
                'bound_record_key': 'plan-materialize',
                'bound_record_ref': 'implementation_plan:plan-1',
                'is_primary': True,
                'notes': 'current plan',
                'metadata': {'source': 'materializer'},
                'created_at': '2026-05-30T12:10:00+00:00',
                'updated_at': '2026-05-30T12:11:00+00:00',
            },
        ]
        with patch(
            'paa_core.repositories.methodology_execution.postgres.query_json_rows',
            return_value=binding_rows,
        ) as mock_query:
            bindings = repo.list_methodology_execution_bindings('exec-1')

        self.assertTrue(bindings[0].is_primary)
        self.assertEqual(bindings[0].bound_record_ref, 'implementation_plan:plan-1')
        self.assertIn(
            'ORDER BY meb.is_primary DESC, meb.binding_kind, meb.created_at, meb.methodology_execution_binding_id',
            mock_query.call_args.args[0],
        )

    def test_load_projection_inputs_stitches_root_history_and_bindings(self) -> None:
        repo = PostgresMethodologyExecutionRepository()
        with (
            patch.object(repo, 'get_methodology_execution', return_value=self._execution_record()) as mock_get,
            patch.object(repo, 'list_methodology_execution_events', return_value=[self._event_record()]) as mock_events,
            patch.object(repo, 'list_methodology_execution_bindings', return_value=[self._binding_record()]) as mock_bindings,
        ):
            projection = repo.load_methodology_execution_projection_inputs('exec-1')

        self.assertEqual(projection.execution.methodology_execution_id, 'exec-1')
        self.assertEqual(len(projection.events), 1)
        self.assertEqual(projection.bindings[0].binding_kind, 'packet')
        self.assertEqual(projection.related_records, {})
        mock_get.assert_called_once_with('exec-1')
        mock_events.assert_called_once_with('exec-1')
        mock_bindings.assert_called_once_with('exec-1')

    def test_projection_inputs_fail_closed_when_execution_is_missing(self) -> None:
        repo = PostgresMethodologyExecutionRepository()
        with patch.object(repo, 'get_methodology_execution', return_value=None):
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

    def test_upsert_methodology_execution_preserves_null_optional_refs(self) -> None:
        repo = PostgresMethodologyExecutionRepository()
        spec = MethodologyExecutionUpsertSpec(
            methodology_execution_id='11111111-1111-1111-1111-111111111111',
            project_id='22222222-2222-2222-2222-222222222222',
            lane='component_realization',
            stage='slice_execution',
            step='implement_adapter',
            status='active',
            current_owner_role='architect',
        )
        with patch('paa_core.repositories.methodology_execution.postgres.run_psql', return_value='') as mock_run:
            repo.upsert_methodology_execution(spec)

        sql = mock_run.call_args.args[0]
        self.assertIn('NULL', sql)
        self.assertIn("'{}'::jsonb", sql)

    def test_append_methodology_execution_event_emits_expected_sql(self) -> None:
        repo = PostgresMethodologyExecutionRepository()
        append_spec = MethodologyExecutionEventAppendSpec(
            methodology_execution_id='11111111-1111-1111-1111-111111111111',
            to_lane='component_realization',
            to_stage='slice_execution',
            to_step='implement_adapter',
            to_status='active',
            transition_kind='manual_update',
            evidence={'component_id': 'component-1'},
        )
        with patch('paa_core.repositories.methodology_execution.postgres.run_psql', return_value='') as mock_run:
            repo.append_methodology_execution_event(append_spec)

        event_sql = mock_run.call_args.args[0]
        self.assertIn('INSERT INTO paa.methodology_execution_events', event_sql)
        self.assertIn("'manual_update'::paa.methodology_transition_kind", event_sql)

    def test_replace_bindings_replace_all_emits_delete_then_insert(self) -> None:
        repo = PostgresMethodologyExecutionRepository()
        replace_spec = MethodologyExecutionBindingReplaceSpec(
            methodology_execution_id='11111111-1111-1111-1111-111111111111',
            replace_scope='replace_all',
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
            repo.replace_methodology_execution_bindings(replace_spec)

        calls = [call.args[0] for call in mock_run.call_args_list]
        self.assertIn('DELETE FROM paa.methodology_execution_bindings', calls[0])
        self.assertIn('INSERT INTO paa.methodology_execution_bindings', calls[1])

    def test_replace_bindings_replace_kind_emits_scoped_delete_then_insert(self) -> None:
        repo = PostgresMethodologyExecutionRepository()
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
            repo.replace_methodology_execution_bindings(replace_spec)

        calls = [call.args[0] for call in mock_run.call_args_list]
        self.assertIn('DELETE FROM paa.methodology_execution_bindings', calls[0])
        self.assertIn("binding_kind IN ('implementation_plan')", calls[0])
        self.assertIn('INSERT INTO paa.methodology_execution_bindings', calls[1])

    def test_replace_bindings_rejects_unsupported_scope(self) -> None:
        repo = PostgresMethodologyExecutionRepository()
        replace_spec = MethodologyExecutionBindingReplaceSpec(
            methodology_execution_id='11111111-1111-1111-1111-111111111111',
            replace_scope='replace_unknown',
            bindings=(),
        )

        with self.assertRaises(ValueError):
            repo.replace_methodology_execution_bindings(replace_spec)

    def _execution_row(self, methodology_execution_id: str, *, component_id: str | None = 'component-1') -> dict[str, object]:
        return {
            'methodology_execution_id': methodology_execution_id,
            'project_id': 'proj-1',
            'work_item_id': 'work-1',
            'lane': 'runtime_execution',
            'stage': 'qa_verification',
            'step': 'await_result',
            'status': 'active',
            'current_owner_role': 'qa',
            'next_action_key': 'qa-review',
            'blocked_reason': None,
            'component_id': component_id,
            'design_package_id': None,
            'implementation_plan_id': None,
            'coder_run_brief_id': 'brief-1',
            'packet_id': 'packet-1',
            'workflow_state_id': 'workflow-1',
            'active_authority_ref': None,
            'active_artifact_ref': None,
            'metadata': {},
            'created_at': None,
            'updated_at': None,
        }

    def _execution_record(self):
        return PostgresMethodologyExecutionRepository()._execution_from_row(self._execution_row('exec-1'))

    def _event_record(self):
        return PostgresMethodologyExecutionRepository()._event_from_row(
            {
                'methodology_execution_event_id': 'event-1',
                'methodology_execution_id': 'exec-1',
                'from_lane': None,
                'to_lane': 'runtime_execution',
                'from_stage': None,
                'to_stage': 'qa_verification',
                'from_step': None,
                'to_step': 'await_result',
                'from_status': None,
                'to_status': 'active',
                'transition_kind': 'manual_update',
                'actor_role_id': None,
                'actor_name': None,
                'notes': None,
                'evidence': {},
                'created_at': None,
            }
        )

    def _binding_record(self):
        return PostgresMethodologyExecutionRepository()._binding_from_row(
            {
                'methodology_execution_binding_id': 'binding-1',
                'methodology_execution_id': 'exec-1',
                'binding_kind': 'packet',
                'bound_record_id': 'packet-1',
                'bound_record_key': None,
                'bound_record_ref': 'packet:packet-1',
                'is_primary': True,
                'notes': None,
                'metadata': {},
                'created_at': None,
                'updated_at': None,
            }
        )


if __name__ == '__main__':
    unittest.main()

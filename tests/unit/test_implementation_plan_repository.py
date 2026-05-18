from __future__ import annotations

import sys
from pathlib import Path
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'packages' / 'paa-core' / 'src'))

from paa_core.repositories.implementation_plan import (
    ImplementationPlanActivityDependencyUpsertSpec,
    ImplementationPlanActivityUpsertSpec,
    ImplementationPlanUpsertSpec,
    PostgresImplementationPlanRepository,
)


class ImplementationPlanRepositoryTests(unittest.TestCase):
    def test_get_implementation_plan_by_external_parses_root(self) -> None:
        repo = PostgresImplementationPlanRepository()
        output = '{"implementation_plan_id":"plan-1","project_id":"proj-1","work_item_id":"work-1","design_package_id":"pkg-1","spec_fragment_id":"frag-1","implementation_target_id":"target-1","authority_version_id":"auth-1","primary_component_id":"comp-1","plan_id_external":"impl-plan-1","schema_version":"1.0","consumer_context_key":"python","plan_title":"Implementation Plan","plan_kind":"service_slice","status":"draft","authority_state":"draft_plan","authority_state_updated_at":"2026-05-17T12:00:00+00:00","plan":{"scope":"repo"},"build_sequence":{"activities":["a1"]},"touch_surfaces":{"modules":["postgres.py"]},"protected_constraints":{"forbid":["workflow"]},"verification_plan":{"required":["unit"]},"provenance":{"source":"design-package"},"metadata":{"proof":true},"created_by_role_id":"role-1","created_by_agent_id":"agent-1","approved_at":null,"activated_at":null,"completed_at":null,"created_at":"2026-05-17T12:00:00+00:00","updated_at":"2026-05-17T12:05:00+00:00"}'
        with patch('paa_core.repositories.implementation_plan.postgres.run_psql', return_value=output):
            row = repo.get_implementation_plan_by_external('proj-1', 'impl-plan-1')

        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row.plan_id_external, 'impl-plan-1')
        self.assertEqual(row.consumer_context_key, 'python')
        self.assertEqual(row.plan, {'scope': 'repo'})
        self.assertEqual(row.metadata, {'proof': True})

    def test_list_implementation_plan_activities_parses_sequence(self) -> None:
        repo = PostgresImplementationPlanRepository()
        output = '\n'.join(
            [
                '{"implementation_plan_activity_id":"a1","implementation_plan_id":"plan-1","component_element_id":"ce-1","component_element_realization_id":null,"assigned_role_id":"role-1","activity_key":"define-interface","activity_title":"Define interface","activity_kind":"design_contract","activity_state":"planned","sequence_order":1,"target_path":"packages/paa-core/src/.../contracts.py","target_module":"contracts.py","planned_artifact_type_key":"repository_interface","blocking_reason":null,"metadata":{"component":"ImplementationPlanRepository"},"started_at":null,"completed_at":null,"created_at":"2026-05-17T12:00:00+00:00","updated_at":"2026-05-17T12:00:00+00:00"}',
                '{"implementation_plan_activity_id":"a2","implementation_plan_id":"plan-1","component_element_id":"ce-2","component_element_realization_id":"cer-2","assigned_role_id":"role-1","activity_key":"implement-postgres","activity_title":"Implement Postgres repository","activity_kind":"implement_artifact","activity_state":"planned","sequence_order":2,"target_path":"packages/paa-core/src/.../postgres.py","target_module":"postgres.py","planned_artifact_type_key":"concrete_repository_class","blocking_reason":"await interface","metadata":{},"started_at":null,"completed_at":null,"created_at":"2026-05-17T12:00:00+00:00","updated_at":"2026-05-17T12:00:00+00:00"}',
            ]
        )
        with patch('paa_core.repositories.implementation_plan.postgres.run_psql', return_value=output):
            rows = repo.list_implementation_plan_activities('plan-1')

        self.assertEqual([row.activity_key for row in rows], ['define-interface', 'implement-postgres'])
        self.assertEqual(rows[1].planned_artifact_type_key, 'concrete_repository_class')
        self.assertEqual(rows[1].blocking_reason, 'await interface')

    def test_list_activity_dependencies_parses_keys(self) -> None:
        repo = PostgresImplementationPlanRepository()
        output = '{"implementation_plan_activity_dependency_id":"d1","implementation_plan_id":"plan-1","predecessor_activity_id":"a1","predecessor_activity_key":"define-interface","successor_activity_id":"a2","successor_activity_key":"implement-postgres","sequencing_requirement":"hard","dependency_strength":"required","notes":"Implementation follows interface","metadata":{"phase":"first-slice"},"created_at":"2026-05-17T12:00:00+00:00"}'
        with patch('paa_core.repositories.implementation_plan.postgres.run_psql', return_value=output):
            rows = repo.list_implementation_plan_activity_dependencies('plan-1')

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].predecessor_activity_key, 'define-interface')
        self.assertEqual(rows[0].successor_activity_key, 'implement-postgres')
        self.assertEqual(rows[0].metadata, {'phase': 'first-slice'})

    def test_list_verification_surfaces_parses_required_flag(self) -> None:
        repo = PostgresImplementationPlanRepository()
        output = '{"implementation_plan_verification_surface_id":"vs1","implementation_plan_id":"plan-1","implementation_plan_activity_id":"a2","verification_obligation_id":"vo1","surface_kind":"unit_test","surface_ref":"tests/unit/test_implementation_plan_repository.py","required":true,"sequence_order":10,"status":"planned","metadata":{"scope":"repository"},"created_at":"2026-05-17T12:00:00+00:00","updated_at":"2026-05-17T12:00:00+00:00"}'
        with patch('paa_core.repositories.implementation_plan.postgres.run_psql', return_value=output):
            rows = repo.list_implementation_plan_verification_surfaces('plan-1')

        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0].required)
        self.assertEqual(rows[0].surface_ref, 'tests/unit/test_implementation_plan_repository.py')

    def test_upsert_implementation_plan_emits_upsert_sql(self) -> None:
        repo = PostgresImplementationPlanRepository()
        spec = ImplementationPlanUpsertSpec(
            project_id='11111111-1111-1111-1111-111111111111',
            work_item_id='22222222-2222-2222-2222-222222222222',
            design_package_id='33333333-3333-3333-3333-333333333333',
            spec_fragment_id='44444444-4444-4444-4444-444444444444',
            implementation_target_id='55555555-5555-5555-5555-555555555555',
            authority_version_id='66666666-6666-6666-6666-666666666666',
            primary_component_id='77777777-7777-7777-7777-777777777777',
            plan_id_external='impl-plan-1',
            consumer_context_key='python',
            plan_title='Implementation Plan Repository First Slice',
            plan_kind='repository_slice',
            plan={'component': 'ImplementationPlanRepository'},
            build_sequence={'activities': ['define-interface', 'implement-postgres']},
        )
        with patch('paa_core.repositories.implementation_plan.postgres.run_psql', return_value='') as mock_run:
            repo.upsert_implementation_plan(spec)

        sql = mock_run.call_args.args[0]
        self.assertIn('INSERT INTO paa.implementation_plans', sql)
        self.assertIn('impl-plan-1', sql)
        self.assertIn('ON CONFLICT (design_package_id, consumer_context_key) DO UPDATE', sql)
        self.assertIn('authority_state_updated_at = now()', sql)

    def test_upsert_implementation_plan_activity_emits_upsert_sql(self) -> None:
        repo = PostgresImplementationPlanRepository()
        spec = ImplementationPlanActivityUpsertSpec(
            implementation_plan_id='11111111-1111-1111-1111-111111111111',
            component_element_id='22222222-2222-2222-2222-222222222222',
            component_element_realization_id='33333333-3333-3333-3333-333333333333',
            assigned_role_id='44444444-4444-4444-4444-444444444444',
            activity_key='implement-postgres',
            activity_title='Implement Postgres repository class',
            activity_kind='implement_artifact',
            activity_state='planned',
            sequence_order=3,
            target_path='packages/paa-core/src/paa_core/repositories/implementation_plan/postgres.py',
            target_module='postgres.py',
            planned_artifact_type_key='concrete_repository_class',
            blocking_reason='await interface and dto',
            metadata={'component': 'ImplementationPlanRepository'},
        )
        with patch('paa_core.repositories.implementation_plan.postgres.run_psql', return_value='') as mock_run:
            repo.upsert_implementation_plan_activity(spec)

        sql = mock_run.call_args.args[0]
        self.assertIn('INSERT INTO paa.implementation_plan_activities', sql)
        self.assertIn('implement-postgres', sql)
        self.assertIn('concrete_repository_class', sql)
        self.assertIn('ON CONFLICT (implementation_plan_id, activity_key) DO UPDATE', sql)

    def test_upsert_implementation_plan_activity_dependency_uses_activity_keys(self) -> None:
        repo = PostgresImplementationPlanRepository()
        spec = ImplementationPlanActivityDependencyUpsertSpec(
            implementation_plan_id='11111111-1111-1111-1111-111111111111',
            predecessor_activity_key='define-interface',
            successor_activity_key='implement-postgres',
            sequencing_requirement='hard',
            dependency_strength='required',
            notes='Implementation waits on interface',
            metadata={'bridge': 'component-elements->targets'},
        )
        with patch('paa_core.repositories.implementation_plan.postgres.run_psql', return_value='') as mock_run:
            repo.upsert_implementation_plan_activity_dependency(spec)

        sql = mock_run.call_args.args[0]
        self.assertIn('INSERT INTO paa.implementation_plan_activity_dependencies', sql)
        self.assertIn("pred.activity_key = 'define-interface'", sql)
        self.assertIn("succ.activity_key = 'implement-postgres'", sql)
        self.assertIn('ON CONFLICT (implementation_plan_id, predecessor_activity_id, successor_activity_id) DO UPDATE', sql)


if __name__ == '__main__':
    unittest.main()

from __future__ import annotations

import sys
from pathlib import Path
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'packages' / 'paa-core' / 'src'))

from paa_core.repositories.component_design import (
    BriefRealizationTargetUpsertSpec,
    ComponentElementUpsertSpec,
    ComponentElementRealizationUpsertSpec,
    ElementTypeRealizationLinkSpec,
    PostgresComponentDesignRepository,
    RealizationTypeUpsertSpec,
)


class ComponentDesignRepositoryTests(unittest.TestCase):
    def test_get_component_by_id_parses_row(self) -> None:
        repo = PostgresComponentDesignRepository()
        output = '{"component_id":"1","project_id":"p","name":"Component Design Planning Service","role":"planner","system_layer":"domain-services","tier":"runtime","description":"desc","status":"active","metadata":{"x":1}}'
        with patch('paa_core.repositories.component_design.postgres.run_psql', return_value=output):
            row = repo.get_component_by_id('1')

        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row.name, 'Component Design Planning Service')
        self.assertEqual(row.metadata, {'x': 1})

    def test_get_component_element_by_id_parses_row(self) -> None:
        repo = PostgresComponentDesignRepository()
        output = '{"component_element_id":"e1","project_id":"p","component_id":"c","component_element_type_id":"t","element_key":"interfaces","title":"Service Interfaces","status":"active","definition":{"module":"contracts.py"},"provenance":{},"metadata":{"x":1}}'
        with patch('paa_core.repositories.component_design.postgres.run_psql', return_value=output):
            row = repo.get_component_element_by_id('e1')

        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row.element_key, 'interfaces')
        self.assertEqual(row.definition, {'module': 'contracts.py'})

    def test_list_component_element_types_parses_rows(self) -> None:
        repo = PostgresComponentDesignRepository()
        output = '\n'.join(
            [
                '{"component_element_type_id":"1","element_key":"interfaces","label":"Interfaces","category":"dependency","description":"desc","is_brief_targetable":true,"is_multi_instance":true,"sort_order":60,"metadata":{}}',
                '{"component_element_type_id":"2","element_key":"functions","label":"Functions","category":"behavior","description":null,"is_brief_targetable":true,"is_multi_instance":true,"sort_order":70,"metadata":{"x":1}}',
            ]
        )
        with patch('paa_core.repositories.component_design.postgres.run_psql', return_value=output):
            rows = repo.list_component_element_types()

        self.assertEqual([row.element_key for row in rows], ['interfaces', 'functions'])
        self.assertEqual(rows[1].metadata, {'x': 1})

    def test_list_realization_types_for_element_type_parses_flags(self) -> None:
        repo = PostgresComponentDesignRepository()
        output = '{"component_element_realization_type_id":"10","realization_key":"repository_interface","label":"Repository Interface","category":"code_artifact","description":"desc","is_brief_targetable":true,"is_multi_instance":false,"sort_order":10,"metadata":{},"is_default_for_element_type":true,"element_type_sort_order":5}'
        with patch('paa_core.repositories.component_design.postgres.run_psql', return_value=output):
            rows = repo.list_realization_types_for_element_type('interfaces')

        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0].is_default_for_element_type)
        self.assertEqual(rows[0].realization_key, 'repository_interface')

    def test_list_brief_realization_targets_keeps_sequence(self) -> None:
        repo = PostgresComponentDesignRepository()
        output = '\n'.join(
            [
                '{"coder_brief_realization_target_id":"a","project_id":"p","work_item_id":"w","coder_run_brief_id":"b","component_id":"c","component_element_id":"e1","component_element_realization_id":"r1","depends_on_target_id":null,"target_intent":"implement","sequence_order":1,"is_required":true,"target_notes":"first","target_contract":{},"metadata":{}}',
                '{"coder_brief_realization_target_id":"b","project_id":"p","work_item_id":"w","coder_run_brief_id":"b","component_id":"c","component_element_id":"e2","component_element_realization_id":"r2","depends_on_target_id":"a","target_intent":"implement","sequence_order":2,"is_required":true,"target_notes":"second","target_contract":{},"metadata":{}}',
            ]
        )
        with patch('paa_core.repositories.component_design.postgres.run_psql', return_value=output):
            rows = repo.list_brief_realization_targets('b')

        self.assertEqual([row.sequence_order for row in rows], [1, 2])
        self.assertEqual(rows[1].depends_on_target_id, 'a')

    def test_upsert_realization_type_emits_upsert_sql(self) -> None:
        repo = PostgresComponentDesignRepository()
        spec = RealizationTypeUpsertSpec(
            realization_key='repository_interface',
            label='Repository Interface',
            category='code_artifact',
            description='Repository interface contract',
            is_brief_targetable=True,
            is_multi_instance=False,
            sort_order=10,
            metadata={'scope': 'dal'},
        )
        with patch('paa_core.repositories.component_design.postgres.run_psql', return_value='') as mock_run:
            repo.upsert_realization_type(spec)

        sql = mock_run.call_args.args[0]
        self.assertIn('INSERT INTO paa.component_element_realization_types', sql)
        self.assertIn('repository_interface', sql)
        self.assertIn('ON CONFLICT (realization_key) DO UPDATE', sql)

    def test_upsert_element_type_realization_link_emits_mapping_sql(self) -> None:
        repo = PostgresComponentDesignRepository()
        spec = ElementTypeRealizationLinkSpec(
            element_type_key='interfaces',
            realization_key='repository_interface',
            is_default=True,
            sort_order=10,
        )
        with patch('paa_core.repositories.component_design.postgres.run_psql', return_value='') as mock_run:
            repo.upsert_element_type_realization_link(spec)

        sql = mock_run.call_args.args[0]
        self.assertIn('INSERT INTO paa.component_element_type_realization_types', sql)
        self.assertIn("WHERE cet.element_key = 'interfaces'", sql)
        self.assertIn("cert.realization_key = 'repository_interface'", sql)

    def test_upsert_component_element_realization_emits_upsert_sql(self) -> None:
        repo = PostgresComponentDesignRepository()
        spec = ComponentElementRealizationUpsertSpec(
            project_id='11111111-1111-1111-1111-111111111111',
            component_id='22222222-2222-2222-2222-222222222222',
            component_element_id='33333333-3333-3333-3333-333333333333',
            realization_type_key='concrete_repository_class',
            realization_key='postgres_workflow_state_repository',
            title='Postgres Workflow State Repository',
            status='active',
            sequence_order=2,
            definition={'ops': ['get', 'list']},
            artifact_ref={'module': 'postgres.py'},
        )
        with patch('paa_core.repositories.component_design.postgres.run_psql', return_value='') as mock_run:
            repo.upsert_component_element_realization(spec)

        sql = mock_run.call_args.args[0]
        self.assertIn('INSERT INTO paa.component_element_realizations', sql)
        self.assertIn('postgres_workflow_state_repository', sql)
        self.assertIn("WHERE cert.realization_key = 'concrete_repository_class'", sql)
        self.assertIn('ON CONFLICT (component_element_id, component_element_realization_type_id, realization_key) DO UPDATE', sql)

    def test_upsert_component_element_emits_upsert_sql(self) -> None:
        repo = PostgresComponentDesignRepository()
        spec = ComponentElementUpsertSpec(
            project_id='11111111-1111-1111-1111-111111111111',
            component_id='22222222-2222-2222-2222-222222222222',
            element_type_key='interfaces',
            element_key='interfaces',
            title='Service Interfaces',
            status='active',
            definition={'modules': ['contracts.py']},
        )
        with patch('paa_core.repositories.component_design.postgres.run_psql', return_value='') as mock_run:
            repo.upsert_component_element(spec)

        sql = mock_run.call_args.args[0]
        self.assertIn('INSERT INTO paa.component_elements', sql)
        self.assertIn("WHERE cet.element_key = 'interfaces'", sql)
        self.assertIn('ON CONFLICT (component_id, component_element_type_id, element_key) DO UPDATE', sql)

    def test_upsert_brief_realization_target_emits_upsert_sql(self) -> None:
        repo = PostgresComponentDesignRepository()
        spec = BriefRealizationTargetUpsertSpec(
            project_id='11111111-1111-1111-1111-111111111111',
            work_item_id='22222222-2222-2222-2222-222222222222',
            coder_run_brief_id='33333333-3333-3333-3333-333333333333',
            component_id='44444444-4444-4444-4444-444444444444',
            component_element_id='55555555-5555-5555-5555-555555555555',
            component_element_realization_id='66666666-6666-6666-6666-666666666666',
            depends_on_target_id='77777777-7777-7777-7777-777777777777',
            target_intent='implement',
            sequence_order=2,
            is_required=True,
            target_notes='Implement after interface',
            target_contract={'required_methods': ['get_component_by_name']},
        )
        with patch('paa_core.repositories.component_design.postgres.run_psql', return_value='') as mock_run:
            repo.upsert_brief_realization_target(spec)

        sql = mock_run.call_args.args[0]
        self.assertIn('INSERT INTO paa.coder_brief_realization_targets', sql)
        self.assertIn('required_methods', sql)
        self.assertIn('ON CONFLICT (coder_run_brief_id, component_element_realization_id, target_intent) DO UPDATE', sql)


if __name__ == '__main__':
    unittest.main()

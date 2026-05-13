from __future__ import annotations

import sys
from pathlib import Path
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'packages' / 'paa-core' / 'src'))

from paa_core.repositories.component_design import PostgresComponentDesignRepository


class ComponentDesignRepositoryTests(unittest.TestCase):
    def test_list_component_element_types_parses_rows(self) -> None:
        repo = PostgresComponentDesignRepository()
        output = '\n'.join(
            [
                '{"component_element_type_id":"1","element_key":"interfaces","label":"Interfaces","category":"dependency","description":"desc","is_brief_targetable":true,"is_multi_instance":true,"sort_order":60,"metadata":{}}',
                '{"component_element_type_id":"2","element_key":"functions","label":"Functions","category":"behavior","description":null,"is_brief_targetable":true,"is_multi_instance":true,"sort_order":70,"metadata":{"x":1}}',
            ]
        )
        with patch('paa_core.repositories.component_design.run_psql', return_value=output):
            rows = repo.list_component_element_types()

        self.assertEqual([row.element_key for row in rows], ['interfaces', 'functions'])
        self.assertEqual(rows[1].metadata, {'x': 1})

    def test_list_realization_types_for_element_type_parses_flags(self) -> None:
        repo = PostgresComponentDesignRepository()
        output = '{"component_element_realization_type_id":"10","realization_key":"repository_interface","label":"Repository Interface","category":"code_artifact","description":"desc","is_brief_targetable":true,"is_multi_instance":false,"sort_order":10,"metadata":{},"is_default_for_element_type":true,"element_type_sort_order":5}'
        with patch('paa_core.repositories.component_design.run_psql', return_value=output):
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
        with patch('paa_core.repositories.component_design.run_psql', return_value=output):
            rows = repo.list_brief_realization_targets('b')

        self.assertEqual([row.sequence_order for row in rows], [1, 2])
        self.assertEqual(rows[1].depends_on_target_id, 'a')


if __name__ == '__main__':
    unittest.main()

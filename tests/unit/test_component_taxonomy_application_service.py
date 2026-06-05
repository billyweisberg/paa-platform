from __future__ import annotations

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'packages' / 'paa-core' / 'src'))

from paa_core.application.dto.component_taxonomy import (
    GetRealizationTypeRequest,
    ListRealizationTypesRequest,
    UpsertRealizationTypeRequest,
)
from paa_core.application.services.component_taxonomy import DefaultComponentTaxonomyApplicationService
from paa_core.repositories.component_design import (
    ComponentElementRealizationTypeRecord,
    RealizationTypeUpsertSpec,
)


class InMemoryComponentDesignRepository:
    def __init__(self) -> None:
        self._rows = {
            'repository_interface': ComponentElementRealizationTypeRecord(
                component_element_realization_type_id='10',
                realization_key='repository_interface',
                label='Repository Interface',
                category='code_artifact',
                description='Repository contract',
                is_brief_targetable=True,
                is_multi_instance=False,
                sort_order=10,
                metadata={'scope': 'dal'},
                is_default_for_element_type=False,
                element_type_sort_order=0,
            ),
            'service_implementation': ComponentElementRealizationTypeRecord(
                component_element_realization_type_id='11',
                realization_key='service_implementation',
                label='Service Implementation',
                category='code_artifact',
                description=None,
                is_brief_targetable=True,
                is_multi_instance=True,
                sort_order=20,
                metadata={},
                is_default_for_element_type=False,
                element_type_sort_order=0,
            ),
        }
        self.last_upsert: RealizationTypeUpsertSpec | None = None

    def list_realization_types(self) -> list[ComponentElementRealizationTypeRecord]:
        return list(self._rows.values())

    def get_realization_type_by_key(self, realization_key: str) -> ComponentElementRealizationTypeRecord | None:
        return self._rows.get(realization_key)

    def upsert_realization_type(self, spec: RealizationTypeUpsertSpec) -> None:
        self.last_upsert = spec
        self._rows[spec.realization_key] = ComponentElementRealizationTypeRecord(
            component_element_realization_type_id='99',
            realization_key=spec.realization_key,
            label=spec.label,
            category=spec.category,
            description=spec.description,
            is_brief_targetable=spec.is_brief_targetable,
            is_multi_instance=spec.is_multi_instance,
            sort_order=spec.sort_order,
            metadata=spec.metadata or {},
            is_default_for_element_type=False,
            element_type_sort_order=0,
        )


class ComponentTaxonomyApplicationServiceTests(unittest.TestCase):
    def test_list_realization_types_returns_stable_payload(self) -> None:
        repo = InMemoryComponentDesignRepository()
        service = DefaultComponentTaxonomyApplicationService(repository=repo)

        result = service.list_realization_types(ListRealizationTypesRequest())

        self.assertEqual(result.exit_code, 0)
        self.assertTrue(result.payload['ok'])
        self.assertEqual(result.payload['count'], 2)
        self.assertEqual(
            [item['realization_key'] for item in result.payload['items']],
            ['repository_interface', 'service_implementation'],
        )
        self.assertEqual(result.payload['items'][0]['metadata'], {'scope': 'dal'})
        self.assertIn('is_default_for_element_type', result.payload['items'][0])
        self.assertIn('element_type_sort_order', result.payload['items'][0])

    def test_get_realization_type_returns_not_found_payload_when_missing(self) -> None:
        repo = InMemoryComponentDesignRepository()
        service = DefaultComponentTaxonomyApplicationService(repository=repo)

        result = service.get_realization_type(GetRealizationTypeRequest(realization_key='missing_type'))

        self.assertEqual(result.exit_code, 1)
        self.assertFalse(result.payload['ok'])
        self.assertEqual(result.payload['code'], 'realization_type_not_found')
        self.assertEqual(result.payload['realization_key'], 'missing_type')

    def test_upsert_realization_type_converts_request_to_repository_spec(self) -> None:
        repo = InMemoryComponentDesignRepository()
        service = DefaultComponentTaxonomyApplicationService(repository=repo)

        result = service.upsert_realization_type(
            UpsertRealizationTypeRequest(
                realization_key='module_operation_surface',
                label='Module Operation Surface',
                category='python_artifact',
                description='Function-style module surface',
                is_brief_targetable=True,
                is_multi_instance=False,
                sort_order=30,
                metadata={'language': 'python'},
            )
        )

        self.assertEqual(result.exit_code, 0)
        self.assertTrue(result.payload['ok'])
        self.assertEqual(result.payload['realization_key'], 'module_operation_surface')
        self.assertEqual(result.payload['action'], 'upserted')
        self.assertIsNotNone(repo.last_upsert)
        assert repo.last_upsert is not None
        self.assertEqual(repo.last_upsert.realization_key, 'module_operation_surface')
        self.assertEqual(repo.last_upsert.category, 'python_artifact')
        self.assertEqual(repo.last_upsert.metadata, {'language': 'python'})

        lookup = service.get_realization_type(GetRealizationTypeRequest(realization_key='module_operation_surface'))
        self.assertTrue(lookup.payload['ok'])
        self.assertEqual(lookup.payload['item']['label'], 'Module Operation Surface')


if __name__ == '__main__':
    unittest.main()

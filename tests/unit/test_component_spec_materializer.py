from __future__ import annotations

import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path
import unittest
from unittest.mock import patch

REPO_ROOT = Path('/Users/billyweisberg/Repos/billyweisberg/paa-platform')
sys.path.insert(0, str(REPO_ROOT / 'packages' / 'paa-core' / 'src'))
sys.path.insert(0, str(REPO_ROOT / 'packages' / 'paa-producer' / 'src'))

from paa_producer.__main__ import main
from paa_producer.component_spec_materializer import materialize_component_spec


class ComponentSpecMaterializerTests(unittest.TestCase):
    def test_materialize_component_spec_returns_result_payload(self) -> None:
        fake_result = type('Result', (), {
            'source_path': 'spec.md',
            'project_id': 'project-1',
            'design_package_id': 'pkg-1',
            'component_id': 'component-1',
            'implementation_plan_id': 'plan-1',
            'plan_id_external': 'plan-ext',
            'consumer_context_key': 'python',
            'component_element_keys': ('a',),
            'realization_keys': ('r',),
            'activity_keys': ('k',),
        })()
        with patch('paa_producer.component_spec_materializer.extract_component_spec_materialization_seed') as mock_extract, \
             patch('paa_producer.component_spec_materializer._query_scalar', side_effect=['project-1', 'pkg-1', 'component-1']) as mock_scalar, \
             patch('paa_producer.component_spec_materializer._anchor_plan') as mock_anchor, \
             patch('paa_producer.component_spec_materializer._query_optional_scalar', return_value=None), \
             patch('paa_producer.component_spec_materializer._element_id', return_value='element-1'), \
             patch('paa_producer.component_spec_materializer._realization_id', return_value='realization-1'), \
             patch('paa_producer.component_spec_materializer.PostgresImplementationPlanRepository') as mock_plan_repo_cls, \
             patch('paa_producer.component_spec_materializer.PostgresComponentDesignRepository'):
            mock_extract.return_value = type('Seed', (), {
                'source_path': 'spec.md',
                'component_identity': type('Identity', (), {'component_name': 'Comp', 'system_layer': 'application-services', 'tier': 'runtime', 'status': 'active'})(),
                'component_elements': (type('Element', (), {'element_name': 'assignment_decision_interface', 'element_kind': 'interface', 'description': 'd', 'owned_by_component': 'Comp'})(),),
                'realizations': (type('Realization', (), {'element_name': 'assignment_decision_interface', 'realization_kind': 'service_interface', 'artifact_kind': 'python-module', 'artifact_target': 'contracts.py', 'verification_role': 'v', 'realization_key': 'rk'})(),),
                'plan_seed': type('PlanSeed', (), {'plan_name': 'plan-ext', 'consumer_context_key': 'python', 'plan_status': 'draft_plan'})(),
                'activity_seeds': (type('Activity', (), {'activity_key': 'a1', 'activity_name': 'A1', 'sequence': 10, 'activity_kind': 'contract-authoring', 'element_name': 'assignment_decision_interface', 'realization_kind': 'service_interface', 'done_definition': 'done'})(),),
                'activity_dependencies': (),
                'verification_surfaces': (),
            })()
            mock_anchor.return_value = type('PlanRecord', (), {
                'implementation_plan_id': 'anchor-plan',
                'work_item_id': 'work-1',
                'spec_fragment_id': 'spec-1',
                'implementation_target_id': 'target-1',
                'authority_version_id': 'auth-1',
            })()
            mock_plan_repo = mock_plan_repo_cls.return_value
            mock_plan_repo.get_implementation_plan_for_design_package.return_value = type('PlanRecord', (), {
                'implementation_plan_id': 'plan-1',
                'plan_id_external': 'plan-ext',
                'consumer_context_key': 'python',
            })()
            result = materialize_component_spec(spec_path=Path('spec.md'))

        self.assertEqual(result.implementation_plan_id, 'plan-1')
        self.assertEqual(result.plan_id_external, 'plan-ext')
        self.assertEqual(mock_scalar.call_count >= 2, True)

    def test_cli_materialize_component_spec_outputs_json(self) -> None:
        stdout = io.StringIO()
        old_argv = sys.argv
        sys.argv = ['paa-producer', 'materialize-component-spec', '--spec', '/tmp/spec.md']
        try:
            with patch('paa_producer.__main__.materialize_component_spec') as mock_materialize:
                mock_materialize.return_value = type('Result', (), {
                    'source_path': 'spec.md',
                    'project_id': 'project-1',
                    'design_package_id': 'pkg-1',
                    'component_id': 'component-1',
                    'implementation_plan_id': 'plan-1',
                    'plan_id_external': 'plan-ext',
                    'consumer_context_key': 'python',
                    'component_element_keys': ('a',),
                    'realization_keys': ('r',),
                    'activity_keys': ('k',),
                })()
                with redirect_stdout(stdout):
                    exit_code = main()
        finally:
            sys.argv = old_argv
        self.assertEqual(exit_code, 0)
        self.assertEqual(json.loads(stdout.getvalue())['implementation_plan_id'], 'plan-1')


if __name__ == '__main__':
    unittest.main()

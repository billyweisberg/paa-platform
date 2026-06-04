from __future__ import annotations

import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

REPO_ROOT = Path('/Users/billyweisberg/Repos/billyweisberg/paa-platform')
sys.path.insert(0, str(REPO_ROOT / 'packages' / 'paa-core' / 'src'))
sys.path.insert(0, str(REPO_ROOT / 'packages' / 'paa-cli' / 'src'))

from paa_cli.app import _run_producer_command
from paa_core.application.dto.producer import ProducerOperationResult
from paa_core.producer.component_spec_materializer import materialize_component_spec


class ComponentSpecMaterializerTests(unittest.TestCase):
    def test_materialize_component_spec_returns_result_payload(self) -> None:
        with patch('paa_core.producer.component_spec_materializer.extract_component_spec_materialization_seed') as mock_extract, \
             patch('paa_core.producer.component_spec_materializer._query_scalar', side_effect=['project-1', 'pkg-1']) as mock_scalar, \
             patch('paa_core.producer.component_spec_materializer._anchor_plan') as mock_anchor, \
             patch('paa_core.producer.component_spec_materializer._ensure_component_row', return_value='component-1'), \
             patch('paa_core.producer.component_spec_materializer._query_optional_scalar', return_value=None), \
             patch('paa_core.producer.component_spec_materializer._element_id', return_value='element-1'), \
             patch('paa_core.producer.component_spec_materializer._realization_id', return_value='realization-1'), \
             patch('paa_core.producer.component_spec_materializer.PostgresImplementationPlanRepository') as mock_plan_repo_cls, \
             patch('paa_core.producer.component_spec_materializer.PostgresComponentDesignRepository'):
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
            mock_plan_repo.get_implementation_plan_for_design_package.return_value = None
            mock_plan_repo.get_implementation_plan_by_external.return_value = type('PlanRecord', (), {
                'implementation_plan_id': 'plan-1',
                'plan_id_external': 'plan-ext',
                'consumer_context_key': 'python',
            })()
            result = materialize_component_spec(spec_path=Path('spec.md'))

        self.assertEqual(result.implementation_plan_id, 'plan-1')
        self.assertEqual(result.plan_id_external, 'plan-ext')
        self.assertTrue(mock_scalar.call_count >= 2)

    def test_materialize_component_spec_fails_closed_on_consumer_context_collision(self) -> None:
        with patch('paa_core.producer.component_spec_materializer.extract_component_spec_materialization_seed') as mock_extract, \
             patch('paa_core.producer.component_spec_materializer._query_scalar', side_effect=['project-1', 'pkg-1']), \
             patch('paa_core.producer.component_spec_materializer._anchor_plan') as mock_anchor, \
             patch('paa_core.producer.component_spec_materializer._ensure_component_row', return_value='component-1'), \
             patch('paa_core.producer.component_spec_materializer.PostgresImplementationPlanRepository') as mock_plan_repo_cls, \
             patch('paa_core.producer.component_spec_materializer.PostgresComponentDesignRepository'):
            mock_extract.return_value = type('Seed', (), {
                'source_path': 'spec.md',
                'component_identity': type('Identity', (), {'component_name': 'QueueClaimRuntimeService', 'system_layer': 'application-services', 'tier': 'runtime', 'status': 'active'})(),
                'component_elements': (),
                'realizations': (),
                'plan_seed': type('PlanSeed', (), {'plan_name': 'plan-materialize-queue-claim-runtime-service-proof-python', 'consumer_context_key': 'governance-materialization-python-queue-runtime', 'plan_status': 'draft_plan'})(),
                'activity_seeds': (),
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
                'implementation_plan_id': 'plan-old',
                'plan_id_external': 'plan-materialize-queue-packet-runtime-controller-proof-python',
                'primary_component_id': 'different-component',
            })()

            with self.assertRaisesRegex(RuntimeError, 'consumer_context_key collision'):
                materialize_component_spec(spec_path=Path('spec.md'))

    def test_cli_materialize_component_spec_outputs_json(self) -> None:
        stdout = io.StringIO()
        fake_client = Mock()
        fake_client.materialize_component_spec.return_value = ProducerOperationResult(
            payload={
                'source_path': 'spec.md',
                'project_id': 'project-1',
                'design_package_id': 'pkg-1',
                'component_id': 'component-1',
                'implementation_plan_id': 'plan-1',
                'plan_id_external': 'plan-ext',
                'consumer_context_key': 'python',
                'component_element_keys': ['a'],
                'realization_keys': ['r'],
                'activity_keys': ['k'],
            },
            exit_code=0,
        )
        with redirect_stdout(stdout):
            exit_code = _run_producer_command(
                ['materialize-component-spec', '--spec', '/tmp/spec.md'],
                fake_client,
            )
        self.assertEqual(exit_code, 0)
        self.assertEqual(json.loads(stdout.getvalue())['implementation_plan_id'], 'plan-1')
        fake_client.materialize_component_spec.assert_called_once()


if __name__ == '__main__':
    unittest.main()

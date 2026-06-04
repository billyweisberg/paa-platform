import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from paa_core.repositories.implementation_plan import (
    ImplementationPlanActivityDependencyRecord,
    ImplementationPlanActivityRecord,
)
from paa_core.producer.coder_brief_assembler import (
    _derive_forbidden_surfaces,
    _resolve_coder_brief_schema_path,
    assemble_coder_brief,
)
from paa_core.producer.derivation_readiness import DerivationReadinessResult
from paa_core.producer.design_package_deriver import _resolve_stage1_schema_path, validate_stage1_design_package


REPO_ROOT = Path('/Users/billyweisberg/Repos/billyweisberg/paa-platform')
PACKAGE_PATH = REPO_ROOT / 'docs/2_Design/2026-05-16-component-design-planning-service-stage1-design-package.json'
OUTPUT_PATH = REPO_ROOT / '.codex-work' / 'coder-brief-assembler-tests' / 'assembled-draft-coder-run-brief.json'


class CoderBriefAssemblerTests(unittest.TestCase):
    def test_resolve_coder_brief_schema_path_prefers_local_copy(self):
        schema_path = _resolve_coder_brief_schema_path()
        self.assertEqual(schema_path, REPO_ROOT / 'schemas/derivation/coder_run_brief.schema.json')

    def test_derive_forbidden_surfaces_for_proof_slice(self):
        package = validate_stage1_design_package(PACKAGE_PATH, _resolve_stage1_schema_path())
        forbidden = _derive_forbidden_surfaces(package)
        self.assertIn('packages/paa-core/src/paa_core/repositories/component_design/postgres.py', forbidden)
        self.assertIn('packages/paa-core/src/paa_core/services/workflow_lifecycle/', forbidden)
        self.assertIn('migrations/postgres/', forbidden)

    def test_assemble_coder_brief_for_proof_slice_without_db_persist(self):
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        if OUTPUT_PATH.exists():
            OUTPUT_PATH.unlink()
        with patch(
            'paa_core.producer.coder_brief_assembler._existing_brief_for_design_package',
            return_value=None,
        ), patch.dict(os.environ, {'PAA_DB_PROFILE': 'agenthub_paa_dev_legacy'}, clear=False):
            result = assemble_coder_brief(
                package_path=PACKAGE_PATH,
                output_path=OUTPUT_PATH,
                persist_db=False,
            )
        self.assertEqual(result.project_slug, 'paa-platform')
        self.assertEqual(result.readiness_class, 'derivation_ready')
        self.assertTrue(OUTPUT_PATH.exists())
        brief = json.loads(OUTPUT_PATH.read_text())
        self.assertEqual(brief['schema_type'], 'coder_run_brief')
        self.assertEqual(brief['project'], 'paa-platform')
        self.assertEqual(brief['component_assignment']['component_name'], 'Component Design Planning Service')
        self.assertEqual(brief['execution_readiness']['readiness_class'], 'derivation_ready')
        OUTPUT_PATH.unlink(missing_ok=True)

    def test_assemble_coder_brief_uses_component_design_planning_payload(self):
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_PATH.unlink(missing_ok=True)
        planning_payload = {
            'component_name': 'Component Design Planning Service',
            'component_aspects': ['interfaces', 'functions', 'data_contract', 'tests'],
            'target_modules': [
                'packages/paa-core/src/paa_core/services/component_design_planning/contracts.py',
                'packages/paa-core/src/paa_core/services/component_design_planning/models.py',
            ],
            'warnings': [],
            'gaps': [],
            'metadata': {'system_layer': 'domain-services', 'tier': 'runtime'},
        }
        with patch(
            'paa_core.producer.coder_brief_assembler._existing_brief_for_design_package',
            return_value=None,
        ), patch(
            'paa_core.producer.coder_brief_assembler._load_component_brief_planning_payload',
            return_value=planning_payload,
        ), patch.dict(os.environ, {'PAA_DB_PROFILE': 'agenthub_paa_dev_legacy'}, clear=False):
            assemble_coder_brief(
                package_path=PACKAGE_PATH,
                output_path=OUTPUT_PATH,
                persist_db=False,
            )
        brief = json.loads(OUTPUT_PATH.read_text())
        self.assertEqual(
            brief['component_assignment']['component_aspects'],
            planning_payload['component_aspects'],
        )
        self.assertEqual(
            brief['component_assignment']['target_modules'],
            planning_payload['target_modules'],
        )
        self.assertEqual(
            brief['architecture_constraints']['allowed_edit_surfaces'],
            planning_payload['target_modules'],
        )
        OUTPUT_PATH.unlink(missing_ok=True)


    def test_assemble_coder_brief_carries_implementation_plan_binding_forward(self):
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_PATH.unlink(missing_ok=True)
        with patch(
            'paa_core.producer.coder_brief_assembler._existing_brief_for_design_package',
            return_value=None,
        ), patch(
            'paa_core.producer.coder_brief_assembler._load_implementation_plan_binding',
            return_value={'implementation_plan_id': 'impl-plan-1', 'plan_id_external': 'plan-external-1', 'authority_state': 'draft_plan', 'status': 'draft'},
        ), patch.dict(os.environ, {'PAA_DB_PROFILE': 'agenthub_paa_dev_legacy'}, clear=False):
            result = assemble_coder_brief(
                package_path=PACKAGE_PATH,
                output_path=OUTPUT_PATH,
                persist_db=False,
            )
        self.assertEqual(result.implementation_plan_id, 'impl-plan-1')
        OUTPUT_PATH.unlink(missing_ok=True)

    def test_assemble_coder_brief_embeds_implementation_plan_activity_context(self):
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_PATH.unlink(missing_ok=True)
        plan_context = {
            'plan_id_external': 'plan-external-1',
            'plan_title': 'Implementation Plan',
            'consumer_context_key': 'python',
            'activities': [
                ImplementationPlanActivityRecord(
                    implementation_plan_activity_id='activity-1',
                    implementation_plan_id='impl-plan-1',
                    component_element_id='element-1',
                    component_element_realization_id='realization-1',
                    assigned_role_id=None,
                    activity_key='define-service-interface',
                    activity_title='Service Interface',
                    activity_kind='artifact_construction',
                    activity_state='planned',
                    sequence_order=10,
                    target_path='packages/paa-core/src/paa_core/services/component_design_planning/contracts.py',
                    target_module='contracts.py',
                    planned_artifact_type_key='service_interface',
                    blocking_reason=None,
                    metadata={},
                    started_at=None,
                    completed_at=None,
                    created_at=None,
                    updated_at=None,
                ),
            ],
            'dependencies': [
                ImplementationPlanActivityDependencyRecord(
                    implementation_plan_activity_dependency_id='dep-1',
                    implementation_plan_id='impl-plan-1',
                    predecessor_activity_id='activity-1',
                    predecessor_activity_key='define-service-interface',
                    successor_activity_id='activity-2',
                    successor_activity_key='define-planning-dtos',
                    sequencing_requirement='hard',
                    dependency_strength='required',
                    notes=None,
                    metadata={},
                    created_at=None,
                ),
            ],
            'verification_surfaces': [],
        }
        with patch(
            'paa_core.producer.coder_brief_assembler._existing_brief_for_design_package',
            return_value=None,
        ), patch(
            'paa_core.producer.coder_brief_assembler._load_component_brief_planning_payload',
            return_value={
                'component_name': 'Component Design Planning Service',
                'component_aspects': ['interfaces', 'functions'],
                'target_modules': ['packages/paa-core/src/paa_core/services/component_design_planning/contracts.py'],
                'warnings': [],
                'gaps': [],
                'metadata': {'system_layer': 'domain-services', 'tier': 'runtime'},
            },
        ), patch(
            'paa_core.producer.coder_brief_assembler._load_implementation_plan_binding',
            return_value={'implementation_plan_id': 'impl-plan-1', 'plan_id_external': 'plan-external-1', 'authority_state': 'draft_plan', 'status': 'draft'},
        ), patch(
            'paa_core.producer.coder_brief_assembler._load_implementation_plan_context',
            return_value=plan_context,
        ), patch.dict(os.environ, {'PAA_DB_PROFILE': 'agenthub_paa_dev_legacy'}, clear=False):
            assemble_coder_brief(
                package_path=PACKAGE_PATH,
                output_path=OUTPUT_PATH,
                persist_db=False,
            )
        brief = json.loads(OUTPUT_PATH.read_text())
        self.assertIn(
            'implementation-plan:plan-external-1',
            brief['execution_prerequisites']['prerequisite_briefs'],
        )
        self.assertIn(
            'define-service-interface -> define-planning-dtos',
            brief['execution_prerequisites']['blocking_dependency_edges'],
        )
        self.assertTrue(
            any('planned activity 10: Service Interface [define-service-interface]' in item
                for item in brief['execution_prerequisites']['sequencing_notes'])
        )
        self.assertTrue(
            any('implementation-plan activity artifact: Service Interface (service_interface)' == item
                for item in brief['test_contract']['artifacts_expected'])
        )
        self.assertTrue(
            any('Execute implementation-plan activity: Service Interface [define-service-interface]' == item
                for item in brief['behavioral_contract']['behavior_to_add_or_change'])
        )
        OUTPUT_PATH.unlink(missing_ok=True)

    def test_assemble_coder_brief_refuses_to_overwrite_approved_authority(self):
        with patch(
            'paa_core.producer.coder_brief_assembler._existing_brief_for_design_package',
            return_value=('brief-id', 'brief-external', 'approved_brief'),
        ), patch(
            'paa_core.producer.coder_brief_assembler.evaluate_derivation_readiness'
        ) as mock_readiness, patch(
            'paa_core.producer.coder_brief_assembler._load_design_package_json'
        ) as mock_package:
            mock_readiness.return_value = DerivationReadinessResult(
                project_slug='paa-platform',
                package_id='package',
                package_path=str(PACKAGE_PATH),
                schema_path='schema',
                design_package_id='design-package',
                work_item_id='work-item',
                authority_version_id='authority-version',
                spec_fragment_id='spec-fragment',
                implementation_target_id='implementation-target',
                component_id='component-id',
                primary_component_name='Component Design Planning Service',
                readiness_class='derivation_ready',
                ready=True,
                blockers=[],
                warnings=[],
                checks=[],
                recommendations=[],
                evaluation_mode='evaluation_only',
            )
            mock_package.return_value = validate_stage1_design_package(PACKAGE_PATH, _resolve_stage1_schema_path())
            with self.assertRaisesRegex(RuntimeError, 'already approved_brief'):
                assemble_coder_brief(package_path=PACKAGE_PATH, persist_db=False)


if __name__ == '__main__':
    unittest.main()

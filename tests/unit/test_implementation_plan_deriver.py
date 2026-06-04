from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from paa_core.repositories.implementation_plan import (
    ImplementationPlanActivityDependencyUpsertSpec,
    ImplementationPlanActivityUpsertSpec,
    ImplementationPlanRecord,
    ImplementationPlanUpsertSpec,
)
from paa_core.services.implementation_plan_derivation import (
    ImplementationPlanActivityBlueprint,
    ImplementationPlanDerivationResult,
    ImplementationPlanVerificationSurfaceDraft,
)
from paa_core.producer.derivation_readiness import DerivationReadinessResult
from paa_core.producer.implementation_plan_deriver import (
    _activity_blueprints,
    derive_implementation_plan,
)

REPO_ROOT = Path('/Users/billyweisberg/Repos/billyweisberg/paa-platform')
PACKAGE_PATH = REPO_ROOT / 'docs/2_Design/2026-05-16-component-design-planning-service-stage1-design-package.json'
OUTPUT_PATH = REPO_ROOT / '.codex-work' / 'implementation-plan-deriver-tests' / 'implementation-plan.json'


class ImplementationPlanDeriverTests(unittest.TestCase):
    def test_activity_blueprints_follow_service_target_order(self) -> None:
        package = json.loads(PACKAGE_PATH.read_text())
        fake_ids = {
            'component_design_planning_service_service_interface': ('element-1', 'realization-1'),
            'component_design_planning_service_planning_dto': ('element-2', 'realization-2'),
            'component_design_planning_service_service_implementation': ('element-3', 'realization-3'),
            'component_design_planning_service_service_tests': ('element-4', 'realization-4'),
            'component_design_planning_service_package_export': ('element-1', 'realization-5'),
        }
        with patch('paa_core.producer.implementation_plan_deriver._ensure_component_design_records', return_value=fake_ids):
            rows = _activity_blueprints(package, 'component-1', 'project-1')

        self.assertEqual([row.activity_key for row in rows], [
            'define-service-interface',
            'define-planning-dtos',
            'implement-service-default',
            'prove-service-behavior',
            'export-service-package',
        ])
        self.assertEqual(rows[1].predecessor_activity_keys, ('define-service-interface',))
        self.assertEqual(rows[2].code_artifact_target_key, 'service_implementation')

    def test_derive_implementation_plan_returns_materialized_result(self) -> None:
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_PATH.unlink(missing_ok=True)
        package = json.loads(PACKAGE_PATH.read_text())
        readiness = DerivationReadinessResult(
            project_slug='paa-platform',
            package_id='paa-stage1-2026-05-16-component-design-planning-service',
            package_path=str(PACKAGE_PATH),
            schema_path='schema',
            design_package_id='design-package-1',
            work_item_id='work-item-1',
            authority_version_id='authority-1',
            spec_fragment_id='spec-fragment-1',
            implementation_target_id='implementation-target-1',
            component_id='component-1',
            primary_component_name='Component Design Planning Service',
            readiness_class='derivation_ready',
            ready=True,
            blockers=[],
            warnings=[],
            checks=[],
            recommendations=[],
            evaluation_mode='evaluation_only',
        )
        activity_blueprints = (
            ImplementationPlanActivityBlueprint(
                activity_key='define-service-interface',
                activity_title='Service Interface',
                activity_kind='artifact_construction',
                sequence_order=10,
                component_element_id='element-1',
                component_element_key='interfaces',
                component_element_realization_id='realization-1',
                code_artifact_target_key='service_interface',
                target_path='contracts.py',
                target_module='contracts.py',
            ),
        )
        verification_surfaces = (
            ImplementationPlanVerificationSurfaceDraft(
                activity_key='define-service-interface',
                surface_kind='unit_test',
                surface_ref='tests/unit/test_component_design_planning_service.py',
            ),
        )
        service_result = ImplementationPlanDerivationResult(
            plan_record=ImplementationPlanRecord(
                implementation_plan_id='impl-plan-1',
                project_id='project-1',
                work_item_id='work-item-1',
                design_package_id='design-package-1',
                spec_fragment_id='spec-fragment-1',
                implementation_target_id='implementation-target-1',
                authority_version_id='authority-1',
                primary_component_id='component-1',
                plan_id_external='plan-spec-component-design-planning-service-implementation-python',
                schema_version='1.0',
                consumer_context_key='python',
                plan_title='Implementation Plan',
                plan_kind='implementation_slice',
                status='draft',
                authority_state='draft_plan',
                authority_state_updated_at=None,
                plan={},
                build_sequence={},
                touch_surfaces={},
                protected_constraints={},
                verification_plan={},
                provenance={},
                metadata={},
                created_by_role_id=None,
                created_by_agent_id=None,
                approved_at=None,
                activated_at=None,
                completed_at=None,
                created_at=None,
                updated_at=None,
            ),
            activity_specs=(
                ImplementationPlanActivityUpsertSpec(
                    implementation_plan_id='impl-plan-1',
                    activity_key='define-service-interface',
                    activity_title='Service Interface',
                    activity_kind='artifact_construction',
                    sequence_order=10,
                ),
            ),
            dependency_specs=(
                ImplementationPlanActivityDependencyUpsertSpec(
                    implementation_plan_id='impl-plan-1',
                    predecessor_activity_key='define-service-interface',
                    successor_activity_key='define-service-interface',
                ),
            ),
            verification_surfaces=verification_surfaces,
            warnings=(),
            gaps=(),
            persisted=True,
        )
        with patch('paa_core.producer.implementation_plan_deriver.evaluate_derivation_readiness', return_value=readiness), \
             patch('paa_core.producer.implementation_plan_deriver.validate_stage1_design_package', return_value=package), \
             patch('paa_core.producer.implementation_plan_deriver._resolve_stage1_schema_path', return_value=REPO_ROOT / 'schemas/derivation/stage1_design_package.schema.json'), \
             patch('paa_core.producer.implementation_plan_deriver._project_id_for_slug', return_value='project-1'), \
             patch('paa_core.producer.implementation_plan_deriver._activity_blueprints', return_value=activity_blueprints), \
             patch('paa_core.producer.implementation_plan_deriver._verification_surfaces', return_value=verification_surfaces), \
             patch('paa_core.producer.implementation_plan_deriver.DefaultImplementationPlanDerivationService') as mock_service_cls:
            mock_service_cls.return_value.derive_plan.return_value = service_result
            result = derive_implementation_plan(
                package_path=PACKAGE_PATH,
                output_path=OUTPUT_PATH,
                persist_db=True,
            )

        self.assertEqual(result.implementation_plan_id, 'impl-plan-1')
        self.assertEqual(result.activity_count, 1)
        self.assertTrue(OUTPUT_PATH.exists())
        payload = json.loads(OUTPUT_PATH.read_text())
        self.assertEqual(payload['implementation_plan_id'], 'impl-plan-1')
        OUTPUT_PATH.unlink(missing_ok=True)


if __name__ == '__main__':
    unittest.main()

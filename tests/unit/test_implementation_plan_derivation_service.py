from __future__ import annotations

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'packages' / 'paa-core' / 'src'))

from paa_core.repositories.implementation_plan import ImplementationPlanRecord, ImplementationPlanUpsertSpec
from paa_core.services.implementation_plan_derivation import (
    DefaultImplementationPlanDerivationService,
    ImplementationPlanActivityBlueprint,
    ImplementationPlanDerivationRequest,
    ImplementationPlanVerificationSurfaceDraft,
)


class _FakeRepository:
    def __init__(self) -> None:
        self.plan_specs = []
        self.activity_specs = []
        self.dependency_specs = []
        self.plan_record = ImplementationPlanRecord(
            implementation_plan_id='plan-1',
            project_id='project-1',
            work_item_id='work-1',
            design_package_id='package-1',
            spec_fragment_id='spec-1',
            implementation_target_id='target-1',
            authority_version_id='authority-1',
            primary_component_id='component-1',
            plan_id_external='impl-plan-1',
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
        )

    def upsert_implementation_plan(self, spec):
        self.plan_specs.append(spec)

    def get_implementation_plan_for_design_package(self, design_package_id, consumer_context_key):
        return self.plan_record

    def upsert_implementation_plan_activity(self, spec):
        self.activity_specs.append(spec)

    def upsert_implementation_plan_activity_dependency(self, spec):
        self.dependency_specs.append(spec)


class _FakeLogger:
    def __init__(self) -> None:
        self.infos = []
        self.warnings = []

    def info(self, event: str, **fields: object) -> None:
        self.infos.append((event, fields))

    def warning(self, event: str, **fields: object) -> None:
        self.warnings.append((event, fields))


class ImplementationPlanDerivationServiceTests(unittest.TestCase):
    def test_derive_plan_persists_root_activities_and_dependencies(self) -> None:
        repo = _FakeRepository()
        logger = _FakeLogger()
        service = DefaultImplementationPlanDerivationService(repository=repo, logger=logger)
        request = ImplementationPlanDerivationRequest(
            plan=ImplementationPlanUpsertSpec(
                project_id='project-1',
                work_item_id='work-1',
                design_package_id='package-1',
                spec_fragment_id='spec-1',
                implementation_target_id='target-1',
                authority_version_id='authority-1',
                primary_component_id='component-1',
                plan_id_external='impl-plan-1',
                consumer_context_key='python',
                plan_title='Implementation Plan',
                plan_kind='implementation_slice',
                build_sequence={'bands': [10, 20]},
            ),
            activity_blueprints=(
                ImplementationPlanActivityBlueprint(
                    activity_key='define-interface',
                    activity_title='Define interface',
                    activity_kind='artifact_construction',
                    sequence_order=10,
                    component_element_id='ce-1',
                    component_element_key='interfaces',
                    component_element_realization_id='cer-1',
                    code_artifact_target_key='service_interface',
                    target_path='contracts.py',
                    target_module='contracts.py',
                ),
                ImplementationPlanActivityBlueprint(
                    activity_key='implement-service',
                    activity_title='Implement service',
                    activity_kind='artifact_construction',
                    sequence_order=30,
                    component_element_id='ce-2',
                    component_element_key='functions',
                    component_element_realization_id='cer-2',
                    code_artifact_target_key='service_implementation',
                    target_path='default.py',
                    target_module='default.py',
                    predecessor_activity_keys=('define-interface',),
                ),
            ),
            verification_surfaces=(
                ImplementationPlanVerificationSurfaceDraft(
                    activity_key='implement-service',
                    surface_kind='unit_test',
                    surface_ref='tests/unit/test_component_design_planning_service.py',
                    required=True,
                    sequence_order=40,
                ),
            ),
            persist=True,
        )

        result = service.derive_plan(request)

        self.assertTrue(result.persisted)
        self.assertEqual(result.plan_record.implementation_plan_id, 'plan-1')
        self.assertEqual(len(repo.plan_specs), 1)
        self.assertEqual(len(repo.activity_specs), 2)
        self.assertEqual(len(repo.dependency_specs), 1)
        self.assertEqual(repo.activity_specs[0].implementation_plan_id, 'plan-1')
        self.assertEqual(repo.dependency_specs[0].predecessor_activity_key, 'define-interface')
        self.assertEqual(result.verification_surfaces[0].surface_kind, 'unit_test')
        self.assertEqual(logger.infos[0][0], 'implementation_plan_derivation.persist_start')

    def test_derive_plan_reports_gap_when_no_activities_present(self) -> None:
        repo = _FakeRepository()
        logger = _FakeLogger()
        service = DefaultImplementationPlanDerivationService(repository=repo, logger=logger)
        request = ImplementationPlanDerivationRequest(
            plan=ImplementationPlanUpsertSpec(
                project_id='project-1',
                work_item_id='work-1',
                design_package_id='package-1',
                implementation_target_id='target-1',
                plan_id_external='impl-plan-1',
                consumer_context_key='python',
                plan_title='Implementation Plan',
                plan_kind='implementation_slice',
            ),
            activity_blueprints=(),
            persist=False,
        )

        result = service.derive_plan(request)

        self.assertFalse(result.persisted)
        self.assertIn('No implementation-plan activities were supplied for derivation.', result.gaps)
        self.assertEqual(result.plan_record.plan_id_external, 'impl-plan-1')


if __name__ == '__main__':
    unittest.main()

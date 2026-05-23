from __future__ import annotations

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'packages' / 'paa-core' / 'src'))

from paa_core.repositories.implementation_plan import (
    ImplementationPlanActivityDependencyRecord,
    ImplementationPlanActivityRecord,
    ImplementationPlanRecord,
    ImplementationPlanVerificationSurfaceRecord,
)
from paa_core.services.implementation_plan_progress import (
    DefaultImplementationPlanProgressService,
    ImplementationPlanProgressRequest,
    NextActivityBundleRequest,
)


class _FakeRepository:
    def __init__(self, *, plan, activities, dependencies, verification_surfaces) -> None:
        self.plan = plan
        self.activities = list(activities)
        self.dependencies = list(dependencies)
        self.verification_surfaces = list(verification_surfaces)

    def get_implementation_plan(self, implementation_plan_id):
        return self.plan if implementation_plan_id == self.plan.implementation_plan_id else None

    def list_implementation_plan_activities(self, implementation_plan_id):
        return list(self.activities)

    def list_implementation_plan_activity_dependencies(self, implementation_plan_id):
        return list(self.dependencies)

    def list_implementation_plan_verification_surfaces(self, implementation_plan_id):
        return list(self.verification_surfaces)


class _FakeLogger:
    def info(self, event: str, **fields: object) -> None:
        return None

    def warning(self, event: str, **fields: object) -> None:
        return None


def _plan() -> ImplementationPlanRecord:
    return ImplementationPlanRecord(
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


def _activity(activity_id: str, key: str, sequence: int, state: str = 'planned', blocking_reason: str | None = None):
    return ImplementationPlanActivityRecord(
        implementation_plan_activity_id=activity_id,
        implementation_plan_id='plan-1',
        component_element_id=None,
        component_element_realization_id=None,
        assigned_role_id=None,
        activity_key=key,
        activity_title=key,
        activity_kind='artifact_construction',
        activity_state=state,
        sequence_order=sequence,
        target_path=None,
        target_module=None,
        planned_artifact_type_key=None,
        blocking_reason=blocking_reason,
        metadata={},
        started_at=None,
        completed_at=None,
        created_at=None,
        updated_at=None,
    )


def _dependency(pred_id: str, pred_key: str, succ_id: str, succ_key: str):
    return ImplementationPlanActivityDependencyRecord(
        implementation_plan_activity_dependency_id=f'{pred_id}-{succ_id}',
        implementation_plan_id='plan-1',
        predecessor_activity_id=pred_id,
        predecessor_activity_key=pred_key,
        successor_activity_id=succ_id,
        successor_activity_key=succ_key,
        sequencing_requirement='must_precede',
        dependency_strength='hard',
        notes=None,
        metadata={},
        created_at=None,
    )


def _surface(activity_id: str, ref: str, status: str = 'passed', required: bool = True):
    return ImplementationPlanVerificationSurfaceRecord(
        implementation_plan_verification_surface_id=f'vs-{activity_id}-{ref}',
        implementation_plan_id='plan-1',
        implementation_plan_activity_id=activity_id,
        verification_obligation_id=None,
        surface_kind='unit_test',
        surface_ref=ref,
        required=required,
        sequence_order=10,
        status=status,
        metadata={},
        created_at=None,
        updated_at=None,
    )


class ImplementationPlanProgressServiceTests(unittest.TestCase):
    def test_all_planned_returns_first_dependency_free_activity(self) -> None:
        repo = _FakeRepository(
            plan=_plan(),
            activities=(
                _activity('a1', 'define-interface', 10),
                _activity('a2', 'define-models', 20),
                _activity('a3', 'implement-default', 30),
            ),
            dependencies=(
                _dependency('a1', 'define-interface', 'a2', 'define-models'),
                _dependency('a2', 'define-models', 'a3', 'implement-default'),
            ),
            verification_surfaces=(),
        )
        service = DefaultImplementationPlanProgressService(repository=repo, logger=_FakeLogger())

        summary = service.summarize_plan_progress(ImplementationPlanProgressRequest(implementation_plan_id='plan-1'))
        next_result = service.derive_next_activity_bundle(NextActivityBundleRequest(implementation_plan_id='plan-1'))

        self.assertEqual(summary.next_activity_key, 'define-interface')
        self.assertEqual(summary.realization_state, 'not_started')
        self.assertEqual(next_result.next_bundle_activity_keys, ('define-interface',))
        self.assertTrue(next_result.ok)

    def test_completed_predecessor_advances_next_activity(self) -> None:
        repo = _FakeRepository(
            plan=_plan(),
            activities=(
                _activity('a1', 'define-interface', 10, state='completed'),
                _activity('a2', 'define-models', 20),
                _activity('a3', 'implement-default', 30),
            ),
            dependencies=(
                _dependency('a1', 'define-interface', 'a2', 'define-models'),
                _dependency('a2', 'define-models', 'a3', 'implement-default'),
            ),
            verification_surfaces=(),
        )
        service = DefaultImplementationPlanProgressService(repository=repo, logger=_FakeLogger())

        summary = service.summarize_plan_progress(ImplementationPlanProgressRequest(implementation_plan_id='plan-1'))

        self.assertEqual(summary.next_activity_key, 'define-models')
        self.assertEqual(summary.realization_state, 'partially_realized')
        self.assertEqual(summary.last_completed_activity_key, 'define-interface')

    def test_deferred_activity_is_counted_but_not_next(self) -> None:
        repo = _FakeRepository(
            plan=_plan(),
            activities=(
                _activity('a1', 'define-interface', 10, state='completed'),
                _activity('a2', 'define-models', 20, state='deferred'),
                _activity('a3', 'implement-default', 30),
            ),
            dependencies=(
                _dependency('a1', 'define-interface', 'a2', 'define-models'),
            ),
            verification_surfaces=(),
        )
        service = DefaultImplementationPlanProgressService(repository=repo, logger=_FakeLogger())

        summary = service.summarize_plan_progress(ImplementationPlanProgressRequest(implementation_plan_id='plan-1'))

        self.assertIn('define-models', summary.deferred_activity_keys)
        self.assertEqual(summary.next_activity_key, 'implement-default')

    def test_blocked_predecessor_prevents_successor_execution(self) -> None:
        repo = _FakeRepository(
            plan=_plan(),
            activities=(
                _activity('a1', 'define-interface', 10, state='blocked', blocking_reason='need schema'),
                _activity('a2', 'define-models', 20),
            ),
            dependencies=(
                _dependency('a1', 'define-interface', 'a2', 'define-models'),
            ),
            verification_surfaces=(),
        )
        service = DefaultImplementationPlanProgressService(repository=repo, logger=_FakeLogger())

        summary = service.summarize_plan_progress(ImplementationPlanProgressRequest(implementation_plan_id='plan-1'))
        next_result = service.derive_next_activity_bundle(NextActivityBundleRequest(implementation_plan_id='plan-1'))

        self.assertEqual(summary.realization_state, 'blocked')
        self.assertIsNone(summary.next_activity_key)
        self.assertFalse(next_result.ok)
        self.assertIn('define-interface', next_result.blocking_reasons[0])

    def test_no_remaining_activities_reports_fully_realized(self) -> None:
        repo = _FakeRepository(
            plan=_plan(),
            activities=(
                _activity('a1', 'define-interface', 10, state='completed'),
                _activity('a2', 'define-models', 20, state='completed'),
            ),
            dependencies=(),
            verification_surfaces=(),
        )
        service = DefaultImplementationPlanProgressService(repository=repo, logger=_FakeLogger())

        summary = service.summarize_plan_progress(ImplementationPlanProgressRequest(implementation_plan_id='plan-1'))

        self.assertEqual(summary.authority_state_summary, 'completed_plan')
        self.assertEqual(summary.realization_state, 'fully_realized')
        self.assertEqual(summary.completion_ratio, 1.0)

    def test_required_verification_missing_blocks_completed_classification(self) -> None:
        repo = _FakeRepository(
            plan=_plan(),
            activities=(
                _activity('a1', 'define-interface', 10, state='completed'),
            ),
            dependencies=(),
            verification_surfaces=(
                _surface('a1', 'tests/unit/test_define_interface.py', status='planned', required=True),
            ),
        )
        service = DefaultImplementationPlanProgressService(repository=repo, logger=_FakeLogger())

        summary = service.summarize_plan_progress(ImplementationPlanProgressRequest(implementation_plan_id='plan-1'))

        self.assertEqual(summary.realization_state, 'blocked')
        self.assertEqual(summary.blocked_activity_keys, ('define-interface',))

    def test_duplicate_executable_sequence_fails_closed(self) -> None:
        repo = _FakeRepository(
            plan=_plan(),
            activities=(
                _activity('a1', 'define-interface', 10),
                _activity('a2', 'define-models', 10),
            ),
            dependencies=(),
            verification_surfaces=(),
        )
        service = DefaultImplementationPlanProgressService(repository=repo, logger=_FakeLogger())

        summary = service.summarize_plan_progress(ImplementationPlanProgressRequest(implementation_plan_id='plan-1'))
        next_result = service.derive_next_activity_bundle(NextActivityBundleRequest(implementation_plan_id='plan-1'))

        self.assertIsNone(summary.next_activity_key)
        self.assertEqual(summary.realization_state, 'blocked')
        self.assertFalse(next_result.ok)


if __name__ == '__main__':
    unittest.main()

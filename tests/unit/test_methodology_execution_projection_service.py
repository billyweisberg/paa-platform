from __future__ import annotations

import sys
from pathlib import Path
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))

from paa_core.repositories.methodology_execution import (
    MethodologyExecutionBindingRecord,
    MethodologyExecutionEventRecord,
    MethodologyExecutionProjectionInputRecord,
    MethodologyExecutionRecord,
)
from paa_core.governance.component_registry import COMPONENT_METADATA_BY_NAME
from paa_core.runtime.workflow.methodology_execution_projection import (
    DefaultMethodologyExecutionProjectionService,
    METHODOLOGY_EXECUTION_PROJECTION_SERVICE_METADATA,
    MethodologyExecutionProjectionRequest,
)


class MethodologyExecutionProjectionServiceTests(unittest.TestCase):
    def _repository(self) -> Mock:
        return Mock()

    def _projection_input(self) -> MethodologyExecutionProjectionInputRecord:
        return MethodologyExecutionProjectionInputRecord(
            execution=MethodologyExecutionRecord(
                methodology_execution_id='exec-1',
                project_id='proj-1',
                work_item_id='work-1',
                lane='component_realization',
                stage='slice_execution',
                step='derive_next_activity_bundle',
                status='ready',
                current_owner_role='System',
                next_action_key='execute_component_activity',
                blocked_reason=None,
                component_id='component-1',
                design_package_id='design-1',
                implementation_plan_id='plan-1',
                coder_run_brief_id=None,
                packet_id=None,
                workflow_state_id='workflow-1',
                active_authority_ref='docs/spec.md',
                active_artifact_ref='default.py',
                metadata={'source': 'test'},
                created_at=None,
                updated_at=None,
            ),
            events=(
                MethodologyExecutionEventRecord(
                    methodology_execution_event_id='event-1',
                    methodology_execution_id='exec-1',
                    from_lane='component_realization',
                    to_lane='component_realization',
                    from_stage='slice_execution',
                    to_stage='slice_execution',
                    from_step='reconcile_component_plan_progress',
                    to_step='derive_next_activity_bundle',
                    from_status='active',
                    to_status='ready',
                    transition_kind='component-progress-reconciled',
                    actor_role_id='system',
                    actor_name='System',
                    notes='advanced projection state',
                    evidence={},
                    created_at=None,
                ),
            ),
            bindings=(
                MethodologyExecutionBindingRecord(
                    methodology_execution_binding_id='binding-1',
                    methodology_execution_id='exec-1',
                    binding_kind='implementation_plan',
                    bound_record_id='plan-1',
                    bound_record_key='plan-materialize',
                    bound_record_ref='implementation_plan:plan-1',
                    is_primary=True,
                    notes=None,
                    metadata={},
                    created_at=None,
                    updated_at=None,
                ),
            ),
            related_records={},
        )

    def test_get_status_projection_returns_structured_projection(self) -> None:
        repo = self._repository()
        repo.load_methodology_execution_projection_inputs.return_value = self._projection_input()
        service = DefaultMethodologyExecutionProjectionService(methodology_execution_repository=repo)

        projection = service.get_status_projection('exec-1')

        self.assertEqual(projection.methodology_execution_id, 'exec-1')
        self.assertEqual(projection.binding_refs, ('implementation_plan:plan-1',))
        self.assertIn('execute_component_activity', projection.summary_text)

    def test_find_status_projection_returns_none_when_missing(self) -> None:
        repo = self._repository()
        repo.find_methodology_execution_by_primary_ref.return_value = None
        service = DefaultMethodologyExecutionProjectionService(methodology_execution_repository=repo)

        projection = service.find_status_projection('proj-1', 'work-1', 'component-1')

        self.assertIsNone(projection)

    def test_metadata_is_registered_for_projection_service(self) -> None:
        self.assertIs(
            COMPONENT_METADATA_BY_NAME['MethodologyExecutionProjectionService'],
            METHODOLOGY_EXECUTION_PROJECTION_SERVICE_METADATA,
        )

    def test_get_next_action_projection_returns_structured_projection(self) -> None:
        repo = self._repository()
        repo.load_methodology_execution_projection_inputs.return_value = self._projection_input()
        service = DefaultMethodologyExecutionProjectionService(methodology_execution_repository=repo)

        projection = service.get_next_action_projection('exec-1')

        self.assertEqual(projection.recommended_next_action_key, 'execute_component_activity')
        self.assertEqual(projection.recommended_owner_role, 'System')
        self.assertEqual(
            projection.prerequisite_summary,
            ('current-step:derive_next_activity_bundle', 'current-status:ready', 'implementation-plan:plan-1'),
        )

    def test_explain_current_methodology_execution_uses_latest_transition_context(self) -> None:
        repo = self._repository()
        repo.load_methodology_execution_projection_inputs.return_value = self._projection_input()
        service = DefaultMethodologyExecutionProjectionService(methodology_execution_repository=repo)

        projection = service.explain_current_methodology_execution('exec-1')

        self.assertEqual(projection.transition_context, 'component-progress-reconciled')
        self.assertIn('next recommended action is execute_component_activity', projection.explanation_summary)

    def test_get_status_projection_raises_for_missing_execution(self) -> None:
        repo = self._repository()
        repo.load_methodology_execution_projection_inputs.side_effect = LookupError('missing')
        service = DefaultMethodologyExecutionProjectionService(methodology_execution_repository=repo)

        with self.assertRaises(LookupError):
            service.get_status_projection('missing-exec')

    def test_get_projection_fails_closed_for_missing_execution(self) -> None:
        repo = self._repository()
        repo.load_methodology_execution_projection_inputs.side_effect = LookupError('missing')
        service = DefaultMethodologyExecutionProjectionService(methodology_execution_repository=repo)

        result = service.get_projection(
            MethodologyExecutionProjectionRequest(
                methodology_execution_id='missing-exec',
                projection_mode='status',
            )
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'missing_methodology_execution')

    def test_get_projection_fails_closed_for_unsupported_mode(self) -> None:
        service = DefaultMethodologyExecutionProjectionService(methodology_execution_repository=self._repository())

        result = service.get_projection(
            MethodologyExecutionProjectionRequest(
                methodology_execution_id='exec-1',
                projection_mode='timeline',
            )
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'unsupported_projection_mode')

    def test_get_projection_resolves_execution_from_primary_anchors(self) -> None:
        repo = self._repository()
        projection_input = self._projection_input()
        repo.find_methodology_execution_by_primary_ref.return_value = projection_input.execution
        repo.load_methodology_execution_projection_inputs.return_value = projection_input
        service = DefaultMethodologyExecutionProjectionService(methodology_execution_repository=repo)

        result = service.get_projection(
            MethodologyExecutionProjectionRequest(
                project_id='proj-1',
                work_item_id='work-1',
                component_id='component-1',
                projection_mode='status',
            )
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.methodology_execution_id, 'exec-1')
        self.assertEqual(result.status_projection.summary_text, 'Methodology execution is ready in component_realization/slice_execution/derive_next_activity_bundle and is ready for execute_component_activity.')

    def test_get_projection_returns_mode_specific_result(self) -> None:
        repo = self._repository()
        repo.load_methodology_execution_projection_inputs.return_value = self._projection_input()
        service = DefaultMethodologyExecutionProjectionService(methodology_execution_repository=repo)

        result = service.get_projection(
            MethodologyExecutionProjectionRequest(
                methodology_execution_id='exec-1',
                projection_mode='next',
            )
        )

        self.assertTrue(result.ok)
        self.assertIsNone(result.status_projection)
        self.assertIsNotNone(result.next_action_projection)
        self.assertEqual(result.next_action_projection.recommended_next_action_key, 'execute_component_activity')


if __name__ == '__main__':
    unittest.main()

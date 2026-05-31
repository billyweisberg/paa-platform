from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))

from paa_core.repositories.methodology_execution import MethodologyExecutionBindingEntrySpec
from paa_core.services.methodology_execution_state import (
    MethodologyExecutionStateRequest,
    MethodologyExecutionStateResult,
    MethodologyExecutionStateSummary,
    MethodologyExecutionTransitionSummary,
)


class MethodologyExecutionStateServiceModelsTests(unittest.TestCase):
    def test_state_request_captures_transition_and_binding_inputs(self) -> None:
        request = MethodologyExecutionStateRequest(
            project_id='proj-1',
            work_item_id='work-1',
            component_id='component-1',
            transition_key='component-spec-materialized',
            to_lane='component_realization',
            to_stage='slice_execution',
            to_step='reconcile_component_plan_progress',
            to_status='ready',
            actor_role_id='architect',
            actor_name='Authority Architect',
            notes='enter the realization loop',
            evidence={'component_id': 'component-1'},
            binding_entries=(
                MethodologyExecutionBindingEntrySpec(
                    binding_kind='implementation_plan',
                    bound_record_id='plan-1',
                    is_primary=True,
                ),
            ),
            metadata={'source': 'unit-test'},
        )

        self.assertEqual(request.transition_key, 'component-spec-materialized')
        self.assertEqual(request.binding_entries[0].binding_kind, 'implementation_plan')
        self.assertEqual(request.metadata, {'source': 'unit-test'})

    def test_state_summary_preserves_pointer_context(self) -> None:
        summary = MethodologyExecutionStateSummary(
            methodology_execution_id='exec-1',
            lane='component_realization',
            stage='slice_execution',
            step='derive_next_activity_bundle',
            status='active',
            current_owner_role='operator',
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
            binding_refs=('implementation_plan:plan-1',),
            notes=('realization loop active',),
            metadata={'priority': 'high'},
        )

        self.assertEqual(summary.lane, 'component_realization')
        self.assertEqual(summary.binding_refs[0], 'implementation_plan:plan-1')
        self.assertEqual(summary.metadata, {'priority': 'high'})

    def test_transition_summary_and_result_capture_successful_transition(self) -> None:
        request = MethodologyExecutionStateRequest(
            methodology_execution_id='exec-1',
            transition_key='component-progress-reconciled',
        )
        summary = MethodologyExecutionStateSummary(
            methodology_execution_id='exec-1',
            lane='component_realization',
            stage='slice_execution',
            step='derive_next_activity_bundle',
            status='ready',
            current_owner_role='system',
            next_action_key='execute_component_activity',
            blocked_reason=None,
            component_id='component-1',
            design_package_id='design-1',
            implementation_plan_id='plan-1',
            coder_run_brief_id=None,
            packet_id=None,
            workflow_state_id=None,
            active_authority_ref=None,
            active_artifact_ref=None,
            binding_refs=(),
            notes=(),
        )
        transition = MethodologyExecutionTransitionSummary(
            transition_key='component-progress-reconciled',
            transition_kind='automated_progression',
            from_lane='component_realization',
            to_lane='component_realization',
            from_stage='slice_execution',
            to_stage='slice_execution',
            from_step='reconcile_component_plan_progress',
            to_step='derive_next_activity_bundle',
            from_status='active',
            to_status='ready',
            current_owner_role='operator',
            next_owner_role='system',
            prerequisites_satisfied=True,
            blocking_reasons=(),
            recommended_next_action='derive-next-activity-bundle',
        )
        result = MethodologyExecutionStateResult(
            methodology_execution_id='exec-1',
            request=request,
            current_state=summary,
            transition=transition,
            ok=True,
            binding_update_applied=False,
            metadata={'source': 'state-service'},
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.transition.transition_key, 'component-progress-reconciled')
        self.assertFalse(result.binding_update_applied)


if __name__ == '__main__':
    unittest.main()

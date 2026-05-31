from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))

from paa_core.services.methodology_execution_projection import (
    MethodologyExecutionExplainProjection,
    MethodologyExecutionNextActionProjection,
    MethodologyExecutionProjectionRequest,
    MethodologyExecutionProjectionResult,
    MethodologyExecutionStatusProjection,
)


class MethodologyExecutionProjectionServiceModelsTests(unittest.TestCase):
    def test_projection_request_captures_anchor_and_mode_inputs(self) -> None:
        request = MethodologyExecutionProjectionRequest(
            project_id='proj-1',
            work_item_id='work-1',
            component_id='component-1',
            projection_mode='status',
            actor_role_id='operator',
            actor_name='Authority Architect',
            metadata={'source': 'unit-test'},
        )

        self.assertEqual(request.projection_mode, 'status')
        self.assertEqual(request.component_id, 'component-1')
        self.assertEqual(request.metadata, {'source': 'unit-test'})

    def test_status_projection_preserves_pointer_context(self) -> None:
        projection = MethodologyExecutionStatusProjection(
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
            workflow_state_id='workflow-1',
            active_authority_ref='docs/spec.md',
            active_artifact_ref='default.py',
            binding_refs=('implementation_plan:plan-1',),
            summary_text='Ready to execute the next component activity.',
            metadata={'priority': 'high'},
        )

        self.assertEqual(projection.lane, 'component_realization')
        self.assertEqual(projection.binding_refs[0], 'implementation_plan:plan-1')
        self.assertEqual(projection.summary_text, 'Ready to execute the next component activity.')

    def test_next_action_and_explain_projection_result_capture_supported_slice(self) -> None:
        request = MethodologyExecutionProjectionRequest(
            methodology_execution_id='exec-1',
            projection_mode='explain',
        )
        status_projection = MethodologyExecutionStatusProjection(
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
            summary_text='Ready for the next authority action.',
        )
        next_action_projection = MethodologyExecutionNextActionProjection(
            methodology_execution_id='exec-1',
            recommended_next_action_key='execute_component_activity',
            recommended_owner_role='operator',
            lane='component_realization',
            stage='slice_execution',
            step='derive_next_activity_bundle',
            prerequisite_summary=('plan progress reconciled',),
            blocked_reason=None,
            component_id='component-1',
            implementation_plan_id='plan-1',
            packet_id=None,
            metadata={'source': 'projection-service'},
        )
        explain_projection = MethodologyExecutionExplainProjection(
            methodology_execution_id='exec-1',
            lane='component_realization',
            stage='slice_execution',
            step='derive_next_activity_bundle',
            status='ready',
            current_owner_role='system',
            explanation_summary='The component plan has been reconciled and the next activity is ready to derive.',
            transition_context='component-progress-reconciled',
            binding_refs=('implementation_plan:plan-1',),
            blocked_reason=None,
        )
        result = MethodologyExecutionProjectionResult(
            methodology_execution_id='exec-1',
            request=request,
            status_projection=status_projection,
            next_action_projection=next_action_projection,
            explain_projection=explain_projection,
            ok=True,
            metadata={'source': 'projection-service'},
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.next_action_projection.recommended_next_action_key, 'execute_component_activity')
        self.assertEqual(result.explain_projection.transition_context, 'component-progress-reconciled')


if __name__ == '__main__':
    unittest.main()

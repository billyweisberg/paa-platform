from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))

from paa_core.services.methodology_execution_preflight import (
    MethodologyExecutionPreflightOutcome,
    MethodologyExecutionPreflightRequest,
    MethodologyExecutionPreflightResult,
)
from paa_core.services.methodology_execution_projection import MethodologyExecutionStatusProjection


class MethodologyExecutionPreflightServiceModelsTests(unittest.TestCase):
    def test_preflight_request_captures_command_and_anchor_inputs(self) -> None:
        request = MethodologyExecutionPreflightRequest(
            project_id='proj-1',
            work_item_id='work-1',
            component_id='component-1',
            command_family='component',
            command_name='reconcile',
            command_arguments={'plan_id': 'plan-1'},
            actor_role_id='operator',
            actor_name='Authority Architect',
            metadata={'source': 'unit-test'},
        )

        self.assertEqual(request.command_family, 'component')
        self.assertEqual(request.command_name, 'reconcile')
        self.assertEqual(request.command_arguments, {'plan_id': 'plan-1'})

    def test_preflight_outcome_preserves_redirect_and_reasoning(self) -> None:
        outcome = MethodologyExecutionPreflightOutcome(
            methodology_execution_id='exec-1',
            outcome_kind='redirect',
            rule_key='wrong-lane-component-command',
            lane='runtime_execution',
            stage='verification',
            step='await_qa_review',
            status='active',
            current_owner_role='QA',
            redirect_target='status',
            recommended_next_action_key='inspect-methodology-status',
            reason='Component commands are not valid in the runtime lane.',
            details='Use a lane-native command instead.',
            metadata={'source': 'preflight'},
        )

        self.assertEqual(outcome.outcome_kind, 'redirect')
        self.assertEqual(outcome.redirect_target, 'status')
        self.assertEqual(outcome.metadata, {'source': 'preflight'})

    def test_preflight_result_carries_status_projection_and_outcome(self) -> None:
        request = MethodologyExecutionPreflightRequest(
            methodology_execution_id='exec-1',
            command_family='plan',
            command_name='progress',
        )
        status_projection = MethodologyExecutionStatusProjection(
            methodology_execution_id='exec-1',
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
            workflow_state_id=None,
            active_authority_ref=None,
            active_artifact_ref=None,
            binding_refs=('implementation_plan:plan-1',),
            summary_text='Ready to execute the next component activity.',
        )
        outcome = MethodologyExecutionPreflightOutcome(
            methodology_execution_id='exec-1',
            outcome_kind='allowed',
            rule_key='plan-progress-allowed',
            lane='component_realization',
            stage='slice_execution',
            step='derive_next_activity_bundle',
            status='ready',
            current_owner_role='System',
            redirect_target=None,
            recommended_next_action_key='execute_component_activity',
            reason='Plan progress is allowed for the active component-realization lane.',
        )
        result = MethodologyExecutionPreflightResult(
            methodology_execution_id='exec-1',
            request=request,
            status_projection=status_projection,
            outcome=outcome,
            ok=True,
            metadata={'source': 'preflight-service'},
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.outcome.rule_key, 'plan-progress-allowed')
        self.assertEqual(result.status_projection.binding_refs, ('implementation_plan:plan-1',))


if __name__ == '__main__':
    unittest.main()

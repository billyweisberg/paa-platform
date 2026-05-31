from __future__ import annotations

import sys
from pathlib import Path
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))

from paa_core.governance.component_registry import COMPONENT_METADATA_BY_NAME
from paa_core.services.methodology_execution_preflight import (
    DefaultMethodologyExecutionPreflightService,
    METHODOLOGY_EXECUTION_PREFLIGHT_SERVICE_METADATA,
    MethodologyExecutionPreflightRequest,
)
from paa_core.services.methodology_execution_projection import MethodologyExecutionStatusProjection


class MethodologyExecutionPreflightServiceTests(unittest.TestCase):
    def test_metadata_is_registered_for_preflight_service(self) -> None:
        self.assertIs(
            COMPONENT_METADATA_BY_NAME['MethodologyExecutionPreflightService'],
            METHODOLOGY_EXECUTION_PREFLIGHT_SERVICE_METADATA,
        )

    def _repository(self) -> Mock:
        return Mock()

    def _state_service(self) -> Mock:
        return Mock()

    def _projection_service(self) -> Mock:
        return Mock()

    def _component_projection(
        self,
        *,
        lane: str = 'component_realization',
        stage: str = 'slice_execution',
        step: str = 'derive_next_activity_bundle',
        status: str = 'ready',
        implementation_plan_id: str | None = 'plan-1',
        blocked_reason: str | None = None,
    ) -> MethodologyExecutionStatusProjection:
        binding_refs = ('implementation_plan:plan-1',) if implementation_plan_id else ()
        return MethodologyExecutionStatusProjection(
            methodology_execution_id='exec-1',
            lane=lane,
            stage=stage,
            step=step,
            status=status,
            current_owner_role='System',
            next_action_key='execute_component_activity',
            blocked_reason=blocked_reason,
            component_id='component-1',
            design_package_id='design-1',
            implementation_plan_id=implementation_plan_id,
            coder_run_brief_id=None,
            packet_id=None,
            workflow_state_id=None,
            active_authority_ref=None,
            active_artifact_ref=None,
            binding_refs=binding_refs,
            summary_text='projection summary',
        )

    def test_evaluate_command_allows_component_next_for_supported_state(self) -> None:
        projection_service = self._projection_service()
        projection_service.get_status_projection.return_value = self._component_projection()
        service = DefaultMethodologyExecutionPreflightService(
            methodology_execution_repository=self._repository(),
            methodology_execution_state_service=self._state_service(),
            methodology_execution_projection_service=projection_service,
        )

        result = service.evaluate_command(
            MethodologyExecutionPreflightRequest(
                methodology_execution_id='exec-1',
                command_family='component',
                command_name='next',
            )
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.outcome.outcome_kind, 'allowed')
        self.assertEqual(result.outcome.rule_key, 'component-next-allowed')

    def test_evaluate_command_warns_on_materialize_during_active_slice(self) -> None:
        projection_service = self._projection_service()
        projection_service.get_status_projection.return_value = self._component_projection(
            step='execute_component_activity',
            status='active',
        )
        service = DefaultMethodologyExecutionPreflightService(
            methodology_execution_repository=self._repository(),
            methodology_execution_state_service=self._state_service(),
            methodology_execution_projection_service=projection_service,
        )

        result = service.evaluate_command(
            MethodologyExecutionPreflightRequest(
                methodology_execution_id='exec-1',
                command_family='component',
                command_name='materialize',
            )
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.outcome.outcome_kind, 'warn')
        self.assertEqual(result.outcome.redirect_target, 'component progress')

    def test_evaluate_command_redirects_when_component_command_is_in_wrong_lane(self) -> None:
        projection_service = self._projection_service()
        projection_service.get_status_projection.return_value = self._component_projection(
            lane='runtime_execution',
            stage='verification',
            step='await_qa_review',
            status='active',
        )
        service = DefaultMethodologyExecutionPreflightService(
            methodology_execution_repository=self._repository(),
            methodology_execution_state_service=self._state_service(),
            methodology_execution_projection_service=projection_service,
        )

        result = service.evaluate_command(
            MethodologyExecutionPreflightRequest(
                methodology_execution_id='exec-1',
                command_family='component',
                command_name='progress',
            )
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.outcome.outcome_kind, 'redirect')
        self.assertEqual(result.outcome.redirect_target, 'status')

    def test_evaluate_command_blocks_when_mutating_command_hits_blocked_state(self) -> None:
        projection_service = self._projection_service()
        projection_service.get_status_projection.return_value = self._component_projection(
            status='blocked',
            blocked_reason='waiting for manual review',
        )
        service = DefaultMethodologyExecutionPreflightService(
            methodology_execution_repository=self._repository(),
            methodology_execution_state_service=self._state_service(),
            methodology_execution_projection_service=projection_service,
        )

        result = service.evaluate_command(
            MethodologyExecutionPreflightRequest(
                methodology_execution_id='exec-1',
                command_family='component',
                command_name='next',
            )
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.outcome.outcome_kind, 'blocked')
        self.assertEqual(result.outcome.redirect_target, 'explain')

    def test_evaluate_command_blocks_when_required_binding_is_missing(self) -> None:
        projection_service = self._projection_service()
        projection_service.get_status_projection.return_value = self._component_projection(
            implementation_plan_id=None,
        )
        service = DefaultMethodologyExecutionPreflightService(
            methodology_execution_repository=self._repository(),
            methodology_execution_state_service=self._state_service(),
            methodology_execution_projection_service=projection_service,
        )

        result = service.evaluate_command(
            MethodologyExecutionPreflightRequest(
                methodology_execution_id='exec-1',
                command_family='plan',
                command_name='progress',
            )
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'missing_required_binding')

    def test_evaluate_command_blocks_when_projection_is_missing(self) -> None:
        projection_service = self._projection_service()
        projection_service.get_status_projection.side_effect = LookupError('missing')
        service = DefaultMethodologyExecutionPreflightService(
            methodology_execution_repository=self._repository(),
            methodology_execution_state_service=self._state_service(),
            methodology_execution_projection_service=projection_service,
        )

        result = service.evaluate_command(
            MethodologyExecutionPreflightRequest(
                methodology_execution_id='missing-exec',
                command_family='component',
                command_name='progress',
            )
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'missing_methodology_execution')

    def test_evaluate_command_blocks_for_unsupported_command_family(self) -> None:
        service = DefaultMethodologyExecutionPreflightService(
            methodology_execution_repository=self._repository(),
            methodology_execution_state_service=self._state_service(),
            methodology_execution_projection_service=self._projection_service(),
        )

        result = service.evaluate_command(
            MethodologyExecutionPreflightRequest(
                methodology_execution_id='exec-1',
                command_family='worker',
                command_name='run',
            )
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'unsupported_command_family')

    def test_evaluate_command_blocks_for_supported_family_but_unsupported_command(self) -> None:
        service = DefaultMethodologyExecutionPreflightService(
            methodology_execution_repository=self._repository(),
            methodology_execution_state_service=self._state_service(),
            methodology_execution_projection_service=self._projection_service(),
        )

        result = service.evaluate_command(
            MethodologyExecutionPreflightRequest(
                methodology_execution_id='exec-1',
                command_family='component',
                command_name='close',
            )
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'unsupported_command')

    def test_blocked_outcome_helper_preserves_context(self) -> None:
        service = DefaultMethodologyExecutionPreflightService(
            methodology_execution_repository=self._repository(),
            methodology_execution_state_service=self._state_service(),
            methodology_execution_projection_service=self._projection_service(),
        )

        outcome = service.blocked_outcome(
            MethodologyExecutionPreflightRequest(
                methodology_execution_id='exec-1',
                command_family='component',
                command_name='next',
            ),
            methodology_execution_id='exec-1',
            lane='component_realization',
            stage='slice_execution',
            step='derive_next_activity_bundle',
            status='blocked',
            current_owner_role='System',
            redirect_target='explain',
            recommended_next_action_key='execute_component_activity',
            reason='blocked_state',
            details='blocked for review',
        )

        self.assertEqual(outcome.outcome_kind, 'blocked')
        self.assertEqual(outcome.redirect_target, 'explain')
        self.assertEqual(outcome.metadata, {'blocking_reason': 'blocked_state'})

    def test_evaluate_command_resolves_projection_from_primary_anchors(self) -> None:
        projection_service = self._projection_service()
        projection_service.find_status_projection.return_value = self._component_projection()
        service = DefaultMethodologyExecutionPreflightService(
            methodology_execution_repository=self._repository(),
            methodology_execution_state_service=self._state_service(),
            methodology_execution_projection_service=projection_service,
        )

        result = service.evaluate_command(
            MethodologyExecutionPreflightRequest(
                project_id='proj-1',
                work_item_id='work-1',
                component_id='component-1',
                command_family='plan',
                command_name='inspect',
            )
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.outcome.rule_key, 'plan-inspect-allowed')


if __name__ == '__main__':
    unittest.main()

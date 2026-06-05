from __future__ import annotations

import sys
from pathlib import Path
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))

from paa_core.application.dto.methodology_execution import (
    ApplyMethodologyExecutionTransitionRequest,
    EvaluateMethodologyExecutionPreflightRequest,
    ExplainMethodologyExecutionRequest,
    GetMethodologyExecutionNextActionRequest,
    GetMethodologyExecutionStatusRequest,
    MethodologyExecutionBindingEntryInput,
)
from paa_core.application.services.methodology_execution import (
    DefaultMethodologyExecutionApplicationService,
)
from paa_core.repositories.methodology_execution import MethodologyExecutionRecord
from paa_core.runtime.workflow.methodology_execution_preflight import (
    MethodologyExecutionPreflightOutcome,
    MethodologyExecutionPreflightRequest,
    MethodologyExecutionPreflightResult,
)
from paa_core.runtime.workflow.methodology_execution_projection import (
    MethodologyExecutionExplainProjection,
    MethodologyExecutionNextActionProjection,
    MethodologyExecutionProjectionRequest,
    MethodologyExecutionStatusProjection,
)
from paa_core.runtime.workflow.methodology_execution_state import (
    MethodologyExecutionStateRequest,
    MethodologyExecutionStateResult,
    MethodologyExecutionStateSummary,
    MethodologyExecutionTransitionSummary,
)


class MethodologyExecutionApplicationServiceTests(unittest.TestCase):
    def _repository(self) -> Mock:
        return Mock()

    def _projection_service(self) -> Mock:
        return Mock()

    def _state_service(self) -> Mock:
        return Mock()

    def _preflight_service(self) -> Mock:
        return Mock()

    def _service(self, *, repository: Mock | None = None, projection_service: Mock | None = None, state_service: Mock | None = None, preflight_service: Mock | None = None) -> DefaultMethodologyExecutionApplicationService:
        return DefaultMethodologyExecutionApplicationService(
            methodology_execution_repository=repository or self._repository(),
            methodology_execution_projection_service=projection_service or self._projection_service(),
            methodology_execution_state_service=state_service or self._state_service(),
            methodology_execution_preflight_service=preflight_service or self._preflight_service(),
        )

    def test_get_status_returns_payload_for_direct_id(self) -> None:
        projection_service = self._projection_service()
        projection_service.get_status_projection.return_value = self._status_projection()
        service = self._service(projection_service=projection_service)

        result = service.get_status(GetMethodologyExecutionStatusRequest(methodology_execution_id='exec-1'))

        self.assertEqual(result.exit_code, 0)
        self.assertTrue(result.payload['ok'])
        self.assertEqual(result.payload['item']['methodology_execution_id'], 'exec-1')

    def test_get_status_returns_payload_for_primary_anchors(self) -> None:
        projection_service = self._projection_service()
        projection_service.find_status_projection.return_value = self._status_projection()
        service = self._service(projection_service=projection_service)

        result = service.get_status(
            GetMethodologyExecutionStatusRequest(
                project_id='proj-1',
                work_item_id='work-1',
                component_id='component-1',
            )
        )

        self.assertEqual(result.exit_code, 0)
        self.assertTrue(result.payload['ok'])
        self.assertEqual(result.payload['item']['component_id'], 'component-1')

    def test_get_status_returns_missing_identity_when_no_identity_present(self) -> None:
        service = self._service()

        result = service.get_status(GetMethodologyExecutionStatusRequest())

        self.assertEqual(result.exit_code, 1)
        self.assertEqual(result.payload['code'], 'missing_methodology_identity')

    def test_get_status_returns_not_found_when_missing(self) -> None:
        projection_service = self._projection_service()
        projection_service.find_status_projection.return_value = None
        service = self._service(projection_service=projection_service)

        result = service.get_status(
            GetMethodologyExecutionStatusRequest(project_id='proj-1', work_item_id='work-1')
        )

        self.assertEqual(result.exit_code, 1)
        self.assertEqual(result.payload['code'], 'methodology_execution_not_found')

    def test_get_next_action_returns_payload_for_direct_id(self) -> None:
        projection_service = self._projection_service()
        projection_service.get_next_action_projection.return_value = self._next_action_projection()
        service = self._service(projection_service=projection_service)

        result = service.get_next_action(
            GetMethodologyExecutionNextActionRequest(methodology_execution_id='exec-1')
        )

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.payload['item']['recommended_next_action_key'], 'derive-next-activity-bundle')

    def test_get_next_action_resolves_anchor_through_repository(self) -> None:
        repository = self._repository()
        repository.find_methodology_execution_by_primary_ref.return_value = self._record()
        projection_service = self._projection_service()
        projection_service.get_next_action_projection.return_value = self._next_action_projection()
        service = self._service(repository=repository, projection_service=projection_service)

        result = service.get_next_action(
            GetMethodologyExecutionNextActionRequest(
                project_id='proj-1',
                work_item_id='work-1',
                component_id='component-1',
            )
        )

        self.assertEqual(result.exit_code, 0)
        repository.find_methodology_execution_by_primary_ref.assert_called_once_with(
            'proj-1',
            'work-1',
            'component-1',
        )
        projection_service.get_next_action_projection.assert_called_once_with('exec-1')

    def test_get_next_action_returns_not_found_when_anchor_missing(self) -> None:
        repository = self._repository()
        repository.find_methodology_execution_by_primary_ref.return_value = None
        service = self._service(repository=repository)

        result = service.get_next_action(
            GetMethodologyExecutionNextActionRequest(project_id='proj-1', work_item_id='work-1')
        )

        self.assertEqual(result.exit_code, 1)
        self.assertEqual(result.payload['code'], 'methodology_execution_not_found')

    def test_explain_returns_payload_for_direct_id(self) -> None:
        projection_service = self._projection_service()
        projection_service.explain_current_methodology_execution.return_value = self._explain_projection()
        service = self._service(projection_service=projection_service)

        result = service.explain(ExplainMethodologyExecutionRequest(methodology_execution_id='exec-1'))

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.payload['item']['transition_context'], 'automated_progression')

    def test_explain_resolves_anchor_through_repository(self) -> None:
        repository = self._repository()
        repository.find_methodology_execution_by_primary_ref.return_value = self._record()
        projection_service = self._projection_service()
        projection_service.explain_current_methodology_execution.return_value = self._explain_projection()
        service = self._service(repository=repository, projection_service=projection_service)

        result = service.explain(
            ExplainMethodologyExecutionRequest(project_id='proj-1', work_item_id='work-1')
        )

        self.assertEqual(result.exit_code, 0)
        projection_service.explain_current_methodology_execution.assert_called_once_with('exec-1')

    def test_explain_returns_not_found_when_anchor_missing(self) -> None:
        repository = self._repository()
        repository.find_methodology_execution_by_primary_ref.return_value = None
        service = self._service(repository=repository)

        result = service.explain(ExplainMethodologyExecutionRequest(project_id='proj-1', work_item_id='work-1'))

        self.assertEqual(result.exit_code, 1)
        self.assertEqual(result.payload['code'], 'methodology_execution_not_found')

    def test_apply_transition_converts_binding_inputs_and_returns_success_payload(self) -> None:
        state_service = self._state_service()
        state_service.apply_transition.return_value = self._state_result(ok=True)
        service = self._service(state_service=state_service)

        result = service.apply_transition(
            ApplyMethodologyExecutionTransitionRequest(
                methodology_execution_id='exec-1',
                transition_key='component-progress-reconciled',
                binding_entries=(
                    MethodologyExecutionBindingEntryInput(
                        binding_kind='implementation_plan',
                        bound_record_id='plan-1',
                        bound_record_ref='implementation_plan:plan-1',
                        is_primary=True,
                        metadata={'source': 'test'},
                    ),
                ),
            )
        )

        self.assertEqual(result.exit_code, 0)
        self.assertTrue(result.payload['ok'])
        self.assertTrue(result.payload['binding_update_applied'])
        request = state_service.apply_transition.call_args.args[0]
        self.assertEqual(request.binding_entries[0].binding_kind, 'implementation_plan')
        self.assertEqual(request.binding_entries[0].metadata, {'source': 'test'})

    def test_apply_transition_returns_blocked_payload(self) -> None:
        state_service = self._state_service()
        state_service.apply_transition.return_value = self._state_result(
            ok=False,
            reason='unsupported_current_state',
            details='not allowed here',
        )
        service = self._service(state_service=state_service)

        result = service.apply_transition(
            ApplyMethodologyExecutionTransitionRequest(
                methodology_execution_id='exec-1',
                transition_key='component-progress-reconciled',
            )
        )

        self.assertEqual(result.exit_code, 1)
        self.assertFalse(result.payload['ok'])
        self.assertEqual(result.payload['code'], 'unsupported_current_state')
        self.assertIn('current_state', result.payload)

    def test_apply_transition_returns_not_found_for_missing_anchor_resolution(self) -> None:
        repository = self._repository()
        repository.find_methodology_execution_by_primary_ref.return_value = None
        service = self._service(repository=repository)

        result = service.apply_transition(
            ApplyMethodologyExecutionTransitionRequest(
                project_id='proj-1',
                work_item_id='work-1',
                transition_key='component-progress-reconciled',
            )
        )

        self.assertEqual(result.exit_code, 1)
        self.assertEqual(result.payload['code'], 'methodology_execution_not_found')

    def test_evaluate_preflight_returns_exit_zero_for_allowed(self) -> None:
        preflight_service = self._preflight_service()
        preflight_service.evaluate_command.return_value = self._preflight_result(ok=True, outcome_kind='allowed')
        service = self._service(preflight_service=preflight_service)

        result = service.evaluate_preflight(
            EvaluateMethodologyExecutionPreflightRequest(
                methodology_execution_id='exec-1',
                command_family='component',
                command_name='next',
            )
        )

        self.assertEqual(result.exit_code, 0)
        self.assertTrue(result.payload['ok'])
        self.assertEqual(result.payload['outcome']['outcome_kind'], 'allowed')

    def test_evaluate_preflight_returns_exit_zero_for_warn_and_redirect(self) -> None:
        service = self._service(preflight_service=self._preflight_service())
        service._preflight_service.evaluate_command.side_effect = [
            self._preflight_result(ok=True, outcome_kind='warn'),
            self._preflight_result(ok=True, outcome_kind='redirect'),
        ]

        warn_result = service.evaluate_preflight(
            EvaluateMethodologyExecutionPreflightRequest(
                methodology_execution_id='exec-1',
                command_family='component',
                command_name='materialize',
            )
        )
        redirect_result = service.evaluate_preflight(
            EvaluateMethodologyExecutionPreflightRequest(
                methodology_execution_id='exec-1',
                command_family='component',
                command_name='progress',
            )
        )

        self.assertEqual(warn_result.exit_code, 0)
        self.assertEqual(warn_result.payload['outcome']['outcome_kind'], 'warn')
        self.assertEqual(redirect_result.exit_code, 0)
        self.assertEqual(redirect_result.payload['outcome']['outcome_kind'], 'redirect')

    def test_evaluate_preflight_returns_exit_one_for_blocked(self) -> None:
        preflight_service = self._preflight_service()
        preflight_service.evaluate_command.return_value = self._preflight_result(
            ok=False,
            outcome_kind='blocked',
            reason='blocked_state',
        )
        service = self._service(preflight_service=preflight_service)

        result = service.evaluate_preflight(
            EvaluateMethodologyExecutionPreflightRequest(
                methodology_execution_id='exec-1',
                command_family='component',
                command_name='next',
            )
        )

        self.assertEqual(result.exit_code, 1)
        self.assertFalse(result.payload['ok'])
        self.assertEqual(result.payload['reason'], 'blocked_state')

    def test_evaluate_preflight_returns_missing_identity_when_no_identity_present(self) -> None:
        service = self._service()

        result = service.evaluate_preflight(
            EvaluateMethodologyExecutionPreflightRequest(
                command_family='component',
                command_name='next',
            )
        )

        self.assertEqual(result.exit_code, 1)
        self.assertEqual(result.payload['code'], 'missing_methodology_identity')

    def _record(self) -> MethodologyExecutionRecord:
        return MethodologyExecutionRecord(
            methodology_execution_id='exec-1',
            project_id='proj-1',
            work_item_id='work-1',
            lane='component_realization',
            stage='slice_execution',
            step='reconcile_component_plan_progress',
            status='active',
            current_owner_role='Operator',
            next_action_key='derive-next-activity-bundle',
            blocked_reason=None,
            component_id='component-1',
            design_package_id='design-1',
            implementation_plan_id='plan-1',
            coder_run_brief_id=None,
            packet_id=None,
            workflow_state_id='workflow-1',
            active_authority_ref='docs/spec.md',
            active_artifact_ref='default.py',
            metadata={},
            created_at=None,
            updated_at=None,
        )

    def _status_projection(self) -> MethodologyExecutionStatusProjection:
        return MethodologyExecutionStatusProjection(
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
            workflow_state_id='workflow-1',
            active_authority_ref='docs/spec.md',
            active_artifact_ref='default.py',
            binding_refs=('implementation_plan:plan-1',),
            summary_text='projection summary',
            metadata={'source': 'test'},
        )

    def _next_action_projection(self) -> MethodologyExecutionNextActionProjection:
        return MethodologyExecutionNextActionProjection(
            methodology_execution_id='exec-1',
            recommended_next_action_key='derive-next-activity-bundle',
            recommended_owner_role='System',
            lane='component_realization',
            stage='slice_execution',
            step='derive_next_activity_bundle',
            prerequisite_summary=('current-step:derive_next_activity_bundle',),
            blocked_reason=None,
            component_id='component-1',
            implementation_plan_id='plan-1',
            packet_id=None,
            metadata={'source': 'test'},
        )

    def _explain_projection(self) -> MethodologyExecutionExplainProjection:
        return MethodologyExecutionExplainProjection(
            methodology_execution_id='exec-1',
            lane='component_realization',
            stage='slice_execution',
            step='derive_next_activity_bundle',
            status='ready',
            current_owner_role='System',
            explanation_summary='The current methodology pointer is ready.',
            transition_context='automated_progression',
            binding_refs=('implementation_plan:plan-1',),
            blocked_reason=None,
            metadata={'source': 'test'},
        )

    def _state_summary(self) -> MethodologyExecutionStateSummary:
        return MethodologyExecutionStateSummary(
            methodology_execution_id='exec-1',
            lane='component_realization',
            stage='slice_execution',
            step='derive_next_activity_bundle',
            status='ready',
            current_owner_role='System',
            next_action_key='derive-next-activity-bundle',
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
            notes=('next:derive-next-activity-bundle',),
            metadata={'source': 'test'},
        )

    def _transition_summary(self) -> MethodologyExecutionTransitionSummary:
        return MethodologyExecutionTransitionSummary(
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
            current_owner_role='Operator',
            next_owner_role='System',
            prerequisites_satisfied=True,
            blocking_reasons=(),
            recommended_next_action='derive-next-activity-bundle',
        )

    def _state_result(self, *, ok: bool, reason: str | None = None, details: str | None = None) -> MethodologyExecutionStateResult:
        return MethodologyExecutionStateResult(
            methodology_execution_id='exec-1',
            request=MethodologyExecutionStateRequest(
                methodology_execution_id='exec-1',
                transition_key='component-progress-reconciled',
            ),
            current_state=self._state_summary(),
            transition=self._transition_summary() if ok else None,
            ok=ok,
            reason=reason,
            details=details,
            binding_update_applied=True if ok else False,
            metadata={'source': 'test'},
        )

    def _preflight_result(
        self,
        *,
        ok: bool,
        outcome_kind: str,
        reason: str | None = None,
    ) -> MethodologyExecutionPreflightResult:
        return MethodologyExecutionPreflightResult(
            methodology_execution_id='exec-1',
            request=MethodologyExecutionPreflightRequest(
                methodology_execution_id='exec-1',
                command_family='component',
                command_name='next',
            ),
            status_projection=self._status_projection(),
            outcome=MethodologyExecutionPreflightOutcome(
                methodology_execution_id='exec-1',
                outcome_kind=outcome_kind,
                rule_key='rule-1',
                lane='component_realization',
                stage='slice_execution',
                step='derive_next_activity_bundle',
                status='ready',
                current_owner_role='System',
                redirect_target='status' if outcome_kind == 'redirect' else None,
                recommended_next_action_key='derive-next-activity-bundle',
                reason='preflight summary',
                details='details',
                metadata={'source': 'test'},
            ),
            ok=ok,
            reason=reason,
            details='details' if not ok else None,
            metadata={'source': 'test'},
        )


if __name__ == '__main__':
    unittest.main()

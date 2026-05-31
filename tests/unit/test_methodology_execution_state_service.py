from __future__ import annotations

import sys
from pathlib import Path
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))

from paa_core.repositories.methodology_execution import (
    MethodologyExecutionBindingEntrySpec,
    MethodologyExecutionBindingRecord,
    MethodologyExecutionRecord,
)
from paa_core.services.methodology_execution_state import (
    DefaultMethodologyExecutionStateService,
    MethodologyExecutionStateRequest,
)


class MethodologyExecutionStateServiceTests(unittest.TestCase):
    def _repository(self) -> Mock:
        return Mock()

    def _active_reconcile_record(self) -> MethodologyExecutionRecord:
        return MethodologyExecutionRecord(
            methodology_execution_id='exec-1',
            project_id='proj-1',
            work_item_id='work-1',
            lane='component_realization',
            stage='slice_execution',
            step='reconcile_component_plan_progress',
            status='active',
            current_owner_role='Operator',
            next_action_key='reconcile-component-plan-progress',
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
        )

    def test_get_current_methodology_execution_returns_structured_summary(self) -> None:
        repo = self._repository()
        repo.get_methodology_execution.return_value = self._active_reconcile_record()
        repo.list_methodology_execution_bindings.return_value = (
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
        )
        service = DefaultMethodologyExecutionStateService(methodology_execution_repository=repo)

        summary = service.get_current_methodology_execution('exec-1')

        self.assertEqual(summary.methodology_execution_id, 'exec-1')
        self.assertEqual(summary.binding_refs, ('implementation_plan:plan-1',))

    def test_find_current_methodology_execution_returns_none_when_missing(self) -> None:
        repo = self._repository()
        repo.find_methodology_execution_by_primary_ref.return_value = None
        service = DefaultMethodologyExecutionStateService(methodology_execution_repository=repo)

        summary = service.find_current_methodology_execution('proj-1', 'work-1', 'component-1')

        self.assertIsNone(summary)

    def test_get_current_methodology_execution_raises_for_missing_record(self) -> None:
        repo = self._repository()
        repo.get_methodology_execution.return_value = None
        service = DefaultMethodologyExecutionStateService(methodology_execution_repository=repo)

        with self.assertRaises(LookupError):
            service.get_current_methodology_execution('missing-exec')

    def test_apply_transition_fails_closed_for_unsupported_transition(self) -> None:
        repo = self._repository()
        repo.get_methodology_execution.return_value = self._active_reconcile_record()
        repo.list_methodology_execution_bindings.return_value = ()
        service = DefaultMethodologyExecutionStateService(methodology_execution_repository=repo)

        result = service.apply_transition(
            MethodologyExecutionStateRequest(
                methodology_execution_id='exec-1',
                transition_key='unsupported-transition',
            )
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'unsupported_transition_key')
        repo.upsert_methodology_execution.assert_not_called()

    def test_apply_transition_fails_closed_for_missing_execution(self) -> None:
        repo = self._repository()
        repo.get_methodology_execution.return_value = None
        service = DefaultMethodologyExecutionStateService(methodology_execution_repository=repo)

        result = service.apply_transition(
            MethodologyExecutionStateRequest(
                methodology_execution_id='missing-exec',
                transition_key='component-progress-reconciled',
            )
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'missing_methodology_execution')
        repo.append_methodology_execution_event.assert_not_called()

    def test_apply_transition_fails_closed_for_wrong_current_state(self) -> None:
        repo = self._repository()
        repo.get_methodology_execution.return_value = MethodologyExecutionRecord(
            methodology_execution_id='exec-1',
            project_id='proj-1',
            work_item_id='work-1',
            lane='component_realization',
            stage='slice_execution',
            step='execute_component_activity',
            status='active',
            current_owner_role='Operator',
            next_action_key='execute-component-activity',
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
        repo.list_methodology_execution_bindings.return_value = ()
        service = DefaultMethodologyExecutionStateService(methodology_execution_repository=repo)

        result = service.apply_transition(
            MethodologyExecutionStateRequest(
                methodology_execution_id='exec-1',
                transition_key='component-progress-reconciled',
            )
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'unsupported_current_state')
        repo.upsert_methodology_execution.assert_not_called()

    def test_apply_transition_updates_root_appends_event_and_refreshes_bindings(self) -> None:
        repo = self._repository()
        current = self._active_reconcile_record()
        updated = MethodologyExecutionRecord(
            methodology_execution_id='exec-1',
            project_id='proj-1',
            work_item_id='work-1',
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
            metadata={'source': 'test'},
            created_at=None,
            updated_at=None,
        )
        repo.get_methodology_execution.side_effect = [current, updated]
        repo.list_methodology_execution_bindings.side_effect = [
            (),
            (
                MethodologyExecutionBindingRecord(
                    methodology_execution_binding_id='binding-1',
                    methodology_execution_id='exec-1',
                    binding_kind='implementation_plan',
                    bound_record_id='plan-1',
                    bound_record_key=None,
                    bound_record_ref='implementation_plan:plan-1',
                    is_primary=True,
                    notes=None,
                    metadata={},
                    created_at=None,
                    updated_at=None,
                ),
            ),
        ]
        service = DefaultMethodologyExecutionStateService(methodology_execution_repository=repo)

        result = service.apply_transition(
            MethodologyExecutionStateRequest(
                methodology_execution_id='exec-1',
                transition_key='component-progress-reconciled',
                actor_role_id='operator',
                actor_name='Operator',
                notes='reconciled current slice',
                evidence={'source': 'unit-test'},
                binding_entries=(
                    MethodologyExecutionBindingEntrySpec(
                        binding_kind='implementation_plan',
                        bound_record_id='plan-1',
                        bound_record_ref='implementation_plan:plan-1',
                        is_primary=True,
                    ),
                ),
            )
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.transition.transition_key, 'component-progress-reconciled')
        self.assertTrue(result.binding_update_applied)
        repo.upsert_methodology_execution.assert_called_once()
        repo.append_methodology_execution_event.assert_called_once()
        repo.replace_methodology_execution_bindings.assert_called_once()

    def test_supports_transition_only_for_first_supported_key(self) -> None:
        service = DefaultMethodologyExecutionStateService(methodology_execution_repository=self._repository())
        self.assertTrue(service.supports_transition('component-progress-reconciled'))
        self.assertFalse(service.supports_transition('packet-prepared'))


if __name__ == '__main__':
    unittest.main()

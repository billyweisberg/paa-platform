from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'packages' / 'paa-core' / 'src'))

from paa_core.repositories.methodology_execution import (
    MethodologyExecutionBindingEntrySpec,
    MethodologyExecutionBindingRecord,
    MethodologyExecutionBindingReplaceSpec,
    MethodologyExecutionEventAppendSpec,
    MethodologyExecutionEventRecord,
    MethodologyExecutionProjectionInputRecord,
    MethodologyExecutionRecord,
    MethodologyExecutionUpsertSpec,
)


class MethodologyExecutionRepositoryModelsTests(unittest.TestCase):
    def test_methodology_execution_record_preserves_pointer_fields(self) -> None:
        record = MethodologyExecutionRecord(
            methodology_execution_id='exec-1',
            project_id='proj-1',
            work_item_id='work-1',
            lane='component_realization',
            stage='slice_execution',
            step='derive_next_activity_bundle',
            status='active',
            current_owner_role='architect',
            next_action_key='operator-cli-host-support',
            blocked_reason=None,
            component_id='component-1',
            design_package_id='design-1',
            implementation_plan_id='plan-1',
            coder_run_brief_id=None,
            packet_id=None,
            workflow_state_id='workflow-1',
            active_authority_ref='docs/2_Design/spec.md',
            active_artifact_ref='packages/paa-cli/src/paa_cli/app.py',
            metadata={'priority': 'high'},
            created_at='2026-05-30T12:00:00Z',
            updated_at='2026-05-30T12:05:00Z',
        )

        self.assertEqual(record.lane, 'component_realization')
        self.assertEqual(record.current_owner_role, 'architect')
        self.assertEqual(record.metadata['priority'], 'high')

    def test_event_and_binding_records_capture_history_and_anchors(self) -> None:
        event = MethodologyExecutionEventRecord(
            methodology_execution_event_id='event-1',
            methodology_execution_id='exec-1',
            from_lane='authority_derivation',
            to_lane='component_realization',
            from_stage='packet_preparation',
            to_stage='slice_execution',
            from_step='prepare_packet',
            to_step='derive_next_activity_bundle',
            from_status='completed',
            to_status='active',
            transition_kind='lane_transition',
            actor_role_id='architect',
            actor_name='Authority Architect',
            notes='handoff to component loop',
            evidence={'packet_id': 'packet-1'},
            created_at='2026-05-30T12:10:00Z',
        )
        binding = MethodologyExecutionBindingRecord(
            methodology_execution_binding_id='binding-1',
            methodology_execution_id='exec-1',
            binding_kind='implementation_plan',
            bound_record_id='plan-1',
            bound_record_key='plan-materialize-proof',
            bound_record_ref='implementation_plan:plan-1',
            is_primary=True,
            notes='current active plan',
            metadata={'source': 'materializer'},
            created_at='2026-05-30T12:10:00Z',
            updated_at='2026-05-30T12:11:00Z',
        )

        self.assertEqual(event.transition_kind, 'lane_transition')
        self.assertTrue(binding.is_primary)
        self.assertEqual(binding.bound_record_id, 'plan-1')

    def test_projection_input_record_groups_execution_history_and_bindings(self) -> None:
        execution = MethodologyExecutionRecord(
            methodology_execution_id='exec-1',
            project_id='proj-1',
            work_item_id=None,
            lane='runtime_execution',
            stage='verification',
            step='await_result',
            status='waiting',
            current_owner_role='qa',
            next_action_key='qa-review',
            blocked_reason=None,
            component_id=None,
            design_package_id=None,
            implementation_plan_id=None,
            coder_run_brief_id='brief-1',
            packet_id='packet-1',
            workflow_state_id='workflow-1',
            active_authority_ref=None,
            active_artifact_ref=None,
            metadata={},
            created_at=None,
            updated_at=None,
        )
        event = MethodologyExecutionEventRecord(
            methodology_execution_event_id='event-1',
            methodology_execution_id='exec-1',
            from_lane=None,
            to_lane='runtime_execution',
            from_stage=None,
            to_stage='verification',
            from_step=None,
            to_step='await_result',
            from_status=None,
            to_status='waiting',
            transition_kind='enter_stage',
            actor_role_id=None,
            actor_name=None,
            notes=None,
            evidence={},
            created_at=None,
        )
        binding = MethodologyExecutionBindingRecord(
            methodology_execution_binding_id='binding-1',
            methodology_execution_id='exec-1',
            binding_kind='packet',
            bound_record_id='packet-1',
            bound_record_key=None,
            bound_record_ref='packet:packet-1',
            is_primary=True,
            notes=None,
            metadata={},
            created_at=None,
            updated_at=None,
        )

        projection = MethodologyExecutionProjectionInputRecord(
            execution=execution,
            events=(event,),
            bindings=(binding,),
            related_records={'workflow_state': {'workflow_state_id': 'workflow-1'}},
        )

        self.assertEqual(projection.execution.methodology_execution_id, 'exec-1')
        self.assertEqual(len(projection.events), 1)
        self.assertEqual(projection.bindings[0].binding_kind, 'packet')

    def test_upsert_append_and_replace_specs_capture_write_shapes(self) -> None:
        upsert = MethodologyExecutionUpsertSpec(
            methodology_execution_id='exec-1',
            project_id='proj-1',
            work_item_id='work-1',
            lane='authority_derivation',
            stage='design',
            step='author_component_spec',
            status='active',
            current_owner_role='architect',
            next_action_key='materialize_component_spec',
            metadata={'source': 'manual'},
        )
        append = MethodologyExecutionEventAppendSpec(
            methodology_execution_id='exec-1',
            to_lane='component_realization',
            to_stage='component_materialization',
            to_step='materialize_component_spec',
            to_status='active',
            transition_kind='advance',
            notes='approved for materialization',
            evidence={'component_id': 'component-1'},
        )
        replace = MethodologyExecutionBindingReplaceSpec(
            methodology_execution_id='exec-1',
            bindings=(
                MethodologyExecutionBindingEntrySpec(
                    binding_kind='component',
                    bound_record_id='component-1',
                    is_primary=True,
                    metadata={'source': 'authority'},
                ),
            ),
        )

        self.assertEqual(upsert.next_action_key, 'materialize_component_spec')
        self.assertEqual(append.to_stage, 'component_materialization')
        self.assertEqual(replace.bindings[0].binding_kind, 'component')
        self.assertTrue(replace.bindings[0].is_primary)


if __name__ == '__main__':
    unittest.main()

from __future__ import annotations

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'packages' / 'paa-core' / 'src'))

from paa_core.repositories.component_design.models import (
    CoderBriefRealizationTargetRecord,
    ComponentElementRealizationRecord,
    ComponentElementRealizationTypeRecord,
    ComponentElementRecord,
    ComponentElementTypeRecord,
    ComponentRecord,
)
from paa_core.services.component_design_planning import (
    ComponentPlanningRequest,
    DefaultComponentDesignPlanningService,
    PlanningGap,
    RealizationOptionView,
)


class _FakeRepository:
    def __init__(self) -> None:
        self.component = ComponentRecord(
            component_id='component-1',
            project_id='project-1',
            name='Component Design Planning Service',
            role='interpret component design into planning outputs',
            system_layer='domain-services',
            tier='runtime',
            description='service',
            status='active',
            metadata={'source': 'test'},
        )
        self.element_types = [
            ComponentElementTypeRecord(
                component_element_type_id='type-interfaces',
                element_key='interfaces',
                label='Interfaces',
                category='dependency',
                description='interface surfaces',
                is_brief_targetable=True,
                is_multi_instance=True,
                sort_order=10,
                metadata={},
            ),
            ComponentElementTypeRecord(
                component_element_type_id='type-functions',
                element_key='functions',
                label='Functions',
                category='behavior',
                description='behavior surfaces',
                is_brief_targetable=True,
                is_multi_instance=True,
                sort_order=20,
                metadata={},
            ),
        ]
        self.elements = [
            ComponentElementRecord(
                component_element_id='element-1',
                project_id='project-1',
                component_id='component-1',
                component_element_type_id='type-interfaces',
                element_key='interfaces',
                title='Service Interfaces',
                status='active',
                definition={'module': 'contracts.py'},
                provenance={},
                metadata={},
            ),
            ComponentElementRecord(
                component_element_id='element-2',
                project_id='project-1',
                component_id='component-1',
                component_element_type_id='type-functions',
                element_key='functions',
                title='Service Functions',
                status='active',
                definition={'module': 'default.py'},
                provenance={},
                metadata={},
            ),
        ]
        self.realization_types = {
            'interfaces': [
                ComponentElementRealizationTypeRecord(
                    component_element_realization_type_id='rt-1',
                    realization_key='service_interface',
                    label='Service Interface',
                    category='code_artifact',
                    description='contract',
                    is_brief_targetable=True,
                    is_multi_instance=False,
                    sort_order=10,
                    metadata={},
                    is_default_for_element_type=True,
                    element_type_sort_order=10,
                )
            ],
            'functions': [
                ComponentElementRealizationTypeRecord(
                    component_element_realization_type_id='rt-2',
                    realization_key='service_implementation',
                    label='Service Implementation',
                    category='code_artifact',
                    description='implementation',
                    is_brief_targetable=True,
                    is_multi_instance=False,
                    sort_order=20,
                    metadata={},
                    is_default_for_element_type=True,
                    element_type_sort_order=20,
                )
            ],
        }
        self.realizations = {
            'element-1': [
                ComponentElementRealizationRecord(
                    component_element_realization_id='realization-1',
                    project_id='project-1',
                    component_id='component-1',
                    component_element_id='element-1',
                    component_element_realization_type_id='rt-1',
                    realization_key='service_interface',
                    title='Component Design Planning Service Interface',
                    status='planned',
                    sequence_order=10,
                    definition={},
                    artifact_ref={'module': 'contracts.py'},
                    provenance={},
                    metadata={},
                )
            ],
            'element-2': [],
        }

    def get_component_by_id(self, component_id: str):
        return self.component if component_id == self.component.component_id else None

    def get_component_by_name(self, project_id: str, name: str):
        if project_id == self.component.project_id and name == self.component.name:
            return self.component
        return None

    def get_component_element_by_id(self, component_element_id: str):
        for element in self.elements:
            if element.component_element_id == component_element_id:
                return element
        return None

    def list_component_element_types(self):
        return list(self.element_types)

    def list_component_elements_for_component(self, component_id: str):
        return [item for item in self.elements if item.component_id == component_id]

    def list_realization_types_for_element_type(self, element_type_key: str):
        return list(self.realization_types.get(element_type_key, []))

    def list_realizations_for_component_element(self, component_element_id: str):
        return list(self.realizations.get(component_element_id, []))

    def list_brief_realization_targets(self, coder_run_brief_id: str):
        if coder_run_brief_id == 'brief-1':
            return [
                CoderBriefRealizationTargetRecord(
                    coder_brief_realization_target_id='target-1',
                    project_id='project-1',
                    work_item_id='work-1',
                    coder_run_brief_id='brief-1',
                    component_id='component-1',
                    component_element_id='element-1',
                    component_element_realization_id='realization-1',
                    depends_on_target_id=None,
                    target_intent='implement',
                    sequence_order=1,
                    is_required=True,
                    target_notes='note',
                    target_contract={},
                    metadata={},
                )
            ]
        return []


class _FakeLogger:
    def __init__(self) -> None:
        self.infos: list[tuple[str, dict[str, object]]] = []

    def info(self, event: str, **fields: object) -> None:
        self.infos.append((event, fields))

    def warning(self, event: str, **fields: object) -> None:
        self.infos.append((event, fields))


class ComponentDesignPlanningServicePhase34Tests(unittest.TestCase):
    def test_default_service_keeps_injected_collaborators(self) -> None:
        repo = _FakeRepository()
        logger = _FakeLogger()

        service = DefaultComponentDesignPlanningService(repository=repo, logger=logger)

        self.assertIs(service.repository, repo)
        self.assertIs(service.logger, logger)

    def test_plan_component_by_name_builds_planning_view(self) -> None:
        logger = _FakeLogger()
        service = DefaultComponentDesignPlanningService(repository=_FakeRepository(), logger=logger)

        view = service.plan_component_by_name('project-1', 'Component Design Planning Service')

        self.assertEqual(view.component_id, 'component-1')
        self.assertEqual(len(view.element_plans), 2)
        self.assertEqual(view.element_plans[0].element_key, 'interfaces')
        self.assertEqual(view.element_plans[0].realization_options[0].realization_type_key, 'service_interface')
        self.assertTrue(any('No current realization instances exist for component element functions.' == item for item in view.design_completeness_warnings))
        events = [event for event, _ in logger.infos]
        self.assertEqual(events, [
            'component_design_planning.plan_component',
            'component_design_planning.list_component_element_plans',
            'component_design_planning.list_component_element_plans',
            'component_design_planning.detect_component_design_gaps',
        ])

    def test_list_realization_options_for_element(self) -> None:
        service = DefaultComponentDesignPlanningService(repository=_FakeRepository(), logger=_FakeLogger())

        rows = service.list_realization_options('element-1')

        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0].is_default)
        self.assertTrue(rows[0].has_instances)

    def test_detect_component_design_gaps_reports_missing_instances(self) -> None:
        service = DefaultComponentDesignPlanningService(repository=_FakeRepository(), logger=_FakeLogger())

        gaps = service.detect_component_design_gaps('component-1')

        self.assertEqual(len(gaps), 1)
        self.assertEqual(gaps[0].gap_code, 'missing_realization_instances')
        self.assertEqual(gaps[0].severity, 'warning')

    def test_build_brief_planning_payload_returns_bridge_payload(self) -> None:
        logger = _FakeLogger()
        service = DefaultComponentDesignPlanningService(repository=_FakeRepository(), logger=logger)

        payload = service.build_brief_planning_payload('component-1', 'brief-1')

        self.assertEqual(payload.component_id, 'component-1')
        self.assertEqual(payload.component_aspects, ('interfaces', 'functions'))
        self.assertEqual(payload.target_modules, ('contracts.py',))
        self.assertEqual(payload.metadata['brief_target_count'], 1)
        self.assertEqual(payload.metadata['brief_target_ids'], ('target-1',))
        self.assertEqual(logger.infos[-1][0], 'component_design_planning.build_brief_planning_payload')

    def test_plan_component_requires_identity(self) -> None:
        service = DefaultComponentDesignPlanningService(repository=_FakeRepository(), logger=_FakeLogger())
        with self.assertRaisesRegex(ValueError, 'requires component_id or component_name'):
            service.plan_component(ComponentPlanningRequest(project_id='project-1'))

    def test_phase1_models_are_instantiable_and_structured(self) -> None:
        option = RealizationOptionView(
            realization_type_key='service_interface',
            realization_label='Service Interface',
            category='code_artifact',
            description='Public service contract',
            is_allowed=True,
            is_default=True,
            has_instances=False,
            is_brief_targetable=True,
            instance_count=0,
            metadata={'artifact_kind': 'service_interface'},
        )
        gap = PlanningGap(
            gap_code='missing_realization',
            severity='warning',
            affected_component_id='component-1',
            affected_component_element_id='element-1',
            note='No current realization exists.',
            recommended_next_action='Add a service interface realization.',
            metadata={'component_element_key': 'interfaces'},
        )

        self.assertEqual(option.realization_type_key, 'service_interface')
        self.assertEqual(gap.severity, 'warning')


if __name__ == '__main__':
    unittest.main()

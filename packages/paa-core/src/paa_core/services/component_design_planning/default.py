"""Default implementation shell for the component design planning service."""

from __future__ import annotations

from paa_core.repositories.component_design import (
    ComponentDesignRepository,
    ComponentElementRecord,
    ComponentElementTypeRecord,
    ComponentRecord,
)
from paa_core.services.implementation_plan_derivation.contracts import StructuredLogger

from .models import (
    BriefPlanningPayload,
    ComponentElementPlanningView,
    ComponentPlanningRequest,
    ComponentPlanningView,
    PlanningGap,
    RealizationOptionView,
)


class _NullStructuredLogger:
    def info(self, event: str, **fields: object) -> None:
        return None

    def warning(self, event: str, **fields: object) -> None:
        return None


class DefaultComponentDesignPlanningService:
    """Read-oriented planning service over structured component-design truth."""

    def __init__(
        self,
        *,
        repository: ComponentDesignRepository,
        logger: StructuredLogger | None = None,
    ) -> None:
        self._repository = repository
        self._logger = logger if logger is not None else _NullStructuredLogger()

    @property
    def repository(self) -> ComponentDesignRepository:
        return self._repository

    @property
    def logger(self) -> StructuredLogger:
        return self._logger

    def plan_component(self, request: ComponentPlanningRequest) -> ComponentPlanningView:
        component = self._resolve_component(request)
        self._logger.info(
            'component_design_planning.plan_component',
            project_id=request.project_id,
            component_id=component.component_id,
            component_name=component.name,
        )
        element_plans = self.list_component_element_plans(component.component_id) if request.include_elements else ()
        gaps = self.detect_component_design_gaps(component.component_id)
        warnings = tuple(gap.note for gap in gaps if gap.severity in {'warning', 'blocker'})
        notes = (
            f'{len(element_plans)} component element planning view(s) assembled.',
            'Planning output derived from structured component-design records.',
        )
        return ComponentPlanningView(
            component_id=component.component_id,
            project_id=component.project_id,
            component_name=component.name,
            component_role=component.role,
            system_layer=component.system_layer,
            tier=component.tier,
            description=component.description,
            status=component.status,
            element_plans=element_plans,
            design_completeness_warnings=warnings,
            planning_notes=notes,
            gaps=gaps,
            metadata=dict(component.metadata or {}),
        )

    def plan_component_by_name(self, project_id: str, component_name: str) -> ComponentPlanningView:
        return self.plan_component(
            ComponentPlanningRequest(
                project_id=project_id,
                component_name=component_name,
            )
        )

    def list_component_element_plans(self, component_id: str) -> tuple[ComponentElementPlanningView, ...]:
        component = self._repository.get_component_by_id(component_id)
        if component is None:
            raise LookupError(f'No component found for id {component_id!r}')
        type_map = self._element_type_map()
        plans: list[ComponentElementPlanningView] = []
        for element in self._repository.list_component_elements_for_component(component_id):
            element_type = type_map.get(element.component_element_type_id)
            if element_type is None:
                self._logger.warning(
                    'component_design_planning.unknown_element_type',
                    component_id=component_id,
                    component_element_id=element.component_element_id,
                    component_element_type_id=element.component_element_type_id,
                )
                continue
            plans.append(self._assemble_element_planning_view(component, element, element_type))
        self._logger.info(
            'component_design_planning.list_component_element_plans',
            component_id=component_id,
            element_count=len(plans),
        )
        return tuple(plans)

    def list_realization_options(self, component_element_id: str) -> tuple[RealizationOptionView, ...]:
        element = self._repository.get_component_element_by_id(component_element_id)
        if element is None:
            raise LookupError(f'No component element found for id {component_element_id!r}')
        element_type = self._element_type_map().get(element.component_element_type_id)
        if element_type is None:
            raise LookupError(
                f'No component element type found for component element {component_element_id!r}'
            )
        options = self._realization_options_for_element(element, element_type)
        self._logger.info(
            'component_design_planning.list_realization_options',
            component_element_id=component_element_id,
            option_count=len(options),
        )
        return options

    def build_brief_planning_payload(
        self, component_id: str, coder_run_brief_id: str | None = None
    ) -> BriefPlanningPayload:
        component = self._repository.get_component_by_id(component_id)
        if component is None:
            raise LookupError(f'No component found for id {component_id!r}')
        element_plans = self.list_component_element_plans(component_id)
        gaps = self.detect_component_design_gaps(component_id)
        warnings = tuple(gap.note for gap in gaps if gap.severity in {'warning', 'blocker'})
        component_aspects = self._component_aspects_from_element_plans(element_plans)
        target_modules = self._target_modules_for_component(component_id)
        brief_targets = self._repository.list_brief_realization_targets(coder_run_brief_id) if coder_run_brief_id else []
        payload = BriefPlanningPayload(
            component_id=component.component_id,
            component_name=component.name,
            coder_run_brief_id=coder_run_brief_id,
            component_aspects=component_aspects,
            target_modules=target_modules,
            element_plans=element_plans,
            gaps=gaps,
            warnings=warnings,
            metadata={
                'system_layer': component.system_layer,
                'tier': component.tier,
                'brief_target_count': len(brief_targets),
                'brief_target_ids': tuple(item.coder_brief_realization_target_id for item in brief_targets),
                'brief_target_intents': tuple(item.target_intent for item in brief_targets),
                'planning_source': 'ComponentDesignPlanningService',
            },
        )
        self._logger.info(
            'component_design_planning.build_brief_planning_payload',
            component_id=component_id,
            coder_run_brief_id=coder_run_brief_id,
            target_module_count=len(target_modules),
            gap_count=len(gaps),
        )
        return payload

    def detect_component_design_gaps(self, component_id: str) -> tuple[PlanningGap, ...]:
        component = self._repository.get_component_by_id(component_id)
        if component is None:
            raise LookupError(f'No component found for id {component_id!r}')
        gaps: list[PlanningGap] = []
        element_plans = self.list_component_element_plans(component_id)
        if not element_plans:
            gaps.append(
                PlanningGap(
                    gap_code='missing_component_elements',
                    severity='blocker',
                    affected_component_id=component_id,
                    affected_component_element_id=None,
                    note='The component has no component-element records to plan from.',
                    recommended_next_action='Author component elements before deriving brief-facing planning outputs.',
                    metadata={'component_name': component.name},
                )
            )
        for plan in element_plans:
            if not plan.realization_options:
                gaps.append(
                    PlanningGap(
                        gap_code='missing_realization_options',
                        severity='blocker',
                        affected_component_id=component_id,
                        affected_component_element_id=plan.component_element_id,
                        note=f'No allowed realization options are defined for component element {plan.element_key}.',
                        recommended_next_action='Add realization-type mappings for this component element type.',
                        metadata={'component_element_key': plan.element_key},
                    )
                )
            elif not plan.current_realization_keys:
                gaps.append(
                    PlanningGap(
                        gap_code='missing_realization_instances',
                        severity='warning',
                        affected_component_id=component_id,
                        affected_component_element_id=plan.component_element_id,
                        note=f'No current realization instances exist for component element {plan.element_key}.',
                        recommended_next_action='Author at least one realization instance for this component element before execution-facing derivation.',
                        metadata={'component_element_key': plan.element_key},
                    )
                )
        self._logger.info(
            'component_design_planning.detect_component_design_gaps',
            component_id=component_id,
            gap_count=len(gaps),
        )
        return tuple(gaps)

    def _resolve_component(self, request: ComponentPlanningRequest) -> ComponentRecord:
        component: ComponentRecord | None = None
        if request.component_id:
            component = self._repository.get_component_by_id(request.component_id)
        elif request.component_name:
            component = self._repository.get_component_by_name(request.project_id, request.component_name)
        else:
            raise ValueError('ComponentPlanningRequest requires component_id or component_name.')
        if component is None:
            raise LookupError('No component matched the planning request.')
        return component

    def _element_type_map(self) -> dict[str, ComponentElementTypeRecord]:
        return {
            record.component_element_type_id: record
            for record in self._repository.list_component_element_types()
        }

    def _realization_options_for_element(
        self,
        element: ComponentElementRecord,
        element_type: ComponentElementTypeRecord,
    ) -> tuple[RealizationOptionView, ...]:
        current_realizations = self._repository.list_realizations_for_component_element(element.component_element_id)
        current_by_key = {item.realization_key: item for item in current_realizations}
        options = []
        for option in self._repository.list_realization_types_for_element_type(element_type.element_key):
            options.append(
                RealizationOptionView(
                    realization_type_key=option.realization_key,
                    realization_label=option.label,
                    category=option.category,
                    description=option.description,
                    is_allowed=True,
                    is_default=option.is_default_for_element_type,
                    has_instances=option.realization_key in current_by_key,
                    is_brief_targetable=option.is_brief_targetable,
                    instance_count=sum(1 for item in current_realizations if item.realization_key == option.realization_key),
                    metadata=dict(option.metadata or {}),
                )
            )
        return tuple(options)

    def _assemble_element_planning_view(
        self,
        component: ComponentRecord,
        element: ComponentElementRecord,
        element_type: ComponentElementTypeRecord,
    ) -> ComponentElementPlanningView:
        current_realizations = self._repository.list_realizations_for_component_element(element.component_element_id)
        options = self._realization_options_for_element(element, element_type)
        warnings: list[str] = []
        if not options:
            warnings.append('No allowed realization options are defined for this element type.')
        if options and not current_realizations:
            warnings.append('No current realization instances exist for this component element.')
        downstream_hints = tuple(
            f'brief_targetable:{option.realization_type_key}'
            for option in options
            if option.is_brief_targetable
        )
        metadata = dict(element.metadata or {})
        metadata.setdefault('component_name', component.name)
        metadata.setdefault('component_role', component.role)
        return ComponentElementPlanningView(
            component_element_id=element.component_element_id,
            component_element_type_id=element.component_element_type_id,
            element_key=element.element_key,
            element_label=element_type.label,
            category=element_type.category,
            title=element.title,
            status=element.status,
            definition=dict(element.definition or {}),
            current_realization_keys=tuple(item.realization_key for item in current_realizations),
            realization_options=options,
            planning_warnings=tuple(warnings),
            downstream_use_hints=downstream_hints,
            metadata=metadata,
        )

    def _component_aspects_from_element_plans(
        self,
        element_plans: tuple[ComponentElementPlanningView, ...],
    ) -> tuple[str, ...]:
        aspects: list[str] = []
        element_keys = {item.element_key for item in element_plans}
        if 'interfaces' in element_keys:
            aspects.append('interfaces')
        if 'functions' in element_keys:
            aspects.append('functions')
        if 'data_contract' in element_keys:
            aspects.append('data_contract')
        if 'verification_surfaces' in element_keys:
            aspects.append('tests')
        return tuple(aspects or ['functions'])

    def _target_modules_for_component(self, component_id: str) -> tuple[str, ...]:
        modules: list[str] = []
        for element in self._repository.list_component_elements_for_component(component_id):
            for realization in self._repository.list_realizations_for_component_element(element.component_element_id):
                artifact_ref = realization.artifact_ref or {}
                module_path = artifact_ref.get('module_path') or artifact_ref.get('module')
                if module_path and module_path not in modules:
                    modules.append(str(module_path))
        if not modules:
            for element in self._repository.list_component_elements_for_component(component_id):
                module_hint = (element.definition or {}).get('module')
                if module_hint and module_hint not in modules:
                    modules.append(str(module_hint))
        return tuple(modules)


__all__ = ['DefaultComponentDesignPlanningService']

"""Default implementation of the Implementation Plan Derivation service."""

from __future__ import annotations

from dataclasses import replace
from typing import cast

from paa_core.repositories.implementation_plan import (
    ImplementationPlanActivityDependencyUpsertSpec,
    ImplementationPlanActivityUpsertSpec,
    ImplementationPlanRepository,
)

from .models import (
    ImplementationPlanActivityBlueprint,
    ImplementationPlanDerivationRequest,
    ImplementationPlanDerivationResult,
)


class _NullStructuredLogger:
    def info(self, event: str, **fields: object) -> None:
        return None

    def warning(self, event: str, **fields: object) -> None:
        return None


class DefaultImplementationPlanDerivationService:
    """Derive implementation-plan truth from structured activity blueprints."""

    def __init__(
        self,
        *,
        repository: ImplementationPlanRepository,
        logger: object | None = None,
    ) -> None:
        self._repository = repository
        self._logger = logger if logger is not None else _NullStructuredLogger()

    def derive_plan(self, request: ImplementationPlanDerivationRequest) -> ImplementationPlanDerivationResult:
        activity_specs = tuple(self._activity_spec_from_blueprint(item) for item in request.activity_blueprints)
        dependency_specs = self._dependency_specs_from_blueprints(request.activity_blueprints)
        warnings, gaps = self._detect_warnings_and_gaps(request.activity_blueprints)

        if request.persist:
            self._log_info(
                'implementation_plan_derivation.persist_start',
                design_package_id=request.plan.design_package_id,
                consumer_context_key=request.plan.consumer_context_key,
                activity_count=len(activity_specs),
            )
            self._repository.upsert_implementation_plan(request.plan)
            plan_record = self._repository.get_implementation_plan_for_design_package(
                request.plan.design_package_id,
                request.plan.consumer_context_key,
            )
            if plan_record is None:
                raise RuntimeError('implementation plan derivation persisted no resolvable plan root')
            for spec in activity_specs:
                self._repository.upsert_implementation_plan_activity(
                    replace(spec, implementation_plan_id=plan_record.implementation_plan_id)
                )
            for spec in dependency_specs:
                self._repository.upsert_implementation_plan_activity_dependency(
                    replace(spec, implementation_plan_id=plan_record.implementation_plan_id)
                )
            self._log_info(
                'implementation_plan_derivation.persist_complete',
                implementation_plan_id=plan_record.implementation_plan_id,
                dependency_count=len(dependency_specs),
                warning_count=len(warnings),
                gap_count=len(gaps),
            )
            persisted = True
        else:
            plan_record = self._ephemeral_plan_record(request)
            persisted = False
            self._log_info(
                'implementation_plan_derivation.dry_run_complete',
                design_package_id=request.plan.design_package_id,
                activity_count=len(activity_specs),
            )

        for warning in warnings:
            self._log_warning('implementation_plan_derivation.warning', message=warning)
        for gap in gaps:
            self._log_warning('implementation_plan_derivation.gap', message=gap)

        return ImplementationPlanDerivationResult(
            plan_record=plan_record,
            activity_specs=tuple(
                replace(spec, implementation_plan_id=plan_record.implementation_plan_id) for spec in activity_specs
            ),
            dependency_specs=tuple(
                replace(spec, implementation_plan_id=plan_record.implementation_plan_id) for spec in dependency_specs
            ),
            verification_surfaces=request.verification_surfaces,
            warnings=warnings,
            gaps=gaps,
            persisted=persisted,
        )

    @staticmethod
    def _activity_spec_from_blueprint(
        blueprint: ImplementationPlanActivityBlueprint,
    ) -> ImplementationPlanActivityUpsertSpec:
        metadata = dict(blueprint.metadata or {})
        if blueprint.component_element_key:
            metadata.setdefault('component_element_key', blueprint.component_element_key)
        if blueprint.code_artifact_target_key:
            metadata.setdefault('code_artifact_target_key', blueprint.code_artifact_target_key)
        return ImplementationPlanActivityUpsertSpec(
            implementation_plan_id='00000000-0000-0000-0000-000000000000',
            component_element_id=blueprint.component_element_id,
            component_element_realization_id=blueprint.component_element_realization_id,
            assigned_role_id=blueprint.assigned_role_id,
            activity_key=blueprint.activity_key,
            activity_title=blueprint.activity_title,
            activity_kind=blueprint.activity_kind,
            activity_state=blueprint.activity_state,
            sequence_order=blueprint.sequence_order,
            target_path=blueprint.target_path,
            target_module=blueprint.target_module,
            planned_artifact_type_key=blueprint.code_artifact_target_key,
            blocking_reason=blueprint.blocking_reason,
            metadata=metadata,
        )

    @staticmethod
    def _dependency_specs_from_blueprints(
        blueprints: tuple[ImplementationPlanActivityBlueprint, ...],
    ) -> tuple[ImplementationPlanActivityDependencyUpsertSpec, ...]:
        specs: list[ImplementationPlanActivityDependencyUpsertSpec] = []
        for blueprint in blueprints:
            for predecessor_key in blueprint.predecessor_activity_keys:
                specs.append(
                    ImplementationPlanActivityDependencyUpsertSpec(
                        implementation_plan_id='00000000-0000-0000-0000-000000000000',
                        predecessor_activity_key=predecessor_key,
                        successor_activity_key=blueprint.activity_key,
                        sequencing_requirement='must_precede',
                        dependency_strength='hard',
                        notes=f'{blueprint.activity_key} follows {predecessor_key}',
                        metadata={
                            'source': 'DefaultImplementationPlanDerivationService',
                            'successor_artifact_target': blueprint.code_artifact_target_key,
                        },
                    )
                )
        return tuple(specs)

    @staticmethod
    def _detect_warnings_and_gaps(
        blueprints: tuple[ImplementationPlanActivityBlueprint, ...],
    ) -> tuple[tuple[str, ...], tuple[str, ...]]:
        warnings: list[str] = []
        gaps: list[str] = []
        if not blueprints:
            gaps.append('No implementation-plan activities were supplied for derivation.')
        seen_keys: set[str] = set()
        for blueprint in blueprints:
            if blueprint.activity_key in seen_keys:
                gaps.append(f"Duplicate activity key detected: {blueprint.activity_key}")
            seen_keys.add(blueprint.activity_key)
            if blueprint.component_element_id is None:
                warnings.append(f"Activity {blueprint.activity_key} has no component_element_id binding.")
            if blueprint.code_artifact_target_key is None:
                warnings.append(f"Activity {blueprint.activity_key} has no code artifact target binding.")
            if blueprint.target_path is None and blueprint.target_module is None:
                warnings.append(f"Activity {blueprint.activity_key} has no target surface hint.")
        return tuple(warnings), tuple(gaps)

    @staticmethod
    def _ephemeral_plan_record(request: ImplementationPlanDerivationRequest):
        from paa_core.repositories.implementation_plan import ImplementationPlanRecord

        return cast(ImplementationPlanRecord, ImplementationPlanRecord(
            implementation_plan_id='00000000-0000-0000-0000-000000000000',
            project_id=request.plan.project_id,
            work_item_id=request.plan.work_item_id,
            design_package_id=request.plan.design_package_id,
            spec_fragment_id=request.plan.spec_fragment_id,
            implementation_target_id=request.plan.implementation_target_id,
            authority_version_id=request.plan.authority_version_id,
            primary_component_id=request.plan.primary_component_id,
            plan_id_external=request.plan.plan_id_external,
            schema_version=request.plan.schema_version,
            consumer_context_key=request.plan.consumer_context_key,
            plan_title=request.plan.plan_title,
            plan_kind=request.plan.plan_kind,
            status=request.plan.status,
            authority_state=request.plan.authority_state,
            authority_state_updated_at=None,
            plan=request.plan.plan or {},
            build_sequence=request.plan.build_sequence or {},
            touch_surfaces=request.plan.touch_surfaces or {},
            protected_constraints=request.plan.protected_constraints or {},
            verification_plan=request.plan.verification_plan or {},
            provenance=request.plan.provenance or {},
            metadata=request.plan.metadata or {},
            created_by_role_id=request.plan.created_by_role_id,
            created_by_agent_id=request.plan.created_by_agent_id,
            approved_at=request.plan.approved_at,
            activated_at=request.plan.activated_at,
            completed_at=request.plan.completed_at,
            created_at=None,
            updated_at=None,
        ))

    def _log_info(self, event: str, **fields: object) -> None:
        info = getattr(self._logger, 'info', None)
        if callable(info):
            info(event, **fields)

    def _log_warning(self, event: str, **fields: object) -> None:
        warning = getattr(self._logger, 'warning', None)
        if callable(warning):
            warning(event, **fields)


__all__ = ['DefaultImplementationPlanDerivationService']

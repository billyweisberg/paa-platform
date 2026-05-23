"""Default implementation-plan progress and successor derivation service."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from paa_core.repositories.implementation_plan import (
    ImplementationPlanActivityDependencyRecord,
    ImplementationPlanActivityRecord,
    ImplementationPlanRecord,
    ImplementationPlanRepository,
    ImplementationPlanVerificationSurfaceRecord,
)
from paa_core.services.implementation_plan_derivation.contracts import StructuredLogger

from .models import (
    ActivityProgressDetail,
    ComponentRealizationState,
    ImplementationPlanProgressRequest,
    ImplementationPlanProgressSummary,
    NextActivityBundleRequest,
    NextActivityBundleResult,
    PlanAuthorityStateSummary,
)


class _NullStructuredLogger:
    def info(self, event: str, **fields: object) -> None:
        return None

    def warning(self, event: str, **fields: object) -> None:
        return None


class DefaultImplementationPlanProgressService:
    """Compute current implementation-plan progress and next executable activity."""

    _REQUIRED_VERIFICATION_COMPLETE = frozenset({'passed', 'waived'})
    _COMPLETED_ACTIVITY_STATES = frozenset({'completed'})
    _CURRENT_ACTIVITY_STATES = frozenset({'in_progress', 'active'})
    _DEFERRED_ACTIVITY_STATES = frozenset({'deferred', 'skipped'})
    _BLOCKED_ACTIVITY_STATES = frozenset({'blocked'})
    _CANCELLED_ACTIVITY_STATES = frozenset({'cancelled', 'superseded'})

    def __init__(
        self,
        *,
        repository: ImplementationPlanRepository,
        logger: StructuredLogger | None = None,
    ) -> None:
        self._repository = repository
        self._logger = logger if logger is not None else _NullStructuredLogger()

    @property
    def repository(self) -> ImplementationPlanRepository:
        return self._repository

    @property
    def logger(self) -> StructuredLogger:
        return self._logger

    def summarize_plan_progress(
        self,
        request: ImplementationPlanProgressRequest,
    ) -> ImplementationPlanProgressSummary:
        plan = self._require_plan(request.implementation_plan_id)
        activities = self._repository.list_implementation_plan_activities(plan.implementation_plan_id)
        dependencies = self._repository.list_implementation_plan_activity_dependencies(plan.implementation_plan_id)
        verification_surfaces = self._repository.list_implementation_plan_verification_surfaces(plan.implementation_plan_id)
        summary = self._build_summary(plan, activities, dependencies, verification_surfaces)
        self._logger.info(
            'implementation_plan_progress.summarize',
            implementation_plan_id=summary.implementation_plan_id,
            authority_state_summary=summary.authority_state_summary,
            realization_state=summary.realization_state,
            next_activity_key=summary.next_activity_key,
        )
        return summary

    def derive_next_activity_bundle(
        self,
        request: NextActivityBundleRequest,
    ) -> NextActivityBundleResult:
        summary = self.summarize_plan_progress(
            ImplementationPlanProgressRequest(
                implementation_plan_id=request.implementation_plan_id,
                metadata=request.metadata,
            )
        )
        if summary.realization_state == 'fully_realized':
            return NextActivityBundleResult(
                implementation_plan_id=summary.implementation_plan_id,
                plan_id_external=summary.plan_id_external,
                ok=False,
                next_bundle_activity_keys=(),
                bundle_kind='none',
                decision_reason='No required incomplete activities remain for the currently authorized implementation plan.',
                blocking_reasons=(),
                unattended_safe=True,
                recommended_next_authority_action='Mark the component fully realized or derive a successor authority update only if design truth changes.',
                realization_state=summary.realization_state,
                metadata={'progress_summary': asdict(summary)},
            )
        if summary.next_activity_key is None:
            blocking = list(summary.blocked_activity_keys)
            if summary.remaining_activity_keys:
                blocking.append('No executable next activity could be derived from the current dependency and verification state.')
            return NextActivityBundleResult(
                implementation_plan_id=summary.implementation_plan_id,
                plan_id_external=summary.plan_id_external,
                ok=False,
                next_bundle_activity_keys=(),
                bundle_kind='blocked',
                decision_reason='The next implementation slice cannot be derived from the current plan state.',
                blocking_reasons=tuple(blocking),
                unattended_safe=False,
                recommended_next_authority_action='Resolve blocked or ambiguous predecessor state before deriving the next activity bundle.',
                realization_state=summary.realization_state,
                metadata={'progress_summary': asdict(summary)},
            )
        return NextActivityBundleResult(
            implementation_plan_id=summary.implementation_plan_id,
            plan_id_external=summary.plan_id_external,
            ok=True,
            next_bundle_activity_keys=(summary.next_activity_key,),
            bundle_kind='single_activity',
            decision_reason='Derived the first dependency-clear remaining activity under the current plan authority.',
            blocking_reasons=(),
            unattended_safe=True,
            recommended_next_authority_action='Execute the next implementation activity and update plan progress after verification.',
            realization_state=summary.realization_state,
            metadata={'progress_summary': asdict(summary)},
        )

    def _require_plan(self, implementation_plan_id: str) -> ImplementationPlanRecord:
        plan = self._repository.get_implementation_plan(implementation_plan_id)
        if plan is None:
            raise LookupError(f'No implementation plan found for {implementation_plan_id!r}')
        return plan

    def _build_summary(
        self,
        plan: ImplementationPlanRecord,
        activities: list[ImplementationPlanActivityRecord],
        dependencies: list[ImplementationPlanActivityDependencyRecord],
        verification_surfaces: list[ImplementationPlanVerificationSurfaceRecord],
    ) -> ImplementationPlanProgressSummary:
        if not activities:
            return ImplementationPlanProgressSummary(
                implementation_plan_id=plan.implementation_plan_id,
                plan_id_external=plan.plan_id_external,
                primary_component_id=plan.primary_component_id,
                authority_state_summary='draft_plan',
                realization_state='not_started',
                completion_ratio=0.0,
                completed_activity_keys=(),
                deferred_activity_keys=(),
                blocked_activity_keys=(),
                remaining_activity_keys=(),
                current_activity_key=None,
                next_activity_key=None,
                remaining_activity_count=0,
                deferred_activity_count=0,
                blocked_activity_count=0,
                last_completed_activity_key=None,
                activity_details=(),
                metadata={'component_completion': self._component_completion_metadata(plan, None, None, (), (), (), (), None, None, 'not_started', 'draft_plan')},
            )

        activities_by_id = {activity.implementation_plan_activity_id: activity for activity in activities}
        required_by_activity_id: dict[str, list[ImplementationPlanVerificationSurfaceRecord]] = {}
        for surface in verification_surfaces:
            if surface.implementation_plan_activity_id is None or not surface.required:
                continue
            required_by_activity_id.setdefault(surface.implementation_plan_activity_id, []).append(surface)

        predecessor_keys_by_successor: dict[str, set[str]] = {}
        for dependency in dependencies:
            predecessor_keys_by_successor.setdefault(dependency.successor_activity_key, set()).add(
                dependency.predecessor_activity_key
            )

        details: list[ActivityProgressDetail] = []
        completed: list[str] = []
        deferred: list[str] = []
        blocked: list[str] = []
        remaining: list[str] = []
        current_activity_key: str | None = None
        last_completed_activity_key: str | None = None

        for activity in activities:
            required_surfaces = tuple(required_by_activity_id.get(activity.implementation_plan_activity_id, ()))
            missing_required = tuple(
                surface.surface_ref
                for surface in required_surfaces
                if surface.status not in self._REQUIRED_VERIFICATION_COMPLETE
            )
            classification = self._classify_activity(activity, missing_required)
            detail = ActivityProgressDetail(
                activity_key=activity.activity_key,
                activity_state=activity.activity_state,
                classification=classification,
                sequence_order=activity.sequence_order,
                blocking_reason=activity.blocking_reason,
                required_verification_statuses=tuple(surface.status for surface in required_surfaces),
                missing_required_verification=missing_required,
            )
            details.append(detail)
            if classification == 'completed':
                completed.append(activity.activity_key)
                last_completed_activity_key = activity.activity_key
            elif classification == 'deferred':
                deferred.append(activity.activity_key)
            elif classification == 'blocked':
                blocked.append(activity.activity_key)
            else:
                remaining.append(activity.activity_key)
            if activity.activity_state in self._CURRENT_ACTIVITY_STATES:
                current_activity_key = activity.activity_key

        successor_issue: str | None = None
        try:
            next_activity_key = self._derive_next_activity_key(
                activities=activities,
                predecessor_keys_by_successor=predecessor_keys_by_successor,
                completed_keys=frozenset(completed),
                blocked_keys=frozenset(blocked),
                remaining_keys=frozenset(remaining),
            )
        except ValueError as exc:
            next_activity_key = None
            successor_issue = str(exc)
            if successor_issue not in blocked:
                blocked.append(successor_issue)
        completion_ratio = len(completed) / len(activities)
        realization_state = self._derive_realization_state(
            completed_count=len(completed),
            remaining_count=len(remaining),
            blocked_count=len(blocked),
            deferred_count=len(deferred),
            total_count=len(activities),
        )
        authority_state_summary = self._derive_authority_state_summary(realization_state, remaining, blocked, deferred)
        metadata = self._component_completion_metadata(
            plan,
            completion_ratio,
            current_activity_key,
            tuple(completed),
            tuple(deferred),
            tuple(blocked),
            tuple(remaining),
            next_activity_key,
            last_completed_activity_key,
            realization_state,
            authority_state_summary,
        )
        if successor_issue is not None:
            metadata['successor_derivation_issue'] = successor_issue
        return ImplementationPlanProgressSummary(
            implementation_plan_id=plan.implementation_plan_id,
            plan_id_external=plan.plan_id_external,
            primary_component_id=plan.primary_component_id,
            authority_state_summary=authority_state_summary,
            realization_state=realization_state,
            completion_ratio=completion_ratio,
            completed_activity_keys=tuple(completed),
            deferred_activity_keys=tuple(deferred),
            blocked_activity_keys=tuple(blocked),
            remaining_activity_keys=tuple(remaining),
            current_activity_key=current_activity_key,
            next_activity_key=next_activity_key,
            remaining_activity_count=len(remaining),
            deferred_activity_count=len(deferred),
            blocked_activity_count=len(blocked),
            last_completed_activity_key=last_completed_activity_key,
            activity_details=tuple(details),
            metadata={'component_completion': metadata},
        )

    def _classify_activity(
        self,
        activity: ImplementationPlanActivityRecord,
        missing_required_verification: tuple[str, ...],
    ) -> str:
        state = activity.activity_state
        if state in self._CANCELLED_ACTIVITY_STATES:
            return 'deferred'
        if state in self._DEFERRED_ACTIVITY_STATES:
            return 'deferred'
        if state in self._BLOCKED_ACTIVITY_STATES:
            return 'blocked'
        if state in self._COMPLETED_ACTIVITY_STATES and not missing_required_verification:
            return 'completed'
        if state in self._COMPLETED_ACTIVITY_STATES and missing_required_verification:
            return 'blocked'
        return 'remaining'

    def _derive_next_activity_key(
        self,
        *,
        activities: list[ImplementationPlanActivityRecord],
        predecessor_keys_by_successor: dict[str, set[str]],
        completed_keys: frozenset[str],
        blocked_keys: frozenset[str],
        remaining_keys: frozenset[str],
    ) -> str | None:
        executable: list[ImplementationPlanActivityRecord] = []
        for activity in activities:
            if activity.activity_key not in remaining_keys:
                continue
            predecessor_keys = predecessor_keys_by_successor.get(activity.activity_key, set())
            if predecessor_keys & blocked_keys:
                continue
            unsatisfied = [key for key in predecessor_keys if key not in completed_keys]
            if unsatisfied:
                continue
            executable.append(activity)
        if not executable:
            return None
        executable.sort(key=lambda item: (item.sequence_order, item.activity_key))
        first = executable[0]
        same_rank = [item for item in executable if item.sequence_order == first.sequence_order]
        if len(same_rank) > 1:
            raise ValueError(
                'Duplicate executable activities share the same sequence order; successor derivation is ambiguous.'
            )
        return first.activity_key

    def _derive_realization_state(
        self,
        *,
        completed_count: int,
        remaining_count: int,
        blocked_count: int,
        deferred_count: int,
        total_count: int,
    ) -> ComponentRealizationState:
        if total_count == 0 or completed_count == 0:
            if blocked_count > 0:
                return 'blocked'
            if deferred_count > 0 and remaining_count == 0:
                return 'deferred'
            return 'not_started'
        if remaining_count == 0 and blocked_count == 0:
            return 'fully_realized'
        if blocked_count > 0 and remaining_count > 0:
            return 'blocked'
        if remaining_count == 0 and deferred_count > 0:
            return 'deferred'
        completion_ratio = completed_count / total_count
        if completion_ratio >= 0.75:
            return 'substantially_realized'
        return 'partially_realized'

    def _derive_authority_state_summary(
        self,
        realization_state: ComponentRealizationState,
        remaining: list[str],
        blocked: list[str],
        deferred: list[str],
    ) -> PlanAuthorityStateSummary:
        if realization_state == 'fully_realized':
            return 'completed_plan'
        if realization_state == 'blocked':
            return 'blocked_plan'
        if realization_state == 'deferred' and not remaining:
            return 'deferred_plan'
        if realization_state in {'partially_realized', 'substantially_realized'}:
            return 'partially_realized_plan'
        if remaining or blocked or deferred:
            return 'active_plan'
        return 'draft_plan'

    def _component_completion_metadata(
        self,
        plan: ImplementationPlanRecord,
        completion_ratio: float | None,
        current_activity_key: str | None,
        completed: tuple[str, ...],
        deferred: tuple[str, ...],
        blocked: tuple[str, ...],
        remaining: tuple[str, ...],
        next_activity_key: str | None,
        last_completed_activity_key: str | None,
        realization_state: ComponentRealizationState,
        authority_state_summary: PlanAuthorityStateSummary,
    ) -> dict[str, Any]:
        existing = dict((plan.metadata or {}).get('component_completion') or {})
        existing.update(
            {
                'realization_state': realization_state,
                'authority_state_summary': authority_state_summary,
                'completion_ratio': completion_ratio if completion_ratio is not None else 0.0,
                'current_activity_key': current_activity_key,
                'next_activity_key': next_activity_key,
                'remaining_activity_count': len(remaining),
                'deferred_activity_count': len(deferred),
                'blocked_activity_count': len(blocked),
                'last_completed_activity_key': last_completed_activity_key,
                'completed_activity_keys': list(completed),
                'deferred_activity_keys': list(deferred),
                'blocked_activity_keys': list(blocked),
                'remaining_activity_keys': list(remaining),
            }
        )
        return existing


__all__ = ['DefaultImplementationPlanProgressService']

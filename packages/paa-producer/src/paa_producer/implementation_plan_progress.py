"""Producer-side entrypoints for implementation-plan progress and successor derivation."""

from __future__ import annotations

from dataclasses import asdict

from paa_core.repositories.implementation_plan import (
    ImplementationPlanProgressUpdateSpec,
    PostgresImplementationPlanRepository,
)
from paa_core.services.implementation_plan_progress import (
    DefaultImplementationPlanProgressService,
    ImplementationPlanProgressRequest,
    NextActivityBundleRequest,
)


class _ServiceLogger:
    def info(self, event: str, **fields: object) -> None:
        return None

    def warning(self, event: str, **fields: object) -> None:
        return None


def implementation_plan_progress(*, plan_id: str) -> dict[str, object]:
    service = DefaultImplementationPlanProgressService(
        repository=PostgresImplementationPlanRepository(),
        logger=_ServiceLogger(),
    )
    summary = service.summarize_plan_progress(
        ImplementationPlanProgressRequest(implementation_plan_id=plan_id)
    )
    return asdict(summary)


def derive_next_activity_bundle(*, plan_id: str) -> dict[str, object]:
    service = DefaultImplementationPlanProgressService(
        repository=PostgresImplementationPlanRepository(),
        logger=_ServiceLogger(),
    )
    result = service.derive_next_activity_bundle(
        NextActivityBundleRequest(implementation_plan_id=plan_id)
    )
    return asdict(result)


def reconcile_implementation_plan_progress(*, plan_id: str) -> dict[str, object]:
    repository = PostgresImplementationPlanRepository()
    service = DefaultImplementationPlanProgressService(
        repository=repository,
        logger=_ServiceLogger(),
    )
    summary = service.summarize_plan_progress(
        ImplementationPlanProgressRequest(implementation_plan_id=plan_id)
    )
    repository.update_implementation_plan_progress(
        ImplementationPlanProgressUpdateSpec(
            implementation_plan_id=plan_id,
            component_completion=dict(summary.metadata.get('component_completion') or {}),
            authority_state=summary.authority_state_summary,
            completed_at=None if summary.authority_state_summary != 'completed_plan' else None,
        )
    )
    return asdict(summary)

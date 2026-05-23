"""Contracts for implementation-plan progress and successor derivation."""

from __future__ import annotations

from typing import Protocol

from paa_core.repositories.implementation_plan import ImplementationPlanRepository
from paa_core.services.implementation_plan_derivation.contracts import StructuredLogger

from .models import (
    ImplementationPlanProgressRequest,
    ImplementationPlanProgressSummary,
    NextActivityBundleRequest,
    NextActivityBundleResult,
)


class ImplementationPlanProgressService(Protocol):
    """Compute iterative plan-progress truth and successor slices."""

    @property
    def repository(self) -> ImplementationPlanRepository:
        ...

    @property
    def logger(self) -> StructuredLogger:
        ...

    def summarize_plan_progress(
        self,
        request: ImplementationPlanProgressRequest,
    ) -> ImplementationPlanProgressSummary:
        ...

    def derive_next_activity_bundle(
        self,
        request: NextActivityBundleRequest,
    ) -> NextActivityBundleResult:
        ...


__all__ = ['ImplementationPlanProgressService', 'StructuredLogger']

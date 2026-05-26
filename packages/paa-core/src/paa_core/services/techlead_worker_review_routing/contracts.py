"""Contracts for the TechLead worker review routing service."""

from __future__ import annotations

from typing import Protocol

from paa_core.services.implementation_plan_derivation.contracts import StructuredLogger

from .models import (
    TechLeadWorkerReviewRoutingRequest,
    TechLeadWorkerReviewRoutingResult,
)


class TechLeadWorkerReviewRoutingService(Protocol):
    """Derive supported worker-review routing decisions for one active slice."""

    @property
    def logger(self) -> StructuredLogger:
        """Return the injected structured logger."""
        ...

    def derive_worker_review_routing(
        self,
        request: TechLeadWorkerReviewRoutingRequest,
    ) -> TechLeadWorkerReviewRoutingResult:
        """Return one structured review-routing result from the provided worker-result context."""
        ...

    def supports_worker_review_routing(
        self,
        workflow_stage: str,
        worker_result_type: str | None = None,
    ) -> bool:
        """Return whether the current slice supports worker-review routing for this stage."""
        ...

__all__ = [
    'StructuredLogger',
    'TechLeadWorkerReviewRoutingRequest',
    'TechLeadWorkerReviewRoutingResult',
    'TechLeadWorkerReviewRoutingService',
]

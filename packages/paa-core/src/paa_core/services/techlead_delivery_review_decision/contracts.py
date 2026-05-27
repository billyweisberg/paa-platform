"""Contracts for the TechLead delivery review decision service."""

from __future__ import annotations

from typing import Protocol

from paa_core.services.implementation_plan_derivation.contracts import StructuredLogger

from .models import (
    TechLeadDeliveryReviewDecisionRequest,
    TechLeadDeliveryReviewDecisionResult,
)


class TechLeadDeliveryReviewDecisionService(Protocol):
    """Derive supported delivery-review routing decisions for one active slice."""

    @property
    def logger(self) -> StructuredLogger:
        """Return the injected structured logger."""
        ...

    def derive_delivery_review_decision(
        self,
        request: TechLeadDeliveryReviewDecisionRequest,
    ) -> TechLeadDeliveryReviewDecisionResult:
        """Return one structured delivery-review decision from the provided review context."""
        ...

    def supports_delivery_review_decision(
        self,
        workflow_stage: str,
        delivery_review_result_type: str | None = None,
    ) -> bool:
        """Return whether the current slice supports delivery-review routing for this stage."""
        ...


__all__ = [
    'StructuredLogger',
    'TechLeadDeliveryReviewDecisionRequest',
    'TechLeadDeliveryReviewDecisionResult',
    'TechLeadDeliveryReviewDecisionService',
]

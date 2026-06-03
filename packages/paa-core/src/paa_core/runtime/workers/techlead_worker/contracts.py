"""Contracts for the TechLead worker service."""

from __future__ import annotations

from typing import Protocol

from paa_core.repositories.methodology_execution import MethodologyExecutionRepository
from paa_core.services.implementation_plan_derivation.contracts import StructuredLogger
from paa_core.runtime.workflow.methodology_execution_preflight import MethodologyExecutionPreflightService
from paa_core.runtime.workflow.methodology_execution_projection import MethodologyExecutionProjectionService
from paa_core.runtime.workflow.methodology_execution_state import MethodologyExecutionStateService
from paa_core.services.techlead_acceptance_decision import TechLeadAcceptanceDecisionService
from paa_core.services.techlead_assignment_decision import TechLeadAssignmentDecisionService
from paa_core.services.techlead_closeout_decision import TechLeadCloseoutDecisionService
from paa_core.services.techlead_delivery_review_decision import TechLeadDeliveryReviewDecisionService
from paa_core.services.techlead_lineage_decision import TechLeadLineageDecisionService
from paa_core.services.techlead_reset_recovery_decision import TechLeadResetRecoveryDecisionService
from paa_core.services.techlead_worker_review_routing import TechLeadWorkerReviewRoutingService

from .models import TechLeadWorkerRequest, TechLeadWorkerResult


class TechLeadWorkerService(Protocol):
    """Coordinate deterministic TechLead packet handling for supported runtime slices."""

    @property
    def methodology_execution_repository(self) -> MethodologyExecutionRepository:
        """Return the injected methodology-execution repository."""
        ...

    @property
    def methodology_execution_state_service(self) -> MethodologyExecutionStateService:
        """Return the injected methodology-execution state service."""
        ...

    @property
    def methodology_execution_projection_service(self) -> MethodologyExecutionProjectionService:
        """Return the injected methodology-execution projection service."""
        ...

    @property
    def methodology_execution_preflight_service(self) -> MethodologyExecutionPreflightService:
        """Return the injected methodology-execution preflight service."""
        ...

    @property
    def techlead_assignment_decision_service(self) -> TechLeadAssignmentDecisionService:
        """Return the injected TechLead assignment decision service."""
        ...

    @property
    def techlead_worker_review_routing_service(self) -> TechLeadWorkerReviewRoutingService:
        """Return the injected TechLead worker-review routing service."""
        ...

    @property
    def techlead_acceptance_decision_service(self) -> TechLeadAcceptanceDecisionService:
        """Return the injected TechLead acceptance decision service."""
        ...

    @property
    def techlead_delivery_review_decision_service(self) -> TechLeadDeliveryReviewDecisionService:
        """Return the injected TechLead delivery-review decision service."""
        ...

    @property
    def techlead_reset_recovery_decision_service(self) -> TechLeadResetRecoveryDecisionService:
        """Return the injected TechLead reset-recovery decision service."""
        ...

    @property
    def techlead_lineage_decision_service(self) -> TechLeadLineageDecisionService:
        """Return the injected TechLead lineage decision service."""
        ...

    @property
    def techlead_closeout_decision_service(self) -> TechLeadCloseoutDecisionService:
        """Return the injected TechLead closeout decision service."""
        ...

    @property
    def logger(self) -> StructuredLogger:
        """Return the injected structured logger."""
        ...

    def handle_packet(self, request: TechLeadWorkerRequest) -> TechLeadWorkerResult:
        """Handle one supported TechLead-visible packet request."""
        ...

    def supports_packet_schema_type(self, packet_schema_type: str) -> bool:
        """Return whether the service slice supports one packet schema type."""
        ...


__all__ = [
    'MethodologyExecutionPreflightService',
    'MethodologyExecutionProjectionService',
    'MethodologyExecutionRepository',
    'MethodologyExecutionStateService',
    'StructuredLogger',
    'TechLeadAcceptanceDecisionService',
    'TechLeadAssignmentDecisionService',
    'TechLeadCloseoutDecisionService',
    'TechLeadDeliveryReviewDecisionService',
    'TechLeadLineageDecisionService',
    'TechLeadResetRecoveryDecisionService',
    'TechLeadWorkerRequest',
    'TechLeadWorkerResult',
    'TechLeadWorkerReviewRoutingService',
    'TechLeadWorkerService',
]

"""TechLead worker service package for PAA."""

from paa_core.governance import GovernedComponentMetadata

from .contracts import (
    MethodologyExecutionPreflightService,
    MethodologyExecutionProjectionService,
    MethodologyExecutionRepository,
    MethodologyExecutionStateService,
    StructuredLogger,
    TechLeadAcceptanceDecisionService,
    TechLeadAssignmentDecisionService,
    TechLeadCloseoutDecisionService,
    TechLeadDeliveryReviewDecisionService,
    TechLeadLineageDecisionService,
    TechLeadResetRecoveryDecisionService,
    TechLeadWorkerReviewRoutingService,
    TechLeadWorkerService,
)
from .default import DefaultTechLeadWorkerService
from .models import (
    TechLeadWorkerDispatchSummary,
    TechLeadWorkerRequest,
    TechLeadWorkerResult,
)

TECHLEAD_WORKER_SERVICE_METADATA = GovernedComponentMetadata(
    name='TechLeadWorkerService',
    kind='service',
    alignment='aligned',
    lifecycle_stage='build',
    owns=(
        'deterministic TechLead packet-handling orchestration for supported runtime slices',
        'handler selection over extracted TechLead decision services',
        'normalized dry-run worker-host results over methodology execution truth',
    ),
    does_not_own=(
        'queue transport implementation',
        'packet schema definitions',
        'cli rendering',
        'dev or qa agent execution',
    ),
)

__all__ = [
    'DefaultTechLeadWorkerService',
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
    'TechLeadWorkerDispatchSummary',
    'TechLeadWorkerRequest',
    'TechLeadWorkerResult',
    'TechLeadWorkerReviewRoutingService',
    'TechLeadWorkerService',
    'TECHLEAD_WORKER_SERVICE_METADATA',
]

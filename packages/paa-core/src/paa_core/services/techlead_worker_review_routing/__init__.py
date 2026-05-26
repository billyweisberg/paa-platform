"""TechLead worker review routing service package for PAA."""

from paa_core.governance import GovernedComponentMetadata

from .contracts import StructuredLogger, TechLeadWorkerReviewRoutingService
from .default import DefaultTechLeadWorkerReviewRoutingService
from .models import (
    TechLeadWorkerReviewRoutingRequest,
    TechLeadWorkerReviewRoutingResult,
    TechLeadWorkerReviewRoutingSummary,
)

TECHLEAD_WORKER_REVIEW_ROUTING_SERVICE_METADATA = GovernedComponentMetadata(
    name='TechLeadWorkerReviewRoutingService',
    kind='service',
    alignment='aligned',
    lifecycle_stage='build',
    owns=(
        'worker-result review outcome classification',
        'qa-routing recommendation derivation',
        'return-to-worker recommendation derivation',
        'return-to-delivery recommendation derivation',
    ),
    does_not_own=(
        'packet transport',
        'queue dispatch',
        'workflow-state mutation',
        'merge or closeout decisions',
    ),
)

__all__ = [
    'DefaultTechLeadWorkerReviewRoutingService',
    'StructuredLogger',
    'TechLeadWorkerReviewRoutingRequest',
    'TechLeadWorkerReviewRoutingResult',
    'TechLeadWorkerReviewRoutingService',
    'TechLeadWorkerReviewRoutingSummary',
    'TECHLEAD_WORKER_REVIEW_ROUTING_SERVICE_METADATA',
]

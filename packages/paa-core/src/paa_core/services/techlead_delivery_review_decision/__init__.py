"""TechLead delivery review decision service package for PAA."""

from paa_core.governance import GovernedComponentMetadata

from .contracts import StructuredLogger, TechLeadDeliveryReviewDecisionService
from .default import DefaultTechLeadDeliveryReviewDecisionService
from .models import (
    TechLeadDeliveryReviewDecisionRequest,
    TechLeadDeliveryReviewDecisionResult,
    TechLeadDeliveryReviewDecisionSummary,
)

TECHLEAD_DELIVERY_REVIEW_DECISION_SERVICE_METADATA = GovernedComponentMetadata(
    name='TechLeadDeliveryReviewDecisionService',
    kind='service',
    alignment='aligned',
    lifecycle_stage='build',
    owns=(
        'delivery-review outcome classification',
        'supported team-worker routing recommendation derivation',
        'structured delivery-review decision outputs',
        'terminal fail-closed delivery-review rejection derivation',
    ),
    does_not_own=(
        'packet transport',
        'queue dispatch',
        'workflow-state mutation',
        'merge execution or GitHub mutation',
    ),
)

__all__ = [
    'DefaultTechLeadDeliveryReviewDecisionService',
    'StructuredLogger',
    'TechLeadDeliveryReviewDecisionRequest',
    'TechLeadDeliveryReviewDecisionResult',
    'TechLeadDeliveryReviewDecisionService',
    'TechLeadDeliveryReviewDecisionSummary',
    'TECHLEAD_DELIVERY_REVIEW_DECISION_SERVICE_METADATA',
]

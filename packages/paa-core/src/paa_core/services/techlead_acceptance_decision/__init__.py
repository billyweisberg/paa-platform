"""TechLead acceptance decision service package for PAA."""

from paa_core.governance import GovernedComponentMetadata

from .contracts import StructuredLogger, TechLeadAcceptanceDecisionService
from .default import DefaultTechLeadAcceptanceDecisionService
from .models import (
    TechLeadAcceptanceDecisionRequest,
    TechLeadAcceptanceDecisionResult,
    TechLeadAcceptanceDecisionSummary,
)

TECHLEAD_ACCEPTANCE_DECISION_SERVICE_METADATA = GovernedComponentMetadata(
    name='TechLeadAcceptanceDecisionService',
    kind='service',
    alignment='aligned',
    lifecycle_stage='build',
    owns=(
        'qa-result acceptance outcome classification',
        'accept or proof-only close decision derivation',
        'reroute or pause recommendation derivation',
        'terminal fail-closed decision derivation',
    ),
    does_not_own=(
        'packet transport',
        'queue dispatch',
        'workflow-state mutation',
        'merge execution or GitHub mutation',
    ),
)

__all__ = [
    'DefaultTechLeadAcceptanceDecisionService',
    'StructuredLogger',
    'TechLeadAcceptanceDecisionRequest',
    'TechLeadAcceptanceDecisionResult',
    'TechLeadAcceptanceDecisionService',
    'TechLeadAcceptanceDecisionSummary',
    'TECHLEAD_ACCEPTANCE_DECISION_SERVICE_METADATA',
]

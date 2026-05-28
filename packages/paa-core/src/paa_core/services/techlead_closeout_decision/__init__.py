"""TechLead closeout decision service package for PAA."""

from paa_core.governance import GovernedComponentMetadata

from .contracts import StructuredLogger, TechLeadCloseoutDecisionService
from .default import DefaultTechLeadCloseoutDecisionService
from .models import (
    TechLeadCloseoutDecisionRequest,
    TechLeadCloseoutDecisionResult,
    TechLeadCloseoutDecisionSummary,
)

TECHLEAD_CLOSEOUT_DECISION_SERVICE_METADATA = GovernedComponentMetadata(
    name='TechLeadCloseoutDecisionService',
    kind='service',
    alignment='aligned',
    lifecycle_stage='build',
    owns=(
        'proof-only closeout outcome classification',
        'supported proof-only-close recommendation derivation',
        'structured closeout decision outputs',
        'terminal fail-closed closeout rejection derivation',
    ),
    does_not_own=(
        'packet transport',
        'queue dispatch',
        'workflow-state mutation',
        'merge execution or GitHub mutation',
    ),
)

__all__ = [
    'DefaultTechLeadCloseoutDecisionService',
    'StructuredLogger',
    'TechLeadCloseoutDecisionRequest',
    'TechLeadCloseoutDecisionResult',
    'TechLeadCloseoutDecisionService',
    'TechLeadCloseoutDecisionSummary',
    'TECHLEAD_CLOSEOUT_DECISION_SERVICE_METADATA',
]

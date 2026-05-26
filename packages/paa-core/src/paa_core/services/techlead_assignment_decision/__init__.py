"""TechLead assignment decision service package for PAA."""

from paa_core.governance import GovernedComponentMetadata

from .contracts import StructuredLogger, TechLeadAssignmentDecisionService
from .default import DefaultTechLeadAssignmentDecisionService
from .models import (
    TechLeadAssignmentDecisionRequest,
    TechLeadAssignmentDecisionResult,
    TechLeadAssignmentDecisionSummary,
)

TECHLEAD_ASSIGNMENT_DECISION_SERVICE_METADATA = GovernedComponentMetadata(
    name='TechLeadAssignmentDecisionService',
    kind='service',
    alignment='aligned',
    lifecycle_stage='build',
    owns=(
        'next-assignment decision derivation',
        'supported target-role determination',
        'supported assignment-type determination',
        'allowed-result-type derivation',
    ),
    does_not_own=(
        'packet dispatch',
        'workflow-state mutation',
        'acceptance or closeout decisions',
        'worker-review routing logic',
    ),
)

__all__ = [
    'DefaultTechLeadAssignmentDecisionService',
    'StructuredLogger',
    'TechLeadAssignmentDecisionRequest',
    'TechLeadAssignmentDecisionResult',
    'TechLeadAssignmentDecisionService',
    'TechLeadAssignmentDecisionSummary',
    'TECHLEAD_ASSIGNMENT_DECISION_SERVICE_METADATA',
]

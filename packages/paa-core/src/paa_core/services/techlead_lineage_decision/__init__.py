"""TechLead lineage decision service package for PAA."""

from paa_core.governance import GovernedComponentMetadata

from .contracts import StructuredLogger, TechLeadLineageDecisionService
from .default import DefaultTechLeadLineageDecisionService
from .models import (
    TechLeadLineageDecisionRequest,
    TechLeadLineageDecisionResult,
    TechLeadLineageDecisionSummary,
)

TECHLEAD_LINEAGE_DECISION_SERVICE_METADATA = GovernedComponentMetadata(
    name='TechLeadLineageDecisionService',
    kind='service',
    alignment='aligned',
    lifecycle_stage='build',
    owns=(
        'superseded-lineage outcome classification',
        'supported supersede-branch-lineage recommendation derivation',
        'structured lineage decision outputs',
        'terminal fail-closed lineage rejection derivation',
    ),
    does_not_own=(
        'packet transport',
        'queue dispatch',
        'workflow-state mutation',
        'physical cleanup execution or GitHub mutation',
    ),
)

__all__ = [
    'DefaultTechLeadLineageDecisionService',
    'StructuredLogger',
    'TechLeadLineageDecisionRequest',
    'TechLeadLineageDecisionResult',
    'TechLeadLineageDecisionService',
    'TechLeadLineageDecisionSummary',
    'TECHLEAD_LINEAGE_DECISION_SERVICE_METADATA',
]

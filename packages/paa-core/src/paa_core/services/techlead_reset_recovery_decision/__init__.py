"""TechLead reset recovery decision service package for PAA."""

from paa_core.governance import GovernedComponentMetadata

from .contracts import StructuredLogger, TechLeadResetRecoveryDecisionService
from .default import DefaultTechLeadResetRecoveryDecisionService
from .models import (
    TechLeadResetRecoveryDecisionRequest,
    TechLeadResetRecoveryDecisionResult,
    TechLeadResetRecoveryDecisionSummary,
)

TECHLEAD_RESET_RECOVERY_DECISION_SERVICE_METADATA = GovernedComponentMetadata(
    name='TechLeadResetRecoveryDecisionService',
    kind='service',
    alignment='aligned',
    lifecycle_stage='build',
    owns=(
        'reset-required outcome classification',
        'supported reset-branch recommendation derivation',
        'structured reset-recovery decision outputs',
        'terminal fail-closed reset-recovery rejection derivation',
    ),
    does_not_own=(
        'packet transport',
        'queue dispatch',
        'workflow-state mutation',
        'branch cleanup execution or GitHub mutation',
    ),
)

__all__ = [
    'DefaultTechLeadResetRecoveryDecisionService',
    'StructuredLogger',
    'TechLeadResetRecoveryDecisionRequest',
    'TechLeadResetRecoveryDecisionResult',
    'TechLeadResetRecoveryDecisionService',
    'TechLeadResetRecoveryDecisionSummary',
    'TECHLEAD_RESET_RECOVERY_DECISION_SERVICE_METADATA',
]

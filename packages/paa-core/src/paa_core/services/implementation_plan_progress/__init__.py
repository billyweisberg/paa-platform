"""Implementation-plan progress service package."""

from paa_core.governance import GovernedComponentMetadata

from .contracts import ImplementationPlanProgressService
from .default import DefaultImplementationPlanProgressService
from .models import (
    ActivityProgressClassification,
    ActivityProgressDetail,
    ComponentRealizationState,
    ImplementationPlanProgressRequest,
    ImplementationPlanProgressSummary,
    NextActivityBundleRequest,
    NextActivityBundleResult,
    PlanAuthorityStateSummary,
)

IMPLEMENTATION_PLAN_PROGRESS_SERVICE_METADATA = GovernedComponentMetadata(
    name='ImplementationPlanProgressService',
    kind='service',
    alignment='aligned',
    lifecycle_stage='build',
    owns=(
        'implementation-plan progress summarization',
        'component realization state computation',
        'next activity bundle derivation',
    ),
    does_not_own=(
        'implementation-plan derivation',
        'coder-brief assembly',
        'packet generation',
        'runtime orchestration',
    ),
)

__all__ = [
    'ActivityProgressClassification',
    'ActivityProgressDetail',
    'ComponentRealizationState',
    'DefaultImplementationPlanProgressService',
    'ImplementationPlanProgressRequest',
    'ImplementationPlanProgressService',
    'ImplementationPlanProgressSummary',
    'IMPLEMENTATION_PLAN_PROGRESS_SERVICE_METADATA',
    'NextActivityBundleRequest',
    'NextActivityBundleResult',
    'PlanAuthorityStateSummary',
]

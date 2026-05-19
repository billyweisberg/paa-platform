"""ImplementationPlan repository package."""

from paa_core.governance import GovernedComponentMetadata

from .contracts import ImplementationPlanRepository
from .models import (
    ImplementationPlanActivityDependencyRecord,
    ImplementationPlanActivityDependencyUpsertSpec,
    ImplementationPlanActivityRecord,
    ImplementationPlanActivityUpsertSpec,
    ImplementationPlanRecord,
    ImplementationPlanUpsertSpec,
    ImplementationPlanVerificationSurfaceRecord,
)
from .postgres import PostgresImplementationPlanRepository

IMPLEMENTATION_PLAN_REPOSITORY_METADATA = GovernedComponentMetadata(
    name='ImplementationPlanRepository',
    kind='repository',
    alignment='aligned',
    lifecycle_stage='build',
    owns=(
        'implementation-plan root persistence',
        'implementation-plan activity persistence',
        'implementation-plan dependency persistence',
        'implementation-plan verification-surface reads',
    ),
    does_not_own=(
        'implementation-plan derivation policy',
        'workflow truth',
        'coder-brief assembly',
        'delivery projection',
    ),
)

__all__ = [
    'ImplementationPlanActivityDependencyRecord',
    'ImplementationPlanActivityDependencyUpsertSpec',
    'ImplementationPlanActivityRecord',
    'ImplementationPlanActivityUpsertSpec',
    'ImplementationPlanRecord',
    'ImplementationPlanRepository',
    'ImplementationPlanUpsertSpec',
    'ImplementationPlanVerificationSurfaceRecord',
    'IMPLEMENTATION_PLAN_REPOSITORY_METADATA',
    'PostgresImplementationPlanRepository',
]

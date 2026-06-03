"""Methodology Execution Preflight service package for PAA."""

from paa_core.governance import GovernedComponentMetadata

from .contracts import (
    MethodologyExecutionPreflightOutcome,
    MethodologyExecutionPreflightRequest,
    MethodologyExecutionPreflightResult,
    MethodologyExecutionPreflightService,
    MethodologyExecutionProjectionService,
    MethodologyExecutionStateService,
    StructuredLogger,
)
from .default import DefaultMethodologyExecutionPreflightService

METHODOLOGY_EXECUTION_PREFLIGHT_SERVICE_METADATA = GovernedComponentMetadata(
    name='MethodologyExecutionPreflightService',
    kind='service',
    alignment='aligned',
    lifecycle_stage='build',
    owns=(
        'methodology-aware preflight classification for supported command families',
        'stable allowed, warn, blocked, and redirect outcomes for supported slices',
        'structured missing-truth and wrong-lane outcomes for supported preflight slices',
    ),
    does_not_own=(
        'command execution',
        'methodology execution state mutation',
        'cli rendering',
        'repository persistence',
    ),
)

__all__ = [
    'DefaultMethodologyExecutionPreflightService',
    'MethodologyExecutionPreflightOutcome',
    'MethodologyExecutionPreflightRequest',
    'MethodologyExecutionPreflightResult',
    'MethodologyExecutionPreflightService',
    'MethodologyExecutionProjectionService',
    'MethodologyExecutionStateService',
    'StructuredLogger',
    'METHODOLOGY_EXECUTION_PREFLIGHT_SERVICE_METADATA',
]

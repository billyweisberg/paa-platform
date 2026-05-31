"""Methodology Execution State service package for PAA."""

from paa_core.governance import GovernedComponentMetadata

from .contracts import (
    MethodologyExecutionStateRequest,
    MethodologyExecutionStateResult,
    MethodologyExecutionStateService,
    MethodologyExecutionStateSummary,
    StructuredLogger,
)
from .default import DefaultMethodologyExecutionStateService
from .models import MethodologyExecutionTransitionSummary

METHODOLOGY_EXECUTION_STATE_SERVICE_METADATA = GovernedComponentMetadata(
    name='MethodologyExecutionStateService',
    kind='service',
    alignment='aligned',
    lifecycle_stage='build',
    owns=(
        'current methodology pointer transition application for supported slices',
        'methodology execution current-state loading and coordination',
        'structured blocked and unsupported transition outcomes for supported slices',
    ),
    does_not_own=(
        'methodology execution repository persistence',
        'cli rendering',
        'preflight command classification',
        'implementation-plan or workflow mutation outside methodology pointer truth',
    ),
)

__all__ = [
    'DefaultMethodologyExecutionStateService',
    'MethodologyExecutionStateRequest',
    'MethodologyExecutionStateResult',
    'MethodologyExecutionStateService',
    'MethodologyExecutionStateSummary',
    'MethodologyExecutionTransitionSummary',
    'StructuredLogger',
    'METHODOLOGY_EXECUTION_STATE_SERVICE_METADATA',
]

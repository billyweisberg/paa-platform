"""Methodology Execution Projection service package for PAA."""

from paa_core.governance import GovernedComponentMetadata

from .contracts import (
    MethodologyExecutionExplainProjection,
    MethodologyExecutionNextActionProjection,
    MethodologyExecutionProjectionRequest,
    MethodologyExecutionProjectionResult,
    MethodologyExecutionProjectionService,
    MethodologyExecutionStatusProjection,
    StructuredLogger,
)
from .default import DefaultMethodologyExecutionProjectionService

METHODOLOGY_EXECUTION_PROJECTION_SERVICE_METADATA = GovernedComponentMetadata(
    name='MethodologyExecutionProjectionService',
    kind='service',
    alignment='aligned',
    lifecycle_stage='build',
    owns=(
        'operator-facing methodology execution status, next-action, and explain projection for supported slices',
        'stable projection summaries over persisted methodology pointer truth',
        'structured missing-truth outcomes for supported projection slices',
    ),
    does_not_own=(
        'methodology execution state mutation',
        'methodology execution repository persistence',
        'cli rendering',
        'preflight command classification',
    ),
)

__all__ = [
    'DefaultMethodologyExecutionProjectionService',
    'MethodologyExecutionExplainProjection',
    'MethodologyExecutionNextActionProjection',
    'MethodologyExecutionProjectionRequest',
    'MethodologyExecutionProjectionResult',
    'MethodologyExecutionProjectionService',
    'MethodologyExecutionStatusProjection',
    'StructuredLogger',
    'METHODOLOGY_EXECUTION_PROJECTION_SERVICE_METADATA',
]

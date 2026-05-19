"""Execution Package Resolution service package for PAA."""

from paa_core.governance import GovernedComponentMetadata

from .contracts import ExecutionPackageResolutionService, StructuredLogger
from .default import DefaultExecutionPackageResolutionService
from .models import (
    ExecutionPackageCapabilitySummary,
    ExecutionPackageGap,
    ExecutionPackageGapSeverity,
    ExecutionPackageResolutionRequest,
    ExecutionPackageResolutionView,
)

EXECUTION_PACKAGE_RESOLUTION_SERVICE_METADATA = GovernedComponentMetadata(
    name='ExecutionPackageResolutionService',
    kind='service',
    alignment='aligned',
    lifecycle_stage='build',
    owns=(
        'execution-package context resolution',
        'normalized execution-context view assembly',
        'execution-package gap reporting',
    ),
    does_not_own=(
        'install mutation',
        'overlay mutation',
        'workflow semantics',
        'queue orchestration',
    ),
)

__all__ = [
    'DefaultExecutionPackageResolutionService',
    'ExecutionPackageCapabilitySummary',
    'ExecutionPackageGap',
    'ExecutionPackageGapSeverity',
    'ExecutionPackageResolutionRequest',
    'ExecutionPackageResolutionService',
    'ExecutionPackageResolutionView',
    'EXECUTION_PACKAGE_RESOLUTION_SERVICE_METADATA',
    'StructuredLogger',
]

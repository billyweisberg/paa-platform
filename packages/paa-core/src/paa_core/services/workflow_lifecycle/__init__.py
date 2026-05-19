"""Workflow Lifecycle service package for PAA."""

from paa_core.governance import GovernedComponentMetadata

from .contracts import StructuredLogger, WorkflowLifecycleService
from .default import DefaultWorkflowLifecycleService
from .models import (
    WorkflowLifecycleDecisionSummary,
    WorkflowLifecycleRequest,
    WorkflowLifecycleResult,
    WorkflowLifecycleStateView,
)

WORKFLOW_LIFECYCLE_SERVICE_METADATA = GovernedComponentMetadata(
    name='WorkflowLifecycleService',
    kind='service',
    alignment='aligned',
    lifecycle_stage='build',
    owns=(
        'workflow transition evaluation for supported families',
        'workflow transition application for supported families',
        'current workflow-state coordination',
    ),
    does_not_own=(
        'queue transport',
        'github mutation',
        'execution-package lookup logic',
        'projection refresh ownership',
    ),
)

__all__ = [
    'DefaultWorkflowLifecycleService',
    'StructuredLogger',
    'WorkflowLifecycleDecisionSummary',
    'WorkflowLifecycleRequest',
    'WorkflowLifecycleResult',
    'WorkflowLifecycleService',
    'WorkflowLifecycleStateView',
    'WORKFLOW_LIFECYCLE_SERVICE_METADATA',
]

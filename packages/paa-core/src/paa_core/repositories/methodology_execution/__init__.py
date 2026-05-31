"""MethodologyExecution repository package."""

from paa_core.governance import GovernedComponentMetadata

from .contracts import MethodologyExecutionBindingEntrySpec, MethodologyExecutionRepository
from .postgres import PostgresMethodologyExecutionRepository
from .models import (
    MethodologyExecutionBindingRecord,
    MethodologyExecutionBindingReplaceSpec,
    MethodologyExecutionEventAppendSpec,
    MethodologyExecutionEventRecord,
    MethodologyExecutionProjectionInputRecord,
    MethodologyExecutionRecord,
    MethodologyExecutionUpsertSpec,
)

METHODOLOGY_EXECUTION_REPOSITORY_METADATA = GovernedComponentMetadata(
    name='MethodologyExecutionRepository',
    kind='repository',
    alignment='aligned',
    lifecycle_stage='build',
    owns=(
        'methodology execution root persistence contract',
        'methodology execution event persistence contract',
        'methodology execution binding persistence contract',
        'methodology execution projection-input read contract',
    ),
    does_not_own=(
        'methodology execution transition policy',
        'methodology execution preflight policy',
        'implementation-plan truth',
        'workflow truth',
    ),
)

__all__ = [
    'MethodologyExecutionBindingEntrySpec',
    'MethodologyExecutionBindingRecord',
    'MethodologyExecutionBindingReplaceSpec',
    'MethodologyExecutionEventAppendSpec',
    'MethodologyExecutionEventRecord',
    'MethodologyExecutionProjectionInputRecord',
    'MethodologyExecutionRecord',
    'MethodologyExecutionRepository',
    'PostgresMethodologyExecutionRepository',
    'MethodologyExecutionUpsertSpec',
    'METHODOLOGY_EXECUTION_REPOSITORY_METADATA',
]

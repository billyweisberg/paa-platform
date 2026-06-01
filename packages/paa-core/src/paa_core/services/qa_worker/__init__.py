"""QA worker service package for PAA."""

from paa_core.governance import GovernedComponentMetadata

from .contracts import (
    MethodologyExecutionProjectionService,
    MethodologyExecutionStateService,
    PacketContextAssemblyService,
    QAVerificationPacketAssembler,
    QAVerificationRunner,
    QAWorkerRequest,
    QAWorkerResult,
    QAWorkerService,
    StructuredLogger,
)
from .default import DefaultQAWorkerService
from .models import QAWorkerVerificationSummary

QA_WORKER_SERVICE_METADATA = GovernedComponentMetadata(
    name='QAWorkerService',
    kind='service',
    alignment='aligned',
    lifecycle_stage='build',
    owns=(
        'deterministic QA verification-packet execution orchestration for supported runtime slices',
        'bounded verification-host composition over assembled packet context',
        'normalized QA verification output surfaces for supported QA slices',
    ),
    does_not_own=(
        'queue transport implementation',
        'packet schema definitions',
        'techlead acceptance decisions',
        'cli rendering',
    ),
)

__all__ = [
    'MethodologyExecutionProjectionService',
    'MethodologyExecutionStateService',
    'PacketContextAssemblyService',
    'DefaultQAWorkerService',
    'QAVerificationPacketAssembler',
    'QAVerificationRunner',
    'QA_WORKER_SERVICE_METADATA',
    'QAWorkerRequest',
    'QAWorkerResult',
    'QAWorkerService',
    'QAWorkerVerificationSummary',
    'StructuredLogger',
]

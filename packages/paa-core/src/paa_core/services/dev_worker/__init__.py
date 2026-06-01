"""Dev worker service package for PAA."""

from paa_core.governance import GovernedComponentMetadata

from .contracts import (
    DevExecutionRunner,
    DevWorkerService,
    DevWorkerRequest,
    DevWorkerResult,
    MethodologyExecutionProjectionService,
    MethodologyExecutionStateService,
    PacketContextAssemblyService,
    StructuredLogger,
    WorkerResultPacketAssembler,
)
from .default import DefaultDevWorkerService
from .models import DevWorkerExecutionSummary

DEV_WORKER_SERVICE_METADATA = GovernedComponentMetadata(
    name='DevWorkerService',
    kind='service',
    alignment='aligned',
    lifecycle_stage='build',
    owns=(
        'deterministic Dev assignment-packet execution orchestration for supported runtime slices',
        'bounded execution-host composition over assembled packet context',
        'normalized worker-result output surfaces for supported Dev slices',
    ),
    does_not_own=(
        'queue transport implementation',
        'packet schema definitions',
        'techlead decision derivation',
        'cli rendering',
    ),
)

__all__ = [
    'DEV_WORKER_SERVICE_METADATA',
    'DefaultDevWorkerService',
    'DevExecutionRunner',
    'DevWorkerExecutionSummary',
    'DevWorkerRequest',
    'DevWorkerResult',
    'DevWorkerService',
    'MethodologyExecutionProjectionService',
    'MethodologyExecutionStateService',
    'PacketContextAssemblyService',
    'StructuredLogger',
    'WorkerResultPacketAssembler',
]

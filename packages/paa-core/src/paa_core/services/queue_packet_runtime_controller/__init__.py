"""Queue packet runtime controller package for PAA."""

from paa_core.governance import GovernedComponentMetadata

from .contracts import (
    DevWorkerService,
    QAWorkerService,
    QueuePacketDeliveryAdapter,
    QueuePacketReader,
    QueuePacketRuntimeController,
    QueuePacketRuntimeRequest,
    QueuePacketRuntimeResult,
    StructuredLogger,
    TechLeadWorkerService,
)
from .default import DefaultQueuePacketRuntimeController
from .models import QueuePacketDispatchSummary

QUEUE_PACKET_RUNTIME_CONTROLLER_METADATA = GovernedComponentMetadata(
    name='QueuePacketRuntimeController',
    kind='service',
    alignment='aligned',
    lifecycle_stage='build',
    owns=(
        'deterministic queue-packet classification and supported worker-host dispatch',
        'runtime-controller composition over realized TechLead, Dev, and QA worker services',
        'normalized runtime-control results for supported queue packet slices',
    ),
    does_not_own=(
        'worker business logic already owned by worker services',
        'queue transport implementation',
        'packet schema definitions',
        'cli rendering',
    ),
)

__all__ = [
    'DefaultQueuePacketRuntimeController',
    'DevWorkerService',
    'QAWorkerService',
    'QueuePacketDeliveryAdapter',
    'QueuePacketDispatchSummary',
    'QueuePacketReader',
    'QUEUE_PACKET_RUNTIME_CONTROLLER_METADATA',
    'QueuePacketRuntimeController',
    'QueuePacketRuntimeRequest',
    'QueuePacketRuntimeResult',
    'StructuredLogger',
    'TechLeadWorkerService',
]

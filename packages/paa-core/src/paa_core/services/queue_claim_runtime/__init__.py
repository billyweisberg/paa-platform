"""Queue claim runtime service package for PAA."""

from paa_core.governance import GovernedComponentMetadata

from .contracts import (
    PacketEnvelopeValidator,
    QueueClaimRuntimeRequest,
    QueueClaimRuntimeResult,
    QueueClaimRuntimeService,
    QueueClaimStateAdapter,
    QueueTransportAdapter,
    StructuredLogger,
)
from .models import QueuePacketClaimSummary, QueuePacketPreviewSummary
from .default import DefaultQueueClaimRuntimeService

QUEUE_CLAIM_RUNTIME_SERVICE_METADATA = GovernedComponentMetadata(
    name='QueueClaimRuntimeService',
    kind='service',
    alignment='aligned',
    lifecycle_stage='build',
    owns=(
        'deterministic queue preview and claim normalization for supported runtime slices',
        'stable queue intake boundaries for runtime-controller and queue cli hosts',
        'fail-closed blocked and unsupported queue-intake results',
    ),
    does_not_own=(
        'worker dispatch logic',
        'packet schema definitions',
        'queue topology provisioning',
        'cli rendering',
    ),
)

__all__ = [
    'DefaultQueueClaimRuntimeService',
    'PacketEnvelopeValidator',
    'QUEUE_CLAIM_RUNTIME_SERVICE_METADATA',
    'QueueClaimRuntimeRequest',
    'QueueClaimRuntimeResult',
    'QueueClaimRuntimeService',
    'QueueClaimStateAdapter',
    'QueuePacketClaimSummary',
    'QueuePacketPreviewSummary',
    'QueueTransportAdapter',
    'StructuredLogger',
]

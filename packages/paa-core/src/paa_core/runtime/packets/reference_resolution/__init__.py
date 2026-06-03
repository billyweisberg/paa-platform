"""Packet reference resolution service package for PAA."""

from paa_core.governance import GovernedComponentMetadata

from .contracts import (
    PacketArtifactReader,
    PacketReferenceResolutionRequest,
    PacketReferenceResolutionResult,
    PacketReferenceResolutionService,
    RuntimeEventRepository,
    RuntimePathAdapter,
    StructuredLogger,
)
from .default import DefaultPacketReferenceResolutionService
from .models import PacketReferenceResolutionSummary

PACKET_REFERENCE_RESOLUTION_SERVICE_METADATA = GovernedComponentMetadata(
    name='PacketReferenceResolutionService',
    kind='service',
    alignment='aligned',
    lifecycle_stage='build',
    owns=(
        'deterministic packet reference lookup for supported runtime slices',
        'stable normalization of queue message ids and packet paths into packet artifact references',
        'fail-closed blocked and unsupported packet-reference resolution results',
    ),
    does_not_own=(
        'queue claim policy',
        'packet-context assembly',
        'worker dispatch logic',
        'cli rendering',
    ),
)

__all__ = [
    'DefaultPacketReferenceResolutionService',
    'PACKET_REFERENCE_RESOLUTION_SERVICE_METADATA',
    'PacketArtifactReader',
    'PacketReferenceResolutionRequest',
    'PacketReferenceResolutionResult',
    'PacketReferenceResolutionSummary',
    'PacketReferenceResolutionService',
    'RuntimeEventRepository',
    'RuntimePathAdapter',
    'StructuredLogger',
]

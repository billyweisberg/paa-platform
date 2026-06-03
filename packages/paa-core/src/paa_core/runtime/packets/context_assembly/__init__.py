"""Packet context assembly service package for PAA."""

from paa_core.governance import GovernedComponentMetadata

from .contracts import (
    ExecutionPackageResolutionService,
    MethodologyExecutionProjectionService,
    MethodologyExecutionRepository,
    PacketContextAssemblyService,
    PacketPayloadReader,
    StructuredLogger,
)
from .default import DefaultPacketContextAssemblyService
from .models import (
    PacketContextAssemblyRequest,
    PacketContextAssemblyResult,
    PacketContextAssemblySummary,
    PacketContextGapSummary,
)

PACKET_CONTEXT_ASSEMBLY_SERVICE_METADATA = GovernedComponentMetadata(
    name='PacketContextAssemblyService',
    kind='service',
    alignment='aligned',
    lifecycle_stage='build',
    owns=(
        'deterministic worker-runtime packet context assembly for supported slices',
        'normalization of thin packet references into shared runtime context packages',
        'fail-closed missing-context reporting for supported packet families',
    ),
    does_not_own=(
        'queue transport implementation',
        'methodology execution state mutation',
        'execution-package installation or activation',
        'worker decision policy',
    ),
)

__all__ = [
    'DefaultPacketContextAssemblyService',
    'ExecutionPackageResolutionService',
    'MethodologyExecutionProjectionService',
    'MethodologyExecutionRepository',
    'PacketContextAssemblyRequest',
    'PacketContextAssemblyResult',
    'PacketContextAssemblyService',
    'PacketContextAssemblySummary',
    'PacketContextGapSummary',
    'PacketPayloadReader',
    'PACKET_CONTEXT_ASSEMBLY_SERVICE_METADATA',
    'StructuredLogger',
]

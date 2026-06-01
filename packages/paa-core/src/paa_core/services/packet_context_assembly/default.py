"""Default implementation for the packet context assembly service."""

from __future__ import annotations

from paa_core.repositories.methodology_execution import MethodologyExecutionRepository
from paa_core.services.execution_package_resolution import (
    ExecutionPackageResolutionRequest,
    ExecutionPackageResolutionService,
    ExecutionPackageResolutionView,
)
from paa_core.services.implementation_plan_derivation.contracts import StructuredLogger
from paa_core.services.methodology_execution_projection import (
    MethodologyExecutionProjectionService,
    MethodologyExecutionStatusProjection,
)

from .models import (
    PacketContextAssemblyRequest,
    PacketContextAssemblyResult,
    PacketContextAssemblySummary,
    PacketContextGapSummary,
)


class _NullStructuredLogger:
    def info(self, event: str, **fields: object) -> None:
        return None

    def warning(self, event: str, **fields: object) -> None:
        return None


class DefaultPacketContextAssemblyService:
    """Assemble the first supported deterministic worker-runtime packet context."""

    _SUPPORTED_PACKET_SCHEMA_TYPES = frozenset({'worker_result_packet'})
    _SUPPORTED_RUNTIME_SURFACES = frozenset({'techlead'})
    _REQUIRED_CAPABILITIES = ('packet-read', 'techlead-runtime')

    def __init__(
        self,
        *,
        methodology_execution_repository: MethodologyExecutionRepository,
        methodology_execution_projection_service: MethodologyExecutionProjectionService,
        execution_package_resolution_service: ExecutionPackageResolutionService,
        packet_payload_reader=None,
        logger: StructuredLogger | None = None,
    ) -> None:
        self._methodology_execution_repository = methodology_execution_repository
        self._methodology_execution_projection_service = methodology_execution_projection_service
        self._execution_package_resolution_service = execution_package_resolution_service
        self._packet_payload_reader = packet_payload_reader
        self._logger = logger if logger is not None else _NullStructuredLogger()

    @property
    def methodology_execution_repository(self) -> MethodologyExecutionRepository:
        return self._methodology_execution_repository

    @property
    def methodology_execution_projection_service(self) -> MethodologyExecutionProjectionService:
        return self._methodology_execution_projection_service

    @property
    def execution_package_resolution_service(self) -> ExecutionPackageResolutionService:
        return self._execution_package_resolution_service

    @property
    def packet_payload_reader(self):
        return self._packet_payload_reader

    @property
    def logger(self) -> StructuredLogger:
        return self._logger

    def supports_packet_context(self, packet_schema_type: str, runtime_surface: str) -> bool:
        return (
            packet_schema_type.strip() in self._SUPPORTED_PACKET_SCHEMA_TYPES
            and runtime_surface.strip() in self._SUPPORTED_RUNTIME_SURFACES
        )

    def assemble_packet_context(
        self,
        request: PacketContextAssemblyRequest,
    ) -> PacketContextAssemblyResult:
        packet_schema_type = request.packet_schema_type.strip()
        runtime_surface = request.runtime_surface.strip()
        self._logger.info(
            'packet_context_assembly.assemble_packet_context.start',
            packet_schema_type=packet_schema_type,
            runtime_surface=runtime_surface,
            packet_message_id=request.packet_message_id,
        )

        if not self.supports_packet_context(packet_schema_type, runtime_surface):
            return self._build_blocked_result(
                request,
                reason='unsupported_packet_context',
                details=(
                    f'Packet schema type {packet_schema_type!r} and runtime surface '
                    f'{runtime_surface!r} are not supported in this slice.'
                ),
                context_kind='unsupported',
                gaps=(
                    PacketContextGapSummary(
                        gap_key='unsupported_packet_context',
                        gap_summary='The provided packet schema type and runtime surface are unsupported.',
                        blocking=True,
                        recommended_next_action='use-supported-techlead-worker-result-slice',
                        notes=('fail-closed',),
                    ),
                ),
            )

        methodology_execution_id = request.methodology_execution_id
        if not methodology_execution_id:
            return self._build_blocked_result(
                request,
                reason='missing_methodology_execution_id',
                details='The supported packet-context assembly slice requires a methodology execution id.',
                context_kind='worker_result_review',
                gaps=(
                    PacketContextGapSummary(
                        gap_key='missing_methodology_execution_id',
                        gap_summary='Methodology execution id is required to assemble worker packet context.',
                        blocking=True,
                        recommended_next_action='include-methodology-execution-id',
                        notes=('fail-closed',),
                    ),
                ),
            )

        packet_payload = self._resolve_packet_payload(request)
        if packet_payload is None:
            return self._build_blocked_result(
                request,
                reason='missing_packet_payload',
                details='The supported packet-context assembly slice requires packet payload or a readable packet path.',
                context_kind='worker_result_review',
                gaps=(
                    PacketContextGapSummary(
                        gap_key='missing_packet_payload',
                        gap_summary='Packet payload could not be resolved for context assembly.',
                        blocking=True,
                        recommended_next_action='provide-packet-payload-or-reader',
                        notes=('fail-closed',),
                    ),
                ),
            )

        methodology_execution_status = self.methodology_execution_projection_service.get_status_projection(
            methodology_execution_id
        )
        execution_package_resolution = self.execution_package_resolution_service.resolve_execution_context_for_surface(
            runtime_surface,
            ExecutionPackageResolutionRequest(
                execution_surface_key=runtime_surface,
                execution_surface_type='worker_runtime',
                required_surface_types=(runtime_surface,),
                required_artifact_refs=('installed_manifest',),
                metadata={
                    'packet_schema_type': packet_schema_type,
                    'methodology_execution_id': methodology_execution_id,
                },
            ),
        )
        gaps = tuple(
            PacketContextGapSummary(
                gap_key=gap.gap_code,
                gap_summary=gap.note,
                blocking=gap.severity == 'blocker',
                recommended_next_action=gap.recommended_next_action,
                notes=(gap.severity,),
            )
            for gap in execution_package_resolution.gaps
        )
        ok = execution_package_resolution.capability_summary.allowed and not any(g.blocking for g in gaps)
        reason = None if ok else self._primary_gap_key(gaps, fallback='execution_package_resolution_blocked')
        details = None if ok else 'Execution package context could not be resolved for the supported runtime slice.'
        summary = PacketContextAssemblySummary(
            packet_schema_type=packet_schema_type,
            runtime_surface=runtime_surface,
            methodology_execution_id=methodology_execution_id,
            execution_package_id=execution_package_resolution.execution_package_install_id,
            context_kind='worker_result_review',
            assembly_supported=ok,
            required_capabilities=self._REQUIRED_CAPABILITIES,
            resolved_capabilities=execution_package_resolution.capability_summary.satisfied_capabilities,
            blocking_gaps=tuple(g.gap_key for g in gaps if g.blocking),
            notes=('dry-run-supported',),
        )
        result = PacketContextAssemblyResult(
            request=request,
            methodology_execution_status=methodology_execution_status,
            execution_package_resolution=execution_package_resolution,
            packet_payload=packet_payload,
            assembly_summary=summary,
            gaps=gaps,
            ok=ok,
            reason=reason,
            details=details,
            metadata={
                'service_component': 'PacketContextAssemblyService',
                'runtime_surface': runtime_surface,
                'packet_schema_type': packet_schema_type,
            },
        )
        self._logger.info(
            'packet_context_assembly.assemble_packet_context.complete',
            packet_schema_type=packet_schema_type,
            runtime_surface=runtime_surface,
            methodology_execution_id=methodology_execution_id,
            ok=result.ok,
            gap_count=len(gaps),
        )
        return result

    def _resolve_packet_payload(self, request: PacketContextAssemblyRequest) -> dict[str, object] | None:
        if request.packet_payload is not None:
            return request.packet_payload
        if request.packet_path and self.packet_payload_reader is not None:
            return self.packet_payload_reader.read_packet_payload(request.packet_path)
        return None

    def _build_blocked_result(
        self,
        request: PacketContextAssemblyRequest,
        *,
        reason: str,
        details: str,
        context_kind: str,
        gaps: tuple[PacketContextGapSummary, ...],
    ) -> PacketContextAssemblyResult:
        self._logger.warning(
            'packet_context_assembly.assemble_packet_context.blocked',
            packet_schema_type=request.packet_schema_type,
            runtime_surface=request.runtime_surface,
            reason=reason,
        )
        return PacketContextAssemblyResult(
            request=request,
            methodology_execution_status=None,
            execution_package_resolution=None,
            packet_payload=request.packet_payload,
            assembly_summary=PacketContextAssemblySummary(
                packet_schema_type=request.packet_schema_type,
                runtime_surface=request.runtime_surface,
                methodology_execution_id=request.methodology_execution_id,
                execution_package_id=None,
                context_kind=context_kind,
                assembly_supported=False,
                required_capabilities=self._REQUIRED_CAPABILITIES,
                resolved_capabilities=(),
                blocking_gaps=tuple(g.gap_key for g in gaps if g.blocking),
                notes=('fail-closed',),
            ),
            gaps=gaps,
            ok=False,
            reason=reason,
            details=details,
            metadata={
                'service_component': 'PacketContextAssemblyService',
                'runtime_surface': request.runtime_surface,
                'packet_schema_type': request.packet_schema_type,
            },
        )

    def _primary_gap_key(self, gaps: tuple[PacketContextGapSummary, ...], *, fallback: str) -> str:
        for gap in gaps:
            if gap.blocking:
                return gap.gap_key
        return fallback


__all__ = ['DefaultPacketContextAssemblyService']

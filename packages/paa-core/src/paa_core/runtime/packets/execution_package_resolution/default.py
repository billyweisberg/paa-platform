"""Default implementation shell for the execution package resolution service."""

from __future__ import annotations

from paa_core.policies.deployment_capability import (
    DeploymentCapabilityContext,
    DeploymentCapabilityDecision,
    DeploymentCapabilityPolicy,
    DeploymentCapabilityRequest,
)
from paa_core.repositories.execution_package import (
    ExecutionPackageInstallRecord,
    ExecutionPackageRepository,
    InstalledExecutionContextRecord,
)
from paa_core.services.implementation_plan_derivation.contracts import StructuredLogger

from .models import (
    ExecutionPackageCapabilitySummary,
    ExecutionPackageGap,
    ExecutionPackageResolutionRequest,
    ExecutionPackageResolutionView,
)


class _NullStructuredLogger:
    def info(self, event: str, **fields: object) -> None:
        return None

    def warning(self, event: str, **fields: object) -> None:
        return None


class DefaultExecutionPackageResolutionService:
    """Read-oriented resolution service over installed execution-package truth."""

    def __init__(
        self,
        *,
        repository: ExecutionPackageRepository,
        capability_policy: DeploymentCapabilityPolicy,
        logger: StructuredLogger | None = None,
    ) -> None:
        self._repository = repository
        self._capability_policy = capability_policy
        self._logger = logger if logger is not None else _NullStructuredLogger()

    @property
    def repository(self) -> ExecutionPackageRepository:
        return self._repository

    @property
    def capability_policy(self) -> DeploymentCapabilityPolicy:
        return self._capability_policy

    @property
    def logger(self) -> StructuredLogger:
        return self._logger

    def resolve_execution_context(
        self,
        request: ExecutionPackageResolutionRequest,
    ) -> ExecutionPackageResolutionView:
        resolution_source = self._resolve_context_source(request)
        if resolution_source == 'execution_surface_key':
            context = self._repository.resolve_active_execution_context(request.execution_surface_key or '')
        elif resolution_source == 'repo_root_path':
            install = self._repository.get_active_install_for_repo_root(request.repo_root_path or '')
            context = self._context_from_install(install)
        elif resolution_source == 'runtime_root_path':
            install = self._repository.get_active_install_for_runtime_root(request.runtime_root_path or '')
            context = self._context_from_install(install)
        else:  # pragma: no cover - guarded by _resolve_context_source
            raise ValueError('ExecutionPackageResolutionRequest did not include a supported resolution identity.')
        capability_request = self._capability_request(request, context)
        capability_context = self._capability_context(request, context)
        decision = self._capability_policy.evaluate_capability(
            capability_request,
            capability_context,
        )
        gaps = self._derive_gaps(request, context, decision)
        warnings = tuple(gap.note for gap in gaps if gap.severity in {'warning', 'blocker'})
        view = self._assemble_resolution_view(
            request=request,
            context=context,
            decision=decision,
            gaps=gaps,
        )
        self._logger.info(
            'execution_package_resolution.resolve_execution_context',
            resolution_source=resolution_source,
            execution_surface_key=view.execution_surface_key,
            allowed=view.capability_summary.allowed,
            gap_count=len(gaps),
        )
        if warnings:
            self._logger.warning(
                'execution_package_resolution.resolve_execution_context.gaps',
                execution_surface_key=view.execution_surface_key,
                warnings=warnings,
            )
        return view

    def resolve_execution_context_for_surface(
        self,
        execution_surface_key: str,
        request: ExecutionPackageResolutionRequest | None = None,
    ) -> ExecutionPackageResolutionView:
        merged_request = ExecutionPackageResolutionRequest(
            execution_surface_key=execution_surface_key,
            execution_surface_type=request.execution_surface_type if request else None,
            repo_root_path=request.repo_root_path if request else None,
            runtime_root_path=request.runtime_root_path if request else None,
            work_item_id=request.work_item_id if request else None,
            coder_run_brief_id=request.coder_run_brief_id if request else None,
            consumer_context_key=request.consumer_context_key if request else None,
            required_surface_types=request.required_surface_types if request else (),
            required_artifact_refs=request.required_artifact_refs if request else (),
            required_overlay_keys=request.required_overlay_keys if request else (),
            metadata=dict(request.metadata or {}) if request and request.metadata else None,
        )
        return self.resolve_execution_context(merged_request)

    def resolve_execution_context_for_repo_root(
        self,
        repo_root_path: str,
        request: ExecutionPackageResolutionRequest | None = None,
    ) -> ExecutionPackageResolutionView:
        merged_request = ExecutionPackageResolutionRequest(
            execution_surface_key=request.execution_surface_key if request else None,
            execution_surface_type=request.execution_surface_type if request else None,
            repo_root_path=repo_root_path,
            runtime_root_path=request.runtime_root_path if request else None,
            work_item_id=request.work_item_id if request else None,
            coder_run_brief_id=request.coder_run_brief_id if request else None,
            consumer_context_key=request.consumer_context_key if request else None,
            required_surface_types=request.required_surface_types if request else (),
            required_artifact_refs=request.required_artifact_refs if request else (),
            required_overlay_keys=request.required_overlay_keys if request else (),
            metadata=dict(request.metadata or {}) if request and request.metadata else None,
        )
        return self.resolve_execution_context(merged_request)

    def resolve_execution_context_for_runtime_root(
        self,
        runtime_root_path: str,
        request: ExecutionPackageResolutionRequest | None = None,
    ) -> ExecutionPackageResolutionView:
        merged_request = ExecutionPackageResolutionRequest(
            execution_surface_key=request.execution_surface_key if request else None,
            execution_surface_type=request.execution_surface_type if request else None,
            repo_root_path=request.repo_root_path if request else None,
            runtime_root_path=runtime_root_path,
            work_item_id=request.work_item_id if request else None,
            coder_run_brief_id=request.coder_run_brief_id if request else None,
            consumer_context_key=request.consumer_context_key if request else None,
            required_surface_types=request.required_surface_types if request else (),
            required_artifact_refs=request.required_artifact_refs if request else (),
            required_overlay_keys=request.required_overlay_keys if request else (),
            metadata=dict(request.metadata or {}) if request and request.metadata else None,
        )
        return self.resolve_execution_context(merged_request)

    def detect_execution_package_gaps(
        self,
        request: ExecutionPackageResolutionRequest,
    ) -> tuple[ExecutionPackageGap, ...]:
        view = self.resolve_execution_context(request)
        self._logger.info(
            'execution_package_resolution.detect_execution_package_gaps',
            execution_surface_key=view.execution_surface_key,
            gap_count=len(view.gaps),
        )
        return view.gaps

    def _resolve_context_source(self, request: ExecutionPackageResolutionRequest) -> str:
        if request.execution_surface_key:
            return 'execution_surface_key'
        if request.repo_root_path:
            return 'repo_root_path'
        if request.runtime_root_path:
            return 'runtime_root_path'
        raise ValueError(
            'ExecutionPackageResolutionRequest requires execution_surface_key, repo_root_path, or runtime_root_path.'
        )

    def _context_from_install(
        self,
        context: InstalledExecutionContextRecord | ExecutionPackageInstallRecord | None,
    ) -> InstalledExecutionContextRecord | None:
        if context is None:
            return None
        if isinstance(context, InstalledExecutionContextRecord):
            return context
        install = context
        overlays = tuple(
            self._repository.list_active_overlays_for_install(install.execution_package_install_id)
        )
        return InstalledExecutionContextRecord(
            execution_surface_key=install.execution_surface_key,
            execution_surface_type=install.execution_surface_type,
            install=install,
            active_overlays=overlays,
            manifest_path=install.installed_manifest_path,
            package_metadata_path=install.installed_package_metadata_path,
            docs_root_path=install.installed_docs_root_path,
            artifacts_root_path=install.installed_artifacts_root_path,
            repo_root_path=install.repo_root_path,
            runtime_root_path=install.runtime_root_path,
            metadata={
                'package_name': install.package_name,
                'package_version': install.package_version,
                'authority_version_id': install.authority_version_id,
                'active_overlay_keys': tuple(item.overlay_key for item in overlays),
            },
        )

    def _capability_request(
        self,
        request: ExecutionPackageResolutionRequest,
        context: InstalledExecutionContextRecord | None,
    ) -> DeploymentCapabilityRequest:
        return DeploymentCapabilityRequest(
            execution_surface_type=(
                context.execution_surface_type
                if context is not None
                else (request.execution_surface_type or 'unknown')
            ),
            execution_surface_key=(
                context.execution_surface_key
                if context is not None
                else (
                    request.execution_surface_key
                    or request.repo_root_path
                    or request.runtime_root_path
                    or 'unknown'
                )
            ),
            required_surface_types=request.required_surface_types,
            required_artifact_refs=request.required_artifact_refs,
            required_overlay_keys=request.required_overlay_keys,
            require_active_install=True,
            metadata=dict(request.metadata or {}),
        )

    def _capability_context(
        self,
        request: ExecutionPackageResolutionRequest,
        context: InstalledExecutionContextRecord | None,
    ) -> DeploymentCapabilityContext:
        if context is None:
            return DeploymentCapabilityContext(
                install_status=None,
                execution_surface_type=request.execution_surface_type or 'unknown',
                execution_surface_key=(
                    request.execution_surface_key
                    or request.repo_root_path
                    or request.runtime_root_path
                    or 'unknown'
                ),
                manifest_path=None,
                package_metadata_path=None,
                docs_root_path=None,
                artifacts_root_path=None,
                active_overlay_keys=(),
                metadata=dict(request.metadata or {}),
            )
        return DeploymentCapabilityContext(
            install_status=context.install.install_status,
            execution_surface_type=context.execution_surface_type,
            execution_surface_key=context.execution_surface_key,
            manifest_path=context.manifest_path,
            package_metadata_path=context.package_metadata_path,
            docs_root_path=context.docs_root_path,
            artifacts_root_path=context.artifacts_root_path,
            active_overlay_keys=tuple(item.overlay_key for item in context.active_overlays),
            metadata=dict(context.metadata or {}),
        )

    def _derive_gaps(
        self,
        request: ExecutionPackageResolutionRequest,
        context: InstalledExecutionContextRecord | None,
        decision: DeploymentCapabilityDecision,
    ) -> tuple[ExecutionPackageGap, ...]:
        gaps: list[ExecutionPackageGap] = []
        surface_key = (
            context.execution_surface_key
            if context is not None
            else (
                request.execution_surface_key
                or request.repo_root_path
                or request.runtime_root_path
            )
        )
        surface_type = (
            context.execution_surface_type
            if context is not None
            else request.execution_surface_type
        )
        if context is None:
            gaps.append(
                ExecutionPackageGap(
                    gap_code='missing_active_install',
                    severity='blocker',
                    execution_surface_key=surface_key,
                    execution_surface_type=surface_type,
                    note='No active installed execution package could be resolved for the requested runtime surface.',
                    recommended_next_action='Install or activate an execution package for this runtime surface before execution-time resolution.',
                    metadata={'resolution_request': self._request_metadata(request)},
                )
            )
            return tuple(gaps)
        for capability in decision.missing_capabilities:
            if capability == 'active_install':
                continue
            if capability == 'execution_surface_type':
                gaps.append(
                    ExecutionPackageGap(
                        gap_code='incompatible_execution_surface_type',
                        severity='blocker',
                        execution_surface_key=surface_key,
                        execution_surface_type=surface_type,
                        note='The resolved execution surface type does not satisfy the requested deployment capability.',
                        recommended_next_action='Route execution to a compatible surface type or relax the required surface-type constraint.',
                        metadata={'required_surface_types': request.required_surface_types},
                    )
                )
            elif capability.startswith('artifact:'):
                artifact_key = capability.split(':', 1)[1]
                gaps.append(
                    ExecutionPackageGap(
                        gap_code='missing_required_artifact_surface',
                        severity='blocker',
                        execution_surface_key=surface_key,
                        execution_surface_type=surface_type,
                        note=f'The active install is missing required artifact surface {artifact_key!r}.',
                        recommended_next_action='Repair or republish the installed execution package so the required artifact pointer is present.',
                        metadata={'artifact_key': artifact_key},
                    )
                )
            elif capability.startswith('overlay:'):
                overlay_key = capability.split(':', 1)[1]
                gaps.append(
                    ExecutionPackageGap(
                        gap_code='missing_required_overlay',
                        severity='blocker',
                        execution_surface_key=surface_key,
                        execution_surface_type=surface_type,
                        note=f'The active install is missing required overlay {overlay_key!r}.',
                        recommended_next_action='Activate the required overlay or adjust the requested overlay requirements.',
                        metadata={'overlay_key': overlay_key},
                    )
                )
            elif capability.startswith('unknown_artifact:'):
                artifact_key = capability.split(':', 1)[1]
                gaps.append(
                    ExecutionPackageGap(
                        gap_code='unknown_artifact_requirement',
                        severity='warning',
                        execution_surface_key=surface_key,
                        execution_surface_type=surface_type,
                        note=f'Unknown deployment-capability artifact requirement {artifact_key!r} was requested.',
                        recommended_next_action='Normalize the requested artifact capability key before relying on this resolution.',
                        metadata={'artifact_key': artifact_key},
                    )
                )
        return tuple(gaps)

    def _assemble_resolution_view(
        self,
        *,
        request: ExecutionPackageResolutionRequest,
        context: InstalledExecutionContextRecord | None,
        decision: DeploymentCapabilityDecision,
        gaps: tuple[ExecutionPackageGap, ...],
    ) -> ExecutionPackageResolutionView:
        if context is None:
            execution_surface_key = (
                request.execution_surface_key
                or request.repo_root_path
                or request.runtime_root_path
                or 'unknown'
            )
            execution_surface_type = request.execution_surface_type or 'unknown'
            capability_summary = self._capability_summary(decision)
            return ExecutionPackageResolutionView(
                execution_surface_key=execution_surface_key,
                execution_surface_type=execution_surface_type,
                execution_package_install_id=None,
                package_name=None,
                package_version=None,
                authority_version_id=None,
                active_overlay_keys=(),
                manifest_path=None,
                package_metadata_path=None,
                docs_root_path=None,
                artifacts_root_path=None,
                repo_root_path=request.repo_root_path,
                runtime_root_path=request.runtime_root_path,
                capability_summary=capability_summary,
                warnings=tuple(gap.note for gap in gaps if gap.severity in {'warning', 'blocker'}),
                gaps=gaps,
                metadata={'resolution_request': self._request_metadata(request)},
            )
        capability_summary = self._capability_summary(decision)
        return ExecutionPackageResolutionView(
            execution_surface_key=context.execution_surface_key,
            execution_surface_type=context.execution_surface_type,
            execution_package_install_id=context.install.execution_package_install_id,
            package_name=context.install.package_name,
            package_version=context.install.package_version,
            authority_version_id=context.install.authority_version_id,
            active_overlay_keys=tuple(item.overlay_key for item in context.active_overlays),
            manifest_path=context.manifest_path,
            package_metadata_path=context.package_metadata_path,
            docs_root_path=context.docs_root_path,
            artifacts_root_path=context.artifacts_root_path,
            repo_root_path=context.repo_root_path,
            runtime_root_path=context.runtime_root_path,
            capability_summary=capability_summary,
            warnings=tuple(gap.note for gap in gaps if gap.severity in {'warning', 'blocker'}),
            gaps=gaps,
            metadata=dict(context.metadata or {}),
        )

    def _capability_summary(
        self,
        decision: DeploymentCapabilityDecision,
    ) -> ExecutionPackageCapabilitySummary:
        return ExecutionPackageCapabilitySummary(
            allowed=decision.allowed,
            missing_capabilities=decision.missing_capabilities,
            blocking_reasons=decision.blocking_reasons,
            satisfied_capabilities=decision.satisfied_capabilities,
            notes=decision.notes,
            metadata=dict(decision.metadata or {}),
        )

    def _request_metadata(self, request: ExecutionPackageResolutionRequest) -> dict[str, object]:
        return {
            'execution_surface_key': request.execution_surface_key,
            'execution_surface_type': request.execution_surface_type,
            'repo_root_path': request.repo_root_path,
            'runtime_root_path': request.runtime_root_path,
            'consumer_context_key': request.consumer_context_key,
        }


__all__ = ['DefaultExecutionPackageResolutionService']

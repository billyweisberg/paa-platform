"""Models for the execution package resolution service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


ExecutionPackageGapSeverity = Literal['info', 'warning', 'blocker']


@dataclass(frozen=True)
class ExecutionPackageResolutionRequest:
    execution_surface_key: str | None = None
    execution_surface_type: str | None = None
    repo_root_path: str | None = None
    runtime_root_path: str | None = None
    work_item_id: str | None = None
    coder_run_brief_id: str | None = None
    consumer_context_key: str | None = None
    required_surface_types: tuple[str, ...] = ()
    required_artifact_refs: tuple[str, ...] = ()
    required_overlay_keys: tuple[str, ...] = ()
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class ExecutionPackageCapabilitySummary:
    allowed: bool
    missing_capabilities: tuple[str, ...]
    blocking_reasons: tuple[str, ...]
    satisfied_capabilities: tuple[str, ...]
    notes: tuple[str, ...]
    metadata: dict[str, Any]


@dataclass(frozen=True)
class ExecutionPackageGap:
    gap_code: str
    severity: ExecutionPackageGapSeverity
    execution_surface_key: str | None
    execution_surface_type: str | None
    note: str
    recommended_next_action: str | None
    metadata: dict[str, Any]


@dataclass(frozen=True)
class ExecutionPackageResolutionView:
    execution_surface_key: str
    execution_surface_type: str
    execution_package_install_id: str | None
    package_name: str | None
    package_version: str | None
    authority_version_id: str | None
    active_overlay_keys: tuple[str, ...]
    manifest_path: str | None
    package_metadata_path: str | None
    docs_root_path: str | None
    artifacts_root_path: str | None
    repo_root_path: str | None
    runtime_root_path: str | None
    capability_summary: ExecutionPackageCapabilitySummary
    warnings: tuple[str, ...]
    gaps: tuple[ExecutionPackageGap, ...]
    metadata: dict[str, Any]


__all__ = [
    'ExecutionPackageCapabilitySummary',
    'ExecutionPackageGap',
    'ExecutionPackageGapSeverity',
    'ExecutionPackageResolutionRequest',
    'ExecutionPackageResolutionView',
]

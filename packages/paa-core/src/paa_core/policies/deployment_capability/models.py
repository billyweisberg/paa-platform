"""Models for the deployment capability policy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DeploymentCapabilityRequest:
    execution_surface_type: str
    execution_surface_key: str
    required_surface_types: tuple[str, ...] = ()
    required_artifact_refs: tuple[str, ...] = ()
    required_overlay_keys: tuple[str, ...] = ()
    require_active_install: bool = True
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class DeploymentCapabilityContext:
    install_status: str | None
    execution_surface_type: str
    execution_surface_key: str
    manifest_path: str | None
    package_metadata_path: str | None
    docs_root_path: str | None
    artifacts_root_path: str | None
    active_overlay_keys: tuple[str, ...] = ()
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class DeploymentCapabilityDecision:
    allowed: bool
    missing_capabilities: tuple[str, ...]
    blocking_reasons: tuple[str, ...]
    satisfied_capabilities: tuple[str, ...]
    notes: tuple[str, ...]
    metadata: dict[str, Any]


__all__ = [
    'DeploymentCapabilityContext',
    'DeploymentCapabilityDecision',
    'DeploymentCapabilityRequest',
]

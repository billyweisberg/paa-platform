"""DTOs for ExecutionPackage repository records."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ExecutionPackageInstallRecord:
    execution_package_install_id: str
    project_id: str
    authority_version_id: str
    installed_by_agent_id: str | None
    installed_by_role_id: str | None
    execution_surface_type: str
    execution_surface_key: str
    repo_root_path: str | None
    runtime_root_path: str | None
    install_slot_name: str | None
    package_name: str
    package_version: str | None
    package_build_ref: str | None
    package_hash: str | None
    package_schema_version: str | None
    install_status: str
    installed_from_source: str
    superseded_by_install_id: str | None
    replaced_install_id: str | None
    deactivation_reason_code: str | None
    deactivation_reason_text: str | None
    installed_manifest_path: str | None
    installed_package_metadata_path: str | None
    installed_docs_root_path: str | None
    installed_artifacts_root_path: str | None
    installed_at: str | None
    activated_at: str | None
    deactivated_at: str | None
    metadata: dict[str, Any]
    created_at: str | None
    updated_at: str | None


@dataclass(frozen=True)
class ExecutionPackageOverlayRecord:
    execution_package_overlay_id: str
    execution_package_install_id: str
    project_id: str
    authority_version_id: str | None
    work_item_id: str | None
    activated_by_agent_id: str | None
    activated_by_role_id: str | None
    overlay_key: str
    overlay_type: str
    overlay_name: str
    overlay_version: str | None
    overlay_hash: str | None
    overlay_schema_version: str | None
    overlay_status: str
    overlay_source: str
    replaced_overlay_id: str | None
    superseded_by_overlay_id: str | None
    deactivation_reason_code: str | None
    deactivation_reason_text: str | None
    overlay_root_path: str | None
    overlay_metadata_path: str | None
    overlay_manifest_task_path: str | None
    overlay_summary_path: str | None
    activated_at: str | None
    deactivated_at: str | None
    metadata: dict[str, Any]
    created_at: str | None
    updated_at: str | None


@dataclass(frozen=True)
class InstalledExecutionContextRecord:
    execution_surface_key: str
    execution_surface_type: str
    install: ExecutionPackageInstallRecord
    active_overlays: tuple[ExecutionPackageOverlayRecord, ...]
    manifest_path: str | None
    package_metadata_path: str | None
    docs_root_path: str | None
    artifacts_root_path: str | None
    repo_root_path: str | None
    runtime_root_path: str | None
    metadata: dict[str, Any]


__all__ = [
    'ExecutionPackageInstallRecord',
    'ExecutionPackageOverlayRecord',
    'InstalledExecutionContextRecord',
]

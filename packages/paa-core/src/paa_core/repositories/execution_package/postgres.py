"""Postgres-backed ExecutionPackage repository implementation."""

from __future__ import annotations

from typing import Any

from paa_core.db import DBSettings, query_json_rows, sql_literal

from .models import (
    ExecutionPackageInstallRecord,
    ExecutionPackageOverlayRecord,
    InstalledExecutionContextRecord,
)


class PostgresExecutionPackageRepository:
    """Postgres-backed repository for active execution-package resolution."""

    def __init__(self, *, settings: DBSettings | None = None) -> None:
        self._settings = settings

    def get_execution_package_install(
        self,
        execution_package_install_id: str,
    ) -> ExecutionPackageInstallRecord | None:
        sql = f"""
SELECT row_to_json(t)
FROM (
  SELECT
    i.execution_package_install_id::text,
    i.project_id::text,
    i.authority_version_id::text,
    i.installed_by_agent_id::text,
    i.installed_by_role_id::text,
    i.execution_surface_type::text AS execution_surface_type,
    i.execution_surface_key,
    i.repo_root_path,
    i.runtime_root_path,
    i.install_slot_name,
    i.package_name,
    i.package_version,
    i.package_build_ref,
    i.package_hash,
    i.package_schema_version,
    i.install_status::text AS install_status,
    i.installed_from_source::text AS installed_from_source,
    i.superseded_by_install_id::text,
    i.replaced_install_id::text,
    i.deactivation_reason_code,
    i.deactivation_reason_text,
    i.installed_manifest_path,
    i.installed_package_metadata_path,
    i.installed_docs_root_path,
    i.installed_artifacts_root_path,
    i.installed_at::text,
    i.activated_at::text,
    i.deactivated_at::text,
    i.metadata_json AS metadata,
    i.created_at::text,
    i.updated_at::text
  FROM paa.execution_package_installs i
  WHERE i.execution_package_install_id = {sql_literal(execution_package_install_id)}::uuid
) AS t;
"""
        rows = self._query_json_rows(sql)
        if not rows:
            return None
        return self._install_from_row(rows[0])

    def get_active_install_for_execution_surface(
        self,
        execution_surface_key: str,
    ) -> ExecutionPackageInstallRecord | None:
        sql = self._active_install_sql(
            where_clause=f"i.execution_surface_key = {sql_literal(execution_surface_key)}"
        )
        rows = self._query_json_rows(sql)
        if not rows:
            return None
        return self._install_from_row(rows[0])

    def get_active_install_for_repo_root(
        self,
        repo_root_path: str,
    ) -> ExecutionPackageInstallRecord | None:
        sql = self._active_install_sql(
            where_clause=f"i.repo_root_path = {sql_literal(repo_root_path)}"
        )
        rows = self._query_json_rows(sql)
        if not rows:
            return None
        return self._install_from_row(rows[0])

    def get_active_install_for_runtime_root(
        self,
        runtime_root_path: str,
    ) -> ExecutionPackageInstallRecord | None:
        sql = self._active_install_sql(
            where_clause=f"i.runtime_root_path = {sql_literal(runtime_root_path)}"
        )
        rows = self._query_json_rows(sql)
        if not rows:
            return None
        return self._install_from_row(rows[0])

    def list_overlays_for_install(
        self,
        execution_package_install_id: str,
    ) -> list[ExecutionPackageOverlayRecord]:
        sql = self._overlay_sql(
            execution_package_install_id=execution_package_install_id,
            active_only=False,
        )
        return [self._overlay_from_row(row) for row in self._query_json_rows(sql)]

    def list_active_overlays_for_install(
        self,
        execution_package_install_id: str,
    ) -> list[ExecutionPackageOverlayRecord]:
        sql = self._overlay_sql(
            execution_package_install_id=execution_package_install_id,
            active_only=True,
        )
        return [self._overlay_from_row(row) for row in self._query_json_rows(sql)]

    def resolve_active_execution_context(
        self,
        execution_surface_key: str,
    ) -> InstalledExecutionContextRecord | None:
        install = self.get_active_install_for_execution_surface(execution_surface_key)
        if install is None:
            return None
        overlays = tuple(
            self.list_active_overlays_for_install(install.execution_package_install_id)
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

    def _active_install_sql(self, *, where_clause: str) -> str:
        return f"""
SELECT row_to_json(t)
FROM (
  SELECT
    i.execution_package_install_id::text,
    i.project_id::text,
    i.authority_version_id::text,
    i.installed_by_agent_id::text,
    i.installed_by_role_id::text,
    i.execution_surface_type::text AS execution_surface_type,
    i.execution_surface_key,
    i.repo_root_path,
    i.runtime_root_path,
    i.install_slot_name,
    i.package_name,
    i.package_version,
    i.package_build_ref,
    i.package_hash,
    i.package_schema_version,
    i.install_status::text AS install_status,
    i.installed_from_source::text AS installed_from_source,
    i.superseded_by_install_id::text,
    i.replaced_install_id::text,
    i.deactivation_reason_code,
    i.deactivation_reason_text,
    i.installed_manifest_path,
    i.installed_package_metadata_path,
    i.installed_docs_root_path,
    i.installed_artifacts_root_path,
    i.installed_at::text,
    i.activated_at::text,
    i.deactivated_at::text,
    i.metadata_json AS metadata,
    i.created_at::text,
    i.updated_at::text
  FROM paa.execution_package_installs i
  WHERE {where_clause}
    AND i.install_status = 'active'::paa.execution_package_install_status
  ORDER BY i.activated_at DESC NULLS LAST, i.installed_at DESC
  LIMIT 1
) AS t;
"""

    def _overlay_sql(self, *, execution_package_install_id: str, active_only: bool) -> str:
        active_filter = (
            "AND o.overlay_status = 'active'::paa.execution_package_overlay_status"
            if active_only
            else ""
        )
        return f"""
SELECT row_to_json(t)
FROM (
  SELECT
    o.execution_package_overlay_id::text,
    o.execution_package_install_id::text,
    o.project_id::text,
    o.authority_version_id::text,
    o.work_item_id::text,
    o.activated_by_agent_id::text,
    o.activated_by_role_id::text,
    o.overlay_key,
    o.overlay_type::text AS overlay_type,
    o.overlay_name,
    o.overlay_version,
    o.overlay_hash,
    o.overlay_schema_version,
    o.overlay_status::text AS overlay_status,
    o.overlay_source::text AS overlay_source,
    o.replaced_overlay_id::text,
    o.superseded_by_overlay_id::text,
    o.deactivation_reason_code,
    o.deactivation_reason_text,
    o.overlay_root_path,
    o.overlay_metadata_path,
    o.overlay_manifest_task_path,
    o.overlay_summary_path,
    o.activated_at::text,
    o.deactivated_at::text,
    o.metadata_json AS metadata,
    o.created_at::text,
    o.updated_at::text
  FROM paa.execution_package_overlays o
  WHERE o.execution_package_install_id = {sql_literal(execution_package_install_id)}::uuid
    {active_filter}
  ORDER BY o.created_at DESC, o.overlay_key
) AS t;
"""

    def _query_json_rows(self, sql: str) -> list[dict[str, Any]]:
        return query_json_rows(sql, settings=self._settings)

    def _install_from_row(self, row: dict[str, Any]) -> ExecutionPackageInstallRecord:
        return ExecutionPackageInstallRecord(
            execution_package_install_id=row['execution_package_install_id'],
            project_id=row['project_id'],
            authority_version_id=row['authority_version_id'],
            installed_by_agent_id=row.get('installed_by_agent_id'),
            installed_by_role_id=row.get('installed_by_role_id'),
            execution_surface_type=row['execution_surface_type'],
            execution_surface_key=row['execution_surface_key'],
            repo_root_path=row.get('repo_root_path'),
            runtime_root_path=row.get('runtime_root_path'),
            install_slot_name=row.get('install_slot_name'),
            package_name=row['package_name'],
            package_version=row.get('package_version'),
            package_build_ref=row.get('package_build_ref'),
            package_hash=row.get('package_hash'),
            package_schema_version=row.get('package_schema_version'),
            install_status=row['install_status'],
            installed_from_source=row['installed_from_source'],
            superseded_by_install_id=row.get('superseded_by_install_id'),
            replaced_install_id=row.get('replaced_install_id'),
            deactivation_reason_code=row.get('deactivation_reason_code'),
            deactivation_reason_text=row.get('deactivation_reason_text'),
            installed_manifest_path=row.get('installed_manifest_path'),
            installed_package_metadata_path=row.get('installed_package_metadata_path'),
            installed_docs_root_path=row.get('installed_docs_root_path'),
            installed_artifacts_root_path=row.get('installed_artifacts_root_path'),
            installed_at=row.get('installed_at'),
            activated_at=row.get('activated_at'),
            deactivated_at=row.get('deactivated_at'),
            metadata=dict(row.get('metadata') or {}),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
        )

    def _overlay_from_row(self, row: dict[str, Any]) -> ExecutionPackageOverlayRecord:
        return ExecutionPackageOverlayRecord(
            execution_package_overlay_id=row['execution_package_overlay_id'],
            execution_package_install_id=row['execution_package_install_id'],
            project_id=row['project_id'],
            authority_version_id=row.get('authority_version_id'),
            work_item_id=row.get('work_item_id'),
            activated_by_agent_id=row.get('activated_by_agent_id'),
            activated_by_role_id=row.get('activated_by_role_id'),
            overlay_key=row['overlay_key'],
            overlay_type=row['overlay_type'],
            overlay_name=row['overlay_name'],
            overlay_version=row.get('overlay_version'),
            overlay_hash=row.get('overlay_hash'),
            overlay_schema_version=row.get('overlay_schema_version'),
            overlay_status=row['overlay_status'],
            overlay_source=row['overlay_source'],
            replaced_overlay_id=row.get('replaced_overlay_id'),
            superseded_by_overlay_id=row.get('superseded_by_overlay_id'),
            deactivation_reason_code=row.get('deactivation_reason_code'),
            deactivation_reason_text=row.get('deactivation_reason_text'),
            overlay_root_path=row.get('overlay_root_path'),
            overlay_metadata_path=row.get('overlay_metadata_path'),
            overlay_manifest_task_path=row.get('overlay_manifest_task_path'),
            overlay_summary_path=row.get('overlay_summary_path'),
            activated_at=row.get('activated_at'),
            deactivated_at=row.get('deactivated_at'),
            metadata=dict(row.get('metadata') or {}),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
        )


__all__ = ['PostgresExecutionPackageRepository']

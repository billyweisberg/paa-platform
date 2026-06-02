"""Postgres-backed runtime identity repository implementation."""

from __future__ import annotations

import json
from typing import Any

from paa_core.db import DBSettings, run_psql, sql_literal

from .models import AgentRecord, AgentUpsertSpec, RoleRecord, RoleUpsertSpec


class PostgresRuntimeIdentityRepository:
    """Create and read project-scoped runtime roles and agents."""

    def __init__(self, *, settings: DBSettings | None = None) -> None:
        self._settings = settings

    def get_role_by_name(self, project_slug: str, role_name: str) -> RoleRecord | None:
        sql = self._role_sql(
            where_clause=(
                f"p.slug = {sql_literal(project_slug)} AND r.name = {sql_literal(role_name)}"
            )
        )
        rows = self._query_json_rows(sql)
        return self._role_from_row(rows[0]) if rows else None

    def upsert_role(self, spec: RoleUpsertSpec) -> RoleRecord:
        project_id = self._resolve_project_id(spec.project_slug)
        sql = f"""
INSERT INTO paa.roles (
  project_id,
  name,
  category,
  description,
  is_human_capable,
  is_automation_capable,
  sort_order,
  active
)
VALUES (
  {sql_literal(project_id)}::uuid,
  {sql_literal(spec.name)},
  {sql_literal(spec.category)}::paa.role_category,
  {sql_literal(spec.description)},
  {self._bool_sql(spec.is_human_capable)},
  {self._bool_sql(spec.is_automation_capable)},
  {spec.sort_order},
  {self._bool_sql(spec.active)}
)
ON CONFLICT (project_id, name) DO UPDATE SET
  category = EXCLUDED.category,
  description = EXCLUDED.description,
  is_human_capable = EXCLUDED.is_human_capable,
  is_automation_capable = EXCLUDED.is_automation_capable,
  sort_order = EXCLUDED.sort_order,
  active = EXCLUDED.active,
  updated_at = now();
"""
        run_psql(sql, settings=self._settings)
        record = self.get_role_by_name(spec.project_slug, spec.name)
        if record is None:
            raise RuntimeError(f'Role upsert did not return a persisted record for {spec.name!r}.')
        return record

    def get_agent_by_name(self, project_slug: str, agent_name: str) -> AgentRecord | None:
        sql = self._agent_sql(
            where_clause=(
                f"p.slug = {sql_literal(project_slug)} AND a.name = {sql_literal(agent_name)}"
            )
        )
        rows = self._query_json_rows(sql)
        return self._agent_from_row(rows[0]) if rows else None

    def upsert_agent(self, spec: AgentUpsertSpec) -> AgentRecord:
        project_id = self._resolve_project_id(spec.project_slug)
        role_id_sql = 'NULL'
        if spec.role_name is not None:
            role = self.get_role_by_name(spec.project_slug, spec.role_name)
            if role is None:
                raise LookupError(
                    f'Role {spec.role_name!r} does not exist in project {spec.project_slug!r}.'
                )
            role_id_sql = f"{sql_literal(role.role_id)}::uuid"
        metadata_json = json.dumps(spec.metadata or {}, sort_keys=True)
        sql = f"""
INSERT INTO paa.agents (
  project_id,
  role_id,
  name,
  agent_type,
  runtime_kind,
  active,
  metadata_json
)
VALUES (
  {sql_literal(project_id)}::uuid,
  {role_id_sql},
  {sql_literal(spec.name)},
  {sql_literal(spec.agent_type)}::paa.agent_type,
  {sql_literal(spec.runtime_kind)},
  {self._bool_sql(spec.active)},
  {sql_literal(metadata_json)}::jsonb
)
ON CONFLICT (project_id, name) DO UPDATE SET
  role_id = EXCLUDED.role_id,
  agent_type = EXCLUDED.agent_type,
  runtime_kind = EXCLUDED.runtime_kind,
  active = EXCLUDED.active,
  metadata_json = paa.agents.metadata_json || EXCLUDED.metadata_json,
  updated_at = now();
"""
        run_psql(sql, settings=self._settings)
        record = self.get_agent_by_name(spec.project_slug, spec.name)
        if record is None:
            raise RuntimeError(f'Agent upsert did not return a persisted record for {spec.name!r}.')
        return record

    def _resolve_project_id(self, project_slug: str) -> str:
        sql = f"SELECT project_id::text FROM paa.projects WHERE slug = {sql_literal(project_slug)} LIMIT 1;"
        output = run_psql(sql, settings=self._settings).strip()
        if not output:
            raise LookupError(f'Project slug {project_slug!r} does not exist.')
        return output

    def _role_sql(self, *, where_clause: str) -> str:
        return f"""
SELECT row_to_json(t)
FROM (
  SELECT
    r.role_id::text,
    r.project_id::text,
    r.name,
    r.category::text AS category,
    r.description,
    r.is_human_capable,
    r.is_automation_capable,
    r.sort_order,
    r.active,
    r.created_at::text,
    r.updated_at::text
  FROM paa.roles r
  JOIN paa.projects p ON p.project_id = r.project_id
  WHERE {where_clause}
) AS t;
"""

    def _agent_sql(self, *, where_clause: str) -> str:
        return f"""
SELECT row_to_json(t)
FROM (
  SELECT
    a.agent_id::text,
    a.project_id::text,
    a.role_id::text,
    a.name,
    a.agent_type::text AS agent_type,
    a.runtime_kind,
    a.active,
    a.metadata_json AS metadata,
    a.created_at::text,
    a.updated_at::text
  FROM paa.agents a
  JOIN paa.projects p ON p.project_id = a.project_id
  WHERE {where_clause}
) AS t;
"""

    def _query_json_rows(self, sql: str) -> list[dict[str, Any]]:
        output = run_psql(sql, settings=self._settings)
        rows: list[dict[str, Any]] = []
        for line in output.splitlines():
            text = line.strip()
            if not text:
                continue
            rows.append(json.loads(text))
        return rows

    @staticmethod
    def _bool_sql(value: bool) -> str:
        return 'true' if value else 'false'

    @staticmethod
    def _role_from_row(row: dict[str, Any]) -> RoleRecord:
        return RoleRecord(
            role_id=row['role_id'],
            project_id=row['project_id'],
            name=row['name'],
            category=row['category'],
            description=row.get('description'),
            is_human_capable=bool(row['is_human_capable']),
            is_automation_capable=bool(row['is_automation_capable']),
            sort_order=int(row['sort_order']),
            active=bool(row['active']),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
        )

    @staticmethod
    def _agent_from_row(row: dict[str, Any]) -> AgentRecord:
        return AgentRecord(
            agent_id=row['agent_id'],
            project_id=row['project_id'],
            role_id=row.get('role_id'),
            name=row['name'],
            agent_type=row['agent_type'],
            runtime_kind=row.get('runtime_kind'),
            active=bool(row['active']),
            metadata=dict(row.get('metadata') or {}),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
        )


__all__ = ['PostgresRuntimeIdentityRepository']

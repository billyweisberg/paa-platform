"""Postgres-backed source-authority repository implementation."""

from __future__ import annotations

import json
from typing import Any

from paa_core.db import DBSettings, execute_sql, query_json_rows, query_scalar, sql_literal

from .models import (
    AuthorityVersionRecord,
    AuthorityVersionUpsertSpec,
    ImplementationTargetRecord,
    ImplementationTargetUpsertSpec,
    ProjectRecord,
    ProjectUpsertSpec,
    SpecFragmentRecord,
    SpecFragmentUpsertSpec,
    WorkItemRecord,
    WorkItemUpsertSpec,
)


class PostgresSourceAuthorityRepository:
    """Create and read source-authority anchor records."""

    def __init__(self, *, settings: DBSettings | None = None) -> None:
        self._settings = settings

    def get_project_by_slug(self, project_slug: str) -> ProjectRecord | None:
        sql = f"""
SELECT row_to_json(t)
FROM (
  SELECT
    p.project_id::text,
    p.slug,
    p.name,
    p.repo_url,
    p.execution_surface,
    p.status::text AS status,
    p.created_at::text,
    p.updated_at::text
  FROM paa.projects p
  WHERE p.slug = {sql_literal(project_slug)}
) AS t;
"""
        rows = self._query_json_rows(sql)
        return self._project_from_row(rows[0]) if rows else None

    def upsert_project(self, spec: ProjectUpsertSpec) -> ProjectRecord:
        sql = f"""
INSERT INTO paa.projects (slug, name, repo_url, execution_surface, status)
VALUES (
  {sql_literal(spec.slug)},
  {sql_literal(spec.name)},
  {sql_literal(spec.repo_url)},
  {sql_literal(spec.execution_surface)},
  {sql_literal(spec.status)}::paa.project_status
)
ON CONFLICT (slug) DO UPDATE SET
  name = EXCLUDED.name,
  repo_url = COALESCE(EXCLUDED.repo_url, paa.projects.repo_url),
  execution_surface = EXCLUDED.execution_surface,
  status = EXCLUDED.status,
  updated_at = now();
"""
        self._execute(sql)
        record = self.get_project_by_slug(spec.slug)
        if record is None:
            raise RuntimeError(f'Project upsert did not return a persisted record for {spec.slug!r}.')
        return record

    def upsert_authority_version(self, spec: AuthorityVersionUpsertSpec) -> AuthorityVersionRecord:
        project = self._require_project(spec.project_slug)
        sql = f"""
INSERT INTO paa.authority_versions (
  project_id,
  version_label,
  source_commit,
  published_from_ref,
  manifest_path,
  published_at,
  status,
  notes
)
VALUES (
  {sql_literal(project.project_id)}::uuid,
  {sql_literal(spec.version_label)},
  {sql_literal(spec.source_commit)},
  {sql_literal(spec.published_from_ref)},
  {sql_literal(spec.manifest_path)},
  {self._timestamp_or_null(spec.published_at)},
  {sql_literal(spec.status)}::paa.authority_status,
  {sql_literal(spec.notes)}
)
ON CONFLICT (project_id, version_label) DO UPDATE SET
  source_commit = COALESCE(EXCLUDED.source_commit, paa.authority_versions.source_commit),
  published_from_ref = COALESCE(EXCLUDED.published_from_ref, paa.authority_versions.published_from_ref),
  manifest_path = COALESCE(EXCLUDED.manifest_path, paa.authority_versions.manifest_path),
  published_at = COALESCE(EXCLUDED.published_at, paa.authority_versions.published_at),
  status = EXCLUDED.status,
  notes = COALESCE(EXCLUDED.notes, paa.authority_versions.notes),
  updated_at = now();
"""
        self._execute(sql)
        record = self._get_authority_version(project.project_id, spec.version_label)
        if record is None:
            raise RuntimeError(
                f'Authority version upsert did not return a persisted record for {spec.version_label!r}.'
            )
        return record

    def upsert_spec_fragment(self, spec: SpecFragmentUpsertSpec) -> SpecFragmentRecord:
        project = self._require_project(spec.project_slug)
        metadata = dict(spec.metadata or {})
        if spec.external_fragment_id is not None:
            metadata['spec_fragment_id_external'] = spec.external_fragment_id
        sql = f"""
WITH existing AS (
  SELECT sf.spec_fragment_id
  FROM paa.spec_fragments sf
  WHERE sf.project_id = {sql_literal(project.project_id)}::uuid
    AND (
      ({sql_literal(spec.external_fragment_id)} IS NOT NULL AND sf.metadata_json->>'spec_fragment_id_external' = {sql_literal(spec.external_fragment_id)})
      OR ({sql_literal(spec.external_fragment_id)} IS NULL AND sf.delta_family IS NOT DISTINCT FROM {sql_literal(spec.delta_family)})
    )
  ORDER BY sf.created_at ASC, sf.spec_fragment_id
  LIMIT 1
), updated AS (
  UPDATE paa.spec_fragments sf
  SET
    title = {sql_literal(spec.title)},
    canonical_statement = {sql_literal(spec.canonical_statement)},
    fragment_kind = {sql_literal(spec.fragment_kind)}::paa.fragment_kind,
    delta_family = {sql_literal(spec.delta_family)},
    authorized_delta_family = {sql_literal(spec.authorized_delta_family)},
    out_of_scope_delta_families_json = {self._json_sql(list(spec.out_of_scope_delta_families))}::jsonb,
    expected_touch_surfaces_json = {self._json_sql(list(spec.expected_touch_surfaces))}::jsonb,
    status = {sql_literal(spec.status)}::paa.knowledge_status,
    metadata_json = {self._json_sql(metadata)}::jsonb,
    updated_at = now()
  FROM existing
  WHERE sf.spec_fragment_id = existing.spec_fragment_id
  RETURNING sf.spec_fragment_id
), inserted AS (
  INSERT INTO paa.spec_fragments (
    project_id,
    title,
    canonical_statement,
    fragment_kind,
    delta_family,
    authorized_delta_family,
    out_of_scope_delta_families_json,
    expected_touch_surfaces_json,
    status,
    metadata_json
  )
  SELECT
    {sql_literal(project.project_id)}::uuid,
    {sql_literal(spec.title)},
    {sql_literal(spec.canonical_statement)},
    {sql_literal(spec.fragment_kind)}::paa.fragment_kind,
    {sql_literal(spec.delta_family)},
    {sql_literal(spec.authorized_delta_family)},
    {self._json_sql(list(spec.out_of_scope_delta_families))}::jsonb,
    {self._json_sql(list(spec.expected_touch_surfaces))}::jsonb,
    {sql_literal(spec.status)}::paa.knowledge_status,
    {self._json_sql(metadata)}::jsonb
  WHERE NOT EXISTS (SELECT 1 FROM existing)
  RETURNING spec_fragment_id
)
SELECT 1;
"""
        self._execute(sql)
        record = self._get_spec_fragment(
            project.project_id,
            external_fragment_id=spec.external_fragment_id,
            delta_family=spec.delta_family,
        )
        if record is None:
            raise RuntimeError('Spec fragment upsert did not return a persisted record.')
        return record

    def upsert_implementation_target(
        self, spec: ImplementationTargetUpsertSpec
    ) -> ImplementationTargetRecord:
        self._require_spec_fragment(spec.spec_fragment_id)
        metadata = dict(spec.metadata or {})
        if spec.external_target_id is not None:
            metadata['implementation_target_id_external'] = spec.external_target_id
        sql = f"""
WITH existing AS (
  SELECT it.implementation_target_id
  FROM paa.implementation_targets it
  WHERE it.spec_fragment_id = {sql_literal(spec.spec_fragment_id)}::uuid
    AND (
      ({sql_literal(spec.external_target_id)} IS NOT NULL AND it.metadata_json->>'implementation_target_id_external' = {sql_literal(spec.external_target_id)})
      OR ({sql_literal(spec.external_target_id)} IS NULL AND it.title = {sql_literal(spec.title)})
    )
  ORDER BY it.created_at ASC, it.implementation_target_id
  LIMIT 1
), updated AS (
  UPDATE paa.implementation_targets it
  SET
    title = {sql_literal(spec.title)},
    current_gap_json = {self._json_sql(list(spec.current_gap))}::jsonb,
    desired_state_json = {self._json_sql(list(spec.desired_state))}::jsonb,
    protected_baseline_json = {self._json_sql(list(spec.protected_baseline))}::jsonb,
    out_of_scope_json = {self._json_sql(list(spec.out_of_scope))}::jsonb,
    pre_handoff_scope_checks_json = {self._json_sql(list(spec.pre_handoff_scope_checks))}::jsonb,
    risk_level = {sql_literal(spec.risk_level)}::paa.risk_level,
    status = {sql_literal(spec.status)}::paa.knowledge_status,
    metadata_json = {self._json_sql(metadata)}::jsonb,
    updated_at = now()
  FROM existing
  WHERE it.implementation_target_id = existing.implementation_target_id
  RETURNING it.implementation_target_id
), inserted AS (
  INSERT INTO paa.implementation_targets (
    spec_fragment_id,
    title,
    current_gap_json,
    desired_state_json,
    protected_baseline_json,
    out_of_scope_json,
    pre_handoff_scope_checks_json,
    risk_level,
    status,
    metadata_json
  )
  SELECT
    {sql_literal(spec.spec_fragment_id)}::uuid,
    {sql_literal(spec.title)},
    {self._json_sql(list(spec.current_gap))}::jsonb,
    {self._json_sql(list(spec.desired_state))}::jsonb,
    {self._json_sql(list(spec.protected_baseline))}::jsonb,
    {self._json_sql(list(spec.out_of_scope))}::jsonb,
    {self._json_sql(list(spec.pre_handoff_scope_checks))}::jsonb,
    {sql_literal(spec.risk_level)}::paa.risk_level,
    {sql_literal(spec.status)}::paa.knowledge_status,
    {self._json_sql(metadata)}::jsonb
  WHERE NOT EXISTS (SELECT 1 FROM existing)
  RETURNING implementation_target_id
)
SELECT 1;
"""
        self._execute(sql)
        record = self._get_implementation_target(
            spec.spec_fragment_id,
            external_target_id=spec.external_target_id,
            title=spec.title,
        )
        if record is None:
            raise RuntimeError('Implementation target upsert did not return a persisted record.')
        return record

    def upsert_work_item(self, spec: WorkItemUpsertSpec) -> WorkItemRecord:
        project = self._require_project(spec.project_slug)
        self._require_authority_version(spec.authority_version_id)
        if spec.spec_fragment_id is not None:
            self._require_spec_fragment(spec.spec_fragment_id)
        if spec.implementation_target_id is not None:
            self._require_implementation_target(spec.implementation_target_id)
        sql = f"""
WITH existing AS (
  SELECT wi.work_item_id
  FROM paa.work_items wi
  WHERE wi.project_id = {sql_literal(project.project_id)}::uuid
    AND (
      ({'true' if spec.issue_number is not None else 'false'} AND wi.issue_number = {self._int_or_null(spec.issue_number)})
      OR ({sql_literal(spec.spec_fragment_ref)} IS NOT NULL AND wi.spec_fragment_ref = {sql_literal(spec.spec_fragment_ref)})
    )
  ORDER BY wi.created_at ASC, wi.work_item_id
  LIMIT 1
), updated AS (
  UPDATE paa.work_items wi
  SET
    authority_version_id = {sql_literal(spec.authority_version_id)}::uuid,
    title = {sql_literal(spec.title)},
    status = {sql_literal(spec.status)}::paa.work_item_status,
    merge_policy = {sql_literal(spec.merge_policy)},
    requires_qa = {self._bool_sql(spec.requires_qa)},
    issue_number = COALESCE({self._int_or_null(spec.issue_number)}, wi.issue_number),
    implementation_target_ref = {sql_literal(spec.implementation_target_ref)},
    spec_fragment_ref = {sql_literal(spec.spec_fragment_ref)},
    domain_ref = {self._json_sql(spec.domain_ref or {})}::jsonb,
    spec_fragment_id = {self._uuid_or_null(spec.spec_fragment_id)},
    implementation_target_id = {self._uuid_or_null(spec.implementation_target_id)},
    updated_at = now()
  FROM existing
  WHERE wi.work_item_id = existing.work_item_id
  RETURNING wi.work_item_id
), inserted AS (
  INSERT INTO paa.work_items (
    project_id,
    authority_version_id,
    title,
    status,
    merge_policy,
    requires_qa,
    issue_number,
    implementation_target_ref,
    spec_fragment_ref,
    domain_ref,
    spec_fragment_id,
    implementation_target_id
  )
  SELECT
    {sql_literal(project.project_id)}::uuid,
    {sql_literal(spec.authority_version_id)}::uuid,
    {sql_literal(spec.title)},
    {sql_literal(spec.status)}::paa.work_item_status,
    {sql_literal(spec.merge_policy)},
    {self._bool_sql(spec.requires_qa)},
    {self._int_or_null(spec.issue_number)},
    {sql_literal(spec.implementation_target_ref)},
    {sql_literal(spec.spec_fragment_ref)},
    {self._json_sql(spec.domain_ref or {})}::jsonb,
    {self._uuid_or_null(spec.spec_fragment_id)},
    {self._uuid_or_null(spec.implementation_target_id)}
  WHERE NOT EXISTS (SELECT 1 FROM existing)
  RETURNING work_item_id
)
SELECT 1;
"""
        self._execute(sql)
        record = self.find_work_item_by_project_and_authority_anchor(
            spec.project_slug,
            issue_number=spec.issue_number,
            spec_fragment_ref=spec.spec_fragment_ref,
        )
        if record is None:
            raise RuntimeError('Work item upsert did not return a persisted record.')
        return record

    def find_work_item_by_project_and_authority_anchor(
        self,
        project_slug: str,
        *,
        issue_number: int | None = None,
        spec_fragment_ref: str | None = None,
    ) -> WorkItemRecord | None:
        if issue_number is None and spec_fragment_ref is None:
            raise ValueError('find_work_item_by_project_and_authority_anchor requires issue_number or spec_fragment_ref.')
        predicates: list[str] = []
        if issue_number is not None:
            predicates.append(f"wi.issue_number = {int(issue_number)}")
        if spec_fragment_ref is not None:
            predicates.append(f"wi.spec_fragment_ref = {sql_literal(spec_fragment_ref)}")
        sql = f"""
SELECT row_to_json(t)
FROM (
  SELECT
    wi.work_item_id::text,
    wi.project_id::text,
    wi.authority_version_id::text,
    wi.title,
    wi.status::text AS status,
    wi.merge_policy,
    wi.requires_qa,
    wi.issue_number,
    wi.implementation_target_ref,
    wi.spec_fragment_ref,
    wi.domain_ref,
    wi.spec_fragment_id::text,
    wi.implementation_target_id::text,
    wi.created_at::text,
    wi.updated_at::text
  FROM paa.work_items wi
  JOIN paa.projects p ON p.project_id = wi.project_id
  WHERE p.slug = {sql_literal(project_slug)}
    AND ({' OR '.join(predicates)})
  ORDER BY wi.updated_at DESC, wi.created_at DESC, wi.work_item_id DESC
  LIMIT 1
) AS t;
"""
        rows = self._query_json_rows(sql)
        return self._work_item_from_row(rows[0]) if rows else None

    def _get_authority_version(self, project_id: str, version_label: str) -> AuthorityVersionRecord | None:
        sql = f"""
SELECT row_to_json(t)
FROM (
  SELECT
    av.authority_version_id::text,
    av.project_id::text,
    av.version_label,
    av.source_commit,
    av.published_from_ref,
    av.manifest_path,
    av.published_at::text,
    av.status::text AS status,
    av.notes,
    av.created_at::text,
    av.updated_at::text
  FROM paa.authority_versions av
  WHERE av.project_id = {sql_literal(project_id)}::uuid
    AND av.version_label = {sql_literal(version_label)}
) AS t;
"""
        rows = self._query_json_rows(sql)
        return self._authority_version_from_row(rows[0]) if rows else None

    def _get_spec_fragment(
        self,
        project_id: str,
        *,
        external_fragment_id: str | None,
        delta_family: str | None,
    ) -> SpecFragmentRecord | None:
        predicates: list[str] = []
        if external_fragment_id is not None:
            predicates.append(
                f"sf.metadata_json->>'spec_fragment_id_external' = {sql_literal(external_fragment_id)}"
            )
        if delta_family is not None:
            predicates.append(f"sf.delta_family IS NOT DISTINCT FROM {sql_literal(delta_family)}")
        elif external_fragment_id is None:
            predicates.append("sf.delta_family IS NULL")
        if not predicates:
            raise ValueError('Spec fragment lookup requires external_fragment_id or delta_family.')
        sql = f"""
SELECT row_to_json(t)
FROM (
  SELECT
    sf.spec_fragment_id::text,
    sf.project_id::text,
    sf.title,
    sf.canonical_statement,
    sf.fragment_kind::text AS fragment_kind,
    sf.delta_family,
    sf.authorized_delta_family,
    sf.out_of_scope_delta_families_json AS out_of_scope_delta_families,
    sf.expected_touch_surfaces_json AS expected_touch_surfaces,
    sf.status::text AS status,
    sf.metadata_json AS metadata,
    sf.created_at::text,
    sf.updated_at::text
  FROM paa.spec_fragments sf
  WHERE sf.project_id = {sql_literal(project_id)}::uuid
    AND ({' OR '.join(predicates)})
  ORDER BY sf.updated_at DESC, sf.created_at DESC, sf.spec_fragment_id DESC
  LIMIT 1
) AS t;
"""
        rows = self._query_json_rows(sql)
        return self._spec_fragment_from_row(rows[0]) if rows else None

    def _get_implementation_target(
        self,
        spec_fragment_id: str,
        *,
        external_target_id: str | None,
        title: str,
    ) -> ImplementationTargetRecord | None:
        predicates = [f"it.title = {sql_literal(title)}"]
        if external_target_id is not None:
            predicates.insert(
                0,
                f"it.metadata_json->>'implementation_target_id_external' = {sql_literal(external_target_id)}",
            )
        sql = f"""
SELECT row_to_json(t)
FROM (
  SELECT
    it.implementation_target_id::text,
    it.spec_fragment_id::text,
    it.title,
    it.current_gap_json AS current_gap,
    it.desired_state_json AS desired_state,
    it.protected_baseline_json AS protected_baseline,
    it.out_of_scope_json AS out_of_scope,
    it.pre_handoff_scope_checks_json AS pre_handoff_scope_checks,
    it.risk_level::text AS risk_level,
    it.status::text AS status,
    it.metadata_json AS metadata,
    it.created_at::text,
    it.updated_at::text
  FROM paa.implementation_targets it
  WHERE it.spec_fragment_id = {sql_literal(spec_fragment_id)}::uuid
    AND ({' OR '.join(predicates)})
  ORDER BY it.updated_at DESC, it.created_at DESC, it.implementation_target_id DESC
  LIMIT 1
) AS t;
"""
        rows = self._query_json_rows(sql)
        return self._implementation_target_from_row(rows[0]) if rows else None

    def _require_project(self, project_slug: str) -> ProjectRecord:
        record = self.get_project_by_slug(project_slug)
        if record is None:
            raise LookupError(f'Project slug {project_slug!r} does not exist.')
        return record

    def _require_authority_version(self, authority_version_id: str) -> None:
        sql = f"SELECT 1 FROM paa.authority_versions WHERE authority_version_id = {sql_literal(authority_version_id)}::uuid LIMIT 1;"
        if query_scalar(sql, settings=self._settings) is None:
            raise LookupError(f'Authority version {authority_version_id!r} does not exist.')

    def _require_spec_fragment(self, spec_fragment_id: str) -> None:
        sql = f"SELECT 1 FROM paa.spec_fragments WHERE spec_fragment_id = {sql_literal(spec_fragment_id)}::uuid LIMIT 1;"
        if query_scalar(sql, settings=self._settings) is None:
            raise LookupError(f'Spec fragment {spec_fragment_id!r} does not exist.')

    def _require_implementation_target(self, implementation_target_id: str) -> None:
        sql = f"SELECT 1 FROM paa.implementation_targets WHERE implementation_target_id = {sql_literal(implementation_target_id)}::uuid LIMIT 1;"
        if query_scalar(sql, settings=self._settings) is None:
            raise LookupError(f'Implementation target {implementation_target_id!r} does not exist.')

    def _execute(self, sql: str) -> None:
        execute_sql(sql, settings=self._settings)

    def _query_json_rows(self, sql: str) -> list[dict[str, Any]]:
        return query_json_rows(sql, settings=self._settings)

    @staticmethod
    def _project_from_row(row: dict[str, Any]) -> ProjectRecord:
        return ProjectRecord(
            project_id=row['project_id'],
            slug=row['slug'],
            name=row['name'],
            repo_url=row.get('repo_url'),
            execution_surface=row['execution_surface'],
            status=row['status'],
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
        )

    @staticmethod
    def _authority_version_from_row(row: dict[str, Any]) -> AuthorityVersionRecord:
        return AuthorityVersionRecord(
            authority_version_id=row['authority_version_id'],
            project_id=row['project_id'],
            version_label=row['version_label'],
            source_commit=row.get('source_commit'),
            published_from_ref=row.get('published_from_ref'),
            manifest_path=row.get('manifest_path'),
            published_at=row.get('published_at'),
            status=row['status'],
            notes=row.get('notes'),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
        )

    @staticmethod
    def _spec_fragment_from_row(row: dict[str, Any]) -> SpecFragmentRecord:
        return SpecFragmentRecord(
            spec_fragment_id=row['spec_fragment_id'],
            project_id=row['project_id'],
            title=row['title'],
            canonical_statement=row['canonical_statement'],
            fragment_kind=row['fragment_kind'],
            delta_family=row.get('delta_family'),
            authorized_delta_family=row.get('authorized_delta_family'),
            out_of_scope_delta_families=tuple(row.get('out_of_scope_delta_families') or ()),
            expected_touch_surfaces=tuple(row.get('expected_touch_surfaces') or ()),
            status=row['status'],
            metadata=dict(row.get('metadata') or {}),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
        )

    @staticmethod
    def _implementation_target_from_row(row: dict[str, Any]) -> ImplementationTargetRecord:
        return ImplementationTargetRecord(
            implementation_target_id=row['implementation_target_id'],
            spec_fragment_id=row['spec_fragment_id'],
            title=row['title'],
            current_gap=tuple(row.get('current_gap') or ()),
            desired_state=tuple(row.get('desired_state') or ()),
            protected_baseline=tuple(row.get('protected_baseline') or ()),
            out_of_scope=tuple(row.get('out_of_scope') or ()),
            pre_handoff_scope_checks=tuple(row.get('pre_handoff_scope_checks') or ()),
            risk_level=row['risk_level'],
            status=row['status'],
            metadata=dict(row.get('metadata') or {}),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
        )

    @staticmethod
    def _work_item_from_row(row: dict[str, Any]) -> WorkItemRecord:
        return WorkItemRecord(
            work_item_id=row['work_item_id'],
            project_id=row['project_id'],
            authority_version_id=row.get('authority_version_id'),
            title=row['title'],
            status=row['status'],
            merge_policy=row.get('merge_policy'),
            requires_qa=bool(row['requires_qa']),
            issue_number=int(row['issue_number']) if row.get('issue_number') is not None else None,
            implementation_target_ref=row.get('implementation_target_ref'),
            spec_fragment_ref=row.get('spec_fragment_ref'),
            domain_ref=dict(row.get('domain_ref') or {}),
            spec_fragment_id=row.get('spec_fragment_id'),
            implementation_target_id=row.get('implementation_target_id'),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
        )

    @staticmethod
    def _json_sql(value: Any) -> str:
        return sql_literal(json.dumps(value, sort_keys=True))

    @staticmethod
    def _bool_sql(value: bool) -> str:
        return 'true' if value else 'false'

    @staticmethod
    def _int_or_null(value: int | None) -> str:
        if value is None:
            return 'NULL'
        return str(int(value))

    @staticmethod
    def _timestamp_or_null(value: str | None) -> str:
        if value is None:
            return 'NULL'
        return f"{sql_literal(value)}::timestamptz"

    @staticmethod
    def _uuid_or_null(value: str | None) -> str:
        if value is None:
            return 'NULL'
        return f"{sql_literal(value)}::uuid"


__all__ = ['PostgresSourceAuthorityRepository']

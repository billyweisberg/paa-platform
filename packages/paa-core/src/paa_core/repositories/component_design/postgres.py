"""Postgres-backed Component Design repository implementation."""

from __future__ import annotations

import json
from typing import Any

from paa_core.db import DBSettings, run_psql, sql_literal

from .models import (
    BriefRealizationTargetUpsertSpec,
    ComponentElementUpsertSpec,
    CoderBriefRealizationTargetRecord,
    ComponentElementRealizationRecord,
    ComponentElementRealizationTypeRecord,
    ComponentElementRealizationUpsertSpec,
    ComponentElementRecord,
    ComponentElementTypeRecord,
    ComponentRecord,
    ElementTypeRealizationLinkSpec,
    RealizationTypeUpsertSpec,
)


class PostgresComponentDesignRepository:
    """Postgres-backed repository for stable Component Design records."""

    def __init__(self, *, settings: DBSettings | None = None) -> None:
        self._settings = settings

    def get_component_by_name(self, project_id: str, name: str) -> ComponentRecord | None:
        sql = f"""
SELECT row_to_json(t)
FROM (
  SELECT
    c.component_id::text,
    c.project_id::text,
    c.name,
    c.role,
    c.system_layer::text AS system_layer,
    c.tier::text AS tier,
    c.description,
    c.status::text AS status,
    c.metadata_json AS metadata
  FROM paa.components c
  WHERE c.project_id = {sql_literal(project_id)}::uuid
    AND c.name = {sql_literal(name)}
) AS t;
"""
        rows = self._query_json_rows(sql)
        if not rows:
            return None
        return self._component_from_row(rows[0])

    def list_component_element_types(self) -> list[ComponentElementTypeRecord]:
        sql = """
SELECT row_to_json(t)
FROM (
  SELECT
    cet.component_element_type_id::text,
    cet.element_key,
    cet.label,
    cet.category,
    cet.description,
    cet.is_brief_targetable,
    cet.is_multi_instance,
    cet.sort_order,
    cet.metadata_json AS metadata
  FROM paa.component_element_types cet
  ORDER BY cet.sort_order, cet.element_key
) AS t;
"""
        return [self._element_type_from_row(row) for row in self._query_json_rows(sql)]

    def list_component_elements_for_component(self, component_id: str) -> list[ComponentElementRecord]:
        sql = f"""
SELECT row_to_json(t)
FROM (
  SELECT
    ce.component_element_id::text,
    ce.project_id::text,
    ce.component_id::text,
    ce.component_element_type_id::text,
    ce.element_key,
    ce.title,
    ce.status::text AS status,
    ce.definition_json AS definition,
    ce.provenance_json AS provenance,
    ce.metadata_json AS metadata
  FROM paa.component_elements ce
  JOIN paa.component_element_types cet
    ON cet.component_element_type_id = ce.component_element_type_id
  WHERE ce.component_id = {sql_literal(component_id)}::uuid
  ORDER BY cet.sort_order, ce.element_key
) AS t;
"""
        return [self._element_from_row(row) for row in self._query_json_rows(sql)]

    def upsert_component_element(self, spec: ComponentElementUpsertSpec) -> None:
        sql = f"""
INSERT INTO paa.component_elements (
  project_id,
  component_id,
  component_element_type_id,
  element_key,
  title,
  status,
  definition_json,
  provenance_json,
  metadata_json,
  created_by_role_id,
  created_by_agent_id
)
SELECT
  {sql_literal(spec.project_id)}::uuid,
  {sql_literal(spec.component_id)}::uuid,
  cet.component_element_type_id,
  {sql_literal(spec.element_key)},
  {sql_literal(spec.title)},
  {sql_literal(spec.status)}::paa.component_element_status,
  {self._json_sql(spec.definition)}::jsonb,
  {self._json_sql(spec.provenance)}::jsonb,
  {self._json_sql(spec.metadata)}::jsonb,
  {self._uuid_or_null(spec.created_by_role_id)},
  {self._uuid_or_null(spec.created_by_agent_id)}
FROM paa.component_element_types cet
WHERE cet.element_key = {sql_literal(spec.element_type_key)}
ON CONFLICT (component_id, component_element_type_id, element_key) DO UPDATE SET
  title = EXCLUDED.title,
  status = EXCLUDED.status,
  definition_json = EXCLUDED.definition_json,
  provenance_json = EXCLUDED.provenance_json,
  metadata_json = EXCLUDED.metadata_json,
  updated_at = now();
"""
        run_psql(sql, settings=self._settings)

    def list_realization_types_for_element_type(
        self, element_type_key: str
    ) -> list[ComponentElementRealizationTypeRecord]:
        sql = f"""
SELECT row_to_json(t)
FROM (
  SELECT
    cert.component_element_realization_type_id::text,
    cert.realization_key,
    cert.label,
    cert.category,
    cert.description,
    cert.is_brief_targetable,
    cert.is_multi_instance,
    cert.sort_order,
    cert.metadata_json AS metadata,
    cetrt.is_default AS is_default_for_element_type,
    cetrt.sort_order AS element_type_sort_order
  FROM paa.component_element_type_realization_types cetrt
  JOIN paa.component_element_types cet
    ON cet.component_element_type_id = cetrt.component_element_type_id
  JOIN paa.component_element_realization_types cert
    ON cert.component_element_realization_type_id = cetrt.component_element_realization_type_id
  WHERE cet.element_key = {sql_literal(element_type_key)}
  ORDER BY cetrt.sort_order, cert.sort_order, cert.realization_key
) AS t;
"""
        return [self._realization_type_from_row(row) for row in self._query_json_rows(sql)]

    def list_realizations_for_component_element(
        self, component_element_id: str
    ) -> list[ComponentElementRealizationRecord]:
        sql = f"""
SELECT row_to_json(t)
FROM (
  SELECT
    cer.component_element_realization_id::text,
    cer.project_id::text,
    cer.component_id::text,
    cer.component_element_id::text,
    cer.component_element_realization_type_id::text,
    cer.realization_key,
    cer.title,
    cer.status::text AS status,
    cer.sequence_order,
    cer.definition_json AS definition,
    cer.artifact_ref_json AS artifact_ref,
    cer.provenance_json AS provenance,
    cer.metadata_json AS metadata
  FROM paa.component_element_realizations cer
  JOIN paa.component_element_realization_types cert
    ON cert.component_element_realization_type_id = cer.component_element_realization_type_id
  WHERE cer.component_element_id = {sql_literal(component_element_id)}::uuid
  ORDER BY cer.sequence_order, cert.sort_order, cer.realization_key
) AS t;
"""
        return [self._realization_from_row(row) for row in self._query_json_rows(sql)]

    def list_brief_realization_targets(
        self, coder_run_brief_id: str
    ) -> list[CoderBriefRealizationTargetRecord]:
        sql = f"""
SELECT row_to_json(t)
FROM (
  SELECT
    cbrt.coder_brief_realization_target_id::text,
    cbrt.project_id::text,
    cbrt.work_item_id::text,
    cbrt.coder_run_brief_id::text,
    cbrt.component_id::text,
    cbrt.component_element_id::text,
    cbrt.component_element_realization_id::text,
    cbrt.depends_on_target_id::text,
    cbrt.target_intent::text AS target_intent,
    cbrt.sequence_order,
    cbrt.is_required,
    cbrt.target_notes,
    cbrt.target_contract_json AS target_contract,
    cbrt.metadata_json AS metadata
  FROM paa.coder_brief_realization_targets cbrt
  WHERE cbrt.coder_run_brief_id = {sql_literal(coder_run_brief_id)}::uuid
  ORDER BY cbrt.sequence_order, cbrt.coder_brief_realization_target_id
) AS t;
"""
        return [self._brief_target_from_row(row) for row in self._query_json_rows(sql)]



    def upsert_realization_type(self, spec: RealizationTypeUpsertSpec) -> None:
        sql = f"""
INSERT INTO paa.component_element_realization_types (
  realization_key,
  label,
  category,
  description,
  is_brief_targetable,
  is_multi_instance,
  sort_order,
  metadata_json
)
VALUES (
  {sql_literal(spec.realization_key)},
  {sql_literal(spec.label)},
  {sql_literal(spec.category)},
  {sql_literal(spec.description)},
  {self._bool_sql(spec.is_brief_targetable)},
  {self._bool_sql(spec.is_multi_instance)},
  {int(spec.sort_order)},
  {self._json_sql(spec.metadata)}::jsonb
)
ON CONFLICT (realization_key) DO UPDATE SET
  label = EXCLUDED.label,
  category = EXCLUDED.category,
  description = EXCLUDED.description,
  is_brief_targetable = EXCLUDED.is_brief_targetable,
  is_multi_instance = EXCLUDED.is_multi_instance,
  sort_order = EXCLUDED.sort_order,
  metadata_json = EXCLUDED.metadata_json,
  updated_at = now();
"""
        run_psql(sql, settings=self._settings)

    def upsert_element_type_realization_link(self, spec: ElementTypeRealizationLinkSpec) -> None:
        sql = f"""
INSERT INTO paa.component_element_type_realization_types (
  component_element_type_id,
  component_element_realization_type_id,
  is_default,
  sort_order,
  metadata_json
)
SELECT
  cet.component_element_type_id,
  cert.component_element_realization_type_id,
  {self._bool_sql(spec.is_default)},
  {int(spec.sort_order)},
  {self._json_sql(spec.metadata)}::jsonb
FROM paa.component_element_types cet
JOIN paa.component_element_realization_types cert
  ON cert.realization_key = {sql_literal(spec.realization_key)}
WHERE cet.element_key = {sql_literal(spec.element_type_key)}
ON CONFLICT (component_element_type_id, component_element_realization_type_id) DO UPDATE SET
  is_default = EXCLUDED.is_default,
  sort_order = EXCLUDED.sort_order,
  metadata_json = EXCLUDED.metadata_json;
"""
        run_psql(sql, settings=self._settings)

    def upsert_component_element_realization(
        self, spec: ComponentElementRealizationUpsertSpec
    ) -> None:
        sql = f"""
INSERT INTO paa.component_element_realizations (
  project_id,
  component_id,
  component_element_id,
  component_element_realization_type_id,
  realization_key,
  title,
  status,
  sequence_order,
  definition_json,
  artifact_ref_json,
  provenance_json,
  metadata_json,
  created_by_role_id,
  created_by_agent_id
)
SELECT
  {sql_literal(spec.project_id)}::uuid,
  {sql_literal(spec.component_id)}::uuid,
  {sql_literal(spec.component_element_id)}::uuid,
  cert.component_element_realization_type_id,
  {sql_literal(spec.realization_key)},
  {sql_literal(spec.title)},
  {sql_literal(spec.status)}::paa.component_realization_status,
  {int(spec.sequence_order)},
  {self._json_sql(spec.definition)}::jsonb,
  {self._json_sql(spec.artifact_ref)}::jsonb,
  {self._json_sql(spec.provenance)}::jsonb,
  {self._json_sql(spec.metadata)}::jsonb,
  {self._uuid_or_null(spec.created_by_role_id)},
  {self._uuid_or_null(spec.created_by_agent_id)}
FROM paa.component_element_realization_types cert
WHERE cert.realization_key = {sql_literal(spec.realization_type_key)}
ON CONFLICT (component_element_id, component_element_realization_type_id, realization_key) DO UPDATE SET
  title = EXCLUDED.title,
  status = EXCLUDED.status,
  sequence_order = EXCLUDED.sequence_order,
  definition_json = EXCLUDED.definition_json,
  artifact_ref_json = EXCLUDED.artifact_ref_json,
  provenance_json = EXCLUDED.provenance_json,
  metadata_json = EXCLUDED.metadata_json,
  updated_at = now();
"""
        run_psql(sql, settings=self._settings)

    def upsert_brief_realization_target(self, spec: BriefRealizationTargetUpsertSpec) -> None:
        sql = f"""
INSERT INTO paa.coder_brief_realization_targets (
  project_id,
  work_item_id,
  coder_run_brief_id,
  component_id,
  component_element_id,
  component_element_realization_id,
  depends_on_target_id,
  target_intent,
  sequence_order,
  is_required,
  target_notes,
  target_contract_json,
  metadata_json
)
VALUES (
  {sql_literal(spec.project_id)}::uuid,
  {self._uuid_or_null(spec.work_item_id)},
  {sql_literal(spec.coder_run_brief_id)}::uuid,
  {sql_literal(spec.component_id)}::uuid,
  {sql_literal(spec.component_element_id)}::uuid,
  {sql_literal(spec.component_element_realization_id)}::uuid,
  {self._uuid_or_null(spec.depends_on_target_id)},
  {sql_literal(spec.target_intent)}::paa.brief_target_intent,
  {int(spec.sequence_order)},
  {self._bool_sql(spec.is_required)},
  {sql_literal(spec.target_notes)},
  {self._json_sql(spec.target_contract)}::jsonb,
  {self._json_sql(spec.metadata)}::jsonb
)
ON CONFLICT (coder_run_brief_id, component_element_realization_id, target_intent) DO UPDATE SET
  work_item_id = EXCLUDED.work_item_id,
  component_id = EXCLUDED.component_id,
  component_element_id = EXCLUDED.component_element_id,
  depends_on_target_id = EXCLUDED.depends_on_target_id,
  sequence_order = EXCLUDED.sequence_order,
  is_required = EXCLUDED.is_required,
  target_notes = EXCLUDED.target_notes,
  target_contract_json = EXCLUDED.target_contract_json,
  metadata_json = EXCLUDED.metadata_json;
"""
        run_psql(sql, settings=self._settings)

    def _query_json_rows(self, sql: str) -> list[dict[str, Any]]:
        out = run_psql(sql, settings=self._settings)
        rows: list[dict[str, Any]] = []
        for line in out.splitlines():
            text = line.strip()
            if not text:
                continue
            rows.append(json.loads(text))
        return rows

    @staticmethod
    def _component_from_row(row: dict[str, Any]) -> ComponentRecord:
        return ComponentRecord(
            component_id=row['component_id'],
            project_id=row['project_id'],
            name=row['name'],
            role=row['role'],
            system_layer=row['system_layer'],
            tier=row.get('tier'),
            description=row.get('description'),
            status=row['status'],
            metadata=row.get('metadata') or {},
        )

    @staticmethod
    def _element_type_from_row(row: dict[str, Any]) -> ComponentElementTypeRecord:
        return ComponentElementTypeRecord(
            component_element_type_id=row['component_element_type_id'],
            element_key=row['element_key'],
            label=row['label'],
            category=row['category'],
            description=row.get('description'),
            is_brief_targetable=bool(row['is_brief_targetable']),
            is_multi_instance=bool(row['is_multi_instance']),
            sort_order=int(row['sort_order']),
            metadata=row.get('metadata') or {},
        )

    @staticmethod
    def _element_from_row(row: dict[str, Any]) -> ComponentElementRecord:
        return ComponentElementRecord(
            component_element_id=row['component_element_id'],
            project_id=row['project_id'],
            component_id=row['component_id'],
            component_element_type_id=row['component_element_type_id'],
            element_key=row['element_key'],
            title=row.get('title'),
            status=row['status'],
            definition=row.get('definition') or {},
            provenance=row.get('provenance') or {},
            metadata=row.get('metadata') or {},
        )

    @staticmethod
    def _realization_type_from_row(row: dict[str, Any]) -> ComponentElementRealizationTypeRecord:
        return ComponentElementRealizationTypeRecord(
            component_element_realization_type_id=row['component_element_realization_type_id'],
            realization_key=row['realization_key'],
            label=row['label'],
            category=row['category'],
            description=row.get('description'),
            is_brief_targetable=bool(row['is_brief_targetable']),
            is_multi_instance=bool(row['is_multi_instance']),
            sort_order=int(row['sort_order']),
            metadata=row.get('metadata') or {},
            is_default_for_element_type=bool(row.get('is_default_for_element_type', False)),
            element_type_sort_order=int(row.get('element_type_sort_order', 0)),
        )

    @staticmethod
    def _realization_from_row(row: dict[str, Any]) -> ComponentElementRealizationRecord:
        return ComponentElementRealizationRecord(
            component_element_realization_id=row['component_element_realization_id'],
            project_id=row['project_id'],
            component_id=row['component_id'],
            component_element_id=row['component_element_id'],
            component_element_realization_type_id=row['component_element_realization_type_id'],
            realization_key=row['realization_key'],
            title=row.get('title'),
            status=row['status'],
            sequence_order=int(row['sequence_order']),
            definition=row.get('definition') or {},
            artifact_ref=row.get('artifact_ref') or {},
            provenance=row.get('provenance') or {},
            metadata=row.get('metadata') or {},
        )

    @staticmethod
    def _brief_target_from_row(row: dict[str, Any]) -> CoderBriefRealizationTargetRecord:
        return CoderBriefRealizationTargetRecord(
            coder_brief_realization_target_id=row['coder_brief_realization_target_id'],
            project_id=row['project_id'],
            work_item_id=row.get('work_item_id'),
            coder_run_brief_id=row['coder_run_brief_id'],
            component_id=row['component_id'],
            component_element_id=row['component_element_id'],
            component_element_realization_id=row['component_element_realization_id'],
            depends_on_target_id=row.get('depends_on_target_id'),
            target_intent=row['target_intent'],
            sequence_order=int(row['sequence_order']),
            is_required=bool(row['is_required']),
            target_notes=row.get('target_notes'),
            target_contract=row.get('target_contract') or {},
            metadata=row.get('metadata') or {},
        )


    @staticmethod
    def _json_sql(value: dict[str, Any] | None) -> str:
        return sql_literal(json.dumps(value or {}, sort_keys=True))

    @staticmethod
    def _bool_sql(value: bool) -> str:
        return 'true' if value else 'false'

    @staticmethod
    def _uuid_or_null(value: str | None) -> str:
        if value is None:
            return 'NULL'
        return f"{sql_literal(value)}::uuid"

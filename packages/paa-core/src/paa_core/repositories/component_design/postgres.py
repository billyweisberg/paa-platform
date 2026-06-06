"""Postgres-backed Component Design repository implementation."""

from __future__ import annotations

import json
from typing import Any

from paa_core.db import DBSettings, run_psql, sql_literal

from .models import (
    BriefRealizationTargetUpsertSpec,
    ComponentUpsertSpec,
    ComponentElementUpsertSpec,
    CoderBriefRealizationTargetRecord,
    ComponentElementRealizationRecord,
    ComponentElementRealizationTypeRecord,
    ComponentElementRealizationUpsertSpec,
    ComponentElementRecord,
    ComponentElementTypeRecord,
    ComponentRecord,
    DesignPackageRecord,
    DesignPackageSignoffRecord,
    DesignPackageSignoffUpsertSpec,
    DesignPackageUpsertSpec,
    ElementTypeRealizationLinkRecord,
    ElementTypeRealizationLinkSpec,
    RealizationTypeUpsertSpec,
)


class PostgresComponentDesignRepository:
    """Postgres-backed repository for stable Component Design records."""

    def __init__(self, *, settings: DBSettings | None = None) -> None:
        self._settings = settings

    def get_component_by_id(self, component_id: str) -> ComponentRecord | None:
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
  WHERE c.component_id = {sql_literal(component_id)}::uuid
) AS t;
"""
        rows = self._query_json_rows(sql)
        if not rows:
            return None
        return self._component_from_row(rows[0])

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

    def upsert_component(self, spec: ComponentUpsertSpec) -> ComponentRecord:
        sql = f"""
INSERT INTO paa.components (
  project_id,
  name,
  role,
  system_layer,
  tier,
  description,
  status,
  metadata_json
)
VALUES (
  {sql_literal(spec.project_id)}::uuid,
  {sql_literal(spec.name)},
  {sql_literal(spec.role)},
  {sql_literal(spec.system_layer)}::paa.system_layer,
  {sql_literal(spec.tier)}::paa.component_tier,
  {sql_literal(spec.description)},
  {sql_literal(spec.status)}::paa.component_status,
  {self._json_sql(spec.metadata)}::jsonb
)
ON CONFLICT (project_id, name) DO UPDATE SET
  role = EXCLUDED.role,
  system_layer = EXCLUDED.system_layer,
  tier = EXCLUDED.tier,
  description = EXCLUDED.description,
  status = EXCLUDED.status,
  metadata_json = paa.components.metadata_json || EXCLUDED.metadata_json,
  updated_at = now()
RETURNING component_id::text;
"""
        out = run_psql(sql, settings=self._settings).strip()
        if not out:
            raise RuntimeError(f'Component upsert did not return a persisted record for {spec.name!r}.')
        record = self.get_component_by_id(out)
        if record is None:
            raise RuntimeError(f'Component upsert did not return a readable record for {spec.name!r}.')
        return record

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

    def get_component_element_type_by_key(self, element_type_key: str) -> ComponentElementTypeRecord | None:
        sql = f"""
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
  WHERE cet.element_key = {sql_literal(element_type_key)}
) AS t;
"""
        rows = self._query_json_rows(sql)
        if not rows:
            return None
        return self._element_type_from_row(rows[0])

    def list_realization_types(self) -> list[ComponentElementRealizationTypeRecord]:
        sql = """
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
    false AS is_default_for_element_type,
    0 AS element_type_sort_order
  FROM paa.component_element_realization_types cert
  ORDER BY cert.sort_order, cert.realization_key
) AS t;
"""
        return [self._realization_type_from_row(row) for row in self._query_json_rows(sql)]

    def get_realization_type_by_key(
        self, realization_key: str
    ) -> ComponentElementRealizationTypeRecord | None:
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
    false AS is_default_for_element_type,
    0 AS element_type_sort_order
  FROM paa.component_element_realization_types cert
  WHERE cert.realization_key = {sql_literal(realization_key)}
) AS t;
"""
        rows = self._query_json_rows(sql)
        if not rows:
            return None
        return self._realization_type_from_row(rows[0])

    def get_component_element_by_id(self, component_element_id: str) -> ComponentElementRecord | None:
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
  WHERE ce.component_element_id = {sql_literal(component_element_id)}::uuid
) AS t;
"""
        rows = self._query_json_rows(sql)
        if not rows:
            return None
        return self._element_from_row(rows[0])

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

    def list_element_type_realization_links(
        self, element_type_key: str
    ) -> list[ElementTypeRealizationLinkRecord]:
        sql = f"""
SELECT row_to_json(t)
FROM (
  SELECT
    cetrt.component_element_type_realization_type_id::text,
    cetrt.component_element_type_id::text,
    cetrt.component_element_realization_type_id::text,
    cet.element_key,
    cert.realization_key,
    cert.label AS realization_label,
    cert.category AS realization_category,
    cetrt.is_default,
    cetrt.sort_order,
    cetrt.metadata_json AS metadata
  FROM paa.component_element_type_realization_types cetrt
  JOIN paa.component_element_types cet
    ON cet.component_element_type_id = cetrt.component_element_type_id
  JOIN paa.component_element_realization_types cert
    ON cert.component_element_realization_type_id = cetrt.component_element_realization_type_id
  WHERE cet.element_key = {sql_literal(element_type_key)}
  ORDER BY cetrt.sort_order, cert.sort_order, cert.realization_key
) AS t;
"""
        return [self._element_type_realization_link_from_row(row) for row in self._query_json_rows(sql)]

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

    def get_design_package_by_id(self, design_package_id: str) -> DesignPackageRecord | None:
        sql = f"""
SELECT row_to_json(t)
FROM (
  SELECT
    dp.design_package_id::text,
    dp.project_id::text,
    dp.work_item_id::text,
    dp.spec_fragment_id::text,
    dp.implementation_target_id::text,
    dp.authority_version_id::text,
    dp.primary_component_id::text,
    dp.package_id_external,
    dp.schema_version,
    dp.status::text AS status,
    dp.package_json,
    dp.provenance_json AS provenance,
    dp.metadata_json AS metadata,
    dp.created_by_role_id::text,
    dp.created_by_agent_id::text,
    dp.created_at::text,
    dp.updated_at::text
  FROM paa.design_packages dp
  WHERE dp.design_package_id = {sql_literal(design_package_id)}::uuid
) AS t;
"""
        rows = self._query_json_rows(sql)
        return self._design_package_from_row(rows[0]) if rows else None

    def get_design_package_by_project_and_external_id(
        self, project_slug: str, package_id_external: str
    ) -> DesignPackageRecord | None:
        sql = f"""
SELECT row_to_json(t)
FROM (
  SELECT
    dp.design_package_id::text,
    dp.project_id::text,
    dp.work_item_id::text,
    dp.spec_fragment_id::text,
    dp.implementation_target_id::text,
    dp.authority_version_id::text,
    dp.primary_component_id::text,
    dp.package_id_external,
    dp.schema_version,
    dp.status::text AS status,
    dp.package_json,
    dp.provenance_json AS provenance,
    dp.metadata_json AS metadata,
    dp.created_by_role_id::text,
    dp.created_by_agent_id::text,
    dp.created_at::text,
    dp.updated_at::text
  FROM paa.design_packages dp
  JOIN paa.projects p ON p.project_id = dp.project_id
  WHERE p.slug = {sql_literal(project_slug)}
    AND dp.package_id_external = {sql_literal(package_id_external)}
) AS t;
"""
        rows = self._query_json_rows(sql)
        return self._design_package_from_row(rows[0]) if rows else None

    def get_active_design_package_for_work_item(self, work_item_id: str) -> DesignPackageRecord | None:
        sql = f"""
SELECT row_to_json(t)
FROM (
  SELECT
    dp.design_package_id::text,
    dp.project_id::text,
    dp.work_item_id::text,
    dp.spec_fragment_id::text,
    dp.implementation_target_id::text,
    dp.authority_version_id::text,
    dp.primary_component_id::text,
    dp.package_id_external,
    dp.schema_version,
    dp.status::text AS status,
    dp.package_json,
    dp.provenance_json AS provenance,
    dp.metadata_json AS metadata,
    dp.created_by_role_id::text,
    dp.created_by_agent_id::text,
    dp.created_at::text,
    dp.updated_at::text
  FROM paa.design_packages dp
  WHERE dp.work_item_id = {sql_literal(work_item_id)}::uuid
    AND dp.status <> 'superseded'::paa.design_package_status
  ORDER BY dp.updated_at DESC, dp.created_at DESC, dp.design_package_id DESC
  LIMIT 1
) AS t;
"""
        rows = self._query_json_rows(sql)
        return self._design_package_from_row(rows[0]) if rows else None

    def list_design_package_signoffs(self, design_package_id: str) -> list[DesignPackageSignoffRecord]:
        sql = f"""
SELECT row_to_json(t)
FROM (
  SELECT
    dps.design_package_signoff_id::text,
    dps.design_package_id::text,
    dps.role_id::text,
    r.name AS role_name,
    r.sort_order AS role_sort_order,
    dps.signer_name,
    dps.signoff_status,
    dps.notes,
    dps.signed_at::text,
    dps.metadata_json AS metadata
  FROM paa.design_package_signoffs dps
  JOIN paa.roles r ON r.role_id = dps.role_id
  WHERE dps.design_package_id = {sql_literal(design_package_id)}::uuid
  ORDER BY r.sort_order, r.name
) AS t;
"""
        return [self._design_package_signoff_from_row(row) for row in self._query_json_rows(sql)]

    def upsert_design_package(self, spec: DesignPackageUpsertSpec) -> DesignPackageRecord:
        sql = f"""
INSERT INTO paa.design_packages (
  project_id,
  work_item_id,
  spec_fragment_id,
  implementation_target_id,
  authority_version_id,
  primary_component_id,
  package_id_external,
  schema_version,
  status,
  package_json,
  provenance_json,
  metadata_json,
  created_by_role_id,
  created_by_agent_id
)
VALUES (
  {sql_literal(spec.project_id)}::uuid,
  {self._uuid_or_null(spec.work_item_id)},
  {self._uuid_or_null(spec.spec_fragment_id)},
  {self._uuid_or_null(spec.implementation_target_id)},
  {self._uuid_or_null(spec.authority_version_id)},
  {self._uuid_or_null(spec.primary_component_id)},
  {sql_literal(spec.package_id_external)},
  {sql_literal(spec.schema_version)},
  {sql_literal(spec.status)}::paa.design_package_status,
  {self._json_sql(spec.package_json)}::jsonb,
  {self._json_sql(spec.provenance)}::jsonb,
  {self._json_sql(spec.metadata)}::jsonb,
  {self._uuid_or_null(spec.created_by_role_id)},
  {self._uuid_or_null(spec.created_by_agent_id)}
)
ON CONFLICT (project_id, package_id_external) DO UPDATE SET
  work_item_id = EXCLUDED.work_item_id,
  spec_fragment_id = EXCLUDED.spec_fragment_id,
  implementation_target_id = EXCLUDED.implementation_target_id,
  authority_version_id = EXCLUDED.authority_version_id,
  primary_component_id = EXCLUDED.primary_component_id,
  schema_version = EXCLUDED.schema_version,
  status = EXCLUDED.status,
  package_json = EXCLUDED.package_json,
  provenance_json = EXCLUDED.provenance_json,
  metadata_json = EXCLUDED.metadata_json,
  created_by_role_id = COALESCE(EXCLUDED.created_by_role_id, paa.design_packages.created_by_role_id),
  created_by_agent_id = COALESCE(EXCLUDED.created_by_agent_id, paa.design_packages.created_by_agent_id),
  updated_at = now()
RETURNING design_package_id::text;
"""
        out = run_psql(sql, settings=self._settings).strip()
        if not out:
            raise RuntimeError(
                f'Design package upsert did not return a persisted record for {spec.package_id_external!r}.'
            )
        record = self.get_design_package_by_id(out)
        if record is None:
            raise RuntimeError(
                f'Design package upsert did not return a readable record for {spec.package_id_external!r}.'
            )
        return record

    def upsert_design_package_signoff(
        self, spec: DesignPackageSignoffUpsertSpec
    ) -> DesignPackageSignoffRecord:
        sql = f"""
INSERT INTO paa.design_package_signoffs (
  design_package_id,
  role_id,
  signer_name,
  signoff_status,
  notes,
  signed_at,
  metadata_json
)
VALUES (
  {sql_literal(spec.design_package_id)}::uuid,
  {sql_literal(spec.role_id)}::uuid,
  {sql_literal(spec.signer_name)},
  {sql_literal(spec.signoff_status)},
  {sql_literal(spec.notes)},
  {self._timestamp_or_null(spec.signed_at)},
  {self._json_sql(spec.metadata)}::jsonb
)
ON CONFLICT (design_package_id, role_id) DO UPDATE SET
  signer_name = EXCLUDED.signer_name,
  signoff_status = EXCLUDED.signoff_status,
  notes = EXCLUDED.notes,
  signed_at = EXCLUDED.signed_at,
  metadata_json = EXCLUDED.metadata_json
RETURNING design_package_signoff_id::text;
"""
        out = run_psql(sql, settings=self._settings).strip()
        if not out:
            raise RuntimeError(
                f'Design package signoff upsert did not return a persisted record for role {spec.role_id!r}.'
            )
        rows = self._query_json_rows(
            f"""
SELECT row_to_json(t)
FROM (
  SELECT
    dps.design_package_signoff_id::text,
    dps.design_package_id::text,
    dps.role_id::text,
    r.name AS role_name,
    r.sort_order AS role_sort_order,
    dps.signer_name,
    dps.signoff_status,
    dps.notes,
    dps.signed_at::text,
    dps.metadata_json AS metadata
  FROM paa.design_package_signoffs dps
  JOIN paa.roles r ON r.role_id = dps.role_id
  WHERE dps.design_package_signoff_id = {sql_literal(out)}::uuid
) AS t;
"""
        )
        if not rows:
            raise RuntimeError(
                f'Design package signoff upsert did not return a readable record for role {spec.role_id!r}.'
            )
        return self._design_package_signoff_from_row(rows[0])


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
        element_type = self.get_component_element_type_by_key(spec.element_type_key)
        if element_type is None:
            raise LookupError(f"Unknown component element type: {spec.element_type_key}")
        realization_type = self.get_realization_type_by_key(spec.realization_key)
        if realization_type is None:
            raise LookupError(f"Unknown realization type: {spec.realization_key}")
        sql = f"""
INSERT INTO paa.component_element_type_realization_types (
  component_element_type_id,
  component_element_realization_type_id,
  is_default,
  sort_order,
  metadata_json
)
VALUES (
  {sql_literal(element_type.component_element_type_id)}::uuid,
  {sql_literal(realization_type.component_element_realization_type_id)}::uuid,
  {self._bool_sql(spec.is_default)},
  {int(spec.sort_order)},
  {self._json_sql(spec.metadata)}::jsonb
)
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
    def _element_type_realization_link_from_row(row: dict[str, Any]) -> ElementTypeRealizationLinkRecord:
        return ElementTypeRealizationLinkRecord(
            component_element_type_realization_type_id=row['component_element_type_realization_type_id'],
            component_element_type_id=row['component_element_type_id'],
            component_element_realization_type_id=row['component_element_realization_type_id'],
            element_type_key=row['element_key'],
            realization_key=row['realization_key'],
            realization_label=row['realization_label'],
            realization_category=row['realization_category'],
            is_default=bool(row['is_default']),
            sort_order=int(row['sort_order']),
            metadata=row.get('metadata') or {},
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
    def _design_package_from_row(row: dict[str, Any]) -> DesignPackageRecord:
        return DesignPackageRecord(
            design_package_id=row['design_package_id'],
            project_id=row['project_id'],
            work_item_id=row.get('work_item_id'),
            spec_fragment_id=row.get('spec_fragment_id'),
            implementation_target_id=row.get('implementation_target_id'),
            authority_version_id=row.get('authority_version_id'),
            primary_component_id=row.get('primary_component_id'),
            package_id_external=row.get('package_id_external'),
            schema_version=row['schema_version'],
            status=row['status'],
            package_json=row.get('package_json') or {},
            provenance=row.get('provenance') or {},
            metadata=row.get('metadata') or {},
            created_by_role_id=row.get('created_by_role_id'),
            created_by_agent_id=row.get('created_by_agent_id'),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
        )

    @staticmethod
    def _design_package_signoff_from_row(row: dict[str, Any]) -> DesignPackageSignoffRecord:
        return DesignPackageSignoffRecord(
            design_package_signoff_id=row['design_package_signoff_id'],
            design_package_id=row['design_package_id'],
            role_id=row['role_id'],
            role_name=row['role_name'],
            role_sort_order=int(row['role_sort_order']),
            signer_name=row.get('signer_name'),
            signoff_status=row['signoff_status'],
            notes=row.get('notes'),
            signed_at=row.get('signed_at'),
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

    @staticmethod
    def _timestamp_or_null(value: str | None) -> str:
        if value is None:
            return 'NULL'
        return f"{sql_literal(value)}::timestamptz"

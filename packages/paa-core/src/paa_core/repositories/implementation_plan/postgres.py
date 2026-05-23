"""Postgres-backed ImplementationPlan repository implementation."""

from __future__ import annotations

import json
from typing import Any

from paa_core.db import DBSettings, run_psql, sql_literal

from .models import (
    ImplementationPlanActivityStateUpdateSpec,
    ImplementationPlanAuthorityEventAppendSpec,
    ImplementationPlanAuthorityEventRecord,
    ImplementationPlanActivityDependencyRecord,
    ImplementationPlanActivityDependencyUpsertSpec,
    ImplementationPlanActivityRecord,
    ImplementationPlanActivityUpsertSpec,
    ImplementationPlanProgressUpdateSpec,
    ImplementationPlanRecord,
    ImplementationPlanUpsertSpec,
    ImplementationPlanVerificationSurfaceRecord,
)


class PostgresImplementationPlanRepository:
    """Postgres-backed repository for ImplementationPlan project-design truth."""

    def __init__(self, *, settings: DBSettings | None = None) -> None:
        self._settings = settings

    def get_implementation_plan(self, implementation_plan_id: str) -> ImplementationPlanRecord | None:
        sql = f"""
SELECT row_to_json(t)
FROM (
  SELECT
    ip.implementation_plan_id::text,
    ip.project_id::text,
    ip.work_item_id::text,
    ip.design_package_id::text,
    ip.spec_fragment_id::text,
    ip.implementation_target_id::text,
    ip.authority_version_id::text,
    ip.primary_component_id::text,
    ip.plan_id_external,
    ip.schema_version,
    ip.consumer_context_key,
    ip.plan_title,
    ip.plan_kind,
    ip.status::text AS status,
    ip.authority_state::text AS authority_state,
    ip.authority_state_updated_at::text,
    ip.plan_json AS plan,
    ip.build_sequence_json AS build_sequence,
    ip.touch_surfaces_json AS touch_surfaces,
    ip.protected_constraints_json AS protected_constraints,
    ip.verification_plan_json AS verification_plan,
    ip.provenance_json AS provenance,
    ip.metadata_json AS metadata,
    ip.created_by_role_id::text,
    ip.created_by_agent_id::text,
    ip.approved_at::text,
    ip.activated_at::text,
    ip.completed_at::text,
    ip.created_at::text,
    ip.updated_at::text
  FROM paa.implementation_plans ip
  WHERE ip.implementation_plan_id = {sql_literal(implementation_plan_id)}::uuid
) AS t;
"""
        rows = self._query_json_rows(sql)
        if not rows:
            return None
        return self._plan_from_row(rows[0])

    def get_implementation_plan_by_external(
        self, project_id: str, plan_id_external: str
    ) -> ImplementationPlanRecord | None:
        sql = f"""
SELECT row_to_json(t)
FROM (
  SELECT
    ip.implementation_plan_id::text,
    ip.project_id::text,
    ip.work_item_id::text,
    ip.design_package_id::text,
    ip.spec_fragment_id::text,
    ip.implementation_target_id::text,
    ip.authority_version_id::text,
    ip.primary_component_id::text,
    ip.plan_id_external,
    ip.schema_version,
    ip.consumer_context_key,
    ip.plan_title,
    ip.plan_kind,
    ip.status::text AS status,
    ip.authority_state::text AS authority_state,
    ip.authority_state_updated_at::text,
    ip.plan_json AS plan,
    ip.build_sequence_json AS build_sequence,
    ip.touch_surfaces_json AS touch_surfaces,
    ip.protected_constraints_json AS protected_constraints,
    ip.verification_plan_json AS verification_plan,
    ip.provenance_json AS provenance,
    ip.metadata_json AS metadata,
    ip.created_by_role_id::text,
    ip.created_by_agent_id::text,
    ip.approved_at::text,
    ip.activated_at::text,
    ip.completed_at::text,
    ip.created_at::text,
    ip.updated_at::text
  FROM paa.implementation_plans ip
  WHERE ip.project_id = {sql_literal(project_id)}::uuid
    AND ip.plan_id_external = {sql_literal(plan_id_external)}
) AS t;
"""
        rows = self._query_json_rows(sql)
        if not rows:
            return None
        return self._plan_from_row(rows[0])

    def get_implementation_plan_for_design_package(
        self, design_package_id: str, consumer_context_key: str
    ) -> ImplementationPlanRecord | None:
        sql = f"""
SELECT row_to_json(t)
FROM (
  SELECT
    ip.implementation_plan_id::text,
    ip.project_id::text,
    ip.work_item_id::text,
    ip.design_package_id::text,
    ip.spec_fragment_id::text,
    ip.implementation_target_id::text,
    ip.authority_version_id::text,
    ip.primary_component_id::text,
    ip.plan_id_external,
    ip.schema_version,
    ip.consumer_context_key,
    ip.plan_title,
    ip.plan_kind,
    ip.status::text AS status,
    ip.authority_state::text AS authority_state,
    ip.authority_state_updated_at::text,
    ip.plan_json AS plan,
    ip.build_sequence_json AS build_sequence,
    ip.touch_surfaces_json AS touch_surfaces,
    ip.protected_constraints_json AS protected_constraints,
    ip.verification_plan_json AS verification_plan,
    ip.provenance_json AS provenance,
    ip.metadata_json AS metadata,
    ip.created_by_role_id::text,
    ip.created_by_agent_id::text,
    ip.approved_at::text,
    ip.activated_at::text,
    ip.completed_at::text,
    ip.created_at::text,
    ip.updated_at::text
  FROM paa.implementation_plans ip
  WHERE ip.design_package_id = {sql_literal(design_package_id)}::uuid
    AND ip.consumer_context_key = {sql_literal(consumer_context_key)}
) AS t;
"""
        rows = self._query_json_rows(sql)
        if not rows:
            return None
        return self._plan_from_row(rows[0])

    def list_implementation_plan_activities(
        self, implementation_plan_id: str
    ) -> list[ImplementationPlanActivityRecord]:
        sql = f"""
SELECT row_to_json(t)
FROM (
  SELECT
    ipa.implementation_plan_activity_id::text,
    ipa.implementation_plan_id::text,
    ipa.component_element_id::text,
    ipa.component_element_realization_id::text,
    ipa.assigned_role_id::text,
    ipa.activity_key,
    ipa.activity_title,
    ipa.activity_kind::text AS activity_kind,
    ipa.activity_state::text AS activity_state,
    ipa.sequence_order,
    ipa.target_path,
    ipa.target_module,
    ipa.planned_artifact_type_key,
    ipa.blocking_reason,
    ipa.metadata_json AS metadata,
    ipa.started_at::text,
    ipa.completed_at::text,
    ipa.created_at::text,
    ipa.updated_at::text
  FROM paa.implementation_plan_activities ipa
  WHERE ipa.implementation_plan_id = {sql_literal(implementation_plan_id)}::uuid
  ORDER BY ipa.sequence_order, ipa.activity_key
) AS t;
"""
        return [self._activity_from_row(row) for row in self._query_json_rows(sql)]

    def get_implementation_plan_activity_by_key(
        self,
        implementation_plan_id: str,
        activity_key: str,
    ) -> ImplementationPlanActivityRecord | None:
        sql = f"""
SELECT row_to_json(t)
FROM (
  SELECT
    ipa.implementation_plan_activity_id::text,
    ipa.implementation_plan_id::text,
    ipa.component_element_id::text,
    ipa.component_element_realization_id::text,
    ipa.assigned_role_id::text,
    ipa.activity_key,
    ipa.activity_title,
    ipa.activity_kind::text AS activity_kind,
    ipa.activity_state::text AS activity_state,
    ipa.sequence_order,
    ipa.target_path,
    ipa.target_module,
    ipa.planned_artifact_type_key,
    ipa.blocking_reason,
    ipa.metadata_json AS metadata,
    ipa.started_at::text,
    ipa.completed_at::text,
    ipa.created_at::text,
    ipa.updated_at::text
  FROM paa.implementation_plan_activities ipa
  WHERE ipa.implementation_plan_id = {sql_literal(implementation_plan_id)}::uuid
    AND ipa.activity_key = {sql_literal(activity_key)}
) AS t;
"""
        rows = self._query_json_rows(sql)
        if not rows:
            return None
        return self._activity_from_row(rows[0])

    def list_implementation_plan_activities_by_state(
        self,
        implementation_plan_id: str,
        activity_state: str,
    ) -> list[ImplementationPlanActivityRecord]:
        sql = f"""
SELECT row_to_json(t)
FROM (
  SELECT
    ipa.implementation_plan_activity_id::text,
    ipa.implementation_plan_id::text,
    ipa.component_element_id::text,
    ipa.component_element_realization_id::text,
    ipa.assigned_role_id::text,
    ipa.activity_key,
    ipa.activity_title,
    ipa.activity_kind::text AS activity_kind,
    ipa.activity_state::text AS activity_state,
    ipa.sequence_order,
    ipa.target_path,
    ipa.target_module,
    ipa.planned_artifact_type_key,
    ipa.blocking_reason,
    ipa.metadata_json AS metadata,
    ipa.started_at::text,
    ipa.completed_at::text,
    ipa.created_at::text,
    ipa.updated_at::text
  FROM paa.implementation_plan_activities ipa
  WHERE ipa.implementation_plan_id = {sql_literal(implementation_plan_id)}::uuid
    AND ipa.activity_state = {sql_literal(activity_state)}::paa.implementation_plan_activity_state
  ORDER BY ipa.sequence_order, ipa.activity_key
) AS t;
"""
        return [self._activity_from_row(row) for row in self._query_json_rows(sql)]

    def list_implementation_plan_activity_dependencies(
        self, implementation_plan_id: str
    ) -> list[ImplementationPlanActivityDependencyRecord]:
        sql = f"""
SELECT row_to_json(t)
FROM (
  SELECT
    ipad.implementation_plan_activity_dependency_id::text,
    ipad.implementation_plan_id::text,
    ipad.predecessor_activity_id::text,
    pred.activity_key AS predecessor_activity_key,
    ipad.successor_activity_id::text,
    succ.activity_key AS successor_activity_key,
    ipad.sequencing_requirement::text AS sequencing_requirement,
    ipad.dependency_strength::text AS dependency_strength,
    ipad.notes,
    ipad.metadata_json AS metadata,
    ipad.created_at::text
  FROM paa.implementation_plan_activity_dependencies ipad
  JOIN paa.implementation_plan_activities pred
    ON pred.implementation_plan_activity_id = ipad.predecessor_activity_id
  JOIN paa.implementation_plan_activities succ
    ON succ.implementation_plan_activity_id = ipad.successor_activity_id
  WHERE ipad.implementation_plan_id = {sql_literal(implementation_plan_id)}::uuid
  ORDER BY pred.sequence_order, succ.sequence_order, pred.activity_key, succ.activity_key
) AS t;
"""
        return [self._dependency_from_row(row) for row in self._query_json_rows(sql)]

    def list_implementation_plan_verification_surfaces(
        self, implementation_plan_id: str
    ) -> list[ImplementationPlanVerificationSurfaceRecord]:
        sql = f"""
SELECT row_to_json(t)
FROM (
  SELECT
    ipvs.implementation_plan_verification_surface_id::text,
    ipvs.implementation_plan_id::text,
    ipvs.implementation_plan_activity_id::text,
    ipvs.verification_obligation_id::text,
    ipvs.surface_kind,
    ipvs.surface_ref,
    ipvs.required,
    ipvs.sequence_order,
    ipvs.status::text AS status,
    ipvs.metadata_json AS metadata,
    ipvs.created_at::text,
    ipvs.updated_at::text
  FROM paa.implementation_plan_verification_surfaces ipvs
  WHERE ipvs.implementation_plan_id = {sql_literal(implementation_plan_id)}::uuid
  ORDER BY ipvs.sequence_order, ipvs.surface_kind, ipvs.surface_ref
) AS t;
"""
        return [self._verification_surface_from_row(row) for row in self._query_json_rows(sql)]

    def list_implementation_plan_verification_surfaces_for_activity(
        self,
        implementation_plan_id: str,
        activity_key: str,
    ) -> list[ImplementationPlanVerificationSurfaceRecord]:
        sql = f"""
SELECT row_to_json(t)
FROM (
  SELECT
    ipvs.implementation_plan_verification_surface_id::text,
    ipvs.implementation_plan_id::text,
    ipvs.implementation_plan_activity_id::text,
    ipvs.verification_obligation_id::text,
    ipvs.surface_kind,
    ipvs.surface_ref,
    ipvs.required,
    ipvs.sequence_order,
    ipvs.status::text AS status,
    ipvs.metadata_json AS metadata,
    ipvs.created_at::text,
    ipvs.updated_at::text
  FROM paa.implementation_plan_verification_surfaces ipvs
  JOIN paa.implementation_plan_activities ipa
    ON ipa.implementation_plan_activity_id = ipvs.implementation_plan_activity_id
  WHERE ipvs.implementation_plan_id = {sql_literal(implementation_plan_id)}::uuid
    AND ipa.activity_key = {sql_literal(activity_key)}
  ORDER BY ipvs.sequence_order, ipvs.surface_kind, ipvs.surface_ref
) AS t;
"""
        return [self._verification_surface_from_row(row) for row in self._query_json_rows(sql)]

    def list_implementation_plan_authority_events(
        self,
        implementation_plan_id: str,
    ) -> list[ImplementationPlanAuthorityEventRecord]:
        sql = f"""
SELECT row_to_json(t)
FROM (
  SELECT
    ipae.implementation_plan_authority_event_id::text,
    ipae.project_id::text,
    ipae.work_item_id::text,
    ipae.implementation_plan_id::text,
    ipae.from_state::text AS from_state,
    ipae.to_state::text AS to_state,
    ipae.transition_kind::text AS transition_kind,
    ipae.actor_role_id::text,
    ipae.actor_name,
    ipae.notes,
    ipae.evidence_json AS evidence,
    ipae.created_at::text
  FROM paa.implementation_plan_authority_events ipae
  WHERE ipae.implementation_plan_id = {sql_literal(implementation_plan_id)}::uuid
  ORDER BY ipae.created_at DESC, ipae.implementation_plan_authority_event_id
) AS t;
"""
        return [self._authority_event_from_row(row) for row in self._query_json_rows(sql)]

    def upsert_implementation_plan(self, spec: ImplementationPlanUpsertSpec) -> None:
        sql = f"""
INSERT INTO paa.implementation_plans (
  project_id,
  work_item_id,
  design_package_id,
  spec_fragment_id,
  implementation_target_id,
  authority_version_id,
  primary_component_id,
  plan_id_external,
  schema_version,
  consumer_context_key,
  plan_title,
  plan_kind,
  status,
  authority_state,
  authority_state_updated_at,
  plan_json,
  build_sequence_json,
  touch_surfaces_json,
  protected_constraints_json,
  verification_plan_json,
  provenance_json,
  metadata_json,
  created_by_role_id,
  created_by_agent_id,
  approved_at,
  activated_at,
  completed_at
)
VALUES (
  {sql_literal(spec.project_id)}::uuid,
  {self._uuid_or_null(spec.work_item_id)},
  {sql_literal(spec.design_package_id)}::uuid,
  {self._uuid_or_null(spec.spec_fragment_id)},
  {self._uuid_or_null(spec.implementation_target_id)},
  {self._uuid_or_null(spec.authority_version_id)},
  {self._uuid_or_null(spec.primary_component_id)},
  {sql_literal(spec.plan_id_external)},
  {sql_literal(spec.schema_version)},
  {sql_literal(spec.consumer_context_key)},
  {sql_literal(spec.plan_title)},
  {sql_literal(spec.plan_kind)},
  {sql_literal(spec.status)}::paa.implementation_plan_status,
  {sql_literal(spec.authority_state)}::paa.implementation_plan_authority_state,
  now(),
  {self._json_sql(spec.plan)}::jsonb,
  {self._json_sql(spec.build_sequence)}::jsonb,
  {self._json_sql(spec.touch_surfaces)}::jsonb,
  {self._json_sql(spec.protected_constraints)}::jsonb,
  {self._json_sql(spec.verification_plan)}::jsonb,
  {self._json_sql(spec.provenance)}::jsonb,
  {self._json_sql(spec.metadata)}::jsonb,
  {self._uuid_or_null(spec.created_by_role_id)},
  {self._uuid_or_null(spec.created_by_agent_id)},
  {self._timestamp_or_null(spec.approved_at)},
  {self._timestamp_or_null(spec.activated_at)},
  {self._timestamp_or_null(spec.completed_at)}
)
ON CONFLICT (design_package_id, consumer_context_key) DO UPDATE SET
  project_id = EXCLUDED.project_id,
  work_item_id = EXCLUDED.work_item_id,
  spec_fragment_id = EXCLUDED.spec_fragment_id,
  implementation_target_id = EXCLUDED.implementation_target_id,
  authority_version_id = EXCLUDED.authority_version_id,
  primary_component_id = EXCLUDED.primary_component_id,
  plan_id_external = EXCLUDED.plan_id_external,
  schema_version = EXCLUDED.schema_version,
  plan_title = EXCLUDED.plan_title,
  plan_kind = EXCLUDED.plan_kind,
  status = EXCLUDED.status,
  authority_state = EXCLUDED.authority_state,
  authority_state_updated_at = now(),
  plan_json = EXCLUDED.plan_json,
  build_sequence_json = EXCLUDED.build_sequence_json,
  touch_surfaces_json = EXCLUDED.touch_surfaces_json,
  protected_constraints_json = EXCLUDED.protected_constraints_json,
  verification_plan_json = EXCLUDED.verification_plan_json,
  provenance_json = EXCLUDED.provenance_json,
  metadata_json = EXCLUDED.metadata_json,
  approved_at = EXCLUDED.approved_at,
  activated_at = EXCLUDED.activated_at,
  completed_at = EXCLUDED.completed_at,
  updated_at = now();
"""
        run_psql(sql, settings=self._settings)

    def update_implementation_plan_progress(self, spec: ImplementationPlanProgressUpdateSpec) -> None:
        component_completion_json = sql_literal(json.dumps(spec.component_completion, sort_keys=True))
        metadata_update = (
            f"jsonb_set(COALESCE(metadata_json, '{{}}'::jsonb), '{{component_completion}}', {component_completion_json}::jsonb, true)"
        )
        status_clause = (
            f"status = {sql_literal(spec.status)}::paa.implementation_plan_status,"
            if spec.status is not None
            else ''
        )
        authority_state_clause = (
            (
                f"authority_state = {sql_literal(spec.authority_state)}::paa.implementation_plan_authority_state,\n"
                "  authority_state_updated_at = now(),"
            )
            if spec.authority_state is not None
            else ''
        )
        completed_clause = (
            f"completed_at = {self._timestamp_or_null(spec.completed_at)},"
            if spec.completed_at is not None
            else ''
        )
        sql = f"""
UPDATE paa.implementation_plans
SET
  metadata_json = {metadata_update},
  {status_clause}
  {authority_state_clause}
  {completed_clause}
  updated_at = now()
WHERE implementation_plan_id = {sql_literal(spec.implementation_plan_id)}::uuid;
"""
        run_psql(sql, settings=self._settings)

    def upsert_implementation_plan_activity(self, spec: ImplementationPlanActivityUpsertSpec) -> None:
        sql = f"""
INSERT INTO paa.implementation_plan_activities (
  implementation_plan_id,
  component_element_id,
  component_element_realization_id,
  assigned_role_id,
  activity_key,
  activity_title,
  activity_kind,
  activity_state,
  sequence_order,
  target_path,
  target_module,
  planned_artifact_type_key,
  blocking_reason,
  metadata_json,
  started_at,
  completed_at
)
VALUES (
  {sql_literal(spec.implementation_plan_id)}::uuid,
  {self._uuid_or_null(spec.component_element_id)},
  {self._uuid_or_null(spec.component_element_realization_id)},
  {self._uuid_or_null(spec.assigned_role_id)},
  {sql_literal(spec.activity_key)},
  {sql_literal(spec.activity_title)},
  {sql_literal(spec.activity_kind)}::paa.implementation_plan_activity_kind,
  {sql_literal(spec.activity_state)}::paa.implementation_plan_activity_state,
  {int(spec.sequence_order)},
  {sql_literal(spec.target_path)},
  {sql_literal(spec.target_module)},
  {sql_literal(spec.planned_artifact_type_key)},
  {sql_literal(spec.blocking_reason)},
  {self._json_sql(spec.metadata)}::jsonb,
  {self._timestamp_or_null(spec.started_at)},
  {self._timestamp_or_null(spec.completed_at)}
)
ON CONFLICT (implementation_plan_id, activity_key) DO UPDATE SET
  component_element_id = EXCLUDED.component_element_id,
  component_element_realization_id = EXCLUDED.component_element_realization_id,
  assigned_role_id = EXCLUDED.assigned_role_id,
  activity_title = EXCLUDED.activity_title,
  activity_kind = EXCLUDED.activity_kind,
  activity_state = EXCLUDED.activity_state,
  sequence_order = EXCLUDED.sequence_order,
  target_path = EXCLUDED.target_path,
  target_module = EXCLUDED.target_module,
  planned_artifact_type_key = EXCLUDED.planned_artifact_type_key,
  blocking_reason = EXCLUDED.blocking_reason,
  metadata_json = EXCLUDED.metadata_json,
  started_at = EXCLUDED.started_at,
  completed_at = EXCLUDED.completed_at,
  updated_at = now();
"""
        run_psql(sql, settings=self._settings)

    def set_implementation_plan_activity_state(self, spec: ImplementationPlanActivityStateUpdateSpec) -> None:
        metadata_expr = (
            f"COALESCE(metadata_json, '{{}}'::jsonb) || {self._json_sql(spec.metadata)}::jsonb"
            if spec.metadata is not None
            else 'metadata_json'
        )
        sql = f"""
UPDATE paa.implementation_plan_activities
SET
  activity_state = {sql_literal(spec.activity_state)}::paa.implementation_plan_activity_state,
  blocking_reason = {sql_literal(spec.blocking_reason)},
  started_at = COALESCE({self._timestamp_or_null(spec.started_at)}, started_at),
  completed_at = {self._timestamp_or_null(spec.completed_at)},
  metadata_json = {metadata_expr},
  updated_at = now()
WHERE implementation_plan_id = {sql_literal(spec.implementation_plan_id)}::uuid
  AND activity_key = {sql_literal(spec.activity_key)};
"""
        run_psql(sql, settings=self._settings)

    def upsert_implementation_plan_activity_dependency(
        self, spec: ImplementationPlanActivityDependencyUpsertSpec
    ) -> None:
        sql = f"""
INSERT INTO paa.implementation_plan_activity_dependencies (
  implementation_plan_id,
  predecessor_activity_id,
  successor_activity_id,
  sequencing_requirement,
  dependency_strength,
  notes,
  metadata_json
)
SELECT
  {sql_literal(spec.implementation_plan_id)}::uuid,
  pred.implementation_plan_activity_id,
  succ.implementation_plan_activity_id,
  {sql_literal(spec.sequencing_requirement)}::paa.sequencing_requirement,
  {sql_literal(spec.dependency_strength)}::paa.dependency_strength,
  {sql_literal(spec.notes)},
  {self._json_sql(spec.metadata)}::jsonb
FROM paa.implementation_plan_activities pred
JOIN paa.implementation_plan_activities succ
  ON succ.implementation_plan_id = pred.implementation_plan_id
WHERE pred.implementation_plan_id = {sql_literal(spec.implementation_plan_id)}::uuid
  AND pred.activity_key = {sql_literal(spec.predecessor_activity_key)}
  AND succ.activity_key = {sql_literal(spec.successor_activity_key)}
ON CONFLICT (implementation_plan_id, predecessor_activity_id, successor_activity_id) DO UPDATE SET
  sequencing_requirement = EXCLUDED.sequencing_requirement,
  dependency_strength = EXCLUDED.dependency_strength,
  notes = EXCLUDED.notes,
  metadata_json = EXCLUDED.metadata_json;
"""
        run_psql(sql, settings=self._settings)

    def append_implementation_plan_authority_event(
        self,
        spec: ImplementationPlanAuthorityEventAppendSpec,
    ) -> None:
        sql = f"""
INSERT INTO paa.implementation_plan_authority_events (
  project_id,
  work_item_id,
  implementation_plan_id,
  from_state,
  to_state,
  transition_kind,
  actor_role_id,
  actor_name,
  notes,
  evidence_json
)
VALUES (
  {sql_literal(spec.project_id)}::uuid,
  {self._uuid_or_null(spec.work_item_id)},
  {sql_literal(spec.implementation_plan_id)}::uuid,
  {sql_literal(spec.from_state)}::paa.implementation_plan_authority_state,
  {sql_literal(spec.to_state)}::paa.implementation_plan_authority_state,
  {sql_literal(spec.transition_kind)}::paa.implementation_plan_authority_transition_kind,
  {self._uuid_or_null(spec.actor_role_id)},
  {sql_literal(spec.actor_name)},
  {sql_literal(spec.notes)},
  {self._json_sql(spec.evidence)}::jsonb
);
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
    def _plan_from_row(row: dict[str, Any]) -> ImplementationPlanRecord:
        return ImplementationPlanRecord(
            implementation_plan_id=row['implementation_plan_id'],
            project_id=row['project_id'],
            work_item_id=row.get('work_item_id'),
            design_package_id=row['design_package_id'],
            spec_fragment_id=row.get('spec_fragment_id'),
            implementation_target_id=row.get('implementation_target_id'),
            authority_version_id=row.get('authority_version_id'),
            primary_component_id=row.get('primary_component_id'),
            plan_id_external=row['plan_id_external'],
            schema_version=row['schema_version'],
            consumer_context_key=row['consumer_context_key'],
            plan_title=row['plan_title'],
            plan_kind=row['plan_kind'],
            status=row['status'],
            authority_state=row['authority_state'],
            authority_state_updated_at=row.get('authority_state_updated_at'),
            plan=row.get('plan') or {},
            build_sequence=row.get('build_sequence') or {},
            touch_surfaces=row.get('touch_surfaces') or {},
            protected_constraints=row.get('protected_constraints') or {},
            verification_plan=row.get('verification_plan') or {},
            provenance=row.get('provenance') or {},
            metadata=row.get('metadata') or {},
            created_by_role_id=row.get('created_by_role_id'),
            created_by_agent_id=row.get('created_by_agent_id'),
            approved_at=row.get('approved_at'),
            activated_at=row.get('activated_at'),
            completed_at=row.get('completed_at'),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
        )

    @staticmethod
    def _activity_from_row(row: dict[str, Any]) -> ImplementationPlanActivityRecord:
        return ImplementationPlanActivityRecord(
            implementation_plan_activity_id=row['implementation_plan_activity_id'],
            implementation_plan_id=row['implementation_plan_id'],
            component_element_id=row.get('component_element_id'),
            component_element_realization_id=row.get('component_element_realization_id'),
            assigned_role_id=row.get('assigned_role_id'),
            activity_key=row['activity_key'],
            activity_title=row['activity_title'],
            activity_kind=row['activity_kind'],
            activity_state=row['activity_state'],
            sequence_order=int(row['sequence_order']),
            target_path=row.get('target_path'),
            target_module=row.get('target_module'),
            planned_artifact_type_key=row.get('planned_artifact_type_key'),
            blocking_reason=row.get('blocking_reason'),
            metadata=row.get('metadata') or {},
            started_at=row.get('started_at'),
            completed_at=row.get('completed_at'),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
        )

    @staticmethod
    def _dependency_from_row(row: dict[str, Any]) -> ImplementationPlanActivityDependencyRecord:
        return ImplementationPlanActivityDependencyRecord(
            implementation_plan_activity_dependency_id=row['implementation_plan_activity_dependency_id'],
            implementation_plan_id=row['implementation_plan_id'],
            predecessor_activity_id=row['predecessor_activity_id'],
            predecessor_activity_key=row['predecessor_activity_key'],
            successor_activity_id=row['successor_activity_id'],
            successor_activity_key=row['successor_activity_key'],
            sequencing_requirement=row['sequencing_requirement'],
            dependency_strength=row['dependency_strength'],
            notes=row.get('notes'),
            metadata=row.get('metadata') or {},
            created_at=row.get('created_at'),
        )

    @staticmethod
    def _verification_surface_from_row(row: dict[str, Any]) -> ImplementationPlanVerificationSurfaceRecord:
        return ImplementationPlanVerificationSurfaceRecord(
            implementation_plan_verification_surface_id=row['implementation_plan_verification_surface_id'],
            implementation_plan_id=row['implementation_plan_id'],
            implementation_plan_activity_id=row.get('implementation_plan_activity_id'),
            verification_obligation_id=row.get('verification_obligation_id'),
            surface_kind=row['surface_kind'],
            surface_ref=row['surface_ref'],
            required=bool(row['required']),
            sequence_order=int(row['sequence_order']),
            status=row['status'],
            metadata=row.get('metadata') or {},
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
        )

    @staticmethod
    def _authority_event_from_row(row: dict[str, Any]) -> ImplementationPlanAuthorityEventRecord:
        return ImplementationPlanAuthorityEventRecord(
            implementation_plan_authority_event_id=row['implementation_plan_authority_event_id'],
            project_id=row['project_id'],
            work_item_id=row.get('work_item_id'),
            implementation_plan_id=row['implementation_plan_id'],
            from_state=row.get('from_state'),
            to_state=row['to_state'],
            transition_kind=row['transition_kind'],
            actor_role_id=row.get('actor_role_id'),
            actor_name=row.get('actor_name'),
            notes=row.get('notes'),
            evidence=row.get('evidence') or {},
            created_at=row.get('created_at'),
        )

    @staticmethod
    def _json_sql(value: dict[str, Any] | None) -> str:
        return sql_literal(json.dumps(value or {}, sort_keys=True))

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


__all__ = ['PostgresImplementationPlanRepository']

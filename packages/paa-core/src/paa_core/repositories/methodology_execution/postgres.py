"""Postgres-backed MethodologyExecution repository implementation."""

from __future__ import annotations

import json
from typing import Any

from paa_core.db import DBSettings, query_json_rows, run_psql, sql_literal

from .models import (
    MethodologyExecutionBindingEntrySpec,
    MethodologyExecutionBindingRecord,
    MethodologyExecutionBindingReplaceSpec,
    MethodologyExecutionEventAppendSpec,
    MethodologyExecutionEventRecord,
    MethodologyExecutionProjectionInputRecord,
    MethodologyExecutionRecord,
    MethodologyExecutionUpsertSpec,
)


class PostgresMethodologyExecutionRepository:
    """Postgres-backed repository for methodology execution pointer truth."""

    def __init__(self, *, settings: DBSettings | None = None) -> None:
        self._settings = settings

    def get_methodology_execution(self, methodology_execution_id: str) -> MethodologyExecutionRecord | None:
        sql = self._execution_sql(
            where_clause=(
                f"me.methodology_execution_id = {sql_literal(methodology_execution_id)}::uuid"
            )
        )
        rows = self._query_json_rows(sql)
        return self._execution_from_row(rows[0]) if rows else None

    def find_methodology_execution_by_primary_ref(
        self,
        project_id: str,
        work_item_id: str,
        component_id: str | None = None,
    ) -> MethodologyExecutionRecord | None:
        where_parts = [
            f"me.project_id = {sql_literal(project_id)}::uuid",
            f"me.work_item_id = {sql_literal(work_item_id)}::uuid",
        ]
        if component_id is None:
            where_parts.append('me.component_id IS NULL')
        else:
            where_parts.append(f"me.component_id = {sql_literal(component_id)}::uuid")
        sql = self._execution_sql(where_clause=' AND '.join(where_parts))
        rows = self._query_json_rows(sql)
        return self._execution_from_row(rows[0]) if rows else None

    def list_methodology_execution_events(
        self,
        methodology_execution_id: str,
    ) -> list[MethodologyExecutionEventRecord]:
        sql = f"""
SELECT row_to_json(t)
FROM (
  SELECT
    mee.methodology_execution_event_id::text,
    mee.methodology_execution_id::text,
    mee.from_lane::text AS from_lane,
    mee.to_lane::text AS to_lane,
    mee.from_stage::text AS from_stage,
    mee.to_stage::text AS to_stage,
    mee.from_step,
    mee.to_step,
    mee.from_status::text AS from_status,
    mee.to_status::text AS to_status,
    mee.transition_kind::text AS transition_kind,
    mee.actor_role_id::text,
    mee.actor_name,
    mee.notes,
    mee.evidence_json AS evidence,
    mee.created_at::text
  FROM paa.methodology_execution_events mee
  WHERE mee.methodology_execution_id = {sql_literal(methodology_execution_id)}::uuid
  ORDER BY mee.created_at, mee.methodology_execution_event_id
) AS t;
"""
        return [self._event_from_row(row) for row in self._query_json_rows(sql)]

    def list_methodology_execution_bindings(
        self,
        methodology_execution_id: str,
    ) -> list[MethodologyExecutionBindingRecord]:
        sql = f"""
SELECT row_to_json(t)
FROM (
  SELECT
    meb.methodology_execution_binding_id::text,
    meb.methodology_execution_id::text,
    meb.binding_kind,
    meb.bound_record_id::text,
    meb.bound_record_key,
    meb.bound_record_ref,
    meb.is_primary,
    meb.notes,
    meb.metadata_json AS metadata,
    meb.created_at::text,
    meb.updated_at::text
  FROM paa.methodology_execution_bindings meb
  WHERE meb.methodology_execution_id = {sql_literal(methodology_execution_id)}::uuid
  ORDER BY meb.is_primary DESC, meb.binding_kind, meb.created_at
) AS t;
"""
        return [self._binding_from_row(row) for row in self._query_json_rows(sql)]

    def load_methodology_execution_projection_inputs(
        self,
        methodology_execution_id: str,
    ) -> MethodologyExecutionProjectionInputRecord:
        execution = self.get_methodology_execution(methodology_execution_id)
        if execution is None:
            raise LookupError(f'MethodologyExecution not found: {methodology_execution_id}')
        return MethodologyExecutionProjectionInputRecord(
            execution=execution,
            events=tuple(self.list_methodology_execution_events(methodology_execution_id)),
            bindings=tuple(self.list_methodology_execution_bindings(methodology_execution_id)),
            related_records={},
        )

    def upsert_methodology_execution(self, spec: MethodologyExecutionUpsertSpec) -> None:
        sql = f"""
INSERT INTO paa.methodology_executions (
  methodology_execution_id,
  project_id,
  work_item_id,
  lane,
  stage,
  step,
  status,
  current_owner_role,
  next_action_key,
  blocked_reason,
  component_id,
  design_package_id,
  implementation_plan_id,
  coder_run_brief_id,
  packet_id,
  workflow_state_id,
  active_authority_ref,
  active_artifact_ref,
  metadata_json
)
VALUES (
  {sql_literal(spec.methodology_execution_id)}::uuid,
  {sql_literal(spec.project_id)}::uuid,
  {self._uuid_or_null(spec.work_item_id)},
  {sql_literal(spec.lane)}::paa.methodology_lane,
  {sql_literal(spec.stage)}::paa.methodology_stage,
  {sql_literal(spec.step)},
  {sql_literal(spec.status)}::paa.methodology_execution_status,
  {sql_literal(spec.current_owner_role)},
  {sql_literal(spec.next_action_key)},
  {sql_literal(spec.blocked_reason)},
  {self._uuid_or_null(spec.component_id)},
  {self._uuid_or_null(spec.design_package_id)},
  {self._uuid_or_null(spec.implementation_plan_id)},
  {self._uuid_or_null(spec.coder_run_brief_id)},
  {self._uuid_or_null(spec.packet_id)},
  {self._uuid_or_null(spec.workflow_state_id)},
  {sql_literal(spec.active_authority_ref)},
  {sql_literal(spec.active_artifact_ref)},
  {self._json_sql(spec.metadata)}::jsonb
)
ON CONFLICT (methodology_execution_id) DO UPDATE SET
  project_id = EXCLUDED.project_id,
  work_item_id = EXCLUDED.work_item_id,
  lane = EXCLUDED.lane,
  stage = EXCLUDED.stage,
  step = EXCLUDED.step,
  status = EXCLUDED.status,
  current_owner_role = EXCLUDED.current_owner_role,
  next_action_key = EXCLUDED.next_action_key,
  blocked_reason = EXCLUDED.blocked_reason,
  component_id = EXCLUDED.component_id,
  design_package_id = EXCLUDED.design_package_id,
  implementation_plan_id = EXCLUDED.implementation_plan_id,
  coder_run_brief_id = EXCLUDED.coder_run_brief_id,
  packet_id = EXCLUDED.packet_id,
  workflow_state_id = EXCLUDED.workflow_state_id,
  active_authority_ref = EXCLUDED.active_authority_ref,
  active_artifact_ref = EXCLUDED.active_artifact_ref,
  metadata_json = EXCLUDED.metadata_json,
  updated_at = now();
"""
        run_psql(sql, settings=self._settings)

    def append_methodology_execution_event(self, spec: MethodologyExecutionEventAppendSpec) -> None:
        sql = f"""
INSERT INTO paa.methodology_execution_events (
  methodology_execution_id,
  from_lane,
  to_lane,
  from_stage,
  to_stage,
  from_step,
  to_step,
  from_status,
  to_status,
  transition_kind,
  actor_role_id,
  actor_name,
  notes,
  evidence_json
)
VALUES (
  {sql_literal(spec.methodology_execution_id)}::uuid,
  {self._enum_or_null(spec.from_lane, 'paa.methodology_lane')},
  {sql_literal(spec.to_lane)}::paa.methodology_lane,
  {self._enum_or_null(spec.from_stage, 'paa.methodology_stage')},
  {sql_literal(spec.to_stage)}::paa.methodology_stage,
  {sql_literal(spec.from_step)},
  {sql_literal(spec.to_step)},
  {self._enum_or_null(spec.from_status, 'paa.methodology_execution_status')},
  {sql_literal(spec.to_status)}::paa.methodology_execution_status,
  {sql_literal(spec.transition_kind)}::paa.methodology_transition_kind,
  {sql_literal(spec.actor_role_id)},
  {sql_literal(spec.actor_name)},
  {sql_literal(spec.notes)},
  {self._json_sql(spec.evidence)}::jsonb
);
"""
        run_psql(sql, settings=self._settings)

    def replace_methodology_execution_bindings(self, spec: MethodologyExecutionBindingReplaceSpec) -> None:
        statements: list[str] = []
        if spec.replace_scope == 'replace_all':
            statements.append(
                f"DELETE FROM paa.methodology_execution_bindings WHERE methodology_execution_id = {sql_literal(spec.methodology_execution_id)}::uuid;"
            )
        elif spec.replace_scope == 'replace_kind':
            binding_kinds = sorted({binding.binding_kind for binding in spec.bindings})
            if binding_kinds:
                kinds_sql = ', '.join(sql_literal(kind) for kind in binding_kinds)
                statements.append(
                    f"DELETE FROM paa.methodology_execution_bindings WHERE methodology_execution_id = {sql_literal(spec.methodology_execution_id)}::uuid AND binding_kind IN ({kinds_sql});"
                )
        else:
            raise ValueError(f'Unsupported replace_scope: {spec.replace_scope}')

        for binding in spec.bindings:
            statements.append(self._binding_insert_sql(spec.methodology_execution_id, binding))

        for statement in statements:
            run_psql(statement, settings=self._settings)

    def _binding_insert_sql(
        self,
        methodology_execution_id: str,
        binding: MethodologyExecutionBindingEntrySpec,
    ) -> str:
        return f"""
INSERT INTO paa.methodology_execution_bindings (
  methodology_execution_id,
  binding_kind,
  bound_record_id,
  bound_record_key,
  bound_record_ref,
  is_primary,
  notes,
  metadata_json
)
VALUES (
  {sql_literal(methodology_execution_id)}::uuid,
  {sql_literal(binding.binding_kind)},
  {self._uuid_or_null(binding.bound_record_id)},
  {sql_literal(binding.bound_record_key)},
  {sql_literal(binding.bound_record_ref)},
  {self._bool_sql(binding.is_primary)},
  {sql_literal(binding.notes)},
  {self._json_sql(binding.metadata)}::jsonb
);
"""

    def _execution_sql(self, *, where_clause: str) -> str:
        return f"""
SELECT row_to_json(t)
FROM (
  SELECT
    me.methodology_execution_id::text,
    me.project_id::text,
    me.work_item_id::text,
    me.lane::text AS lane,
    me.stage::text AS stage,
    me.step,
    me.status::text AS status,
    me.current_owner_role,
    me.next_action_key,
    me.blocked_reason,
    me.component_id::text,
    me.design_package_id::text,
    me.implementation_plan_id::text,
    me.coder_run_brief_id::text,
    me.packet_id::text,
    me.workflow_state_id::text,
    me.active_authority_ref,
    me.active_artifact_ref,
    me.metadata_json AS metadata,
    me.created_at::text,
    me.updated_at::text
  FROM paa.methodology_executions me
  WHERE {where_clause}
) AS t;
"""

    def _query_json_rows(self, sql: str) -> list[dict[str, Any]]:
        return query_json_rows(sql, settings=self._settings)

    def _execution_from_row(self, row: dict[str, Any]) -> MethodologyExecutionRecord:
        return MethodologyExecutionRecord(
            methodology_execution_id=row['methodology_execution_id'],
            project_id=row['project_id'],
            work_item_id=row['work_item_id'],
            lane=row['lane'],
            stage=row['stage'],
            step=row['step'],
            status=row['status'],
            current_owner_role=row['current_owner_role'],
            next_action_key=row['next_action_key'],
            blocked_reason=row['blocked_reason'],
            component_id=row['component_id'],
            design_package_id=row['design_package_id'],
            implementation_plan_id=row['implementation_plan_id'],
            coder_run_brief_id=row['coder_run_brief_id'],
            packet_id=row['packet_id'],
            workflow_state_id=row['workflow_state_id'],
            active_authority_ref=row['active_authority_ref'],
            active_artifact_ref=row['active_artifact_ref'],
            metadata=row.get('metadata') or {},
            created_at=row['created_at'],
            updated_at=row['updated_at'],
        )

    def _event_from_row(self, row: dict[str, Any]) -> MethodologyExecutionEventRecord:
        return MethodologyExecutionEventRecord(
            methodology_execution_event_id=row['methodology_execution_event_id'],
            methodology_execution_id=row['methodology_execution_id'],
            from_lane=row['from_lane'],
            to_lane=row['to_lane'],
            from_stage=row['from_stage'],
            to_stage=row['to_stage'],
            from_step=row['from_step'],
            to_step=row['to_step'],
            from_status=row['from_status'],
            to_status=row['to_status'],
            transition_kind=row['transition_kind'],
            actor_role_id=row['actor_role_id'],
            actor_name=row['actor_name'],
            notes=row['notes'],
            evidence=row.get('evidence') or {},
            created_at=row['created_at'],
        )

    def _binding_from_row(self, row: dict[str, Any]) -> MethodologyExecutionBindingRecord:
        return MethodologyExecutionBindingRecord(
            methodology_execution_binding_id=row['methodology_execution_binding_id'],
            methodology_execution_id=row['methodology_execution_id'],
            binding_kind=row['binding_kind'],
            bound_record_id=row['bound_record_id'],
            bound_record_key=row['bound_record_key'],
            bound_record_ref=row['bound_record_ref'],
            is_primary=row['is_primary'],
            notes=row['notes'],
            metadata=row.get('metadata') or {},
            created_at=row['created_at'],
            updated_at=row['updated_at'],
        )

    def _uuid_or_null(self, value: str | None) -> str:
        if value is None:
            return 'NULL'
        return f"{sql_literal(value)}::uuid"

    def _enum_or_null(self, value: str | None, enum_type: str) -> str:
        if value is None:
            return 'NULL'
        return f"{sql_literal(value)}::{enum_type}"

    def _bool_sql(self, value: bool) -> str:
        return 'TRUE' if value else 'FALSE'

    def _json_sql(self, value: dict[str, Any] | None) -> str:
        return sql_literal(json.dumps(value or {}, sort_keys=True))


__all__ = ['PostgresMethodologyExecutionRepository']

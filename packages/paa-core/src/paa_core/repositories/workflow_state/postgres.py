"""Postgres-backed workflow-state repository implementation."""

from __future__ import annotations

from typing import Any

from paa_core.db import DBSettings, query_json_rows, run_psql, sql_literal

from .models import (
    QueueClaimRecord,
    WorkflowStateRecord,
    WorkflowStateUpsertSpec,
    WorkflowTransitionAppendSpec,
    WorkflowTransitionRecord,
)


class PostgresWorkflowStateRepository:
    """Postgres-backed repository for workflow truth and transition history."""

    def __init__(self, *, settings: DBSettings | None = None) -> None:
        self._settings = settings

    def get_workflow_state(self, workflow_state_id: str) -> WorkflowStateRecord | None:
        sql = self._workflow_state_sql(
            where_clause=f"ws.workflow_state_id = {sql_literal(workflow_state_id)}::uuid"
        )
        rows = self._query_json_rows(sql)
        return self._workflow_state_from_row(rows[0]) if rows else None

    def get_workflow_state_for_work_item(self, work_item_id: str) -> WorkflowStateRecord | None:
        sql = self._workflow_state_sql(
            where_clause=f"ws.work_item_id = {sql_literal(work_item_id)}::uuid"
        )
        rows = self._query_json_rows(sql)
        return self._workflow_state_from_row(rows[0]) if rows else None

    def list_workflow_transitions_for_work_item(
        self, work_item_id: str
    ) -> list[WorkflowTransitionRecord]:
        sql = f"""
SELECT row_to_json(t)
FROM (
  SELECT
    wt.workflow_transition_id::text,
    wt.workflow_state_id::text,
    wt.project_id::text,
    wt.work_item_id::text,
    wt.transition_type::text AS transition_type,
    wt.transition_status::text AS transition_status,
    wt.from_workflow_stage::text AS from_workflow_stage,
    wt.to_workflow_stage::text AS to_workflow_stage,
    wt.from_owner_role_id::text,
    wt.to_owner_role_id::text,
    wt.reason_code,
    wt.reason_text,
    wt.source_handoff_id::text,
    wt.source_queue_message_id::text,
    wt.source_queue_claim_id::text,
    wt.source_message_id_external,
    wt.source_packet_schema_type,
    wt.source_role_id::text,
    wt.source_transition_input_id::text,
    wt.result_handoff_id::text,
    wt.result_queue_message_id::text,
    wt.result_queue_claim_id::text,
    wt.result_message_id_external,
    wt.result_packet_schema_type,
    wt.result_role_id::text,
    wt.performed_by_role_id::text,
    wt.performed_by_agent_id::text,
    wt.automation_run_id::text,
    wt.error_code,
    wt.error_details,
    wt.transition_requested_at::text,
    wt.transition_applied_at::text,
    wt.metadata_json AS metadata,
    wt.created_at::text
  FROM paa.workflow_transitions wt
  WHERE wt.work_item_id = {sql_literal(work_item_id)}::uuid
  ORDER BY wt.transition_applied_at NULLS LAST, wt.created_at
) AS t;
"""
        return [self._workflow_transition_from_row(row) for row in self._query_json_rows(sql)]

    def get_active_queue_claim_for_message(self, queue_message_id: str) -> QueueClaimRecord | None:
        sql = f"""
SELECT row_to_json(t)
FROM (
  SELECT
    qc.queue_claim_id::text,
    qc.queue_message_id::text,
    qc.handoff_id::text,
    qc.project_id::text,
    qc.work_item_id::text,
    qc.claimed_by_role_id::text,
    qc.claimed_by_agent_id::text,
    qc.claim_attempt_source::text AS claim_attempt_source,
    qc.claim_status::text AS claim_status,
    qc.ack_outcome::text AS ack_outcome,
    qc.release_reason_code,
    qc.release_reason_text,
    qc.claimed_at::text,
    qc.lease_expires_at::text,
    qc.released_at::text,
    qc.acked_at::text,
    qc.metadata_json AS metadata,
    qc.created_at::text
  FROM paa.queue_claims qc
  WHERE qc.queue_message_id = {sql_literal(queue_message_id)}::uuid
    AND qc.claim_status = 'active'::paa.queue_claim_status
  ORDER BY qc.created_at DESC
  LIMIT 1
) AS t;
"""
        rows = self._query_json_rows(sql)
        return self._queue_claim_from_row(rows[0]) if rows else None

    def upsert_workflow_state(self, spec: WorkflowStateUpsertSpec) -> None:
        sql = f"""
INSERT INTO paa.workflow_states (
  project_id,
  work_item_id,
  authority_version_id,
  design_package_id,
  coder_run_brief_id,
  workflow_stage,
  current_owner_role_id,
  lineage_state,
  blocking_reason_code,
  blocking_reason_text,
  terminal_decision,
  state_consistency,
  current_issue_number,
  current_pr_number,
  canonical_branch,
  active_role_branch,
  active_handoff_id,
  active_queue_message_id,
  active_message_id_external,
  active_assignment_role_id,
  active_result_role_id,
  active_queue_claim_id,
  state_entered_at,
  last_transition_at,
  closed_at,
  metadata_json
)
VALUES (
  {sql_literal(spec.project_id)}::uuid,
  {sql_literal(spec.work_item_id)}::uuid,
  {self._uuid_or_null(spec.authority_version_id)},
  {self._uuid_or_null(spec.design_package_id)},
  {self._uuid_or_null(spec.coder_run_brief_id)},
  {sql_literal(spec.workflow_stage)}::paa.workflow_stage,
  {self._uuid_or_null(spec.current_owner_role_id)},
  {sql_literal(spec.lineage_state)}::paa.lineage_state,
  {sql_literal(spec.blocking_reason_code)},
  {sql_literal(spec.blocking_reason_text)},
  {sql_literal(spec.terminal_decision)}::paa.workflow_terminal_decision,
  {sql_literal(spec.state_consistency)}::paa.workflow_state_consistency,
  {self._int_or_null(spec.current_issue_number)},
  {self._int_or_null(spec.current_pr_number)},
  {sql_literal(spec.canonical_branch)},
  {sql_literal(spec.active_role_branch)},
  {self._uuid_or_null(spec.active_handoff_id)},
  {self._uuid_or_null(spec.active_queue_message_id)},
  {sql_literal(spec.active_message_id_external)},
  {self._uuid_or_null(spec.active_assignment_role_id)},
  {self._uuid_or_null(spec.active_result_role_id)},
  {self._uuid_or_null(spec.active_queue_claim_id)},
  {self._timestamp_or_now(spec.state_entered_at)},
  {self._timestamp_or_now(spec.last_transition_at)},
  {self._timestamp_or_null(spec.closed_at)},
  {self._json_sql(spec.metadata)}::jsonb
)
ON CONFLICT (work_item_id) DO UPDATE SET
  authority_version_id = EXCLUDED.authority_version_id,
  design_package_id = EXCLUDED.design_package_id,
  coder_run_brief_id = EXCLUDED.coder_run_brief_id,
  workflow_stage = EXCLUDED.workflow_stage,
  current_owner_role_id = EXCLUDED.current_owner_role_id,
  lineage_state = EXCLUDED.lineage_state,
  blocking_reason_code = EXCLUDED.blocking_reason_code,
  blocking_reason_text = EXCLUDED.blocking_reason_text,
  terminal_decision = EXCLUDED.terminal_decision,
  state_consistency = EXCLUDED.state_consistency,
  current_issue_number = EXCLUDED.current_issue_number,
  current_pr_number = EXCLUDED.current_pr_number,
  canonical_branch = EXCLUDED.canonical_branch,
  active_role_branch = EXCLUDED.active_role_branch,
  active_handoff_id = EXCLUDED.active_handoff_id,
  active_queue_message_id = EXCLUDED.active_queue_message_id,
  active_message_id_external = EXCLUDED.active_message_id_external,
  active_assignment_role_id = EXCLUDED.active_assignment_role_id,
  active_result_role_id = EXCLUDED.active_result_role_id,
  active_queue_claim_id = EXCLUDED.active_queue_claim_id,
  state_entered_at = EXCLUDED.state_entered_at,
  last_transition_at = EXCLUDED.last_transition_at,
  closed_at = EXCLUDED.closed_at,
  metadata_json = EXCLUDED.metadata_json,
  updated_at = now();
"""
        run_psql(sql, settings=self._settings)

    def append_workflow_transition(self, spec: WorkflowTransitionAppendSpec) -> None:
        sql = f"""
INSERT INTO paa.workflow_transitions (
  workflow_state_id,
  project_id,
  work_item_id,
  transition_type,
  transition_status,
  from_workflow_stage,
  to_workflow_stage,
  from_owner_role_id,
  to_owner_role_id,
  reason_code,
  reason_text,
  source_handoff_id,
  source_queue_message_id,
  source_queue_claim_id,
  source_message_id_external,
  source_packet_schema_type,
  source_role_id,
  source_transition_input_id,
  result_handoff_id,
  result_queue_message_id,
  result_queue_claim_id,
  result_message_id_external,
  result_packet_schema_type,
  result_role_id,
  performed_by_role_id,
  performed_by_agent_id,
  automation_run_id,
  error_code,
  error_details,
  transition_requested_at,
  transition_applied_at,
  metadata_json
)
VALUES (
  {sql_literal(spec.workflow_state_id)}::uuid,
  {sql_literal(spec.project_id)}::uuid,
  {sql_literal(spec.work_item_id)}::uuid,
  {sql_literal(spec.transition_type)}::paa.workflow_transition_type,
  {sql_literal(spec.transition_status)}::paa.workflow_transition_status,
  {self._enum_or_null(spec.from_workflow_stage, 'paa.workflow_stage')},
  {self._enum_or_null(spec.to_workflow_stage, 'paa.workflow_stage')},
  {self._uuid_or_null(spec.from_owner_role_id)},
  {self._uuid_or_null(spec.to_owner_role_id)},
  {sql_literal(spec.reason_code)},
  {sql_literal(spec.reason_text)},
  {self._uuid_or_null(spec.source_handoff_id)},
  {self._uuid_or_null(spec.source_queue_message_id)},
  {self._uuid_or_null(spec.source_queue_claim_id)},
  {sql_literal(spec.source_message_id_external)},
  {sql_literal(spec.source_packet_schema_type)},
  {self._uuid_or_null(spec.source_role_id)},
  {self._uuid_or_null(spec.source_transition_input_id)},
  {self._uuid_or_null(spec.result_handoff_id)},
  {self._uuid_or_null(spec.result_queue_message_id)},
  {self._uuid_or_null(spec.result_queue_claim_id)},
  {sql_literal(spec.result_message_id_external)},
  {sql_literal(spec.result_packet_schema_type)},
  {self._uuid_or_null(spec.result_role_id)},
  {self._uuid_or_null(spec.performed_by_role_id)},
  {self._uuid_or_null(spec.performed_by_agent_id)},
  {self._uuid_or_null(spec.automation_run_id)},
  {sql_literal(spec.error_code)},
  {sql_literal(spec.error_details)},
  {self._timestamp_or_now(spec.transition_requested_at)},
  {self._timestamp_or_null(spec.transition_applied_at)},
  {self._json_sql(spec.metadata)}::jsonb
);
"""
        run_psql(sql, settings=self._settings)

    def _workflow_state_sql(self, *, where_clause: str) -> str:
        return f"""
SELECT row_to_json(t)
FROM (
  SELECT
    ws.workflow_state_id::text,
    ws.project_id::text,
    ws.work_item_id::text,
    ws.authority_version_id::text,
    ws.design_package_id::text,
    ws.coder_run_brief_id::text,
    ws.workflow_stage::text AS workflow_stage,
    ws.current_owner_role_id::text,
    ws.lineage_state::text AS lineage_state,
    ws.blocking_reason_code,
    ws.blocking_reason_text,
    ws.terminal_decision::text AS terminal_decision,
    ws.state_consistency::text AS state_consistency,
    ws.current_issue_number,
    ws.current_pr_number,
    ws.canonical_branch,
    ws.active_role_branch,
    ws.active_handoff_id::text,
    ws.active_queue_message_id::text,
    ws.active_message_id_external,
    ws.active_assignment_role_id::text,
    ws.active_result_role_id::text,
    ws.active_queue_claim_id::text,
    ws.state_entered_at::text,
    ws.last_transition_at::text,
    ws.closed_at::text,
    ws.metadata_json AS metadata,
    ws.created_at::text,
    ws.updated_at::text
  FROM paa.workflow_states ws
  WHERE {where_clause}
) AS t;
"""

    def _query_json_rows(self, sql: str) -> list[dict[str, Any]]:
        return query_json_rows(sql, settings=self._settings)

    def _workflow_state_from_row(self, row: dict[str, Any]) -> WorkflowStateRecord:
        return WorkflowStateRecord(
            workflow_state_id=row['workflow_state_id'],
            project_id=row['project_id'],
            work_item_id=row['work_item_id'],
            authority_version_id=row.get('authority_version_id'),
            design_package_id=row.get('design_package_id'),
            coder_run_brief_id=row.get('coder_run_brief_id'),
            workflow_stage=row['workflow_stage'],
            current_owner_role_id=row.get('current_owner_role_id'),
            lineage_state=row['lineage_state'],
            blocking_reason_code=row.get('blocking_reason_code'),
            blocking_reason_text=row.get('blocking_reason_text'),
            terminal_decision=row['terminal_decision'],
            state_consistency=row['state_consistency'],
            current_issue_number=row.get('current_issue_number'),
            current_pr_number=row.get('current_pr_number'),
            canonical_branch=row.get('canonical_branch'),
            active_role_branch=row.get('active_role_branch'),
            active_handoff_id=row.get('active_handoff_id'),
            active_queue_message_id=row.get('active_queue_message_id'),
            active_message_id_external=row.get('active_message_id_external'),
            active_assignment_role_id=row.get('active_assignment_role_id'),
            active_result_role_id=row.get('active_result_role_id'),
            active_queue_claim_id=row.get('active_queue_claim_id'),
            state_entered_at=row.get('state_entered_at'),
            last_transition_at=row.get('last_transition_at'),
            closed_at=row.get('closed_at'),
            metadata=dict(row.get('metadata') or {}),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
        )

    def _workflow_transition_from_row(self, row: dict[str, Any]) -> WorkflowTransitionRecord:
        return WorkflowTransitionRecord(
            workflow_transition_id=row['workflow_transition_id'],
            workflow_state_id=row['workflow_state_id'],
            project_id=row['project_id'],
            work_item_id=row['work_item_id'],
            transition_type=row['transition_type'],
            transition_status=row['transition_status'],
            from_workflow_stage=row.get('from_workflow_stage'),
            to_workflow_stage=row.get('to_workflow_stage'),
            from_owner_role_id=row.get('from_owner_role_id'),
            to_owner_role_id=row.get('to_owner_role_id'),
            reason_code=row.get('reason_code'),
            reason_text=row.get('reason_text'),
            source_handoff_id=row.get('source_handoff_id'),
            source_queue_message_id=row.get('source_queue_message_id'),
            source_queue_claim_id=row.get('source_queue_claim_id'),
            source_message_id_external=row.get('source_message_id_external'),
            source_packet_schema_type=row.get('source_packet_schema_type'),
            source_role_id=row.get('source_role_id'),
            source_transition_input_id=row.get('source_transition_input_id'),
            result_handoff_id=row.get('result_handoff_id'),
            result_queue_message_id=row.get('result_queue_message_id'),
            result_queue_claim_id=row.get('result_queue_claim_id'),
            result_message_id_external=row.get('result_message_id_external'),
            result_packet_schema_type=row.get('result_packet_schema_type'),
            result_role_id=row.get('result_role_id'),
            performed_by_role_id=row.get('performed_by_role_id'),
            performed_by_agent_id=row.get('performed_by_agent_id'),
            automation_run_id=row.get('automation_run_id'),
            error_code=row.get('error_code'),
            error_details=row.get('error_details'),
            transition_requested_at=row.get('transition_requested_at'),
            transition_applied_at=row.get('transition_applied_at'),
            metadata=dict(row.get('metadata') or {}),
            created_at=row.get('created_at'),
        )

    def _queue_claim_from_row(self, row: dict[str, Any]) -> QueueClaimRecord:
        return QueueClaimRecord(
            queue_claim_id=row['queue_claim_id'],
            queue_message_id=row['queue_message_id'],
            handoff_id=row.get('handoff_id'),
            project_id=row['project_id'],
            work_item_id=row['work_item_id'],
            claimed_by_role_id=row.get('claimed_by_role_id'),
            claimed_by_agent_id=row.get('claimed_by_agent_id'),
            claim_attempt_source=row['claim_attempt_source'],
            claim_status=row['claim_status'],
            ack_outcome=row['ack_outcome'],
            release_reason_code=row.get('release_reason_code'),
            release_reason_text=row.get('release_reason_text'),
            claimed_at=row.get('claimed_at'),
            lease_expires_at=row.get('lease_expires_at'),
            released_at=row.get('released_at'),
            acked_at=row.get('acked_at'),
            metadata=dict(row.get('metadata') or {}),
            created_at=row.get('created_at'),
        )

    def _uuid_or_null(self, value: str | None) -> str:
        if value is None:
            return 'NULL'
        return f"{sql_literal(value)}::uuid"

    def _enum_or_null(self, value: str | None, enum_type: str) -> str:
        if value is None:
            return 'NULL'
        return f"{sql_literal(value)}::{enum_type}"

    def _timestamp_or_null(self, value: str | None) -> str:
        if value is None:
            return 'NULL'
        return f"{sql_literal(value)}::timestamptz"

    def _timestamp_or_now(self, value: str | None) -> str:
        if value is None:
            return 'now()'
        return f"{sql_literal(value)}::timestamptz"

    def _int_or_null(self, value: int | None) -> str:
        return 'NULL' if value is None else str(value)

    def _json_sql(self, value: dict[str, Any] | None) -> str:
        return sql_literal(json.dumps(value or {}))


__all__ = ['PostgresWorkflowStateRepository']

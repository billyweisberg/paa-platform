"""Postgres-backed runtime-event repository implementation."""

from __future__ import annotations

from typing import Any

from paa_core.db import DBSettings, query_json_rows, sql_literal

from .models import (
    AcceptanceEventRecord,
    AutomationRunEventRecord,
    AutomationRunRecord,
    HandoffRecord,
    QueueMessageRecord,
    TransitionInputRecord,
)


class PostgresRuntimeEventRepository:
    """Postgres-backed repository for runtime transport and evidence records."""

    def __init__(self, *, settings: DBSettings | None = None) -> None:
        self._settings = settings

    def get_handoff(self, handoff_id: str) -> HandoffRecord | None:
        sql = f"""
SELECT row_to_json(t)
FROM (
  SELECT
    h.handoff_id::text,
    h.project_id::text,
    h.work_item_id::text,
    h.from_role_id::text,
    h.to_role_id::text,
    h.handoff_type,
    h.status::text AS status,
    h.created_at::text,
    h.claimed_at::text,
    h.acknowledged_at::text,
    h.closed_at::text,
    h.notes
  FROM paa.handoffs h
  WHERE h.handoff_id = {sql_literal(handoff_id)}::uuid
) AS t;
"""
        rows = self._query_json_rows(sql)
        return self._handoff_from_row(rows[0]) if rows else None

    def get_queue_message(self, queue_message_id: str) -> QueueMessageRecord | None:
        sql = self._queue_message_sql(
            where_clause=f"qm.queue_message_id = {sql_literal(queue_message_id)}::uuid"
        )
        rows = self._query_json_rows(sql)
        return self._queue_message_from_row(rows[0]) if rows else None

    def get_queue_message_by_external(self, message_id_external: str) -> QueueMessageRecord | None:
        sql = self._queue_message_sql(
            where_clause=f"qm.message_id_external = {sql_literal(message_id_external)}"
        )
        rows = self._query_json_rows(sql)
        return self._queue_message_from_row(rows[0]) if rows else None

    def get_automation_run(self, automation_run_id: str) -> AutomationRunRecord | None:
        sql = f"""
SELECT row_to_json(t)
FROM (
  SELECT
    ar.automation_run_id::text,
    ar.agent_id::text,
    ar.work_item_id::text,
    ar.handoff_id::text,
    ar.trigger_type,
    ar.status::text AS status,
    ar.started_at::text,
    ar.finished_at::text,
    ar.summary,
    ar.artifacts_json AS artifacts,
    ar.created_at::text,
    ar.updated_at::text
  FROM paa.automation_runs ar
  WHERE ar.automation_run_id = {sql_literal(automation_run_id)}::uuid
) AS t;
"""
        rows = self._query_json_rows(sql)
        return self._automation_run_from_row(rows[0]) if rows else None

    def get_latest_automation_run_for_message_id(self, message_id_external: str) -> AutomationRunRecord | None:
        sql = f"""
SELECT row_to_json(t)
FROM (
  SELECT
    ar.automation_run_id::text,
    ar.agent_id::text,
    ar.work_item_id::text,
    ar.handoff_id::text,
    ar.trigger_type,
    ar.status::text AS status,
    ar.started_at::text,
    ar.finished_at::text,
    ar.summary,
    ar.artifacts_json AS artifacts,
    ar.created_at::text,
    ar.updated_at::text
  FROM paa.automation_runs ar
  WHERE ar.artifacts_json->>'message_id' = {sql_literal(message_id_external)}
  ORDER BY ar.created_at DESC, ar.updated_at DESC
  LIMIT 1
) AS t;
"""
        rows = self._query_json_rows(sql)
        return self._automation_run_from_row(rows[0]) if rows else None

    def list_transition_inputs_for_work_item(self, work_item_id: str) -> list[TransitionInputRecord]:
        sql = f"""
SELECT row_to_json(t)
FROM (
  SELECT
    ti.transition_input_id::text,
    ti.project_id::text,
    ti.work_item_id::text,
    ti.workflow_state_id::text,
    ti.workflow_transition_id::text,
    ti.automation_run_id::text,
    ti.input_type::text AS input_type,
    ti.input_schema_type,
    ti.input_source_surface::text AS input_source_surface,
    ti.input_key,
    ti.input_hash,
    ti.source_queue_message_id::text,
    ti.source_handoff_id::text,
    ti.source_message_id_external,
    ti.source_report_path,
    ti.payload_json AS payload,
    ti.content_summary_json AS content_summary,
    ti.schema_version,
    ti.captured_at::text,
    ti.metadata_json AS metadata,
    ti.created_at::text
  FROM paa.transition_inputs ti
  WHERE ti.work_item_id = {sql_literal(work_item_id)}::uuid
  ORDER BY ti.captured_at DESC, ti.created_at DESC
) AS t;
"""
        return [self._transition_input_from_row(row) for row in self._query_json_rows(sql)]

    def list_automation_run_events(self, automation_run_id: str) -> list[AutomationRunEventRecord]:
        sql = f"""
SELECT row_to_json(t)
FROM (
  SELECT
    are.automation_run_event_id::text,
    are.automation_run_id::text,
    are.project_id::text,
    are.work_item_id::text,
    are.workflow_state_id::text,
    are.workflow_transition_id::text,
    are.event_type::text AS event_type,
    are.event_status::text AS event_status,
    are.event_phase::text AS event_phase,
    are.event_reason_code,
    are.event_reason_text,
    are.role_id::text,
    are.agent_id::text,
    are.handoff_id::text,
    are.queue_message_id::text,
    are.queue_claim_id::text,
    are.message_id_external,
    are.event_summary_json AS event_summary,
    are.evidence_ref,
    are.raw_log_pointer,
    are.event_recorded_at::text,
    are.metadata_json AS metadata,
    are.created_at::text
  FROM paa.automation_run_events are
  WHERE are.automation_run_id = {sql_literal(automation_run_id)}::uuid
  ORDER BY are.event_recorded_at DESC, are.created_at DESC
) AS t;
"""
        return [self._automation_run_event_from_row(row) for row in self._query_json_rows(sql)]

    def list_acceptance_events_for_work_item(self, work_item_id: str) -> list[AcceptanceEventRecord]:
        sql = f"""
SELECT row_to_json(t)
FROM (
  SELECT
    ae.acceptance_event_id::text,
    ae.project_id::text,
    ae.work_item_id::text,
    ae.handoff_id::text,
    ae.accepted_by_agent_id::text,
    ae.accepted_by_role_id::text,
    ae.decision::text AS decision,
    ae.notes,
    ae.merge_commit_sha,
    ae.metadata_json AS metadata,
    ae.created_at::text
  FROM paa.acceptance_events ae
  WHERE ae.work_item_id = {sql_literal(work_item_id)}::uuid
  ORDER BY ae.created_at DESC
) AS t;
"""
        return [self._acceptance_event_from_row(row) for row in self._query_json_rows(sql)]

    def _queue_message_sql(self, *, where_clause: str) -> str:
        return f"""
SELECT row_to_json(t)
FROM (
  SELECT
    qm.queue_message_id::text,
    qm.handoff_id::text,
    qm.queue_name,
    qm.schema_type,
    qm.message_id_external,
    qm.correlation_key,
    qm.payload_json AS payload,
    qm.status::text AS status,
    qm.sent_at::text,
    qm.claimed_at::text,
    qm.acknowledged_at::text,
    qm.metadata_json AS metadata,
    qm.created_at::text,
    qm.updated_at::text
  FROM paa.queue_messages qm
  WHERE {where_clause}
) AS t;
"""

    def _query_json_rows(self, sql: str) -> list[dict[str, Any]]:
        return query_json_rows(sql, settings=self._settings)

    def _handoff_from_row(self, row: dict[str, Any]) -> HandoffRecord:
        return HandoffRecord(
            handoff_id=row['handoff_id'],
            project_id=row['project_id'],
            work_item_id=row['work_item_id'],
            from_role_id=row['from_role_id'],
            to_role_id=row['to_role_id'],
            handoff_type=row['handoff_type'],
            status=row['status'],
            created_at=row.get('created_at'),
            claimed_at=row.get('claimed_at'),
            acknowledged_at=row.get('acknowledged_at'),
            closed_at=row.get('closed_at'),
            notes=row.get('notes'),
        )

    def _queue_message_from_row(self, row: dict[str, Any]) -> QueueMessageRecord:
        return QueueMessageRecord(
            queue_message_id=row['queue_message_id'],
            handoff_id=row['handoff_id'],
            queue_name=row['queue_name'],
            schema_type=row['schema_type'],
            message_id_external=row.get('message_id_external'),
            correlation_key=row.get('correlation_key'),
            payload=dict(row.get('payload') or {}),
            status=row['status'],
            sent_at=row.get('sent_at'),
            claimed_at=row.get('claimed_at'),
            acknowledged_at=row.get('acknowledged_at'),
            metadata=dict(row.get('metadata') or {}),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
        )

    def _automation_run_from_row(self, row: dict[str, Any]) -> AutomationRunRecord:
        return AutomationRunRecord(
            automation_run_id=row['automation_run_id'],
            agent_id=row['agent_id'],
            work_item_id=row.get('work_item_id'),
            handoff_id=row.get('handoff_id'),
            trigger_type=row.get('trigger_type'),
            status=row['status'],
            started_at=row.get('started_at'),
            finished_at=row.get('finished_at'),
            summary=row.get('summary'),
            artifacts=dict(row.get('artifacts') or {}),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
        )

    def _transition_input_from_row(self, row: dict[str, Any]) -> TransitionInputRecord:
        return TransitionInputRecord(
            transition_input_id=row['transition_input_id'],
            project_id=row['project_id'],
            work_item_id=row['work_item_id'],
            workflow_state_id=row.get('workflow_state_id'),
            workflow_transition_id=row.get('workflow_transition_id'),
            automation_run_id=row.get('automation_run_id'),
            input_type=row['input_type'],
            input_schema_type=row.get('input_schema_type'),
            input_source_surface=row['input_source_surface'],
            input_key=row.get('input_key'),
            input_hash=row.get('input_hash'),
            source_queue_message_id=row.get('source_queue_message_id'),
            source_handoff_id=row.get('source_handoff_id'),
            source_message_id_external=row.get('source_message_id_external'),
            source_report_path=row.get('source_report_path'),
            payload=dict(row.get('payload') or {}),
            content_summary=dict(row.get('content_summary') or {}),
            schema_version=row.get('schema_version'),
            captured_at=row.get('captured_at'),
            metadata=dict(row.get('metadata') or {}),
            created_at=row.get('created_at'),
        )

    def _automation_run_event_from_row(self, row: dict[str, Any]) -> AutomationRunEventRecord:
        return AutomationRunEventRecord(
            automation_run_event_id=row['automation_run_event_id'],
            automation_run_id=row['automation_run_id'],
            project_id=row['project_id'],
            work_item_id=row.get('work_item_id'),
            workflow_state_id=row.get('workflow_state_id'),
            workflow_transition_id=row.get('workflow_transition_id'),
            event_type=row['event_type'],
            event_status=row['event_status'],
            event_phase=row['event_phase'],
            event_reason_code=row.get('event_reason_code'),
            event_reason_text=row.get('event_reason_text'),
            role_id=row.get('role_id'),
            agent_id=row.get('agent_id'),
            handoff_id=row.get('handoff_id'),
            queue_message_id=row.get('queue_message_id'),
            queue_claim_id=row.get('queue_claim_id'),
            message_id_external=row.get('message_id_external'),
            event_summary=dict(row.get('event_summary') or {}),
            evidence_ref=row.get('evidence_ref'),
            raw_log_pointer=row.get('raw_log_pointer'),
            event_recorded_at=row.get('event_recorded_at'),
            metadata=dict(row.get('metadata') or {}),
            created_at=row.get('created_at'),
        )

    def _acceptance_event_from_row(self, row: dict[str, Any]) -> AcceptanceEventRecord:
        return AcceptanceEventRecord(
            acceptance_event_id=row['acceptance_event_id'],
            project_id=row['project_id'],
            work_item_id=row['work_item_id'],
            handoff_id=row.get('handoff_id'),
            accepted_by_agent_id=row.get('accepted_by_agent_id'),
            accepted_by_role_id=row.get('accepted_by_role_id'),
            decision=row['decision'],
            notes=row.get('notes'),
            merge_commit_sha=row.get('merge_commit_sha'),
            metadata=dict(row.get('metadata') or {}),
            created_at=row.get('created_at'),
        )


__all__ = ['PostgresRuntimeEventRepository']

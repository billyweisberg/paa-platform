"""Postgres-backed runtime-event repository implementation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from paa_core.db import DBSettings, execute_sql, query_all_rows, query_json_rows, query_scalar, sql_literal

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

    def resolve_work_item_id_for_message(self, message: dict[str, object]) -> str | None:
        project_slug = self._project_slug_from_message(message)
        issue_number = self._issue_number_from_message(message)
        payload = message.get('payload') or {}
        coder_brief_resolution = payload.get('coder_brief_resolution') if isinstance(payload, dict) else {}
        if not isinstance(coder_brief_resolution, dict):
            coder_brief_resolution = {}
        package_id_external = coder_brief_resolution.get('package_id_external')
        brief_id_external = coder_brief_resolution.get('brief_id_external')
        sql = f"""
WITH project AS (
  SELECT project_id FROM paa.projects WHERE slug = {sql_literal(project_slug)} LIMIT 1
), issue_match AS (
  SELECT wi.work_item_id
  FROM paa.work_items wi
  JOIN project p ON p.project_id = wi.project_id
  WHERE wi.issue_number = {sql_literal(issue_number)}
  LIMIT 1
), package_match AS (
  SELECT dp.work_item_id
  FROM paa.design_packages dp
  JOIN project p ON p.project_id = dp.project_id
  WHERE dp.package_id_external = {sql_literal(package_id_external)}
    AND dp.work_item_id IS NOT NULL
  LIMIT 1
), brief_match AS (
  SELECT cb.work_item_id
  FROM paa.coder_run_briefs cb
  JOIN project p ON p.project_id = cb.project_id
  WHERE cb.brief_id_external = {sql_literal(brief_id_external)}
    AND cb.work_item_id IS NOT NULL
  LIMIT 1
)
SELECT coalesce(
  (SELECT work_item_id::text FROM issue_match),
  (SELECT work_item_id::text FROM package_match),
  (SELECT work_item_id::text FROM brief_match)
);
"""
        output = query_scalar(sql, settings=self._settings)
        return str(output) if output else None

    def find_packet_compilation_run(
        self,
        *,
        message_id_external: str,
        schema_type: str,
    ) -> AutomationRunRecord | None:
        trigger_type = f'packet_compilation:{schema_type}'
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
  WHERE ar.trigger_type = {sql_literal(trigger_type)}
    AND ar.artifacts_json->>'message_id' = {sql_literal(message_id_external)}
  ORDER BY ar.created_at DESC, ar.updated_at DESC
  LIMIT 1
) AS t;
"""
        rows = self._query_json_rows(sql)
        return self._automation_run_from_row(rows[0]) if rows else None

    def create_packet_compilation_run_for_message(
        self,
        *,
        message: dict[str, object],
        message_file: str,
        agent_name: str,
        work_item_id: str | None = None,
    ) -> AutomationRunRecord | None:
        message_id = str(message.get('message_id') or '')
        schema_type = str(message.get('schema_type') or '')
        if not message_id or not schema_type:
            return None
        existing = self.find_packet_compilation_run(
            message_id_external=message_id,
            schema_type=schema_type,
        )
        if existing is not None:
            return existing
        project_slug = self._project_slug_from_message(message)
        resolved_work_item_id = work_item_id or self.resolve_work_item_id_for_message(message)
        issue_number = self._issue_number_from_message(message)
        created_at = str(message.get('created_at') or self._utc_now())
        output_path = str(Path(message_file).expanduser().resolve())
        artifacts = {
            'packet_schema_type': schema_type,
            'message_id': message.get('message_id'),
            'correlation_id': message.get('correlation_id'),
            'output_path': output_path,
            'packet_output_path': output_path,
            'review_output_path': None,
            'source_input_path': output_path,
            'source_packet_path': output_path,
            'packet_json': message,
            'persistence_version': '1.0.0',
        }
        summary = (
            f'Compiled {schema_type} for issue #{issue_number}'
            if issue_number is not None
            else f'Compiled {schema_type}'
        )
        sql = f"""
WITH project AS (
  SELECT project_id FROM paa.projects WHERE slug = {sql_literal(project_slug)} LIMIT 1
), agent AS (
  SELECT a.agent_id
  FROM paa.agents a
  JOIN project p ON p.project_id = a.project_id
  WHERE a.name = {sql_literal(agent_name)}
  LIMIT 1
)
INSERT INTO paa.automation_runs (
  agent_id,
  work_item_id,
  trigger_type,
  status,
  started_at,
  finished_at,
  summary,
  artifacts_json
)
SELECT
  agent.agent_id,
  {sql_literal(resolved_work_item_id)}::uuid,
  {sql_literal(f'packet_compilation:{schema_type}')},
  'completed'::paa.automation_run_status,
  {sql_literal(created_at)}::timestamptz,
  {sql_literal(created_at)}::timestamptz,
  {sql_literal(summary)},
  {sql_literal(json.dumps(artifacts, sort_keys=True))}::jsonb
FROM agent;
"""
        execute_sql(sql, settings=self._settings)
        return self.find_packet_compilation_run(
            message_id_external=message_id,
            schema_type=schema_type,
        )

    def record_queue_send_for_message(
        self,
        *,
        message: dict[str, object],
        queue_name: str,
        exchange: str,
        publish_result: dict[str, object] | None = None,
        work_item_id: str | None = None,
        packet_compilation_run: AutomationRunRecord | None = None,
    ) -> QueueMessageRecord | None:
        project_slug = self._project_slug_from_message(message)
        from_role = self._role_name_for_db(message.get('from_role'))
        to_role = self._role_name_for_db(message.get('to_role'))
        resolved_work_item_id = work_item_id or self.resolve_work_item_id_for_message(message)
        resolved_message_id = str(message.get('message_id') or '')
        if not resolved_message_id:
            return None
        packet_compilation = packet_compilation_run or self.find_packet_compilation_run(
            message_id_external=resolved_message_id,
            schema_type=str(message.get('schema_type') or ''),
        )
        metadata: dict[str, object] = {
            'queue_name': queue_name,
            'exchange': exchange,
            'publish_result': publish_result or {},
        }
        if packet_compilation is not None:
            metadata['compiled_packet_automation_run_id'] = packet_compilation.automation_run_id
            metadata['compiled_packet_trigger_type'] = packet_compilation.trigger_type
            metadata['compiled_packet_summary'] = packet_compilation.summary
            metadata['compiled_packet_package_id_external'] = packet_compilation.artifacts.get('package_id_external')
            metadata['compiled_packet_brief_id_external'] = packet_compilation.artifacts.get('brief_id_external')
        payload_json = json.dumps(message, sort_keys=True)
        metadata_json = json.dumps(metadata, sort_keys=True)
        sql = f"""
WITH project AS (
  SELECT project_id FROM paa.projects WHERE slug = {sql_literal(project_slug)}
), from_role AS (
  SELECT role_id FROM paa.roles r JOIN project p ON p.project_id = r.project_id
  WHERE r.name = {sql_literal(from_role)}
), to_role AS (
  SELECT role_id FROM paa.roles r JOIN project p ON p.project_id = r.project_id
  WHERE r.name = {sql_literal(to_role)}
), existing AS (
  SELECT qm.queue_message_id
  FROM paa.queue_messages qm
  WHERE qm.message_id_external = {sql_literal(resolved_message_id)}
  LIMIT 1
), packet_compilation_run AS (
  SELECT {sql_literal(packet_compilation.automation_run_id if packet_compilation else None)}::uuid AS automation_run_id
), inserted_handoff AS (
  INSERT INTO paa.handoffs (
    project_id,
    work_item_id,
    from_role_id,
    to_role_id,
    handoff_type,
    status,
    created_at,
    notes
  )
  SELECT
    project.project_id,
    {sql_literal(resolved_work_item_id)}::uuid,
    (SELECT role_id FROM from_role),
    (SELECT role_id FROM to_role),
    {sql_literal(message.get('schema_type'))},
    'pending'::paa.handoff_status,
    {sql_literal(message.get('created_at'))}::timestamptz,
    {sql_literal(f"correlation_id={message.get('correlation_id')}")}
  FROM project
  WHERE NOT EXISTS (SELECT 1 FROM existing)
  RETURNING handoff_id
), linked_compilation_run AS (
  UPDATE paa.automation_runs ar
  SET handoff_id = inserted_handoff.handoff_id,
      updated_at = now()
  FROM inserted_handoff, packet_compilation_run
  WHERE ar.automation_run_id = packet_compilation_run.automation_run_id
  RETURNING ar.automation_run_id
)
INSERT INTO paa.queue_messages (
  handoff_id,
  queue_name,
  schema_type,
  message_id_external,
  correlation_key,
  payload_json,
  status,
  sent_at,
  metadata_json
)
SELECT
  inserted_handoff.handoff_id,
  {sql_literal(queue_name)},
  {sql_literal(message.get('schema_type'))},
  {sql_literal(resolved_message_id)},
  {sql_literal(message.get('correlation_id'))},
  {sql_literal(payload_json)}::jsonb,
  'sent'::paa.queue_message_status,
  {sql_literal(self._utc_now())}::timestamptz,
  {sql_literal(metadata_json)}::jsonb
FROM inserted_handoff
WHERE NOT EXISTS (SELECT 1 FROM existing);
"""
        execute_sql(sql, settings=self._settings)
        return self.get_queue_message_by_external(resolved_message_id)

    def update_queue_message_status_by_external(
        self,
        *,
        message_id_external: str,
        queue_status: str,
        handoff_status: str,
        timestamp_field: str,
    ) -> None:
        timestamp = self._utc_now()
        sql = f"""
WITH target AS (
  SELECT qm.queue_message_id, qm.handoff_id
  FROM paa.queue_messages qm
  WHERE qm.message_id_external = {sql_literal(message_id_external)}
  LIMIT 1
), updated_message AS (
  UPDATE paa.queue_messages qm
  SET status = {sql_literal(queue_status)}::paa.queue_message_status,
      {timestamp_field} = {sql_literal(timestamp)}::timestamptz,
      updated_at = now()
  FROM target
  WHERE qm.queue_message_id = target.queue_message_id
  RETURNING qm.handoff_id
)
UPDATE paa.handoffs h
SET status = {sql_literal(handoff_status)}::paa.handoff_status,
    claimed_at = CASE WHEN {sql_literal(handoff_status)} = 'claimed' THEN {sql_literal(timestamp)}::timestamptz ELSE h.claimed_at END,
    acknowledged_at = CASE WHEN {sql_literal(handoff_status)} = 'completed' THEN {sql_literal(timestamp)}::timestamptz ELSE h.acknowledged_at END,
    closed_at = CASE WHEN {sql_literal(handoff_status)} = 'completed' THEN {sql_literal(timestamp)}::timestamptz ELSE h.closed_at END
  FROM updated_message
  WHERE h.handoff_id = updated_message.handoff_id;
"""
        execute_sql(sql, settings=self._settings)

    def resolve_verification_obligation(
        self,
        *,
        project_slug: str,
        issue_number: int,
        verification_key_suffix: str | None = None,
        verification_type: str | None = None,
    ) -> tuple[str, str] | None:
        where_clause = ''
        if verification_key_suffix:
            where_clause = f"vo.verification_key LIKE {sql_literal(f'%{verification_key_suffix}')}"
        elif verification_type:
            where_clause = f"vo.verification_type = {sql_literal(verification_type)}::paa.verification_type"
        else:
            return None
        sql = f"""
WITH project AS (
  SELECT project_id FROM paa.projects WHERE slug = {sql_literal(project_slug)}
), work_item AS (
  SELECT wi.work_item_id
  FROM paa.work_items wi
  JOIN project p ON p.project_id = wi.project_id
  WHERE wi.issue_number = {sql_literal(issue_number)}
  LIMIT 1
)
SELECT vo.verification_key, vo.verification_id::text
FROM paa.verification_obligations vo
JOIN work_item wi ON wi.work_item_id = vo.work_item_id
WHERE {where_clause}
ORDER BY vo.verification_key
LIMIT 1;
"""
        rows = query_all_rows(sql, settings=self._settings)
        if not rows:
            return None
        verification_key, verification_id = rows[0]
        if not verification_key or not verification_id:
            return None
        return str(verification_key), str(verification_id)

    def record_evidence_if_missing(
        self,
        *,
        project_slug: str,
        issue_number: int,
        verification_id: str,
        agent_name: str,
        result: str,
        summary: str,
        artifact_location: str,
        metadata: dict[str, object],
        captured_at: str | None,
    ) -> None:
        metadata_json = json.dumps(metadata, sort_keys=True)
        sql = f"""
WITH project AS (
  SELECT project_id FROM paa.projects WHERE slug = {sql_literal(project_slug)}
), work_item AS (
  SELECT wi.work_item_id
  FROM paa.work_items wi
  JOIN project p ON p.project_id = wi.project_id
  WHERE wi.issue_number = {sql_literal(issue_number)}
  LIMIT 1
), agent AS (
  SELECT a.agent_id
  FROM paa.agents a
  JOIN project p ON p.project_id = a.project_id
  WHERE a.name = {sql_literal(agent_name)}
  LIMIT 1
)
INSERT INTO paa.evidence (
  project_id,
  work_item_id,
  verification_id,
  captured_by_agent_id,
  result,
  summary,
  artifact_location,
  metadata_json,
  captured_at
)
SELECT
  project.project_id,
  work_item.work_item_id,
  {sql_literal(verification_id)}::uuid,
  agent.agent_id,
  {sql_literal(result)}::paa.evidence_result,
  {sql_literal(summary)},
  {sql_literal(artifact_location)},
  {sql_literal(metadata_json)}::jsonb,
  {sql_literal(captured_at)}::timestamptz
FROM project, work_item, agent
WHERE NOT EXISTS (
  SELECT 1 FROM paa.evidence ev
  WHERE ev.work_item_id = work_item.work_item_id
    AND ev.artifact_location = {sql_literal(artifact_location)}
);
"""
        execute_sql(sql, settings=self._settings)

    def record_acceptance_event_if_missing(
        self,
        *,
        project_slug: str,
        issue_number: int,
        agent_name: str,
        role_name: str,
        decision: str,
        notes: str,
        metadata: dict[str, object],
        created_at: str | None,
    ) -> None:
        metadata_json = json.dumps(metadata, sort_keys=True)
        sql = f"""
WITH project AS (
  SELECT project_id FROM paa.projects WHERE slug = {sql_literal(project_slug)}
), work_item AS (
  SELECT wi.work_item_id
  FROM paa.work_items wi
  JOIN project p ON p.project_id = wi.project_id
  WHERE wi.issue_number = {sql_literal(issue_number)}
  LIMIT 1
), agent AS (
  SELECT a.agent_id
  FROM paa.agents a
  JOIN project p ON p.project_id = a.project_id
  WHERE a.name = {sql_literal(agent_name)}
  LIMIT 1
), role AS (
  SELECT r.role_id
  FROM paa.roles r
  JOIN project p ON p.project_id = r.project_id
  WHERE r.name = {sql_literal(role_name)}
  LIMIT 1
)
INSERT INTO paa.acceptance_events (
  project_id,
  work_item_id,
  accepted_by_agent_id,
  accepted_by_role_id,
  decision,
  notes,
  metadata_json,
  created_at
)
SELECT
  project.project_id,
  work_item.work_item_id,
  agent.agent_id,
  role.role_id,
  {sql_literal(decision)}::paa.acceptance_decision,
  {sql_literal(notes)},
  {sql_literal(metadata_json)}::jsonb,
  {sql_literal(created_at)}::timestamptz
FROM project, work_item, agent, role
WHERE NOT EXISTS (
  SELECT 1 FROM paa.acceptance_events ae
  WHERE ae.work_item_id = work_item.work_item_id
    AND ae.notes = {sql_literal(notes)}
);
"""
        execute_sql(sql, settings=self._settings)

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

    @staticmethod
    def _project_slug_from_message(message: dict[str, object]) -> str:
        project = message.get('project')
        if project in {'fractal-core-python', 'fractal-core'}:
            return 'fractal-core-python'
        return str(project or 'fractal-core-python')

    @staticmethod
    def _issue_number_from_message(message: dict[str, object]) -> int | None:
        github_context = message.get('github_context')
        issue_number = github_context.get('issue_number') if isinstance(github_context, dict) else None
        try:
            return int(issue_number) if issue_number is not None else None
        except Exception:
            return None

    @staticmethod
    def _role_name_for_db(raw_role: object) -> str | None:
        normalized = str(raw_role or '')
        mapping = {
            'Python Team': 'Dev',
            'python-team': 'Dev',
            'Python Dev': 'Dev',
            'Frontend Dev': 'Dev',
            'Backend Dev': 'Dev',
            'Infra Dev': 'Dev',
            'Docs Dev': 'Dev',
            'QA': 'QA',
            'qa': 'QA',
            'TechLead': 'TechLead',
            'techlead': 'TechLead',
            'Architect': 'Architect',
            'architect': 'Architect',
            'Authority Architect': 'Architect',
            'Delivery Architect': 'Architect',
        }
        return mapping.get(normalized, normalized or None)

    @staticmethod
    def _utc_now() -> str:
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

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

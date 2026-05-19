#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
CORE_SRC = REPO_ROOT / "packages" / "paa-core" / "src"
if str(CORE_SRC) not in sys.path:
    sys.path.insert(0, str(CORE_SRC))

from paa_core.db import run_psql, sql_literal
from paa_core.repositories.workflow_state import (
    PostgresWorkflowStateRepository,
    WorkflowStateUpsertSpec,
    WorkflowTransitionAppendSpec,
)


PROJECT_ID = "414927ef-6834-4434-9ebf-74bd69582aee"
WORK_ITEM_ID = "f1dfc44f-8d70-418f-80eb-7b33fc8dea11"
DESIGN_PACKAGE_ID = "3d1993fc-5e19-4a4a-b1b7-ce0e1cb396e9"
AUTHORITY_VERSION_ID = "572cd77f-2d39-4044-9c70-09dd8b28dfcb"
ISSUE_NUMBER = 6

ARCHITECT_ROLE_ID = "17d1dde0-803a-4869-9cd3-3b79a104fa52"
TECHLEAD_ROLE_ID = "cd503483-1134-41e4-85c9-6d0248dbb73b"

AGENT_NAME = "Governance Proof Agent"
HANDOFF_TYPE = "governance_runtime_proof"
AUTOMATION_TRIGGER_TYPE = "governance_runtime_proof"
AUTOMATION_SUMMARY = "Governed proof trio runtime evidence materialization"
EXECUTION_RECORD_URL = "https://example.invalid/paa/governed-proof-trio-runtime"
EXECUTION_BRANCH = "codex/governed-proof-trio-runtime"


def _query_scalar(sql: str) -> str:
    output = run_psql(sql)
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"Expected scalar value from SQL, got empty output.\nSQL:\n{sql}")
    return lines[0]


def _ensure_agent() -> str:
    metadata = json.dumps(
        {
            "source": "governance runtime proof",
            "scope": "proof trio",
        },
        sort_keys=True,
    )
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
  {sql_literal(PROJECT_ID)}::uuid,
  {sql_literal(TECHLEAD_ROLE_ID)}::uuid,
  {sql_literal(AGENT_NAME)},
  'automation'::paa.agent_type,
  'codex',
  true,
  {sql_literal(metadata)}::jsonb
)
ON CONFLICT (project_id, name) DO UPDATE SET
  role_id = EXCLUDED.role_id,
  agent_type = EXCLUDED.agent_type,
  runtime_kind = EXCLUDED.runtime_kind,
  active = EXCLUDED.active,
  metadata_json = paa.agents.metadata_json || EXCLUDED.metadata_json,
  updated_at = now()
RETURNING agent_id::text;
"""
    return _query_scalar(sql)


def _ensure_handoff() -> str:
    sql = f"""
WITH existing AS (
  SELECT handoff_id::text
  FROM paa.handoffs
  WHERE work_item_id = {sql_literal(WORK_ITEM_ID)}::uuid
    AND handoff_type = {sql_literal(HANDOFF_TYPE)}
    AND notes = 'governed proof trio runtime evidence'
  LIMIT 1
), inserted AS (
  INSERT INTO paa.handoffs (
    project_id,
    work_item_id,
    from_role_id,
    to_role_id,
    handoff_type,
    status,
    created_at,
    claimed_at,
    acknowledged_at,
    closed_at,
    notes
  )
  SELECT
    {sql_literal(PROJECT_ID)}::uuid,
    {sql_literal(WORK_ITEM_ID)}::uuid,
    {sql_literal(ARCHITECT_ROLE_ID)}::uuid,
    {sql_literal(TECHLEAD_ROLE_ID)}::uuid,
    {sql_literal(HANDOFF_TYPE)},
    'completed'::paa.handoff_status,
    now(),
    now(),
    now(),
    now(),
    'governed proof trio runtime evidence'
  WHERE NOT EXISTS (SELECT 1 FROM existing)
  RETURNING handoff_id::text
)
SELECT handoff_id FROM inserted
UNION ALL
SELECT handoff_id FROM existing
LIMIT 1;
"""
    return _query_scalar(sql)


def _ensure_automation_run(agent_id: str, handoff_id: str) -> str:
    artifacts = json.dumps(
        {
            "proof_scope": "governed-proof-trio",
            "work_item_id": WORK_ITEM_ID,
            "handoff_id": handoff_id,
        },
        sort_keys=True,
    )
    sql = f"""
WITH existing AS (
  SELECT automation_run_id::text
  FROM paa.automation_runs
  WHERE agent_id = {sql_literal(agent_id)}::uuid
    AND work_item_id = {sql_literal(WORK_ITEM_ID)}::uuid
    AND trigger_type = {sql_literal(AUTOMATION_TRIGGER_TYPE)}
    AND summary = {sql_literal(AUTOMATION_SUMMARY)}
  LIMIT 1
), inserted AS (
  INSERT INTO paa.automation_runs (
    agent_id,
    work_item_id,
    handoff_id,
    trigger_type,
    status,
    started_at,
    finished_at,
    summary,
    artifacts_json
  )
  SELECT
    {sql_literal(agent_id)}::uuid,
    {sql_literal(WORK_ITEM_ID)}::uuid,
    {sql_literal(handoff_id)}::uuid,
    {sql_literal(AUTOMATION_TRIGGER_TYPE)},
    'completed'::paa.automation_run_status,
    now(),
    now(),
    {sql_literal(AUTOMATION_SUMMARY)},
    {sql_literal(artifacts)}::jsonb
  WHERE NOT EXISTS (SELECT 1 FROM existing)
  RETURNING automation_run_id::text
)
SELECT automation_run_id FROM inserted
UNION ALL
SELECT automation_run_id FROM existing
LIMIT 1;
"""
    return _query_scalar(sql)


def _ensure_execution_record() -> str:
    metadata = json.dumps(
        {
            "source": "governance runtime proof",
            "work_item_id": WORK_ITEM_ID,
        },
        sort_keys=True,
    )
    sql = f"""
WITH existing AS (
  SELECT execution_record_id::text
  FROM paa.execution_records
  WHERE work_item_id = {sql_literal(WORK_ITEM_ID)}::uuid
    AND url = {sql_literal(EXECUTION_RECORD_URL)}
  LIMIT 1
), inserted AS (
  INSERT INTO paa.execution_records (
    work_item_id,
    system_type,
    issue_number,
    branch_name,
    url,
    status,
    metadata_json
  )
  SELECT
    {sql_literal(WORK_ITEM_ID)}::uuid,
    'github',
    {ISSUE_NUMBER},
    {sql_literal(EXECUTION_BRANCH)},
    {sql_literal(EXECUTION_RECORD_URL)},
    'ready_for_review'::paa.execution_record_status,
    {sql_literal(metadata)}::jsonb
  WHERE NOT EXISTS (SELECT 1 FROM existing)
  RETURNING execution_record_id::text
)
SELECT execution_record_id FROM inserted
UNION ALL
SELECT execution_record_id FROM existing
LIMIT 1;
"""
    return _query_scalar(sql)


def main() -> int:
    agent_id = _ensure_agent()
    handoff_id = _ensure_handoff()
    automation_run_id = _ensure_automation_run(agent_id, handoff_id)
    execution_record_id = _ensure_execution_record()

    workflow_repo = PostgresWorkflowStateRepository()
    workflow_repo.upsert_workflow_state(
        WorkflowStateUpsertSpec(
            project_id=PROJECT_ID,
            work_item_id=WORK_ITEM_ID,
            authority_version_id=AUTHORITY_VERSION_ID,
            design_package_id=DESIGN_PACKAGE_ID,
            workflow_stage="techlead_delivery_review_pending",
            current_owner_role_id=TECHLEAD_ROLE_ID,
            lineage_state="active",
            current_issue_number=ISSUE_NUMBER,
            active_handoff_id=handoff_id,
            active_result_role_id=TECHLEAD_ROLE_ID,
            last_transition_at=None,
            metadata={"source": "governance runtime proof"},
        )
    )

    workflow_state_id = _query_scalar(
        f"SELECT workflow_state_id::text FROM paa.workflow_states WHERE work_item_id = {sql_literal(WORK_ITEM_ID)}::uuid LIMIT 1;"
    )

    existing_transition = run_psql(
        f"""
SELECT workflow_transition_id::text
FROM paa.workflow_transitions
WHERE work_item_id = {sql_literal(WORK_ITEM_ID)}::uuid
  AND transition_type = 'delivery_review_returned'::paa.workflow_transition_type
  AND reason_code = 'governance_runtime_proof'
LIMIT 1;
"""
    ).strip()
    if not existing_transition:
        workflow_repo.append_workflow_transition(
            WorkflowTransitionAppendSpec(
                workflow_state_id=workflow_state_id,
                project_id=PROJECT_ID,
                work_item_id=WORK_ITEM_ID,
                transition_type="delivery_review_returned",
                transition_status="applied",
                from_workflow_stage="delivery_review_in_progress",
                to_workflow_stage="techlead_delivery_review_pending",
                from_owner_role_id=ARCHITECT_ROLE_ID,
                to_owner_role_id=TECHLEAD_ROLE_ID,
                reason_code="governance_runtime_proof",
                reason_text="Materialize the first runtime evidence chain for the governed proof trio.",
                source_handoff_id=handoff_id,
                result_handoff_id=handoff_id,
                result_role_id=TECHLEAD_ROLE_ID,
                performed_by_role_id=TECHLEAD_ROLE_ID,
                performed_by_agent_id=agent_id,
                automation_run_id=automation_run_id,
                transition_applied_at=None,
                metadata={"source": "governance runtime proof"},
            )
        )

    output = {
        "agent_id": agent_id,
        "handoff_id": handoff_id,
        "automation_run_id": automation_run_id,
        "execution_record_id": execution_record_id,
        "workflow_state_id": workflow_state_id,
        "work_item_id": WORK_ITEM_ID,
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

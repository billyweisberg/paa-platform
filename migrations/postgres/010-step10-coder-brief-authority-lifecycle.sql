-- Project for Autonomous Agents
-- Step 10 Postgres DDL: explicit coder-brief authority lifecycle governance
--
-- Purpose:
-- - make draft, approved, and packet-ready execution authority distinct in primary DB state
-- - preserve transition history for governance and audit
-- - stop relying on informal interpretation of coder_run_briefs.status alone
--
-- Prerequisites:
-- - 004-step4-coder-briefs.sql
-- - 005-step5-design-packages-and-sequencing.sql
-- - 008-step8-component-element-realizations.sql

BEGIN;

CREATE SCHEMA IF NOT EXISTS paa;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE t.typname = 'coder_brief_authority_state' AND n.nspname = 'paa'
  ) THEN
    CREATE TYPE paa.coder_brief_authority_state AS ENUM (
      'draft_brief',
      'approved_brief',
      'packet_ready_execution_authority',
      'superseded_authority',
      'rejected_authority'
    );
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE t.typname = 'coder_brief_authority_transition_kind' AND n.nspname = 'paa'
  ) THEN
    CREATE TYPE paa.coder_brief_authority_transition_kind AS ENUM (
      'derive_draft',
      'approve_brief',
      'mark_packet_ready',
      'supersede_brief',
      'reject_brief',
      'reopen_draft'
    );
  END IF;
END$$;

ALTER TABLE paa.coder_run_briefs
  ADD COLUMN IF NOT EXISTS authority_state paa.coder_brief_authority_state NOT NULL DEFAULT 'draft_brief',
  ADD COLUMN IF NOT EXISTS authority_state_updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  ADD COLUMN IF NOT EXISTS approved_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS packet_ready_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS approval_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  ADD COLUMN IF NOT EXISTS packet_preparation_json JSONB NOT NULL DEFAULT '{}'::jsonb;

CREATE INDEX IF NOT EXISTS coder_run_briefs_authority_state_idx
  ON paa.coder_run_briefs(project_id, authority_state, created_at DESC);

UPDATE paa.coder_run_briefs
SET authority_state = CASE
      WHEN status = 'approved'::paa.coder_brief_status THEN 'approved_brief'::paa.coder_brief_authority_state
      WHEN status IN ('active'::paa.coder_brief_status, 'consumed'::paa.coder_brief_status) THEN 'packet_ready_execution_authority'::paa.coder_brief_authority_state
      WHEN status = 'superseded'::paa.coder_brief_status THEN 'superseded_authority'::paa.coder_brief_authority_state
      WHEN status = 'rejected'::paa.coder_brief_status THEN 'rejected_authority'::paa.coder_brief_authority_state
      ELSE 'draft_brief'::paa.coder_brief_authority_state
    END,
    authority_state_updated_at = COALESCE(updated_at, created_at, now()),
    approved_at = CASE
      WHEN status IN ('approved'::paa.coder_brief_status, 'active'::paa.coder_brief_status, 'consumed'::paa.coder_brief_status)
      THEN COALESCE(approved_at, updated_at, created_at, now())
      ELSE approved_at
    END,
    packet_ready_at = CASE
      WHEN status IN ('active'::paa.coder_brief_status, 'consumed'::paa.coder_brief_status)
      THEN COALESCE(packet_ready_at, updated_at, created_at, now())
      ELSE packet_ready_at
    END
WHERE authority_state IS DISTINCT FROM CASE
      WHEN status = 'approved'::paa.coder_brief_status THEN 'approved_brief'::paa.coder_brief_authority_state
      WHEN status IN ('active'::paa.coder_brief_status, 'consumed'::paa.coder_brief_status) THEN 'packet_ready_execution_authority'::paa.coder_brief_authority_state
      WHEN status = 'superseded'::paa.coder_brief_status THEN 'superseded_authority'::paa.coder_brief_authority_state
      WHEN status = 'rejected'::paa.coder_brief_status THEN 'rejected_authority'::paa.coder_brief_authority_state
      ELSE 'draft_brief'::paa.coder_brief_authority_state
    END;

CREATE TABLE IF NOT EXISTS paa.coder_brief_authority_events (
  coder_brief_authority_event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES paa.projects(project_id) ON DELETE CASCADE,
  work_item_id UUID REFERENCES paa.work_items(work_item_id) ON DELETE SET NULL,
  coder_run_brief_id UUID NOT NULL REFERENCES paa.coder_run_briefs(coder_run_brief_id) ON DELETE CASCADE,
  from_state paa.coder_brief_authority_state,
  to_state paa.coder_brief_authority_state NOT NULL,
  transition_kind paa.coder_brief_authority_transition_kind NOT NULL,
  actor_role_id UUID REFERENCES paa.roles(role_id) ON DELETE SET NULL,
  actor_name TEXT,
  notes TEXT,
  evidence_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS coder_brief_authority_events_brief_idx
  ON paa.coder_brief_authority_events(coder_run_brief_id, created_at DESC);

CREATE INDEX IF NOT EXISTS coder_brief_authority_events_project_idx
  ON paa.coder_brief_authority_events(project_id, to_state, created_at DESC);

COMMIT;

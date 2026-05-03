-- Project for Autonomous Agents
-- Step 2 Postgres DDL: verification, acceptance, and run history
--
-- Prerequisite:
-- - 54-step1-postgres-ddl.sql
--
-- Scope:
-- - agents
-- - automation_runs
-- - verification_obligations
-- - evidence
-- - acceptance_events
--
-- This step adds the minimum durable verification and recovery truth.

BEGIN;

CREATE SCHEMA IF NOT EXISTS paa;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'agent_type') THEN
    CREATE TYPE paa.agent_type AS ENUM (
      'human',
      'automation',
      'service'
    );
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'automation_run_status') THEN
    CREATE TYPE paa.automation_run_status AS ENUM (
      'running',
      'completed',
      'failed',
      'blocked',
      'cancelled'
    );
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'verification_type') THEN
    CREATE TYPE paa.verification_type AS ENUM (
      'tooling',
      'test',
      'trace',
      'parity',
      'artifact',
      'qa_review',
      'architect_review',
      'manual_review'
    );
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'verification_status') THEN
    CREATE TYPE paa.verification_status AS ENUM (
      'required',
      'satisfied',
      'failed',
      'waived'
    );
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'evidence_result') THEN
    CREATE TYPE paa.evidence_result AS ENUM (
      'pass',
      'fail',
      'warning'
    );
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'acceptance_decision') THEN
    CREATE TYPE paa.acceptance_decision AS ENUM (
      'accepted',
      'rejected',
      'needs_changes',
      'blocked',
      'needs_human_review'
    );
  END IF;
END
$$;

CREATE TABLE IF NOT EXISTS paa.agents (
  agent_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES paa.projects(project_id) ON DELETE CASCADE,
  role_id UUID REFERENCES paa.roles(role_id) ON DELETE SET NULL,
  name TEXT NOT NULL,
  agent_type paa.agent_type NOT NULL,
  runtime_kind TEXT,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (project_id, name)
);

CREATE TABLE IF NOT EXISTS paa.automation_runs (
  automation_run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id UUID NOT NULL REFERENCES paa.agents(agent_id) ON DELETE CASCADE,
  work_item_id UUID REFERENCES paa.work_items(work_item_id) ON DELETE SET NULL,
  handoff_id UUID REFERENCES paa.handoffs(handoff_id) ON DELETE SET NULL,
  trigger_type TEXT,
  status paa.automation_run_status NOT NULL,
  started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  finished_at TIMESTAMPTZ,
  summary TEXT,
  artifacts_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS automation_runs_agent_idx
  ON paa.automation_runs(agent_id, started_at DESC);

CREATE INDEX IF NOT EXISTS automation_runs_work_item_idx
  ON paa.automation_runs(work_item_id);

CREATE INDEX IF NOT EXISTS automation_runs_status_idx
  ON paa.automation_runs(status, started_at DESC);

CREATE TABLE IF NOT EXISTS paa.verification_obligations (
  verification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES paa.projects(project_id) ON DELETE CASCADE,
  work_item_id UUID REFERENCES paa.work_items(work_item_id) ON DELETE CASCADE,
  verification_key TEXT NOT NULL,
  verification_type paa.verification_type NOT NULL,
  method TEXT NOT NULL,
  pass_criteria TEXT NOT NULL,
  required_for_acceptance BOOLEAN NOT NULL DEFAULT TRUE,
  status paa.verification_status NOT NULL DEFAULT 'required',
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (project_id, work_item_id, verification_key)
);

CREATE INDEX IF NOT EXISTS verification_obligations_work_item_idx
  ON paa.verification_obligations(work_item_id);

CREATE TABLE IF NOT EXISTS paa.evidence (
  evidence_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES paa.projects(project_id) ON DELETE CASCADE,
  work_item_id UUID NOT NULL REFERENCES paa.work_items(work_item_id) ON DELETE CASCADE,
  verification_id UUID REFERENCES paa.verification_obligations(verification_id) ON DELETE SET NULL,
  captured_by_agent_id UUID REFERENCES paa.agents(agent_id) ON DELETE SET NULL,
  automation_run_id UUID REFERENCES paa.automation_runs(automation_run_id) ON DELETE SET NULL,
  result paa.evidence_result NOT NULL,
  summary TEXT NOT NULL,
  artifact_location TEXT,
  artifact_hash TEXT,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  captured_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS evidence_work_item_idx
  ON paa.evidence(work_item_id, captured_at DESC);

CREATE INDEX IF NOT EXISTS evidence_verification_idx
  ON paa.evidence(verification_id, captured_at DESC)
  WHERE verification_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS evidence_result_idx
  ON paa.evidence(result, captured_at DESC);

CREATE TABLE IF NOT EXISTS paa.acceptance_events (
  acceptance_event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES paa.projects(project_id) ON DELETE CASCADE,
  work_item_id UUID NOT NULL REFERENCES paa.work_items(work_item_id) ON DELETE CASCADE,
  handoff_id UUID REFERENCES paa.handoffs(handoff_id) ON DELETE SET NULL,
  accepted_by_agent_id UUID REFERENCES paa.agents(agent_id) ON DELETE SET NULL,
  accepted_by_role_id UUID REFERENCES paa.roles(role_id) ON DELETE SET NULL,
  decision paa.acceptance_decision NOT NULL,
  notes TEXT,
  merge_commit_sha TEXT,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS acceptance_events_work_item_idx
  ON paa.acceptance_events(work_item_id, created_at DESC);

CREATE INDEX IF NOT EXISTS acceptance_events_decision_idx
  ON paa.acceptance_events(decision, created_at DESC);

COMMIT;

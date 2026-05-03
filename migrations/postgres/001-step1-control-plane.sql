-- Project for Autonomous Agents
-- Step 1 Postgres DDL: durable workflow/control plane only
--
-- Scope:
-- - projects
-- - roles
-- - authority_versions
-- - work_items
-- - execution_records
-- - handoffs
-- - queue_messages
--
-- This intentionally stops short of the full project knowledge graph.
-- The goal is to make the current autonomous loop durable before
-- normalizing source statements, requirements, spec fragments, and
-- implementation targets into first-class tables.

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS paa;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'project_status') THEN
    CREATE TYPE paa.project_status AS ENUM (
      'active',
      'paused',
      'archived'
    );
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'role_category') THEN
    CREATE TYPE paa.role_category AS ENUM (
      'architecture',
      'engineering',
      'verification',
      'operations',
      'coordination'
    );
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'authority_status') THEN
    CREATE TYPE paa.authority_status AS ENUM (
      'draft',
      'published',
      'superseded',
      'blocked'
    );
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'work_item_status') THEN
    CREATE TYPE paa.work_item_status AS ENUM (
      'draft',
      'authorized',
      'in_progress',
      'ready_for_verification',
      'in_qa',
      'ready_for_acceptance',
      'accepted',
      'rejected',
      'superseded',
      'deferred',
      'blocked'
    );
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'execution_record_status') THEN
    CREATE TYPE paa.execution_record_status AS ENUM (
      'open',
      'draft',
      'ready_for_review',
      'merged',
      'closed',
      'superseded',
      'blocked'
    );
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'handoff_status') THEN
    CREATE TYPE paa.handoff_status AS ENUM (
      'pending',
      'claimed',
      'completed',
      'blocked',
      'requeued',
      'abandoned'
    );
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'queue_message_status') THEN
    CREATE TYPE paa.queue_message_status AS ENUM (
      'prepared',
      'sent',
      'claimed',
      'acknowledged',
      'requeued',
      'dead_lettered',
      'blocked'
    );
  END IF;
END
$$;

CREATE TABLE IF NOT EXISTS paa.projects (
  project_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  repo_url TEXT,
  execution_surface TEXT NOT NULL DEFAULT 'github',
  status paa.project_status NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS paa.roles (
  role_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES paa.projects(project_id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  category paa.role_category NOT NULL,
  description TEXT,
  is_human_capable BOOLEAN NOT NULL DEFAULT TRUE,
  is_automation_capable BOOLEAN NOT NULL DEFAULT TRUE,
  sort_order INTEGER NOT NULL DEFAULT 100,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (project_id, name)
);

CREATE TABLE IF NOT EXISTS paa.authority_versions (
  authority_version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES paa.projects(project_id) ON DELETE CASCADE,
  version_label TEXT NOT NULL,
  source_commit TEXT,
  published_from_ref TEXT,
  manifest_path TEXT,
  published_at TIMESTAMPTZ,
  status paa.authority_status NOT NULL DEFAULT 'draft',
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (project_id, version_label)
);

CREATE TABLE IF NOT EXISTS paa.work_items (
  work_item_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES paa.projects(project_id) ON DELETE CASCADE,
  authority_version_id UUID REFERENCES paa.authority_versions(authority_version_id) ON DELETE SET NULL,
  title TEXT NOT NULL,
  status paa.work_item_status NOT NULL DEFAULT 'draft',
  merge_policy TEXT,
  requires_qa BOOLEAN NOT NULL DEFAULT FALSE,
  issue_number INTEGER,
  implementation_target_ref TEXT,
  spec_fragment_ref TEXT,
  domain_ref JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT work_items_issue_number_positive CHECK (issue_number IS NULL OR issue_number > 0)
);

CREATE UNIQUE INDEX IF NOT EXISTS work_items_project_issue_uidx
  ON paa.work_items(project_id, issue_number)
  WHERE issue_number IS NOT NULL;

CREATE INDEX IF NOT EXISTS work_items_project_status_idx
  ON paa.work_items(project_id, status);

CREATE INDEX IF NOT EXISTS work_items_authority_idx
  ON paa.work_items(authority_version_id);

CREATE TABLE IF NOT EXISTS paa.execution_records (
  execution_record_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  work_item_id UUID NOT NULL REFERENCES paa.work_items(work_item_id) ON DELETE CASCADE,
  system_type TEXT NOT NULL DEFAULT 'github',
  issue_number INTEGER,
  pr_number INTEGER,
  branch_name TEXT,
  commit_sha TEXT,
  url TEXT,
  status paa.execution_record_status NOT NULL DEFAULT 'open',
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT execution_records_issue_positive CHECK (issue_number IS NULL OR issue_number > 0),
  CONSTRAINT execution_records_pr_positive CHECK (pr_number IS NULL OR pr_number > 0)
);

CREATE INDEX IF NOT EXISTS execution_records_work_item_idx
  ON paa.execution_records(work_item_id);

CREATE INDEX IF NOT EXISTS execution_records_issue_idx
  ON paa.execution_records(issue_number)
  WHERE issue_number IS NOT NULL;

CREATE INDEX IF NOT EXISTS execution_records_pr_idx
  ON paa.execution_records(pr_number)
  WHERE pr_number IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS execution_records_github_pr_uidx
  ON paa.execution_records(system_type, pr_number)
  WHERE system_type = 'github' AND pr_number IS NOT NULL;

CREATE TABLE IF NOT EXISTS paa.handoffs (
  handoff_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES paa.projects(project_id) ON DELETE CASCADE,
  work_item_id UUID NOT NULL REFERENCES paa.work_items(work_item_id) ON DELETE CASCADE,
  from_role_id UUID NOT NULL REFERENCES paa.roles(role_id) ON DELETE RESTRICT,
  to_role_id UUID NOT NULL REFERENCES paa.roles(role_id) ON DELETE RESTRICT,
  handoff_type TEXT NOT NULL,
  status paa.handoff_status NOT NULL DEFAULT 'pending',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  claimed_at TIMESTAMPTZ,
  acknowledged_at TIMESTAMPTZ,
  closed_at TIMESTAMPTZ,
  notes TEXT
);

CREATE INDEX IF NOT EXISTS handoffs_project_status_idx
  ON paa.handoffs(project_id, status);

CREATE INDEX IF NOT EXISTS handoffs_work_item_idx
  ON paa.handoffs(work_item_id);

CREATE INDEX IF NOT EXISTS handoffs_route_idx
  ON paa.handoffs(from_role_id, to_role_id, status);

CREATE TABLE IF NOT EXISTS paa.queue_messages (
  queue_message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  handoff_id UUID NOT NULL REFERENCES paa.handoffs(handoff_id) ON DELETE CASCADE,
  queue_name TEXT NOT NULL,
  schema_type TEXT NOT NULL,
  message_id_external TEXT,
  correlation_key TEXT,
  payload_json JSONB NOT NULL,
  status paa.queue_message_status NOT NULL DEFAULT 'prepared',
  sent_at TIMESTAMPTZ,
  claimed_at TIMESTAMPTZ,
  acknowledged_at TIMESTAMPTZ,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS queue_messages_external_uidx
  ON paa.queue_messages(message_id_external)
  WHERE message_id_external IS NOT NULL;

CREATE INDEX IF NOT EXISTS queue_messages_handoff_idx
  ON paa.queue_messages(handoff_id);

CREATE INDEX IF NOT EXISTS queue_messages_queue_status_idx
  ON paa.queue_messages(queue_name, status);

CREATE INDEX IF NOT EXISTS queue_messages_correlation_idx
  ON paa.queue_messages(correlation_key)
  WHERE correlation_key IS NOT NULL;

COMMIT;

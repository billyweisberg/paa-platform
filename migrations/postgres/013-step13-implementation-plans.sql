-- Project for Autonomous Agents
-- Step 13 Postgres DDL: implementation-plan family for Project Design
--
-- Purpose:
-- - add DB-primary project-design truth between design packages and coder briefs
-- - model authoritative implementation-plan activities
-- - model activity dependencies and verification surfaces
-- - bind coder briefs back to the implementation plan they were derived from
--
-- Prerequisites:
-- - 001-step1-control-plane.sql
-- - 002-step2-verification-recovery.sql
-- - 003-step3-knowledge-graph.sql
-- - 004-step4-coder-briefs.sql
-- - 005-step5-design-packages-and-sequencing.sql
-- - 008-step8-component-element-realizations.sql
-- - 010-step10-coder-brief-authority-lifecycle.sql

BEGIN;

CREATE SCHEMA IF NOT EXISTS paa;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE t.typname = 'implementation_plan_status' AND n.nspname = 'paa'
  ) THEN
    CREATE TYPE paa.implementation_plan_status AS ENUM (
      'draft',
      'under_review',
      'approved_for_briefing',
      'active_execution',
      'completed',
      'superseded',
      'rejected'
    );
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE t.typname = 'implementation_plan_authority_state' AND n.nspname = 'paa'
  ) THEN
    CREATE TYPE paa.implementation_plan_authority_state AS ENUM (
      'draft_plan',
      'approved_plan',
      'superseded_plan',
      'rejected_plan'
    );
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE t.typname = 'implementation_plan_activity_kind' AND n.nspname = 'paa'
  ) THEN
    CREATE TYPE paa.implementation_plan_activity_kind AS ENUM (
      'artifact_construction',
      'dependency_wiring',
      'configuration',
      'verification',
      'integration',
      'delivery_preparation',
      'documentation'
    );
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE t.typname = 'implementation_plan_activity_state' AND n.nspname = 'paa'
  ) THEN
    CREATE TYPE paa.implementation_plan_activity_state AS ENUM (
      'planned',
      'ready',
      'active',
      'completed',
      'blocked',
      'skipped',
      'superseded'
    );
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE t.typname = 'implementation_plan_verification_status' AND n.nspname = 'paa'
  ) THEN
    CREATE TYPE paa.implementation_plan_verification_status AS ENUM (
      'planned',
      'ready',
      'active',
      'passed',
      'failed',
      'waived'
    );
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE t.typname = 'implementation_plan_authority_transition_kind' AND n.nspname = 'paa'
  ) THEN
    CREATE TYPE paa.implementation_plan_authority_transition_kind AS ENUM (
      'derive_plan',
      'approve_plan',
      'activate_plan',
      'complete_plan',
      'supersede_plan',
      'reject_plan',
      'reopen_plan'
    );
  END IF;
END
$$;

CREATE TABLE IF NOT EXISTS paa.implementation_plans (
  implementation_plan_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES paa.projects(project_id) ON DELETE CASCADE,
  work_item_id UUID NOT NULL REFERENCES paa.work_items(work_item_id) ON DELETE CASCADE,
  design_package_id UUID NOT NULL REFERENCES paa.design_packages(design_package_id) ON DELETE CASCADE,
  spec_fragment_id UUID REFERENCES paa.spec_fragments(spec_fragment_id) ON DELETE SET NULL,
  implementation_target_id UUID NOT NULL REFERENCES paa.implementation_targets(implementation_target_id) ON DELETE RESTRICT,
  authority_version_id UUID REFERENCES paa.authority_versions(authority_version_id) ON DELETE SET NULL,
  primary_component_id UUID REFERENCES paa.components(component_id) ON DELETE SET NULL,
  plan_id_external TEXT,
  schema_version TEXT NOT NULL,
  consumer_context_key TEXT NOT NULL,
  plan_title TEXT NOT NULL,
  plan_kind TEXT NOT NULL DEFAULT 'implementation_slice',
  status paa.implementation_plan_status NOT NULL DEFAULT 'draft',
  authority_state paa.implementation_plan_authority_state NOT NULL DEFAULT 'draft_plan',
  authority_state_updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  plan_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  build_sequence_json JSONB NOT NULL DEFAULT '[]'::jsonb,
  touch_surfaces_json JSONB NOT NULL DEFAULT '[]'::jsonb,
  protected_constraints_json JSONB NOT NULL DEFAULT '[]'::jsonb,
  verification_plan_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  provenance_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_by_role_id UUID REFERENCES paa.roles(role_id) ON DELETE SET NULL,
  created_by_agent_id UUID REFERENCES paa.agents(agent_id) ON DELETE SET NULL,
  approved_at TIMESTAMPTZ,
  activated_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (project_id, plan_id_external),
  UNIQUE (design_package_id, consumer_context_key)
);

CREATE INDEX IF NOT EXISTS implementation_plans_project_status_idx
  ON paa.implementation_plans(project_id, status, created_at DESC);

CREATE INDEX IF NOT EXISTS implementation_plans_work_item_idx
  ON paa.implementation_plans(work_item_id, status, created_at DESC);

CREATE INDEX IF NOT EXISTS implementation_plans_component_idx
  ON paa.implementation_plans(primary_component_id, status, created_at DESC);

CREATE TABLE IF NOT EXISTS paa.implementation_plan_activities (
  implementation_plan_activity_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  implementation_plan_id UUID NOT NULL REFERENCES paa.implementation_plans(implementation_plan_id) ON DELETE CASCADE,
  component_element_id UUID REFERENCES paa.component_elements(component_element_id) ON DELETE SET NULL,
  component_element_realization_id UUID REFERENCES paa.component_element_realizations(component_element_realization_id) ON DELETE SET NULL,
  assigned_role_id UUID REFERENCES paa.roles(role_id) ON DELETE SET NULL,
  activity_key TEXT NOT NULL,
  activity_title TEXT NOT NULL,
  activity_kind paa.implementation_plan_activity_kind NOT NULL,
  activity_state paa.implementation_plan_activity_state NOT NULL DEFAULT 'planned',
  sequence_order INTEGER NOT NULL DEFAULT 100,
  target_path TEXT,
  target_module TEXT,
  planned_artifact_type_key TEXT,
  blocking_reason TEXT,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (implementation_plan_id, activity_key)
);

CREATE INDEX IF NOT EXISTS implementation_plan_activities_plan_state_idx
  ON paa.implementation_plan_activities(implementation_plan_id, activity_state, sequence_order);

CREATE INDEX IF NOT EXISTS implementation_plan_activities_element_idx
  ON paa.implementation_plan_activities(component_element_id, activity_state, sequence_order);

CREATE TABLE IF NOT EXISTS paa.implementation_plan_activity_dependencies (
  implementation_plan_activity_dependency_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  implementation_plan_id UUID NOT NULL REFERENCES paa.implementation_plans(implementation_plan_id) ON DELETE CASCADE,
  predecessor_activity_id UUID NOT NULL REFERENCES paa.implementation_plan_activities(implementation_plan_activity_id) ON DELETE CASCADE,
  successor_activity_id UUID NOT NULL REFERENCES paa.implementation_plan_activities(implementation_plan_activity_id) ON DELETE CASCADE,
  sequencing_requirement paa.sequencing_requirement NOT NULL DEFAULT 'must_precede',
  dependency_strength paa.dependency_strength NOT NULL DEFAULT 'hard',
  notes TEXT,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (implementation_plan_id, predecessor_activity_id, successor_activity_id),
  CONSTRAINT implementation_plan_activity_dependencies_no_self
    CHECK (predecessor_activity_id <> successor_activity_id)
);

CREATE INDEX IF NOT EXISTS implementation_plan_activity_dependencies_plan_idx
  ON paa.implementation_plan_activity_dependencies(implementation_plan_id, successor_activity_id, predecessor_activity_id);

CREATE TABLE IF NOT EXISTS paa.implementation_plan_artifacts (
  implementation_plan_artifact_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  implementation_plan_id UUID NOT NULL REFERENCES paa.implementation_plans(implementation_plan_id) ON DELETE CASCADE,
  implementation_plan_activity_id UUID REFERENCES paa.implementation_plan_activities(implementation_plan_activity_id) ON DELETE SET NULL,
  component_element_id UUID REFERENCES paa.component_elements(component_element_id) ON DELETE SET NULL,
  component_element_realization_id UUID REFERENCES paa.component_element_realizations(component_element_realization_id) ON DELETE SET NULL,
  artifact_type_key TEXT NOT NULL,
  artifact_title TEXT NOT NULL,
  target_path TEXT,
  target_module TEXT,
  status paa.implementation_plan_activity_state NOT NULL DEFAULT 'planned',
  sequence_order INTEGER NOT NULL DEFAULT 100,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS implementation_plan_artifacts_plan_idx
  ON paa.implementation_plan_artifacts(implementation_plan_id, status, sequence_order);

CREATE TABLE IF NOT EXISTS paa.implementation_plan_verification_surfaces (
  implementation_plan_verification_surface_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  implementation_plan_id UUID NOT NULL REFERENCES paa.implementation_plans(implementation_plan_id) ON DELETE CASCADE,
  implementation_plan_activity_id UUID REFERENCES paa.implementation_plan_activities(implementation_plan_activity_id) ON DELETE SET NULL,
  verification_obligation_id UUID REFERENCES paa.verification_obligations(verification_id) ON DELETE SET NULL,
  surface_kind TEXT NOT NULL,
  surface_ref TEXT,
  required BOOLEAN NOT NULL DEFAULT true,
  sequence_order INTEGER NOT NULL DEFAULT 100,
  status paa.implementation_plan_verification_status NOT NULL DEFAULT 'planned',
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (implementation_plan_id, surface_kind, surface_ref)
);

CREATE INDEX IF NOT EXISTS implementation_plan_verification_surfaces_plan_idx
  ON paa.implementation_plan_verification_surfaces(implementation_plan_id, status, sequence_order);

CREATE TABLE IF NOT EXISTS paa.implementation_plan_authority_events (
  implementation_plan_authority_event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES paa.projects(project_id) ON DELETE CASCADE,
  work_item_id UUID REFERENCES paa.work_items(work_item_id) ON DELETE SET NULL,
  implementation_plan_id UUID NOT NULL REFERENCES paa.implementation_plans(implementation_plan_id) ON DELETE CASCADE,
  from_state paa.implementation_plan_authority_state,
  to_state paa.implementation_plan_authority_state NOT NULL,
  transition_kind paa.implementation_plan_authority_transition_kind NOT NULL,
  actor_role_id UUID REFERENCES paa.roles(role_id) ON DELETE SET NULL,
  actor_name TEXT,
  notes TEXT,
  evidence_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS implementation_plan_authority_events_plan_idx
  ON paa.implementation_plan_authority_events(implementation_plan_id, created_at DESC);

CREATE INDEX IF NOT EXISTS implementation_plan_authority_events_project_idx
  ON paa.implementation_plan_authority_events(project_id, to_state, created_at DESC);

ALTER TABLE paa.coder_run_briefs
  ADD COLUMN IF NOT EXISTS implementation_plan_id UUID REFERENCES paa.implementation_plans(implementation_plan_id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS coder_run_briefs_implementation_plan_idx
  ON paa.coder_run_briefs(implementation_plan_id, authority_state, created_at DESC)
  WHERE implementation_plan_id IS NOT NULL;

COMMIT;

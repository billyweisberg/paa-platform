#!/usr/bin/env python3
"""Install the minimal methodology execution persistence schema for PAA local runtime."""

from __future__ import annotations

from paa_core.db import run_psql


SQL = r"""
CREATE SCHEMA IF NOT EXISTS paa;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE n.nspname = 'paa' AND t.typname = 'methodology_lane'
  ) THEN
    CREATE TYPE paa.methodology_lane AS ENUM (
      'authority_derivation',
      'component_realization',
      'slice_execution',
      'runtime_execution',
      'acceptance_closeout'
    );
  END IF;
END
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE n.nspname = 'paa' AND t.typname = 'methodology_stage'
  ) THEN
    CREATE TYPE paa.methodology_stage AS ENUM (
      'component_design',
      'slice_execution',
      'reconcile_component_plan_progress',
      'derive_next_activity_bundle',
      'techlead_worker_dispatch',
      'dev_execution',
      'qa_verification',
      'acceptance_closeout'
    );
  END IF;
END
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE n.nspname = 'paa' AND t.typname = 'methodology_execution_status'
  ) THEN
    CREATE TYPE paa.methodology_execution_status AS ENUM (
      'ready',
      'active',
      'blocked',
      'completed'
    );
  END IF;
END
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE n.nspname = 'paa' AND t.typname = 'methodology_transition_kind'
  ) THEN
    CREATE TYPE paa.methodology_transition_kind AS ENUM (
      'created',
      'automated_progression',
      'manual_update',
      'worker_dispatch',
      'worker_result_received',
      'qa_result_received'
    );
  END IF;
END
$$;

CREATE TABLE IF NOT EXISTS paa.methodology_executions (
  methodology_execution_id uuid PRIMARY KEY,
  project_id uuid NOT NULL,
  work_item_id uuid NULL,
  lane paa.methodology_lane NOT NULL,
  stage paa.methodology_stage NOT NULL,
  step text NOT NULL,
  status paa.methodology_execution_status NOT NULL,
  current_owner_role text NOT NULL,
  next_action_key text NULL,
  blocked_reason text NULL,
  component_id uuid NULL,
  design_package_id uuid NULL,
  implementation_plan_id uuid NULL,
  coder_run_brief_id uuid NULL,
  packet_id uuid NULL,
  workflow_state_id uuid NULL,
  active_authority_ref text NULL,
  active_artifact_ref text NULL,
  metadata_json jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_methodology_executions_project_work_item_component
  ON paa.methodology_executions (project_id, work_item_id, component_id);

CREATE TABLE IF NOT EXISTS paa.methodology_execution_events (
  methodology_execution_event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  methodology_execution_id uuid NOT NULL,
  from_lane paa.methodology_lane NULL,
  to_lane paa.methodology_lane NOT NULL,
  from_stage paa.methodology_stage NULL,
  to_stage paa.methodology_stage NOT NULL,
  from_step text NULL,
  to_step text NOT NULL,
  from_status paa.methodology_execution_status NULL,
  to_status paa.methodology_execution_status NOT NULL,
  transition_kind paa.methodology_transition_kind NOT NULL,
  actor_role_id text NULL,
  actor_name text NULL,
  notes text NULL,
  evidence_json jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_methodology_execution_events_execution
  ON paa.methodology_execution_events (methodology_execution_id, created_at);

CREATE TABLE IF NOT EXISTS paa.methodology_execution_bindings (
  methodology_execution_binding_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  methodology_execution_id uuid NOT NULL,
  binding_kind text NOT NULL,
  bound_record_id uuid NULL,
  bound_record_key text NULL,
  bound_record_ref text NULL,
  is_primary boolean NOT NULL DEFAULT false,
  notes text NULL,
  metadata_json jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_methodology_execution_bindings_execution
  ON paa.methodology_execution_bindings (methodology_execution_id, binding_kind, is_primary DESC);
"""


def main() -> int:
    run_psql(SQL)
    print('ok')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

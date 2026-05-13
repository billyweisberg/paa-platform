-- Project for Autonomous Agents
-- Step 6 Postgres DDL: workflow state, execution-package registration,
-- runtime event normalization, and component normalization statuses
--
-- Prerequisites:
-- - 001-step1-control-plane.sql
-- - 002-step2-verification-recovery.sql
-- - 003-step3-knowledge-graph.sql
-- - 004-step4-coder-briefs.sql
-- - 005-step5-design-packages-and-sequencing.sql

BEGIN;

CREATE SCHEMA IF NOT EXISTS paa;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE t.typname = 'workflow_stage' AND n.nspname = 'paa'
  ) THEN
    CREATE TYPE paa.workflow_stage AS ENUM (
      'authorized_not_assigned',
      'delivery_review_pending',
      'delivery_review_in_progress',
      'techlead_delivery_review_pending',
      'worker_assignment_pending',
      'worker_execution_in_progress',
      'techlead_worker_review_pending',
      'qa_assignment_pending',
      'qa_execution_in_progress',
      'techlead_qa_review_pending',
      'acceptance_in_progress',
      'techlead_decision_recorded',
      'blocked',
      'superseded',
      'closed'
    );
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE t.typname = 'lineage_state' AND n.nspname = 'paa'
  ) THEN
    CREATE TYPE paa.lineage_state AS ENUM (
      'not_started',
      'active',
      'awaiting_result',
      'awaiting_acceptance',
      'closed',
      'superseded'
    );
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE t.typname = 'workflow_state_consistency' AND n.nspname = 'paa'
  ) THEN
    CREATE TYPE paa.workflow_state_consistency AS ENUM (
      'consistent',
      'missing_upstream_context',
      'missing_transport_record',
      'missing_execution_record',
      'conflicting_transition_evidence',
      'manual_repair_required'
    );
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE t.typname = 'workflow_terminal_decision' AND n.nspname = 'paa'
  ) THEN
    CREATE TYPE paa.workflow_terminal_decision AS ENUM (
      'none',
      'accepted',
      'rejected',
      'needs_changes',
      'blocked',
      'needs_human_review',
      'superseded'
    );
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE t.typname = 'workflow_transition_type' AND n.nspname = 'paa'
  ) THEN
    CREATE TYPE paa.workflow_transition_type AS ENUM (
      'assignment_emitted',
      'assignment_claimed',
      'delivery_review_returned',
      'worker_result_returned',
      'qa_result_returned',
      'assignment_advanced',
      'accept_and_merge_completed',
      'decision_recorded',
      'slice_closed',
      'slice_blocked',
      'slice_superseded',
      'manual_repair'
    );
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE t.typname = 'workflow_transition_status' AND n.nspname = 'paa'
  ) THEN
    CREATE TYPE paa.workflow_transition_status AS ENUM (
      'applied',
      'failed',
      'compensated',
      'cancelled'
    );
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE t.typname = 'queue_claim_status' AND n.nspname = 'paa'
  ) THEN
    CREATE TYPE paa.queue_claim_status AS ENUM (
      'active',
      'released',
      'expired',
      'acked',
      'abandoned',
      'superseded'
    );
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE t.typname = 'queue_ack_outcome' AND n.nspname = 'paa'
  ) THEN
    CREATE TYPE paa.queue_ack_outcome AS ENUM (
      'none',
      'acked_source_message',
      'ack_failed',
      'not_required'
    );
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE t.typname = 'queue_claim_attempt_source' AND n.nspname = 'paa'
  ) THEN
    CREATE TYPE paa.queue_claim_attempt_source AS ENUM (
      'role_preflight',
      'role_return_closeout',
      'techlead_advance_closeout',
      'repair_tool',
      'manual_operator_action'
    );
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE t.typname = 'execution_surface_type' AND n.nspname = 'paa'
  ) THEN
    CREATE TYPE paa.execution_surface_type AS ENUM (
      'consumer_repo_runtime',
      'repo_local_runtime',
      'test_fixture_runtime',
      'repair_runtime'
    );
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE t.typname = 'execution_package_install_status' AND n.nspname = 'paa'
  ) THEN
    CREATE TYPE paa.execution_package_install_status AS ENUM (
      'active',
      'superseded',
      'removed',
      'failed',
      'repaired'
    );
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE t.typname = 'execution_package_install_source' AND n.nspname = 'paa'
  ) THEN
    CREATE TYPE paa.execution_package_install_source AS ENUM (
      'published_authority_package',
      'published_authority_package_with_overlay',
      'pilot_fixture_overlay_install',
      'manual_repair_install'
    );
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE t.typname = 'execution_package_overlay_type' AND n.nspname = 'paa'
  ) THEN
    CREATE TYPE paa.execution_package_overlay_type AS ENUM (
      'pilot_fixture',
      'task_override',
      'authority_patch',
      'repair_overlay'
    );
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE t.typname = 'execution_package_overlay_status' AND n.nspname = 'paa'
  ) THEN
    CREATE TYPE paa.execution_package_overlay_status AS ENUM (
      'active',
      'superseded',
      'removed',
      'failed',
      'repaired'
    );
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE t.typname = 'execution_package_overlay_source' AND n.nspname = 'paa'
  ) THEN
    CREATE TYPE paa.execution_package_overlay_source AS ENUM (
      'published_package_overlay',
      'pilot_fixture_overlay_install',
      'manual_repair_overlay'
    );
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE t.typname = 'transition_input_type' AND n.nspname = 'paa'
  ) THEN
    CREATE TYPE paa.transition_input_type AS ENUM (
      'assignment_input',
      'role_result_input',
      'delivery_review_input',
      'qa_verification_input',
      'decision_input',
      'repair_input'
    );
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE t.typname = 'transition_input_source_surface' AND n.nspname = 'paa'
  ) THEN
    CREATE TYPE paa.transition_input_source_surface AS ENUM (
      'queue_packet',
      'runtime_report_artifact',
      'generated_runtime_input',
      'repair_tool'
    );
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE t.typname = 'automation_run_event_type' AND n.nspname = 'paa'
  ) THEN
    CREATE TYPE paa.automation_run_event_type AS ENUM (
      'run_started',
      'preflight_completed',
      'claim_acquired',
      'worktree_prepared',
      'execution_started',
      'validation_completed',
      'result_compiled',
      'result_sent',
      'source_packet_acked',
      'transition_applied',
      'merge_completed',
      'issue_closed',
      'run_blocked',
      'run_failed',
      'run_completed',
      'manual_repair_event'
    );
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE t.typname = 'automation_run_event_status' AND n.nspname = 'paa'
  ) THEN
    CREATE TYPE paa.automation_run_event_status AS ENUM (
      'info',
      'success',
      'warning',
      'failure',
      'compensated'
    );
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE t.typname = 'automation_run_event_phase' AND n.nspname = 'paa'
  ) THEN
    CREATE TYPE paa.automation_run_event_phase AS ENUM (
      'preflight',
      'claim',
      'prepare',
      'execute',
      'validate',
      'return',
      'closeout',
      'repair'
    );
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE t.typname = 'component_normalization_status' AND n.nspname = 'paa'
  ) THEN
    CREATE TYPE paa.component_normalization_status AS ENUM (
      'normalized',
      'component_not_yet_normalized',
      'artifact_only_transitional',
      'multi_component_slice',
      'repair_required'
    );
  END IF;
END
$$;

CREATE TABLE IF NOT EXISTS paa.workflow_states (
  workflow_state_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES paa.projects(project_id) ON DELETE CASCADE,
  work_item_id UUID NOT NULL REFERENCES paa.work_items(work_item_id) ON DELETE CASCADE,
  authority_version_id UUID REFERENCES paa.authority_versions(authority_version_id) ON DELETE SET NULL,
  design_package_id UUID REFERENCES paa.design_packages(design_package_id) ON DELETE SET NULL,
  coder_run_brief_id UUID REFERENCES paa.coder_run_briefs(coder_run_brief_id) ON DELETE SET NULL,
  workflow_stage paa.workflow_stage NOT NULL,
  current_owner_role_id UUID REFERENCES paa.roles(role_id) ON DELETE RESTRICT,
  lineage_state paa.lineage_state NOT NULL,
  blocking_reason_code TEXT,
  blocking_reason_text TEXT,
  terminal_decision paa.workflow_terminal_decision NOT NULL DEFAULT 'none',
  state_consistency paa.workflow_state_consistency NOT NULL DEFAULT 'consistent',
  current_issue_number INTEGER,
  current_pr_number INTEGER,
  canonical_branch TEXT,
  active_role_branch TEXT,
  active_handoff_id UUID REFERENCES paa.handoffs(handoff_id) ON DELETE SET NULL,
  active_queue_message_id UUID REFERENCES paa.queue_messages(queue_message_id) ON DELETE SET NULL,
  active_message_id_external TEXT,
  active_assignment_role_id UUID REFERENCES paa.roles(role_id) ON DELETE SET NULL,
  active_result_role_id UUID REFERENCES paa.roles(role_id) ON DELETE SET NULL,
  active_queue_claim_id UUID,
  state_entered_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_transition_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  closed_at TIMESTAMPTZ,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT workflow_states_issue_positive CHECK (current_issue_number IS NULL OR current_issue_number > 0),
  CONSTRAINT workflow_states_pr_positive CHECK (current_pr_number IS NULL OR current_pr_number > 0),
  CONSTRAINT workflow_states_closed_requires_decision CHECK (
    workflow_stage <> 'closed' OR (closed_at IS NOT NULL AND terminal_decision <> 'none')
  ),
  CONSTRAINT workflow_states_superseded_requires_lineage CHECK (
    workflow_stage <> 'superseded' OR lineage_state = 'superseded'
  ),
  UNIQUE (work_item_id)
);

CREATE INDEX IF NOT EXISTS workflow_states_project_stage_idx
  ON paa.workflow_states(project_id, workflow_stage, last_transition_at DESC);

CREATE INDEX IF NOT EXISTS workflow_states_owner_idx
  ON paa.workflow_states(current_owner_role_id, workflow_stage, last_transition_at DESC)
  WHERE current_owner_role_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS workflow_states_design_package_idx
  ON paa.workflow_states(design_package_id)
  WHERE design_package_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS workflow_states_brief_idx
  ON paa.workflow_states(coder_run_brief_id)
  WHERE coder_run_brief_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS paa.workflow_transitions (
  workflow_transition_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  workflow_state_id UUID NOT NULL REFERENCES paa.workflow_states(workflow_state_id) ON DELETE CASCADE,
  project_id UUID NOT NULL REFERENCES paa.projects(project_id) ON DELETE CASCADE,
  work_item_id UUID NOT NULL REFERENCES paa.work_items(work_item_id) ON DELETE CASCADE,
  transition_type paa.workflow_transition_type NOT NULL,
  transition_status paa.workflow_transition_status NOT NULL,
  from_workflow_stage paa.workflow_stage,
  to_workflow_stage paa.workflow_stage,
  from_owner_role_id UUID REFERENCES paa.roles(role_id) ON DELETE SET NULL,
  to_owner_role_id UUID REFERENCES paa.roles(role_id) ON DELETE SET NULL,
  reason_code TEXT,
  reason_text TEXT,
  source_handoff_id UUID REFERENCES paa.handoffs(handoff_id) ON DELETE SET NULL,
  source_queue_message_id UUID REFERENCES paa.queue_messages(queue_message_id) ON DELETE SET NULL,
  source_queue_claim_id UUID,
  source_message_id_external TEXT,
  source_packet_schema_type TEXT,
  source_role_id UUID REFERENCES paa.roles(role_id) ON DELETE SET NULL,
  source_transition_input_id UUID,
  result_handoff_id UUID REFERENCES paa.handoffs(handoff_id) ON DELETE SET NULL,
  result_queue_message_id UUID REFERENCES paa.queue_messages(queue_message_id) ON DELETE SET NULL,
  result_queue_claim_id UUID,
  result_message_id_external TEXT,
  result_packet_schema_type TEXT,
  result_role_id UUID REFERENCES paa.roles(role_id) ON DELETE SET NULL,
  performed_by_role_id UUID REFERENCES paa.roles(role_id) ON DELETE SET NULL,
  performed_by_agent_id UUID REFERENCES paa.agents(agent_id) ON DELETE SET NULL,
  automation_run_id UUID REFERENCES paa.automation_runs(automation_run_id) ON DELETE SET NULL,
  error_code TEXT,
  error_details TEXT,
  transition_requested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  transition_applied_at TIMESTAMPTZ,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT workflow_transitions_applied_requires_states CHECK (
    transition_status <> 'applied' OR (from_workflow_stage IS NOT NULL AND to_workflow_stage IS NOT NULL)
  ),
  CONSTRAINT workflow_transitions_manual_repair_requires_reason CHECK (
    transition_type <> 'manual_repair' OR reason_text IS NOT NULL
  )
);

CREATE INDEX IF NOT EXISTS workflow_transitions_state_idx
  ON paa.workflow_transitions(workflow_state_id, transition_applied_at DESC, created_at DESC);

CREATE INDEX IF NOT EXISTS workflow_transitions_work_item_idx
  ON paa.workflow_transitions(work_item_id, transition_applied_at DESC, created_at DESC);

CREATE INDEX IF NOT EXISTS workflow_transitions_type_idx
  ON paa.workflow_transitions(transition_type, transition_status, transition_applied_at DESC);

CREATE TABLE IF NOT EXISTS paa.queue_claims (
  queue_claim_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  queue_message_id UUID NOT NULL REFERENCES paa.queue_messages(queue_message_id) ON DELETE CASCADE,
  handoff_id UUID REFERENCES paa.handoffs(handoff_id) ON DELETE SET NULL,
  project_id UUID NOT NULL REFERENCES paa.projects(project_id) ON DELETE CASCADE,
  work_item_id UUID NOT NULL REFERENCES paa.work_items(work_item_id) ON DELETE CASCADE,
  claimed_by_role_id UUID REFERENCES paa.roles(role_id) ON DELETE SET NULL,
  claimed_by_agent_id UUID REFERENCES paa.agents(agent_id) ON DELETE SET NULL,
  claim_attempt_source paa.queue_claim_attempt_source NOT NULL,
  claim_status paa.queue_claim_status NOT NULL,
  ack_outcome paa.queue_ack_outcome NOT NULL DEFAULT 'none',
  release_reason_code TEXT,
  release_reason_text TEXT,
  claimed_at TIMESTAMPTZ,
  lease_expires_at TIMESTAMPTZ,
  released_at TIMESTAMPTZ,
  acked_at TIMESTAMPTZ,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT queue_claims_active_requires_claimant CHECK (
    claim_status <> 'active' OR (claimed_at IS NOT NULL AND claimed_by_role_id IS NOT NULL)
  ),
  CONSTRAINT queue_claims_acked_requires_timestamp CHECK (
    claim_status <> 'acked' OR acked_at IS NOT NULL
  ),
  CONSTRAINT queue_claims_ack_outcome_consistency CHECK (
    ack_outcome <> 'acked_source_message' OR claim_status = 'acked'
  )
);

CREATE INDEX IF NOT EXISTS queue_claims_message_idx
  ON paa.queue_claims(queue_message_id, created_at DESC);

CREATE INDEX IF NOT EXISTS queue_claims_work_item_idx
  ON paa.queue_claims(work_item_id, created_at DESC);

CREATE INDEX IF NOT EXISTS queue_claims_active_idx
  ON paa.queue_claims(queue_message_id)
  WHERE claim_status = 'active';

CREATE UNIQUE INDEX IF NOT EXISTS queue_claims_one_active_per_message_uidx
  ON paa.queue_claims(queue_message_id)
  WHERE claim_status = 'active';

ALTER TABLE paa.workflow_states
  ADD CONSTRAINT workflow_states_active_queue_claim_fk
  FOREIGN KEY (active_queue_claim_id)
  REFERENCES paa.queue_claims(queue_claim_id)
  ON DELETE SET NULL;

ALTER TABLE paa.workflow_transitions
  ADD CONSTRAINT workflow_transitions_source_claim_fk
  FOREIGN KEY (source_queue_claim_id)
  REFERENCES paa.queue_claims(queue_claim_id)
  ON DELETE SET NULL;

ALTER TABLE paa.workflow_transitions
  ADD CONSTRAINT workflow_transitions_result_claim_fk
  FOREIGN KEY (result_queue_claim_id)
  REFERENCES paa.queue_claims(queue_claim_id)
  ON DELETE SET NULL;

CREATE TABLE IF NOT EXISTS paa.execution_package_installs (
  execution_package_install_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES paa.projects(project_id) ON DELETE CASCADE,
  authority_version_id UUID NOT NULL REFERENCES paa.authority_versions(authority_version_id) ON DELETE RESTRICT,
  installed_by_agent_id UUID REFERENCES paa.agents(agent_id) ON DELETE SET NULL,
  installed_by_role_id UUID REFERENCES paa.roles(role_id) ON DELETE SET NULL,
  execution_surface_type paa.execution_surface_type NOT NULL,
  execution_surface_key TEXT NOT NULL,
  repo_root_path TEXT,
  runtime_root_path TEXT,
  install_slot_name TEXT,
  package_name TEXT NOT NULL,
  package_version TEXT,
  package_build_ref TEXT,
  package_hash TEXT,
  package_schema_version TEXT,
  install_status paa.execution_package_install_status NOT NULL,
  installed_from_source paa.execution_package_install_source NOT NULL,
  superseded_by_install_id UUID REFERENCES paa.execution_package_installs(execution_package_install_id) ON DELETE SET NULL,
  replaced_install_id UUID REFERENCES paa.execution_package_installs(execution_package_install_id) ON DELETE SET NULL,
  deactivation_reason_code TEXT,
  deactivation_reason_text TEXT,
  installed_manifest_path TEXT,
  installed_package_metadata_path TEXT,
  installed_docs_root_path TEXT,
  installed_artifacts_root_path TEXT,
  installed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  activated_at TIMESTAMPTZ,
  deactivated_at TIMESTAMPTZ,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT execution_package_installs_active_requires_activation CHECK (
    install_status <> 'active' OR activated_at IS NOT NULL
  ),
  CONSTRAINT execution_package_installs_superseded_requires_deactivation CHECK (
    install_status <> 'superseded' OR deactivated_at IS NOT NULL
  )
);

CREATE INDEX IF NOT EXISTS execution_package_installs_surface_idx
  ON paa.execution_package_installs(execution_surface_key, installed_at DESC);

CREATE INDEX IF NOT EXISTS execution_package_installs_authority_idx
  ON paa.execution_package_installs(authority_version_id, installed_at DESC);

CREATE UNIQUE INDEX IF NOT EXISTS execution_package_installs_one_active_surface_uidx
  ON paa.execution_package_installs(execution_surface_key)
  WHERE install_status = 'active';

CREATE TABLE IF NOT EXISTS paa.execution_package_overlays (
  execution_package_overlay_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  execution_package_install_id UUID NOT NULL REFERENCES paa.execution_package_installs(execution_package_install_id) ON DELETE CASCADE,
  project_id UUID NOT NULL REFERENCES paa.projects(project_id) ON DELETE CASCADE,
  authority_version_id UUID REFERENCES paa.authority_versions(authority_version_id) ON DELETE SET NULL,
  work_item_id UUID REFERENCES paa.work_items(work_item_id) ON DELETE SET NULL,
  activated_by_agent_id UUID REFERENCES paa.agents(agent_id) ON DELETE SET NULL,
  activated_by_role_id UUID REFERENCES paa.roles(role_id) ON DELETE SET NULL,
  overlay_key TEXT NOT NULL,
  overlay_type paa.execution_package_overlay_type NOT NULL,
  overlay_name TEXT NOT NULL,
  overlay_version TEXT,
  overlay_hash TEXT,
  overlay_schema_version TEXT,
  overlay_status paa.execution_package_overlay_status NOT NULL,
  overlay_source paa.execution_package_overlay_source NOT NULL,
  replaced_overlay_id UUID REFERENCES paa.execution_package_overlays(execution_package_overlay_id) ON DELETE SET NULL,
  superseded_by_overlay_id UUID REFERENCES paa.execution_package_overlays(execution_package_overlay_id) ON DELETE SET NULL,
  deactivation_reason_code TEXT,
  deactivation_reason_text TEXT,
  overlay_root_path TEXT,
  overlay_metadata_path TEXT,
  overlay_manifest_task_path TEXT,
  overlay_summary_path TEXT,
  activated_at TIMESTAMPTZ,
  deactivated_at TIMESTAMPTZ,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT execution_package_overlays_active_requires_activation CHECK (
    overlay_status <> 'active' OR activated_at IS NOT NULL
  ),
  CONSTRAINT execution_package_overlays_superseded_requires_deactivation CHECK (
    overlay_status <> 'superseded' OR deactivated_at IS NOT NULL
  )
);

CREATE INDEX IF NOT EXISTS execution_package_overlays_install_idx
  ON paa.execution_package_overlays(execution_package_install_id, created_at DESC);

CREATE INDEX IF NOT EXISTS execution_package_overlays_work_item_idx
  ON paa.execution_package_overlays(work_item_id, created_at DESC)
  WHERE work_item_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS execution_package_overlays_one_active_key_per_install_uidx
  ON paa.execution_package_overlays(execution_package_install_id, overlay_key)
  WHERE overlay_status = 'active';

CREATE TABLE IF NOT EXISTS paa.transition_inputs (
  transition_input_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES paa.projects(project_id) ON DELETE CASCADE,
  work_item_id UUID NOT NULL REFERENCES paa.work_items(work_item_id) ON DELETE CASCADE,
  workflow_state_id UUID REFERENCES paa.workflow_states(workflow_state_id) ON DELETE SET NULL,
  workflow_transition_id UUID REFERENCES paa.workflow_transitions(workflow_transition_id) ON DELETE SET NULL,
  automation_run_id UUID REFERENCES paa.automation_runs(automation_run_id) ON DELETE SET NULL,
  input_type paa.transition_input_type NOT NULL,
  input_schema_type TEXT,
  input_source_surface paa.transition_input_source_surface NOT NULL,
  input_key TEXT,
  input_hash TEXT,
  source_queue_message_id UUID REFERENCES paa.queue_messages(queue_message_id) ON DELETE SET NULL,
  source_handoff_id UUID REFERENCES paa.handoffs(handoff_id) ON DELETE SET NULL,
  source_message_id_external TEXT,
  source_report_path TEXT,
  payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  content_summary_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  schema_version TEXT,
  captured_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS transition_inputs_work_item_idx
  ON paa.transition_inputs(work_item_id, captured_at DESC);

CREATE INDEX IF NOT EXISTS transition_inputs_transition_idx
  ON paa.transition_inputs(workflow_transition_id, captured_at DESC)
  WHERE workflow_transition_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS transition_inputs_run_idx
  ON paa.transition_inputs(automation_run_id, captured_at DESC)
  WHERE automation_run_id IS NOT NULL;

ALTER TABLE paa.workflow_transitions
  ADD CONSTRAINT workflow_transitions_source_input_fk
  FOREIGN KEY (source_transition_input_id)
  REFERENCES paa.transition_inputs(transition_input_id)
  ON DELETE SET NULL;

CREATE TABLE IF NOT EXISTS paa.automation_run_events (
  automation_run_event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  automation_run_id UUID NOT NULL REFERENCES paa.automation_runs(automation_run_id) ON DELETE CASCADE,
  project_id UUID NOT NULL REFERENCES paa.projects(project_id) ON DELETE CASCADE,
  work_item_id UUID REFERENCES paa.work_items(work_item_id) ON DELETE SET NULL,
  workflow_state_id UUID REFERENCES paa.workflow_states(workflow_state_id) ON DELETE SET NULL,
  workflow_transition_id UUID REFERENCES paa.workflow_transitions(workflow_transition_id) ON DELETE SET NULL,
  event_type paa.automation_run_event_type NOT NULL,
  event_status paa.automation_run_event_status NOT NULL,
  event_phase paa.automation_run_event_phase NOT NULL,
  event_reason_code TEXT,
  event_reason_text TEXT,
  role_id UUID REFERENCES paa.roles(role_id) ON DELETE SET NULL,
  agent_id UUID REFERENCES paa.agents(agent_id) ON DELETE SET NULL,
  handoff_id UUID REFERENCES paa.handoffs(handoff_id) ON DELETE SET NULL,
  queue_message_id UUID REFERENCES paa.queue_messages(queue_message_id) ON DELETE SET NULL,
  queue_claim_id UUID REFERENCES paa.queue_claims(queue_claim_id) ON DELETE SET NULL,
  message_id_external TEXT,
  event_summary_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  evidence_ref TEXT,
  raw_log_pointer TEXT,
  event_recorded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS automation_run_events_run_idx
  ON paa.automation_run_events(automation_run_id, event_recorded_at DESC, created_at DESC);

CREATE INDEX IF NOT EXISTS automation_run_events_work_item_idx
  ON paa.automation_run_events(work_item_id, event_recorded_at DESC)
  WHERE work_item_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS automation_run_events_type_idx
  ON paa.automation_run_events(event_type, event_status, event_recorded_at DESC);

ALTER TABLE paa.design_packages
  ADD COLUMN IF NOT EXISTS normalization_status paa.component_normalization_status NOT NULL DEFAULT 'normalized',
  ADD COLUMN IF NOT EXISTS normalization_notes TEXT;

CREATE INDEX IF NOT EXISTS design_packages_normalization_status_idx
  ON paa.design_packages(normalization_status, status, created_at DESC);

ALTER TABLE paa.coder_run_briefs
  ADD COLUMN IF NOT EXISTS normalization_status paa.component_normalization_status NOT NULL DEFAULT 'normalized',
  ADD COLUMN IF NOT EXISTS normalization_notes TEXT;

CREATE INDEX IF NOT EXISTS coder_run_briefs_normalization_status_idx
  ON paa.coder_run_briefs(normalization_status, status, created_at DESC);

COMMIT;

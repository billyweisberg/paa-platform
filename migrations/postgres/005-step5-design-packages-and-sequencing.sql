-- Project for Autonomous Agents
-- Step 5 Postgres DDL: Stage 1 design packages and dependency edges
--
-- Prerequisites:
-- - 54-step1-postgres-ddl.sql
-- - 55-step2-postgres-ddl.sql
-- - 60-step3-postgres-ddl.sql
-- - 77-step4-postgres-ddl-coder-briefs.sql

BEGIN;

CREATE SCHEMA IF NOT EXISTS paa;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type t JOIN pg_namespace n ON n.oid = t.typnamespace WHERE t.typname = 'design_package_status' AND n.nspname = 'paa') THEN
    CREATE TYPE paa.design_package_status AS ENUM ('draft', 'under_review', 'approved_for_derivation', 'superseded', 'rejected');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type t JOIN pg_namespace n ON n.oid = t.typnamespace WHERE t.typname = 'dependency_type' AND n.nspname = 'paa') THEN
    CREATE TYPE paa.dependency_type AS ENUM ('depends_on_contract', 'depends_on_injection', 'depends_on_event', 'depends_on_state', 'depends_on_test_fixture', 'depends_on_hosting');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type t JOIN pg_namespace n ON n.oid = t.typnamespace WHERE t.typname = 'dependency_strength' AND n.nspname = 'paa') THEN
    CREATE TYPE paa.dependency_strength AS ENUM ('hard', 'soft');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type t JOIN pg_namespace n ON n.oid = t.typnamespace WHERE t.typname = 'sequencing_requirement' AND n.nspname = 'paa') THEN
    CREATE TYPE paa.sequencing_requirement AS ENUM ('must_precede', 'may_parallelize', 'must_follow_contract_only');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type t JOIN pg_namespace n ON n.oid = t.typnamespace WHERE t.typname = 'blocking_scope' AND n.nspname = 'paa') THEN
    CREATE TYPE paa.blocking_scope AS ENUM ('design', 'derivation', 'execution', 'verification');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type t JOIN pg_namespace n ON n.oid = t.typnamespace WHERE t.typname = 'dependency_status' AND n.nspname = 'paa') THEN
    CREATE TYPE paa.dependency_status AS ENUM ('undefined', 'defined', 'contract_ready', 'implementation_ready', 'verified');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type t JOIN pg_namespace n ON n.oid = t.typnamespace WHERE t.typname = 'readiness_state' AND n.nspname = 'paa') THEN
    CREATE TYPE paa.readiness_state AS ENUM ('not_derivation_ready', 'derivation_ready', 'blocked_on_dependency', 'blocked_on_contract', 'execution_ready', 'parallel_ready', 'active', 'completed');
  END IF;
END$$;

CREATE TABLE IF NOT EXISTS paa.design_packages (
  design_package_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES paa.projects(project_id) ON DELETE CASCADE,
  work_item_id UUID REFERENCES paa.work_items(work_item_id) ON DELETE SET NULL,
  spec_fragment_id UUID REFERENCES paa.spec_fragments(spec_fragment_id) ON DELETE SET NULL,
  implementation_target_id UUID REFERENCES paa.implementation_targets(implementation_target_id) ON DELETE SET NULL,
  authority_version_id UUID REFERENCES paa.authority_versions(authority_version_id) ON DELETE SET NULL,
  primary_component_id UUID REFERENCES paa.components(component_id) ON DELETE SET NULL,
  package_id_external TEXT,
  schema_version TEXT NOT NULL,
  status paa.design_package_status NOT NULL DEFAULT 'draft',
  package_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  provenance_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_by_role_id UUID REFERENCES paa.roles(role_id) ON DELETE SET NULL,
  created_by_agent_id UUID REFERENCES paa.agents(agent_id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (project_id, package_id_external)
);

CREATE INDEX IF NOT EXISTS design_packages_project_status_idx ON paa.design_packages(project_id, status, created_at DESC);
CREATE INDEX IF NOT EXISTS design_packages_work_item_idx ON paa.design_packages(work_item_id, status, created_at DESC);

CREATE TABLE IF NOT EXISTS paa.design_package_signoffs (
  design_package_signoff_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  design_package_id UUID NOT NULL REFERENCES paa.design_packages(design_package_id) ON DELETE CASCADE,
  role_id UUID NOT NULL REFERENCES paa.roles(role_id) ON DELETE CASCADE,
  signer_name TEXT,
  signoff_status TEXT NOT NULL,
  notes TEXT,
  signed_at TIMESTAMPTZ,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  UNIQUE (design_package_id, role_id)
);

CREATE TABLE IF NOT EXISTS paa.component_dependency_edges (
  component_dependency_edge_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES paa.projects(project_id) ON DELETE CASCADE,
  design_package_id UUID REFERENCES paa.design_packages(design_package_id) ON DELETE SET NULL,
  from_component_id UUID NOT NULL REFERENCES paa.components(component_id) ON DELETE CASCADE,
  to_component_id UUID NOT NULL REFERENCES paa.components(component_id) ON DELETE CASCADE,
  dependency_type paa.dependency_type NOT NULL,
  dependency_strength paa.dependency_strength NOT NULL,
  sequencing_requirement paa.sequencing_requirement NOT NULL,
  blocking_scope paa.blocking_scope NOT NULL,
  dependency_status paa.dependency_status NOT NULL DEFAULT 'undefined',
  estimated_duration_class TEXT,
  estimated_complexity TEXT,
  estimated_runs INTEGER,
  shared_surface_conflict BOOLEAN NOT NULL DEFAULT false,
  notes TEXT,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (design_package_id, from_component_id, to_component_id, dependency_type)
);

CREATE INDEX IF NOT EXISTS component_dependency_edges_project_idx ON paa.component_dependency_edges(project_id, dependency_status, sequencing_requirement);
CREATE INDEX IF NOT EXISTS component_dependency_edges_from_idx ON paa.component_dependency_edges(from_component_id, dependency_strength, dependency_status);
CREATE INDEX IF NOT EXISTS component_dependency_edges_to_idx ON paa.component_dependency_edges(to_component_id, dependency_strength, dependency_status);

CREATE TABLE IF NOT EXISTS paa.coder_brief_sequence_states (
  coder_brief_sequence_state_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES paa.projects(project_id) ON DELETE CASCADE,
  design_package_id UUID REFERENCES paa.design_packages(design_package_id) ON DELETE SET NULL,
  coder_run_brief_id UUID REFERENCES paa.coder_run_briefs(coder_run_brief_id) ON DELETE SET NULL,
  primary_component_id UUID REFERENCES paa.components(component_id) ON DELETE SET NULL,
  readiness_state paa.readiness_state NOT NULL,
  blocking_cause TEXT,
  parallel_group_id TEXT,
  computed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS coder_brief_sequence_states_project_idx ON paa.coder_brief_sequence_states(project_id, readiness_state, computed_at DESC);

COMMIT;

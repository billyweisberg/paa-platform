-- Project for Autonomous Agents
-- Step 4 Postgres DDL: coder-facing architecture and implementation briefs
--
-- Prerequisites:
-- - 54-step1-postgres-ddl.sql
-- - 55-step2-postgres-ddl.sql
-- - 60-step3-postgres-ddl.sql
--
-- Scope:
-- - components
-- - component_surfaces
-- - component_relationships
-- - coder_run_briefs
--
-- Design approach:
-- - normalize stable architectural identity and collaboration structure
-- - keep evolving coder-run detail in JSONB until patterns stabilize

BEGIN;

CREATE SCHEMA IF NOT EXISTS paa;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'component_status') THEN
    CREATE TYPE paa.component_status AS ENUM (
      'draft',
      'active',
      'superseded',
      'retired'
    );
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'system_layer') THEN
    CREATE TYPE paa.system_layer AS ENUM (
      'host-adapter',
      'model-core',
      'policy',
      'hierarchy',
      'diagnostics',
      'contract',
      'integration',
      'test',
      'docs'
    );
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'component_tier') THEN
    CREATE TYPE paa.component_tier AS ENUM (
      'data',
      'compute',
      'ui',
      'framework',
      'runtime'
    );
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'component_surface_type') THEN
    CREATE TYPE paa.component_surface_type AS ENUM (
      'module',
      'doc',
      'test',
      'config',
      'contract',
      'integration',
      'event'
    );
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'component_relationship_type') THEN
    CREATE TYPE paa.component_relationship_type AS ENUM (
      'calls',
      'injects',
      'emits_to',
      'consumes_from',
      'contains',
      'coordinates',
      'depends_on'
    );
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'coder_brief_status') THEN
    CREATE TYPE paa.coder_brief_status AS ENUM (
      'draft',
      'approved',
      'active',
      'superseded',
      'consumed',
      'rejected'
    );
  END IF;
END
$$;

CREATE TABLE IF NOT EXISTS paa.components (
  component_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES paa.projects(project_id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  role TEXT NOT NULL,
  system_layer paa.system_layer NOT NULL,
  tier paa.component_tier,
  description TEXT,
  status paa.component_status NOT NULL DEFAULT 'draft',
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (project_id, name)
);

CREATE INDEX IF NOT EXISTS components_project_layer_idx
  ON paa.components(project_id, system_layer, status);

CREATE TABLE IF NOT EXISTS paa.component_surfaces (
  component_surface_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  component_id UUID NOT NULL REFERENCES paa.components(component_id) ON DELETE CASCADE,
  surface_type paa.component_surface_type NOT NULL,
  path TEXT NOT NULL,
  responsibility TEXT,
  is_primary BOOLEAN NOT NULL DEFAULT false,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (component_id, surface_type, path)
);

CREATE INDEX IF NOT EXISTS component_surfaces_component_type_idx
  ON paa.component_surfaces(component_id, surface_type, is_primary);

CREATE TABLE IF NOT EXISTS paa.component_relationships (
  component_relationship_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES paa.projects(project_id) ON DELETE CASCADE,
  from_component_id UUID NOT NULL REFERENCES paa.components(component_id) ON DELETE CASCADE,
  to_component_id UUID NOT NULL REFERENCES paa.components(component_id) ON DELETE CASCADE,
  relationship_type paa.component_relationship_type NOT NULL,
  description TEXT,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (from_component_id, to_component_id, relationship_type)
);

CREATE INDEX IF NOT EXISTS component_relationships_project_type_idx
  ON paa.component_relationships(project_id, relationship_type);

CREATE TABLE IF NOT EXISTS paa.coder_run_briefs (
  coder_run_brief_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES paa.projects(project_id) ON DELETE CASCADE,
  work_item_id UUID REFERENCES paa.work_items(work_item_id) ON DELETE SET NULL,
  spec_fragment_id UUID REFERENCES paa.spec_fragments(spec_fragment_id) ON DELETE SET NULL,
  implementation_target_id UUID REFERENCES paa.implementation_targets(implementation_target_id) ON DELETE SET NULL,
  authority_version_id UUID REFERENCES paa.authority_versions(authority_version_id) ON DELETE SET NULL,
  primary_component_id UUID REFERENCES paa.components(component_id) ON DELETE SET NULL,
  brief_id_external TEXT,
  schema_version TEXT NOT NULL,
  status paa.coder_brief_status NOT NULL DEFAULT 'draft',
  slice_scope_ref_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  component_assignment_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  architecture_constraints_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  collaboration_context_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  dependency_contract_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  behavioral_contract_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  test_contract_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  change_budget_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  anti_goals_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  brief_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  generated_from_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_by_role_id UUID REFERENCES paa.roles(role_id) ON DELETE SET NULL,
  created_by_agent_id UUID REFERENCES paa.agents(agent_id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (project_id, brief_id_external)
);

CREATE INDEX IF NOT EXISTS coder_run_briefs_project_status_idx
  ON paa.coder_run_briefs(project_id, status, created_at DESC);

CREATE INDEX IF NOT EXISTS coder_run_briefs_work_item_idx
  ON paa.coder_run_briefs(work_item_id, status, created_at DESC);

CREATE INDEX IF NOT EXISTS coder_run_briefs_primary_component_idx
  ON paa.coder_run_briefs(primary_component_id, status, created_at DESC);

COMMIT;

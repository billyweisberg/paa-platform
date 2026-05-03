-- Project for Autonomous Agents
-- Step 3 Postgres DDL: project knowledge graph
--
-- Prerequisites:
-- - 54-step1-postgres-ddl.sql
-- - 55-step2-postgres-ddl.sql
--
-- Scope:
-- - source_artifacts
-- - source_statements
-- - requirements
-- - requirement_sources
-- - design_decisions
-- - decision_requirements
-- - spec_fragments
-- - spec_fragment_requirements
-- - spec_fragment_decisions
-- - implementation_targets
-- - authority_version_fragments
-- - authority_version_targets
-- - bridge columns from work_items / verification_obligations into the knowledge graph

BEGIN;

CREATE SCHEMA IF NOT EXISTS paa;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'artifact_kind') THEN
    CREATE TYPE paa.artifact_kind AS ENUM (
      'code',
      'doc',
      'note',
      'conversation',
      'dataset',
      'reference_output'
    );
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'statement_type') THEN
    CREATE TYPE paa.statement_type AS ENUM (
      'requirement',
      'constraint',
      'vision',
      'target_behavior',
      'invariant',
      'tolerance',
      'open_question'
    );
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'statement_importance') THEN
    CREATE TYPE paa.statement_importance AS ENUM (
      'low',
      'medium',
      'high',
      'critical'
    );
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'statement_status') THEN
    CREATE TYPE paa.statement_status AS ENUM (
      'draft',
      'accepted',
      'superseded',
      'rejected'
    );
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'requirement_kind') THEN
    CREATE TYPE paa.requirement_kind AS ENUM (
      'functional',
      'behavioral',
      'nonfunctional',
      'semantic',
      'verification'
    );
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'requirement_priority') THEN
    CREATE TYPE paa.requirement_priority AS ENUM (
      'low',
      'medium',
      'high',
      'critical'
    );
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'knowledge_status') THEN
    CREATE TYPE paa.knowledge_status AS ENUM (
      'draft',
      'approved',
      'implemented',
      'verified',
      'superseded',
      'rejected'
    );
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'decision_relationship_type') THEN
    CREATE TYPE paa.decision_relationship_type AS ENUM (
      'supports',
      'constrains',
      'conflicts_with',
      'implements'
    );
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'fragment_kind') THEN
    CREATE TYPE paa.fragment_kind AS ENUM (
      'behavior',
      'constraint',
      'transition_rule',
      'boundary',
      'tolerance',
      'artifact_contract'
    );
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'risk_level') THEN
    CREATE TYPE paa.risk_level AS ENUM (
      'low',
      'medium',
      'high',
      'critical'
    );
  END IF;
END
$$;

CREATE TABLE IF NOT EXISTS paa.source_artifacts (
  source_artifact_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES paa.projects(project_id) ON DELETE CASCADE,
  kind paa.artifact_kind NOT NULL,
  title TEXT NOT NULL,
  location TEXT,
  version_ref TEXT,
  content_hash TEXT,
  captured_at TIMESTAMPTZ,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS source_artifacts_project_kind_idx
  ON paa.source_artifacts(project_id, kind);

CREATE TABLE IF NOT EXISTS paa.source_statements (
  source_statement_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_artifact_id UUID NOT NULL REFERENCES paa.source_artifacts(source_artifact_id) ON DELETE CASCADE,
  statement_type paa.statement_type NOT NULL,
  text TEXT NOT NULL,
  anchor TEXT,
  importance paa.statement_importance NOT NULL DEFAULT 'medium',
  status paa.statement_status NOT NULL DEFAULT 'draft',
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS source_statements_artifact_type_idx
  ON paa.source_statements(source_artifact_id, statement_type);

CREATE TABLE IF NOT EXISTS paa.requirements (
  requirement_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES paa.projects(project_id) ON DELETE CASCADE,
  canonical_text TEXT NOT NULL,
  requirement_kind paa.requirement_kind NOT NULL,
  priority paa.requirement_priority NOT NULL DEFAULT 'medium',
  status paa.knowledge_status NOT NULL DEFAULT 'draft',
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS requirements_project_kind_idx
  ON paa.requirements(project_id, requirement_kind, status);

CREATE TABLE IF NOT EXISTS paa.requirement_sources (
  requirement_id UUID NOT NULL REFERENCES paa.requirements(requirement_id) ON DELETE CASCADE,
  source_statement_id UUID NOT NULL REFERENCES paa.source_statements(source_statement_id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (requirement_id, source_statement_id)
);

CREATE TABLE IF NOT EXISTS paa.design_decisions (
  decision_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES paa.projects(project_id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  statement TEXT NOT NULL,
  rationale TEXT,
  status paa.knowledge_status NOT NULL DEFAULT 'draft',
  owner_role_id UUID REFERENCES paa.roles(role_id) ON DELETE SET NULL,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS design_decisions_project_status_idx
  ON paa.design_decisions(project_id, status);

CREATE TABLE IF NOT EXISTS paa.decision_requirements (
  decision_id UUID NOT NULL REFERENCES paa.design_decisions(decision_id) ON DELETE CASCADE,
  requirement_id UUID NOT NULL REFERENCES paa.requirements(requirement_id) ON DELETE CASCADE,
  relationship_type paa.decision_relationship_type NOT NULL DEFAULT 'supports',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (decision_id, requirement_id)
);

CREATE TABLE IF NOT EXISTS paa.spec_fragments (
  spec_fragment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES paa.projects(project_id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  canonical_statement TEXT NOT NULL,
  fragment_kind paa.fragment_kind NOT NULL,
  delta_family TEXT,
  authorized_delta_family TEXT,
  out_of_scope_delta_families_json JSONB NOT NULL DEFAULT '[]'::jsonb,
  expected_touch_surfaces_json JSONB NOT NULL DEFAULT '[]'::jsonb,
  status paa.knowledge_status NOT NULL DEFAULT 'draft',
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS spec_fragments_project_kind_idx
  ON paa.spec_fragments(project_id, fragment_kind, status);

CREATE TABLE IF NOT EXISTS paa.spec_fragment_requirements (
  spec_fragment_id UUID NOT NULL REFERENCES paa.spec_fragments(spec_fragment_id) ON DELETE CASCADE,
  requirement_id UUID NOT NULL REFERENCES paa.requirements(requirement_id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (spec_fragment_id, requirement_id)
);

CREATE TABLE IF NOT EXISTS paa.spec_fragment_decisions (
  spec_fragment_id UUID NOT NULL REFERENCES paa.spec_fragments(spec_fragment_id) ON DELETE CASCADE,
  decision_id UUID NOT NULL REFERENCES paa.design_decisions(decision_id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (spec_fragment_id, decision_id)
);

CREATE TABLE IF NOT EXISTS paa.implementation_targets (
  implementation_target_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  spec_fragment_id UUID NOT NULL REFERENCES paa.spec_fragments(spec_fragment_id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  current_gap_json JSONB NOT NULL DEFAULT '[]'::jsonb,
  desired_state_json JSONB NOT NULL DEFAULT '[]'::jsonb,
  protected_baseline_json JSONB NOT NULL DEFAULT '[]'::jsonb,
  out_of_scope_json JSONB NOT NULL DEFAULT '[]'::jsonb,
  pre_handoff_scope_checks_json JSONB NOT NULL DEFAULT '[]'::jsonb,
  risk_level paa.risk_level NOT NULL DEFAULT 'medium',
  status paa.knowledge_status NOT NULL DEFAULT 'draft',
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS implementation_targets_fragment_status_idx
  ON paa.implementation_targets(spec_fragment_id, status);

CREATE TABLE IF NOT EXISTS paa.authority_version_fragments (
  authority_version_id UUID NOT NULL REFERENCES paa.authority_versions(authority_version_id) ON DELETE CASCADE,
  spec_fragment_id UUID NOT NULL REFERENCES paa.spec_fragments(spec_fragment_id) ON DELETE CASCADE,
  fragment_status paa.knowledge_status NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (authority_version_id, spec_fragment_id)
);

CREATE TABLE IF NOT EXISTS paa.authority_version_targets (
  authority_version_id UUID NOT NULL REFERENCES paa.authority_versions(authority_version_id) ON DELETE CASCADE,
  implementation_target_id UUID NOT NULL REFERENCES paa.implementation_targets(implementation_target_id) ON DELETE CASCADE,
  target_status paa.knowledge_status NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (authority_version_id, implementation_target_id)
);

ALTER TABLE paa.work_items
  ADD COLUMN IF NOT EXISTS spec_fragment_id UUID REFERENCES paa.spec_fragments(spec_fragment_id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS implementation_target_id UUID REFERENCES paa.implementation_targets(implementation_target_id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS work_items_spec_fragment_idx
  ON paa.work_items(spec_fragment_id)
  WHERE spec_fragment_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS work_items_implementation_target_idx
  ON paa.work_items(implementation_target_id)
  WHERE implementation_target_id IS NOT NULL;

ALTER TABLE paa.verification_obligations
  ADD COLUMN IF NOT EXISTS spec_fragment_id UUID REFERENCES paa.spec_fragments(spec_fragment_id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS verification_obligations_spec_fragment_idx
  ON paa.verification_obligations(spec_fragment_id)
  WHERE spec_fragment_id IS NOT NULL;

COMMIT;

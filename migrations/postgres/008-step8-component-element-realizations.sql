-- Project for Autonomous Agents
-- Step 8 Postgres DDL: component element realization taxonomy, instances,
-- and brief-target bindings
--
-- Prerequisites:
-- - 001-step1-control-plane.sql
-- - 002-step2-verification-recovery.sql
-- - 003-step3-knowledge-graph.sql
-- - 004-step4-coder-briefs.sql
-- - 005-step5-design-packages-and-sequencing.sql
-- - 006-step6-workflow-install-runtime-normalization.sql
-- - 007-step7-component-elements.sql

BEGIN;

CREATE SCHEMA IF NOT EXISTS paa;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE t.typname = 'component_realization_status' AND n.nspname = 'paa'
  ) THEN
    CREATE TYPE paa.component_realization_status AS ENUM (
      'draft',
      'planned',
      'active',
      'superseded',
      'retired'
    );
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE t.typname = 'brief_target_intent' AND n.nspname = 'paa'
  ) THEN
    CREATE TYPE paa.brief_target_intent AS ENUM (
      'implement',
      'extend',
      'repair',
      'verify',
      'document'
    );
  END IF;
END$$;

CREATE TABLE IF NOT EXISTS paa.component_element_realization_types (
  component_element_realization_type_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  realization_key TEXT NOT NULL UNIQUE,
  label TEXT NOT NULL,
  category TEXT NOT NULL,
  description TEXT,
  is_brief_targetable BOOLEAN NOT NULL DEFAULT true,
  is_multi_instance BOOLEAN NOT NULL DEFAULT true,
  sort_order INTEGER NOT NULL,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS component_element_realization_types_category_idx
  ON paa.component_element_realization_types(category, sort_order);

CREATE TABLE IF NOT EXISTS paa.component_element_type_realization_types (
  component_element_type_realization_type_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  component_element_type_id UUID NOT NULL REFERENCES paa.component_element_types(component_element_type_id) ON DELETE CASCADE,
  component_element_realization_type_id UUID NOT NULL REFERENCES paa.component_element_realization_types(component_element_realization_type_id) ON DELETE CASCADE,
  is_default BOOLEAN NOT NULL DEFAULT false,
  sort_order INTEGER NOT NULL DEFAULT 0,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (component_element_type_id, component_element_realization_type_id)
);

CREATE INDEX IF NOT EXISTS component_element_type_realization_types_type_idx
  ON paa.component_element_type_realization_types(component_element_type_id, is_default, sort_order);

CREATE TABLE IF NOT EXISTS paa.component_element_realizations (
  component_element_realization_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES paa.projects(project_id) ON DELETE CASCADE,
  component_id UUID NOT NULL REFERENCES paa.components(component_id) ON DELETE CASCADE,
  component_element_id UUID NOT NULL REFERENCES paa.component_elements(component_element_id) ON DELETE CASCADE,
  component_element_realization_type_id UUID NOT NULL REFERENCES paa.component_element_realization_types(component_element_realization_type_id) ON DELETE RESTRICT,
  realization_key TEXT NOT NULL,
  title TEXT,
  status paa.component_realization_status NOT NULL DEFAULT 'draft',
  sequence_order INTEGER NOT NULL DEFAULT 0,
  definition_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  artifact_ref_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  provenance_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_by_role_id UUID REFERENCES paa.roles(role_id) ON DELETE SET NULL,
  created_by_agent_id UUID REFERENCES paa.agents(agent_id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (component_element_id, component_element_realization_type_id, realization_key)
);

CREATE INDEX IF NOT EXISTS component_element_realizations_component_idx
  ON paa.component_element_realizations(project_id, component_id, status, sequence_order, updated_at DESC);

CREATE INDEX IF NOT EXISTS component_element_realizations_element_idx
  ON paa.component_element_realizations(component_element_id, status, sequence_order, updated_at DESC);

CREATE TABLE IF NOT EXISTS paa.coder_brief_realization_targets (
  coder_brief_realization_target_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES paa.projects(project_id) ON DELETE CASCADE,
  work_item_id UUID REFERENCES paa.work_items(work_item_id) ON DELETE SET NULL,
  coder_run_brief_id UUID NOT NULL REFERENCES paa.coder_run_briefs(coder_run_brief_id) ON DELETE CASCADE,
  component_id UUID NOT NULL REFERENCES paa.components(component_id) ON DELETE CASCADE,
  component_element_id UUID NOT NULL REFERENCES paa.component_elements(component_element_id) ON DELETE CASCADE,
  component_element_realization_id UUID NOT NULL REFERENCES paa.component_element_realizations(component_element_realization_id) ON DELETE CASCADE,
  depends_on_target_id UUID REFERENCES paa.coder_brief_realization_targets(coder_brief_realization_target_id) ON DELETE SET NULL,
  target_intent paa.brief_target_intent NOT NULL DEFAULT 'implement',
  sequence_order INTEGER NOT NULL DEFAULT 0,
  is_required BOOLEAN NOT NULL DEFAULT true,
  target_notes TEXT,
  target_contract_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (coder_run_brief_id, component_element_realization_id, target_intent)
);

CREATE INDEX IF NOT EXISTS coder_brief_realization_targets_brief_idx
  ON paa.coder_brief_realization_targets(coder_run_brief_id, sequence_order, is_required);

CREATE INDEX IF NOT EXISTS coder_brief_realization_targets_component_idx
  ON paa.coder_brief_realization_targets(component_id, component_element_id, sequence_order);

INSERT INTO paa.component_element_realization_types (
  realization_key,
  label,
  category,
  description,
  is_brief_targetable,
  is_multi_instance,
  sort_order,
  metadata_json
)
VALUES
  ('repository_interface', 'Repository Interface', 'code_artifact', 'Abstract repository contract or protocol defining supported operations.', true, false, 10, '{}'::jsonb),
  ('concrete_repository_class', 'Concrete Repository Class', 'code_artifact', 'Concrete class implementing a repository interface against one or more backing stores.', true, false, 20, '{}'::jsonb),
  ('dto', 'DTO', 'code_artifact', 'Concrete data transfer object used to carry structured data across boundaries.', true, true, 30, '{}'::jsonb),
  ('mapper', 'Mapper', 'code_artifact', 'Mapping artifact that translates between rows, DTOs, and domain records.', true, true, 40, '{}'::jsonb),
  ('query_object', 'Query Object', 'code_artifact', 'Named query or query-construction artifact for repository reads.', true, true, 50, '{}'::jsonb),
  ('event_handler', 'Event Handler', 'code_artifact', 'Concrete handler that consumes an event or message and applies component logic.', true, true, 60, '{}'::jsonb),
  ('policy_adapter', 'Policy Adapter', 'code_artifact', 'Concrete adapter that realizes a policy or contract against runtime infrastructure.', true, true, 70, '{}'::jsonb),
  ('projection_view', 'Projection View', 'db_artifact', 'Derived read model or view used for projection and reporting access.', true, true, 80, '{}'::jsonb),
  ('schema_definition', 'Schema Definition', 'contract_artifact', 'Concrete schema or contract artifact realized as code or structured spec.', true, true, 90, '{}'::jsonb)
ON CONFLICT (realization_key) DO UPDATE SET
  label = EXCLUDED.label,
  category = EXCLUDED.category,
  description = EXCLUDED.description,
  is_brief_targetable = EXCLUDED.is_brief_targetable,
  is_multi_instance = EXCLUDED.is_multi_instance,
  sort_order = EXCLUDED.sort_order,
  metadata_json = EXCLUDED.metadata_json,
  updated_at = now();

INSERT INTO paa.component_element_type_realization_types (
  component_element_type_id,
  component_element_realization_type_id,
  is_default,
  sort_order,
  metadata_json
)
SELECT cet.component_element_type_id, cert.component_element_realization_type_id, m.is_default, m.sort_order, '{}'::jsonb
FROM (
  VALUES
    ('interfaces', 'repository_interface', true, 10),
    ('functions', 'concrete_repository_class', true, 20),
    ('functions', 'query_object', false, 30),
    ('functions', 'mapper', false, 40),
    ('service_contract', 'repository_interface', false, 50),
    ('data_contract', 'dto', true, 60),
    ('message_data_contracts', 'schema_definition', true, 70),
    ('event_data_contracts', 'schema_definition', true, 80),
    ('event_subscriptions', 'event_handler', true, 90),
    ('component_state_model', 'policy_adapter', false, 100),
    ('component_configuration', 'schema_definition', false, 110)
) AS m(element_key, realization_key, is_default, sort_order)
JOIN paa.component_element_types cet ON cet.element_key = m.element_key
JOIN paa.component_element_realization_types cert ON cert.realization_key = m.realization_key
ON CONFLICT (component_element_type_id, component_element_realization_type_id) DO UPDATE SET
  is_default = EXCLUDED.is_default,
  sort_order = EXCLUDED.sort_order,
  metadata_json = EXCLUDED.metadata_json;

COMMIT;

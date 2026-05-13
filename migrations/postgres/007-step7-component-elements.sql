-- Project for Autonomous Agents
-- Step 7 Postgres DDL: stable component element taxonomy and per-component elements
--
-- Prerequisites:
-- - 001-step1-control-plane.sql
-- - 002-step2-verification-recovery.sql
-- - 003-step3-knowledge-graph.sql
-- - 004-step4-coder-briefs.sql
-- - 005-step5-design-packages-and-sequencing.sql
-- - 006-step6-workflow-install-runtime-normalization.sql

BEGIN;

CREATE SCHEMA IF NOT EXISTS paa;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE t.typname = 'component_element_status' AND n.nspname = 'paa'
  ) THEN
    CREATE TYPE paa.component_element_status AS ENUM (
      'draft',
      'active',
      'superseded',
      'retired'
    );
  END IF;
END$$;

CREATE TABLE IF NOT EXISTS paa.component_element_types (
  component_element_type_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  element_key TEXT NOT NULL UNIQUE,
  label TEXT NOT NULL,
  category TEXT NOT NULL,
  description TEXT,
  is_brief_targetable BOOLEAN NOT NULL DEFAULT false,
  is_multi_instance BOOLEAN NOT NULL DEFAULT false,
  sort_order INTEGER NOT NULL,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS component_element_types_category_idx
  ON paa.component_element_types(category, sort_order);

CREATE TABLE IF NOT EXISTS paa.component_elements (
  component_element_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES paa.projects(project_id) ON DELETE CASCADE,
  component_id UUID NOT NULL REFERENCES paa.components(component_id) ON DELETE CASCADE,
  component_element_type_id UUID NOT NULL REFERENCES paa.component_element_types(component_element_type_id) ON DELETE RESTRICT,
  element_key TEXT NOT NULL,
  title TEXT,
  status paa.component_element_status NOT NULL DEFAULT 'draft',
  definition_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  provenance_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_by_role_id UUID REFERENCES paa.roles(role_id) ON DELETE SET NULL,
  created_by_agent_id UUID REFERENCES paa.agents(agent_id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (component_id, component_element_type_id, element_key)
);

CREATE INDEX IF NOT EXISTS component_elements_project_component_idx
  ON paa.component_elements(project_id, component_id, status, updated_at DESC);

CREATE INDEX IF NOT EXISTS component_elements_type_idx
  ON paa.component_elements(component_element_type_id, status, updated_at DESC);

INSERT INTO paa.component_element_types (
  element_key,
  label,
  category,
  description,
  is_brief_targetable,
  is_multi_instance,
  sort_order,
  metadata_json
)
VALUES
  (
    'role',
    'Role',
    'identity',
    'Single crisp statement of responsibility and authority boundary for the component.',
    true,
    false,
    10,
    '{"glossary_phase":"Component Design"}'::jsonb
  ),
  (
    'component_state_model',
    'Component State Model',
    'state',
    'Internal state, persistence concerns, and state-machine behavior for the component.',
    true,
    false,
    20,
    '{"glossary_phase":"Component Design"}'::jsonb
  ),
  (
    'service_contract',
    'Service Contract',
    'contract',
    'Public API surface, guarantees, and invariants offered by the component.',
    true,
    false,
    30,
    '{"glossary_phase":"Component Design"}'::jsonb
  ),
  (
    'data_contract',
    'Data Contract',
    'contract',
    'Owned data structures and schemas exchanged by the component.',
    true,
    false,
    40,
    '{"glossary_phase":"Component Design"}'::jsonb
  ),
  (
    'injected_services',
    'Injected Services',
    'dependency',
    'Dependencies the component requires at construction or composition time.',
    true,
    true,
    50,
    '{"glossary_phase":"Component Design"}'::jsonb
  ),
  (
    'interfaces',
    'Interfaces',
    'dependency',
    'Interfaces implemented by or depended on by the component.',
    true,
    true,
    60,
    '{"glossary_phase":"Component Design"}'::jsonb
  ),
  (
    'functions',
    'Functions',
    'behavior',
    'Concrete functions or methods that implement the service contract.',
    true,
    true,
    70,
    '{"glossary_phase":"Component Design"}'::jsonb
  ),
  (
    'messages_received',
    'Messages Received',
    'messaging',
    'Commands or queries accepted by the component.',
    true,
    true,
    80,
    '{"glossary_phase":"Component Design"}'::jsonb
  ),
  (
    'messages_published',
    'Messages Published',
    'messaging',
    'Outgoing messages emitted by the component.',
    true,
    true,
    90,
    '{"glossary_phase":"Component Design"}'::jsonb
  ),
  (
    'message_data_contracts',
    'Message Data Contracts',
    'messaging',
    'Schemas and structural contracts for received or published messages.',
    true,
    true,
    100,
    '{"glossary_phase":"Component Design"}'::jsonb
  ),
  (
    'event_subscriptions',
    'Event Subscriptions',
    'eventing',
    'Asynchronous events the component subscribes to and reacts to.',
    true,
    true,
    110,
    '{"glossary_phase":"Component Design"}'::jsonb
  ),
  (
    'events_published',
    'Events Published',
    'eventing',
    'Domain or system events raised by the component.',
    true,
    true,
    120,
    '{"glossary_phase":"Component Design"}'::jsonb
  ),
  (
    'event_data_contracts',
    'Event Data Contracts',
    'eventing',
    'Schemas and structural contracts for published events.',
    true,
    true,
    130,
    '{"glossary_phase":"Component Design"}'::jsonb
  ),
  (
    'component_lifecycle',
    'Component Lifecycle',
    'lifecycle',
    'Construction, steady-state, shutdown, recovery, and replacement behavior.',
    true,
    false,
    140,
    '{"glossary_phase":"Component Design"}'::jsonb
  ),
  (
    'component_configuration',
    'Component Configuration',
    'configuration',
    'Runtime-configurable settings consumed by the component.',
    true,
    false,
    150,
    '{"glossary_phase":"Component Design"}'::jsonb
  )
ON CONFLICT (element_key) DO UPDATE SET
  label = EXCLUDED.label,
  category = EXCLUDED.category,
  description = EXCLUDED.description,
  is_brief_targetable = EXCLUDED.is_brief_targetable,
  is_multi_instance = EXCLUDED.is_multi_instance,
  sort_order = EXCLUDED.sort_order,
  metadata_json = EXCLUDED.metadata_json,
  updated_at = now();

COMMIT;

-- Project for Autonomous Agents
-- Step 11 Postgres DDL: normalize component system_layer to support the layered architecture
--
-- Purpose:
-- - preserve backward compatibility with existing component rows
-- - allow new components to persist the preferred layered architecture vocabulary directly
-- - remove the need to map Domain Services to the older model-core label
--
-- Prerequisites:
-- - 004-step4-coder-briefs.sql

BEGIN;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_enum e
    JOIN pg_type t ON t.oid = e.enumtypid
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE n.nspname = 'paa'
      AND t.typname = 'system_layer'
      AND e.enumlabel = 'domain-core'
  ) THEN
    ALTER TYPE paa.system_layer ADD VALUE 'domain-core';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_enum e
    JOIN pg_type t ON t.oid = e.enumtypid
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE n.nspname = 'paa'
      AND t.typname = 'system_layer'
      AND e.enumlabel = 'domain-services'
  ) THEN
    ALTER TYPE paa.system_layer ADD VALUE 'domain-services';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_enum e
    JOIN pg_type t ON t.oid = e.enumtypid
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE n.nspname = 'paa'
      AND t.typname = 'system_layer'
      AND e.enumlabel = 'application-orchestration'
  ) THEN
    ALTER TYPE paa.system_layer ADD VALUE 'application-orchestration';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_enum e
    JOIN pg_type t ON t.oid = e.enumtypid
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE n.nspname = 'paa'
      AND t.typname = 'system_layer'
      AND e.enumlabel = 'infrastructure-ports'
  ) THEN
    ALTER TYPE paa.system_layer ADD VALUE 'infrastructure-ports';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_enum e
    JOIN pg_type t ON t.oid = e.enumtypid
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE n.nspname = 'paa'
      AND t.typname = 'system_layer'
      AND e.enumlabel = 'infrastructure-adapters'
  ) THEN
    ALTER TYPE paa.system_layer ADD VALUE 'infrastructure-adapters';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_enum e
    JOIN pg_type t ON t.oid = e.enumtypid
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE n.nspname = 'paa'
      AND t.typname = 'system_layer'
      AND e.enumlabel = 'host-surfaces'
  ) THEN
    ALTER TYPE paa.system_layer ADD VALUE 'host-surfaces';
  END IF;
END$$;

COMMIT;

BEGIN;

UPDATE paa.components
SET system_layer = 'domain-services'::paa.system_layer,
    metadata_json = jsonb_set(
      COALESCE(metadata_json, '{}'::jsonb),
      '{normalized_system_layer}',
      to_jsonb('domain-services'::text),
      true
    ),
    updated_at = now()
WHERE name = 'Component Design Planning Service'
  AND system_layer = 'model-core'::paa.system_layer;

COMMIT;

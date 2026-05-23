-- Project for Autonomous Agents
-- Step 15 Postgres DDL: extend component system-layer vocabulary to canonical active terms
--
-- Purpose:
-- - align live DB enum vocabulary with governed component-spec vocabulary
-- - add the canonical application-services layer directly to paa.system_layer
-- - support generic component-spec materialization without ad hoc layer mapping

BEGIN;

ALTER TYPE paa.system_layer ADD VALUE IF NOT EXISTS 'application-services';

COMMIT;

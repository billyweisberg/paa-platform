-- Project for Autonomous Agents
-- Step 14 Postgres DDL: implementation-plan progress and iterative successor vocabulary
--
-- Purpose:
-- - extend implementation-plan authority-state vocabulary for iterative thin-slice realization
-- - extend activity-state vocabulary for in-progress, deferred, and cancelled execution semantics
-- - preserve backward compatibility with existing historical states

BEGIN;

ALTER TYPE paa.implementation_plan_authority_state ADD VALUE IF NOT EXISTS 'active_plan';
ALTER TYPE paa.implementation_plan_authority_state ADD VALUE IF NOT EXISTS 'partially_realized_plan';
ALTER TYPE paa.implementation_plan_authority_state ADD VALUE IF NOT EXISTS 'completed_plan';
ALTER TYPE paa.implementation_plan_authority_state ADD VALUE IF NOT EXISTS 'blocked_plan';
ALTER TYPE paa.implementation_plan_authority_state ADD VALUE IF NOT EXISTS 'deferred_plan';

ALTER TYPE paa.implementation_plan_activity_state ADD VALUE IF NOT EXISTS 'in_progress';
ALTER TYPE paa.implementation_plan_activity_state ADD VALUE IF NOT EXISTS 'deferred';
ALTER TYPE paa.implementation_plan_activity_state ADD VALUE IF NOT EXISTS 'cancelled';

COMMIT;

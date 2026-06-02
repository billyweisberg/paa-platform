Title: PAA DB Cutover Plan
Doc-ID: paa-db-cutover-plan
Doc-Type: plan
Status: active
Lifecycle-Stage: deploy
Created: 2026-05-18
Last-Edited: 2026-05-18
Author: Billy Weisberg
Repo: paa-platform
Component: PaaDatabaseCutover
Domain: deploy-db
Keywords: deploy, db, cutover, postgres, migration
Depends-On: 2026-05-17-paa-local-postgres-setup.md
Supersedes: 
Superseded-By: 
Canonical: true
Review-After: 2026-06-15
Owners: 
Expires: 
Issue: 
PR: 
Authority-Source: 
Implementation-Status: 
Summary: Defines the repo-owned database cutover sequence from the shared AgentHub database to the PAA-local Postgres service.

# PAA DB Cutover Plan

## Goal

Cut `paa-platform` over from the shared AgentHub-backed Postgres container:

- container: `agenthub-mm-db`
- database: `paa_dev`
- user: `mmuser`

to the repo-owned PAA Postgres service:

- container: `paa-postgres-db`
- database: `paa_dev`
- user: `paa`

## Why cut over

The AgentHub database is another project's runtime dependency.

Leaving PAA on that DB creates:

- lifecycle coupling to AgentHub
- unclear ownership of schema changes
- ambiguous incident/debug boundaries
- poor local developer ergonomics
- a weaker deployment story for PAA as its own product

## Current state

Shared DB helper updated:

- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/db.py`

Repo-owned local DB definition added:

- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docker-compose.postgres.yml`

## Current code status

The previously identified runtime modules have now been migrated to use:

- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/db.py`

Completed migrations:

- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-producer/src/paa_producer/authority_runtime.py`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/handoff_runtime.py`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/readiness.py`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/runtime_workflow.py and related paa_core runtime services`

That means the remaining cutover work is now primarily:

- data/bootstrap
- proof-state re-materialization
- operational default flipping

## Recommended cutover phases

### Phase 1. Stand up the PAA-local DB

1. start `paa-postgres-db`
2. verify host connectivity on `127.0.0.1:55433`
3. verify Docker-exec connectivity through `paa_core.db`

### Phase 2. Apply canonical migrations to the local DB

Apply all PAA migrations in order:

- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/migrations/postgres/001-step1-control-plane.sql`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/migrations/postgres/002-step2-verification-recovery.sql`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/migrations/postgres/003-step3-knowledge-graph.sql`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/migrations/postgres/004-step4-coder-briefs.sql`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/migrations/postgres/005-step5-design-packages-and-sequencing.sql`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/migrations/postgres/006-step6-workflow-install-runtime-normalization.sql`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/migrations/postgres/007-step7-component-elements.sql`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/migrations/postgres/008-step8-component-element-realizations.sql`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/migrations/postgres/009-step9-service-oriented-target-taxonomy.sql`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/migrations/postgres/010-step10-coder-brief-authority-lifecycle.sql`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/migrations/postgres/011-step11-layered-system-layer-normalization.sql`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/migrations/postgres/012-step12-proof-only-closeout.sql`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/migrations/postgres/013-step13-implementation-plans.sql`

### Phase 3. Migrate runtime DB callers to shared settings

Refactor each direct DB caller to use:

- `settings_from_profile(...)`
- `run_psql(...)`

from:

- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/db.py`

Status:

- complete

This was the real application cutover step.

### Phase 4. Re-materialize or copy required proof state

Choose one:

1. re-derive proof slices and runtime evidence into the new local DB
2. export/import selected legacy data from AgentHub-backed `paa_dev`

Preferred option:

- re-derive the authoritative proof slices using the now-correct PAA-owned environment

That reduces hidden legacy carryover.

### Phase 5. Flip defaults

After Phase 3 and Phase 4 are complete:

- keep `PAA_DB_PROFILE=paa_dev` as the PAA-local default
- stop using AgentHub legacy profiles in normal docs and commands
- reserve legacy profiles for fallback inspection only

Status:

- partially complete

The code default now points to the PAA-local DB. Remaining work is to update any older operational habits and legacy commands to stop assuming AgentHub profiles during proof-data inspection.

### Phase 6. Retire legacy dependency

When the local DB is stable:

- remove routine dependency on `agenthub-mm-db`
- keep legacy profile support only if historical inspection still matters

## Preferred operating model after cutover

For host development:

- `PAA_DB_PROFILE=paa_dev_host`

For container-exec workflows:

- `PAA_DB_PROFILE=paa_dev_docker`

For general defaults:

- `PAA_DB_PROFILE=paa_dev`

## Decision

The best path is:

1. stand up the PAA-local DB
2. migrate runtime DB callers
3. re-derive proof data into the PAA-local DB
4. stop treating AgentHub as the primary DB dependency

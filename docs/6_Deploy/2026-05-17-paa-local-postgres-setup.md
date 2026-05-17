# PAA Local Postgres Setup

## Purpose

`paa-platform` should not depend on another project's Docker Compose stack for its primary database.

The PAA database is now defined as a repo-owned local service so:

- PAA schema evolution is owned by PAA
- local database development does not require AgentHub coordination
- deployment topology is clearer
- DB cutover and migration work can be tested in isolation

## Service definition

Repo-owned compose file:

- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docker-compose.postgres.yml`

Default local service shape:

- service: `paa-postgres`
- container: `paa-postgres-db`
- image: `postgres:16-alpine`
- database: `paa_dev`
- user: `paa`
- host port: `55433`
- volume: `paa-postgres-data`

The port intentionally differs from AgentHub's `5432` binding so both stacks can coexist during cutover.

## Default startup

```bash
docker compose -f docker-compose.postgres.yml up -d
```

## Default host connection

```bash
export PGPASSWORD="${PAA_LOCAL_DB_PASSWORD:-paadevpass}"
psql -h 127.0.0.1 -p "${PAA_LOCAL_DB_PORT:-55433}" -U "${PAA_LOCAL_DB_USER:-paa}" -d "${PAA_LOCAL_DB_NAME:-paa_dev}"
```

## Runtime profile model

`/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/db.py`

The shared DB helper now supports:

- local Docker-exec mode
- local host TCP mode
- legacy AgentHub Docker-exec mode
- legacy AgentHub host TCP mode

Preferred local profiles:

- `paa_dev`
- `paa_dev_docker`
- `paa_dev_host`

Legacy compatibility profiles:

- `agenthub_paa_dev_legacy`
- `agenthub_paa_dev_legacy_host`

## Design decision

The local PAA DB is now the intended default for:

- migrations
- schema development
- repository development
- derivation-state development
- project-design / implementation-plan development

Canonical migrations have been validated successfully against this local DB, including:

- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/migrations/postgres/013-step13-implementation-plans.sql`

AgentHub remains only a temporary compatibility source for already-materialized proof data and legacy inspection.

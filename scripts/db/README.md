# PAA DB Helpers

PAA now has a dedicated local Postgres definition:

- compose file: `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docker-compose.postgres.yml`
- default container: `paa-postgres-db`
- default database: `paa_dev`
- default user: `paa`
- default host port: `55433`

## Start the local PAA DB

```bash
docker compose -f docker-compose.postgres.yml up -d
```

## Stop the local PAA DB

```bash
docker compose -f docker-compose.postgres.yml down
```

## Connect from the host

```bash
export PGPASSWORD="${PAA_LOCAL_DB_PASSWORD:-paadevpass}"
psql -h 127.0.0.1 -p "${PAA_LOCAL_DB_PORT:-55433}" -U "${PAA_LOCAL_DB_USER:-paa}" -d "${PAA_LOCAL_DB_NAME:-paa_dev}"
```

## Supported `paa_core.db` profiles

- `paa_dev`
  - default PAA-local Docker profile
- `paa_dev_docker`
  - explicit container-exec profile for the PAA-local DB
- `paa_dev_host`
  - host TCP profile for the PAA-local DB
- `agenthub_paa_dev_legacy`
  - legacy Docker-exec profile for the AgentHub-backed DB
- `agenthub_paa_dev_legacy_host`
  - legacy host TCP profile for the AgentHub-backed DB

## Current cutover intent

The PAA-local DB is now the preferred development target.

The AgentHub-backed `paa_dev` remains a temporary legacy profile only until the remaining runtime modules are migrated off direct `agenthub-mm-db` assumptions.

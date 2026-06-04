# PAA Runtime Helpers

## Local RabbitMQ

PAA now has a dedicated local RabbitMQ definition:

- compose file: `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docker-compose.rabbitmq.yml`
- default container: `paa-rabbitmq`
- default AMQP port: `5672`
- default management port: `15672`
- default user: `guest`
- default password: `guest`

Start the local broker:

```bash
docker compose -f docker-compose.rabbitmq.yml up -d
```

Stop the local broker:

```bash
docker compose -f docker-compose.rabbitmq.yml down
```

Open the management UI:

```text
http://127.0.0.1:15672
```

Optional environment overrides:

- `PAA_LOCAL_RABBITMQ_USER`
- `PAA_LOCAL_RABBITMQ_PASSWORD`
- `PAA_LOCAL_RABBITMQ_VHOST`
- `PAA_LOCAL_RABBITMQ_AMQP_PORT`
- `PAA_LOCAL_RABBITMQ_MANAGEMENT_PORT`

## Runtime Supervisor

Foreground launcher:

```bash
/Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/runtime/run_runtime_supervisor.sh
```

Primary CLI control surface:

```bash
PYTHONPATH=packages/paa-core/src:packages/paa-core/src:packages/paa-cli/src:packages/paa-consumer/src:. python -m paa_cli runtime start --repo-root /Users/billyweisberg/Repos/billyweisberg/paa-platform
PYTHONPATH=packages/paa-core/src:packages/paa-core/src:packages/paa-cli/src:packages/paa-consumer/src:. python -m paa_cli runtime status --repo-root /Users/billyweisberg/Repos/billyweisberg/paa-platform
PYTHONPATH=packages/paa-core/src:packages/paa-core/src:packages/paa-cli/src:packages/paa-consumer/src:. python -m paa_cli runtime logs --repo-root /Users/billyweisberg/Repos/billyweisberg/paa-platform
PYTHONPATH=packages/paa-core/src:packages/paa-core/src:packages/paa-cli/src:packages/paa-consumer/src:. python -m paa_cli runtime stop --repo-root /Users/billyweisberg/Repos/billyweisberg/paa-platform
```

Thin wrapper:

```bash
/Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/runtime/runtime_supervisor_ctl.sh start
/Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/runtime/runtime_supervisor_ctl.sh status
/Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/runtime/runtime_supervisor_ctl.sh logs
/Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/runtime/runtime_supervisor_ctl.sh stop
```

What it does:

- uses the repo-local `PYTHONPATH`
- ensures queue topology first
- starts the default three-host runtime set:
  - `TechLead`
  - `Dev`
  - `QA`
- stores PID and logs under:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/.project/data/paa/runtime-supervisor/`

Bounded proof run:

```bash
/Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/runtime/run_runtime_supervisor.sh --max-iterations 1
```

Managed bounded run:

```bash
PYTHONPATH=packages/paa-core/src:packages/paa-core/src:packages/paa-cli/src:packages/paa-consumer/src:. python -m paa_cli runtime restart --repo-root /Users/billyweisberg/Repos/billyweisberg/paa-platform --max-iterations 3
```

The scripts assume:

- local Postgres is available
- local RabbitMQ is available

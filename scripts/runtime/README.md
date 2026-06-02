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

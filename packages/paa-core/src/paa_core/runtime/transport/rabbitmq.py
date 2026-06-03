"""RabbitMQ transport adapter utilities for the PAA runtime."""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request

from paa_core.runtime.support.config import DEFAULT_RUNTIME_QUEUE_EXCHANGE

DEFAULT_HOST = os.environ.get("FRACTAL_CORE_RABBITMQ_HOST", "127.0.0.1")
DEFAULT_MANAGEMENT_PORT = int(os.environ.get("FRACTAL_CORE_RABBITMQ_MANAGEMENT_PORT", "15672"))
DEFAULT_AMQP_PORT = int(os.environ.get("FRACTAL_CORE_RABBITMQ_AMQP_PORT", "5672"))
DEFAULT_USER = os.environ.get("FRACTAL_CORE_RABBITMQ_USER", "guest")
DEFAULT_PASSWORD = os.environ.get("FRACTAL_CORE_RABBITMQ_PASSWORD", "guest")
DEFAULT_VHOST = os.environ.get("FRACTAL_CORE_RABBITMQ_VHOST", "/")
DEFAULT_EXCHANGE = os.environ.get("FRACTAL_CORE_RABBITMQ_EXCHANGE", DEFAULT_RUNTIME_QUEUE_EXCHANGE)


class RabbitMQManagementClient:
    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_MANAGEMENT_PORT,
        user: str = DEFAULT_USER,
        password: str = DEFAULT_PASSWORD,
        vhost: str = DEFAULT_VHOST,
    ) -> None:
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.vhost = vhost
        self.base = f"http://{host}:{port}/api"
        token = base64.b64encode(f"{user}:{password}".encode()).decode()
        self.auth_header = f"Basic {token}"

    def _request(self, method: str, path: str, payload: object = None):
        data = None
        headers = {"Authorization": self.auth_header}
        if payload is not None:
            data = json.dumps(payload).encode()
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(self.base + path, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req) as resp:
                body = resp.read().decode() if resp.length != 0 else ""
                return resp.status, json.loads(body) if body else None
        except urllib.error.HTTPError as exc:
            body = exc.read().decode()
            raise RuntimeError(f"RabbitMQ API {method} {path} failed: {exc.code} {body}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"RabbitMQ API connection failed: {exc}") from exc

    def overview(self):
        return self._request("GET", "/overview")

    def queue(self, name: str):
        vhost = urllib.parse.quote(self.vhost, safe="")
        qname = urllib.parse.quote(name, safe="")
        return self._request("GET", f"/queues/{vhost}/{qname}")

    def declare_exchange(self, name: str, exchange_type: str = "direct", durable: bool = True):
        vhost = urllib.parse.quote(self.vhost, safe="")
        ename = urllib.parse.quote(name, safe="")
        return self._request(
            "PUT",
            f"/exchanges/{vhost}/{ename}",
            {"type": exchange_type, "durable": durable, "auto_delete": False, "internal": False, "arguments": {}},
        )

    def declare_queue(self, name: str, durable: bool = True):
        vhost = urllib.parse.quote(self.vhost, safe="")
        qname = urllib.parse.quote(name, safe="")
        return self._request("PUT", f"/queues/{vhost}/{qname}", {"durable": durable, "auto_delete": False, "arguments": {}})

    def bind_queue(self, exchange: str, queue: str, routing_key: str):
        vhost = urllib.parse.quote(self.vhost, safe="")
        ename = urllib.parse.quote(exchange, safe="")
        qname = urllib.parse.quote(queue, safe="")
        return self._request("POST", f"/bindings/{vhost}/e/{ename}/q/{qname}", {"routing_key": routing_key, "arguments": {}})

    def publish(self, exchange: str, routing_key: str, payload: object):
        vhost = urllib.parse.quote(self.vhost, safe="")
        ename = urllib.parse.quote(exchange, safe="")
        body = {
            "properties": {"delivery_mode": 2},
            "routing_key": routing_key,
            "payload": json.dumps(payload),
            "payload_encoding": "string",
        }
        return self._request("POST", f"/exchanges/{vhost}/{ename}/publish", body)

    def get_messages(self, queue: str, count: int = 1, ackmode: str = "ack_requeue_true", truncate: int = 50000):
        vhost = urllib.parse.quote(self.vhost, safe="")
        qname = urllib.parse.quote(queue, safe="")
        body = {
            "count": count,
            "ackmode": ackmode,
            "encoding": "auto",
            "truncate": truncate,
        }
        return self._request("POST", f"/queues/{vhost}/{qname}/get", body)

    def purge_queue(self, queue: str):
        vhost = urllib.parse.quote(self.vhost, safe="")
        qname = urllib.parse.quote(queue, safe="")
        return self._request("DELETE", f"/queues/{vhost}/{qname}/contents")


def build_default_management_client() -> RabbitMQManagementClient:
    return RabbitMQManagementClient(
        user=DEFAULT_USER,
        password=DEFAULT_PASSWORD,
        host=DEFAULT_HOST,
        port=DEFAULT_MANAGEMENT_PORT,
        vhost=DEFAULT_VHOST,
    )


__all__ = [
    'DEFAULT_AMQP_PORT',
    'DEFAULT_EXCHANGE',
    'DEFAULT_HOST',
    'DEFAULT_MANAGEMENT_PORT',
    'DEFAULT_PASSWORD',
    'DEFAULT_USER',
    'DEFAULT_VHOST',
    'RabbitMQManagementClient',
    'build_default_management_client',
]

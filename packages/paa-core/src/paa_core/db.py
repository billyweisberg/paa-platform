"""Shared DB access for repo-local PAA runtime."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Iterable

import psycopg


@dataclass(frozen=True)
class DBSettings:
    mode: str
    container: str | None
    host: str | None
    port: int | None
    name: str
    user: str
    password: str | None = None


DB_PROFILES = {
    'paa_dev': DBSettings(
        mode='docker_exec',
        container='paa-postgres-db',
        host='127.0.0.1',
        port=55433,
        name='paa_dev',
        user='paa',
    ),
    'paa_dev_docker': DBSettings(
        mode='docker_exec',
        container='paa-postgres-db',
        host='127.0.0.1',
        port=55433,
        name='paa_dev',
        user='paa',
    ),
    'paa_dev_host': DBSettings(
        mode='tcp',
        container='paa-postgres-db',
        host='127.0.0.1',
        port=55433,
        name='paa_dev',
        user='paa',
    ),
    'agenthub_paa_dev_legacy': DBSettings(
        mode='docker_exec',
        container='agenthub-mm-db',
        host='127.0.0.1',
        port=5432,
        name='paa_dev',
        user='mmuser',
    ),
    'agenthub_paa_dev_legacy_host': DBSettings(
        mode='tcp',
        container='agenthub-mm-db',
        host='127.0.0.1',
        port=5432,
        name='paa_dev',
        user='mmuser',
    ),
}


def settings_from_profile(profile: str | None) -> DBSettings:
    profile_name = profile or os.environ.get('PAA_DB_PROFILE', 'paa_dev')
    base = DB_PROFILES.get(profile_name, DB_PROFILES['paa_dev'])
    port_raw = os.environ.get('PAA_DB_PORT')
    return DBSettings(
        mode=os.environ.get('PAA_DB_MODE', base.mode),
        container=os.environ.get('PAA_DB_CONTAINER', base.container),
        host=os.environ.get('PAA_DB_HOST', base.host),
        port=int(port_raw) if port_raw else base.port,
        name=os.environ.get('PAA_DB_NAME', base.name),
        user=os.environ.get('PAA_DB_USER', base.user),
        password=os.environ.get('PAA_DB_PASSWORD', base.password),
    )


def settings_with_overrides(
    profile: str | None,
    *,
    mode: str | None = None,
    container: str | None = None,
    host: str | None = None,
    port: int | None = None,
    name: str | None = None,
    user: str | None = None,
    password: str | None = None,
) -> DBSettings:
    base = settings_from_profile(profile)
    return DBSettings(
        mode=mode or base.mode,
        container=container or base.container,
        host=host or base.host,
        port=port or base.port,
        name=name or base.name,
        user=user or base.user,
        password=password if password is not None else base.password,
    )


def sql_literal(value: object | None) -> str:
    if value is None:
        return 'NULL'
    return "'" + str(value).replace("'", "''") + "'"


def _connect(settings: DBSettings) -> psycopg.Connection:
    if not settings.host or not settings.port:
        raise RuntimeError('PAA DB settings require host and port for Python driver access')
    return psycopg.connect(
        host=settings.host,
        port=settings.port,
        dbname=settings.name,
        user=settings.user,
        password=settings.password,
        autocommit=True,
    )


def _stringify_cell(value: object | None) -> str:
    if value is None:
        return ''
    if isinstance(value, (dict, list)):
        return json.dumps(value)
    return str(value)


def run_psql(sql: str, *, settings: DBSettings | None = None) -> str:
    cfg = settings or settings_from_profile(None)
    try:
        with _connect(cfg) as conn, conn.cursor() as cur:
            cur.execute(sql)
            if cur.description is None:
                return ''
            rows = cur.fetchall()
    except psycopg.Error as exc:
        raise RuntimeError(str(exc).strip() or 'PAA PostgreSQL command failed') from exc
    return '\n'.join('\t'.join(_stringify_cell(cell) for cell in row) for row in rows)


def query_rows(sql: str, *, settings: DBSettings | None = None) -> list[list[str]]:
    out = run_psql(sql, settings=settings)
    rows: list[list[str]] = []
    for line in out.splitlines():
        if not line.strip():
            continue
        rows.append(line.split('	'))
    return rows


def execute_all(statements: Iterable[str], *, settings: DBSettings | None = None) -> None:
    for statement in statements:
        run_psql(statement, settings=settings)

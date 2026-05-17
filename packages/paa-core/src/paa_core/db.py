"""Shared DB access for repo-local PAA runtime."""

from __future__ import annotations

from dataclasses import dataclass
import os
import subprocess
from typing import Iterable


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


def sql_literal(value):
    if value is None:
        return 'NULL'
    return "'" + str(value).replace("'", "''") + "'"


def run_psql(sql: str, *, settings: DBSettings | None = None) -> str:
    cfg = settings or settings_from_profile(None)
    if cfg.mode == 'docker_exec':
        if not cfg.container:
            raise RuntimeError('PAA DB docker_exec mode requires a container name')
        cmd = ['docker', 'exec', '-i', cfg.container, 'psql', '-U', cfg.user, '-d', cfg.name, '-At', '-F', '	']
        env = None
    elif cfg.mode == 'tcp':
        if not cfg.host or not cfg.port:
            raise RuntimeError('PAA DB tcp mode requires host and port')
        cmd = ['psql', '-h', cfg.host, '-p', str(cfg.port), '-U', cfg.user, '-d', cfg.name, '-At', '-F', '	']
        env = os.environ.copy()
        if cfg.password is not None:
            env['PGPASSWORD'] = cfg.password
    else:
        raise RuntimeError(f'Unsupported PAA DB mode: {cfg.mode}')
    result = subprocess.run(
        cmd,
        input=sql,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or 'PAA psql command failed')
    return result.stdout


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

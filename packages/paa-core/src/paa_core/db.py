"""Shared DB access for repo-local PAA runtime."""

from __future__ import annotations

from dataclasses import dataclass
import os
import subprocess
from typing import Iterable


@dataclass(frozen=True)
class DBSettings:
    container: str
    name: str
    user: str


DB_PROFILES = {
    'paa_dev': DBSettings(container='agenthub-mm-db', name='paa_dev', user='mmuser'),
}


def settings_from_profile(profile: str | None) -> DBSettings:
    profile_name = profile or os.environ.get('PAA_DB_PROFILE', 'paa_dev')
    base = DB_PROFILES.get(profile_name, DB_PROFILES['paa_dev'])
    return DBSettings(
        container=os.environ.get('PAA_DB_CONTAINER', base.container),
        name=os.environ.get('PAA_DB_NAME', base.name),
        user=os.environ.get('PAA_DB_USER', base.user),
    )


def sql_literal(value):
    if value is None:
        return 'NULL'
    return "'" + str(value).replace("'", "''") + "'"


def run_psql(sql: str, *, settings: DBSettings | None = None) -> str:
    cfg = settings or settings_from_profile(None)
    result = subprocess.run(
        ['docker', 'exec', '-i', cfg.container, 'psql', '-U', cfg.user, '-d', cfg.name, '-At', '-F', '	'],
        input=sql,
        capture_output=True,
        text=True,
        check=False,
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

#!/usr/bin/env python3
"""Validate repo-local automation TOML files."""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore


def iter_targets(args: list[str]) -> list[Path]:
    if not args:
        raise SystemExit('usage: validate_automation_toml.py <file-or-dir> [<file-or-dir> ...]')
    paths: list[Path] = []
    for raw in args:
        path = Path(raw).expanduser().resolve()
        if path.is_dir():
            paths.extend(sorted(path.glob('*/automation.toml')))
        else:
            paths.append(path)
    return paths


def validate(path: Path) -> dict[str, object]:
    with path.open('rb') as fh:
        data = tomllib.load(fh)
    return {
        'file': str(path),
        'valid': True,
        'top_level_keys': list(data.keys()),
        'id': data.get('id'),
        'status': data.get('status'),
        'execution_environment': data.get('execution_environment'),
    }


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    ok = True
    for path in iter_targets(argv):
        try:
            print(json.dumps(validate(path)))
        except Exception as exc:
            ok = False
            print(json.dumps({'file': str(path), 'valid': False, 'error': str(exc)}))
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())

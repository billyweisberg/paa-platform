"""Managed lifecycle control for the unified PAA runtime supervisor."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

_RUNTIME_DIR_RELATIVE = Path('.project/data/paa/runtime-supervisor')
_PID_FILE_NAME = 'runtime-supervisor.pid'
_LOG_FILE_NAME = 'runtime-supervisor.log'


def runtime_supervisor_paths(repo_root: Path) -> dict[str, Path]:
    runtime_dir = repo_root / _RUNTIME_DIR_RELATIVE
    return {
        'runtime_dir': runtime_dir,
        'pid_file': runtime_dir / _PID_FILE_NAME,
        'log_file': runtime_dir / _LOG_FILE_NAME,
    }


def _pid_from_file(pid_file: Path) -> int | None:
    try:
        raw = pid_file.read_text().strip()
    except FileNotFoundError:
        return None
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def _pid_running(pid: int | None) -> bool:
    if pid is None:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def runtime_supervisor_status(repo_root: Path) -> dict[str, Any]:
    paths = runtime_supervisor_paths(repo_root)
    paths['runtime_dir'].mkdir(parents=True, exist_ok=True)
    pid = _pid_from_file(paths['pid_file'])
    running = _pid_running(pid)
    if not running and paths['pid_file'].exists():
        paths['pid_file'].unlink(missing_ok=True)
    return {
        'ok': True,
        'running': running,
        'pid': pid if running else None,
        'pid_file': str(paths['pid_file']),
        'log_file': str(paths['log_file']),
    }


def start_runtime_supervisor(
    repo_root: Path,
    *,
    intake_mode: str = 'claim_next',
    emit_next_assignment: bool = True,
    emit_worker_result: bool = True,
    emit_verification: bool = True,
    max_iterations: int = 0,
    poll_interval_seconds: float = 5.0,
) -> dict[str, Any]:
    status = runtime_supervisor_status(repo_root)
    if status['running']:
        return {
            'ok': False,
            'reason': 'already_running',
            'pid': status['pid'],
            'pid_file': status['pid_file'],
            'log_file': status['log_file'],
        }

    paths = runtime_supervisor_paths(repo_root)
    paths['runtime_dir'].mkdir(parents=True, exist_ok=True)
    paths['log_file'].write_text('')
    env = os.environ.copy()
    pythonpath = 'packages/paa-core/src:packages/paa-cli/src:packages/paa-consumer/src:.'
    env['PYTHONPATH'] = f"{pythonpath}:{env['PYTHONPATH']}" if env.get('PYTHONPATH') else pythonpath
    env['PYTHONUNBUFFERED'] = '1'

    argv = [
        sys.executable,
        '-m',
        'paa_cli',
        'runtime',
        'supervisor',
        '--repo-root',
        str(repo_root),
        '--intake-mode',
        intake_mode,
        '--max-iterations',
        str(max_iterations),
        '--poll-interval-seconds',
        str(poll_interval_seconds),
    ]
    argv.append('--emit-next-assignment' if emit_next_assignment else '--no-emit-next-assignment')
    argv.append('--emit-worker-result' if emit_worker_result else '--no-emit-worker-result')
    argv.append('--emit-verification' if emit_verification else '--no-emit-verification')

    with paths['log_file'].open('ab', buffering=0) as log:
        proc = subprocess.Popen(
            argv,
            cwd=repo_root,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            close_fds=True,
        )
    paths['pid_file'].write_text(str(proc.pid))
    return {
        'ok': True,
        'pid': proc.pid,
        'pid_file': str(paths['pid_file']),
        'log_file': str(paths['log_file']),
    }


def stop_runtime_supervisor(repo_root: Path) -> dict[str, Any]:
    paths = runtime_supervisor_paths(repo_root)
    pid = _pid_from_file(paths['pid_file'])
    if not _pid_running(pid):
        paths['pid_file'].unlink(missing_ok=True)
        return {
            'ok': False,
            'reason': 'not_running',
            'pid_file': str(paths['pid_file']),
        }
    assert pid is not None
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        paths['pid_file'].unlink(missing_ok=True)
        return {
            'ok': True,
            'stopped': True,
            'pid': pid,
        }
    for _ in range(20):
        time.sleep(0.5)
        if not _pid_running(pid):
            paths['pid_file'].unlink(missing_ok=True)
            return {
                'ok': True,
                'stopped': True,
                'pid': pid,
            }
    try:
        os.kill(pid, signal.SIGKILL)
    except OSError:
        pass
    paths['pid_file'].unlink(missing_ok=True)
    return {
        'ok': True,
        'stopped': True,
        'pid': pid,
        'forced': True,
    }


def restart_runtime_supervisor(repo_root: Path, **kwargs: Any) -> dict[str, Any]:
    stop_runtime_supervisor(repo_root)
    return start_runtime_supervisor(repo_root, **kwargs)


def runtime_supervisor_logs(repo_root: Path, *, lines: int = 200) -> str:
    log_file = runtime_supervisor_paths(repo_root)['log_file']
    if not log_file.exists():
        return ''
    content = log_file.read_text(errors='replace').splitlines()
    if lines <= 0:
        return ''
    return '\n'.join(content[-lines:])


__all__ = [
    'runtime_supervisor_logs',
    'runtime_supervisor_paths',
    'runtime_supervisor_status',
    'restart_runtime_supervisor',
    'start_runtime_supervisor',
    'stop_runtime_supervisor',
]

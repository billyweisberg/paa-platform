#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RUNTIME_DIR="${REPO_ROOT}/.project/data/paa/runtime-supervisor"
PID_FILE="${RUNTIME_DIR}/runtime-supervisor.pid"
LOG_FILE="${RUNTIME_DIR}/runtime-supervisor.log"
LAUNCHER="${REPO_ROOT}/scripts/runtime/run_runtime_supervisor.sh"

mkdir -p "${RUNTIME_DIR}"

usage() {
  cat <<'USAGE'
usage: runtime_supervisor_ctl.sh <start|stop|status|restart|logs> [-- launcher-args...]
USAGE
}

is_running() {
  if [[ ! -f "${PID_FILE}" ]]; then
    return 1
  fi
  local pid
  pid="$(cat "${PID_FILE}")"
  [[ -n "${pid}" ]] || return 1
  kill -0 "${pid}" 2>/dev/null
}

start_cmd() {
  local extra_args=("$@")
  if is_running; then
    printf '{\n  "ok": false,\n  "reason": "already_running",\n  "pid": %s,\n  "pid_file": "%s",\n  "log_file": "%s"\n}\n' "$(cat "${PID_FILE}")" "${PID_FILE}" "${LOG_FILE}"
    return 1
  fi
  rm -f "${PID_FILE}"
  : > "${LOG_FILE}"
  local py_args=(python3 -)
  if (( ${#extra_args[@]} > 0 )); then
    py_args+=("${extra_args[@]}")
  fi
  REPO_ROOT="${REPO_ROOT}" LAUNCHER="${LAUNCHER}" PID_FILE="${PID_FILE}" LOG_FILE="${LOG_FILE}" "${py_args[@]}" <<'PY'
import os
import subprocess
import sys
from pathlib import Path

repo_root = Path(os.environ['REPO_ROOT'])
launcher = os.environ['LAUNCHER']
pid_file = Path(os.environ['PID_FILE'])
log_file = Path(os.environ['LOG_FILE'])
extra_args = sys.argv[1:]

env = os.environ.copy()
pythonpath = 'packages/paa-core/src:packages/paa-producer/src:packages/paa-cli/src:packages/paa-consumer/src:.'
env['PYTHONPATH'] = f"{pythonpath}:{env['PYTHONPATH']}" if env.get('PYTHONPATH') else pythonpath
env['PYTHONUNBUFFERED'] = '1'

with log_file.open('ab', buffering=0) as log:
    proc = subprocess.Popen(
        ['bash', launcher, *extra_args],
        cwd=repo_root,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
        close_fds=True,
    )

pid_file.write_text(str(proc.pid))
print('{')
print('  "ok": true,')
print(f'  "pid": {proc.pid},')
print(f'  "pid_file": "{pid_file}",')
print(f'  "log_file": "{log_file}"')
print('}')
PY
}

stop_cmd() {
  if ! is_running; then
    rm -f "${PID_FILE}"
    printf '{\n  "ok": false,\n  "reason": "not_running",\n  "pid_file": "%s"\n}\n' "${PID_FILE}"
    return 1
  fi
  local pid
  pid="$(cat "${PID_FILE}")"
  kill "${pid}" 2>/dev/null || true
  for _ in $(seq 1 20); do
    if ! kill -0 "${pid}" 2>/dev/null; then
      rm -f "${PID_FILE}"
      printf '{\n  "ok": true,\n  "stopped": true,\n  "pid": %s\n}\n' "${pid}"
      return 0
    fi
    sleep 0.5
  done
  kill -9 "${pid}" 2>/dev/null || true
  rm -f "${PID_FILE}"
  printf '{\n  "ok": true,\n  "stopped": true,\n  "pid": %s,\n  "forced": true\n}\n' "${pid}"
}

status_cmd() {
  if is_running; then
    local pid
    pid="$(cat "${PID_FILE}")"
    printf '{\n  "ok": true,\n  "running": true,\n  "pid": %s,\n  "pid_file": "%s",\n  "log_file": "%s"\n}\n' "${pid}" "${PID_FILE}" "${LOG_FILE}"
    return 0
  fi
  rm -f "${PID_FILE}"
  printf '{\n  "ok": true,\n  "running": false,\n  "pid_file": "%s",\n  "log_file": "%s"\n}\n' "${PID_FILE}" "${LOG_FILE}"
}

logs_cmd() {
  touch "${LOG_FILE}"
  tail -n 200 "${LOG_FILE}"
}

if [[ $# -lt 1 ]]; then
  usage
  exit 2
fi

command="$1"
shift
if [[ $# -gt 0 && "$1" == "--" ]]; then
  shift
fi

case "${command}" in
  start)
    start_cmd "$@"
    ;;
  stop)
    stop_cmd
    ;;
  status)
    status_cmd
    ;;
  restart)
    stop_cmd >/dev/null 2>&1 || true
    start_cmd "$@"
    ;;
  logs)
    logs_cmd
    ;;
  *)
    usage
    exit 2
    ;;
esac

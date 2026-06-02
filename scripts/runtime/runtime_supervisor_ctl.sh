#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${REPO_ROOT}"

PYTHONPATH_VALUE="packages/paa-core/src:packages/paa-producer/src:packages/paa-cli/src:packages/paa-consumer/src:."
export PYTHONPATH="${PYTHONPATH_VALUE}${PYTHONPATH:+:${PYTHONPATH}}"

if [[ $# -lt 1 ]]; then
  echo "usage: runtime_supervisor_ctl.sh <start|stop|status|restart|logs> [-- cli-args...]" >&2
  exit 2
fi

command="$1"
shift

case "${command}" in
  start)
    exec python -m paa_consumer runtime-supervisor-start --repo-root "${REPO_ROOT}" "$@"
    ;;
  stop)
    exec python -m paa_consumer runtime-supervisor-stop --repo-root "${REPO_ROOT}" "$@"
    ;;
  status)
    exec python -m paa_consumer runtime-supervisor-status --repo-root "${REPO_ROOT}" "$@"
    ;;
  restart)
    exec python -m paa_consumer runtime-supervisor-restart --repo-root "${REPO_ROOT}" "$@"
    ;;
  logs)
    exec python -m paa_consumer runtime-supervisor-logs --repo-root "${REPO_ROOT}" "$@"
    ;;
  *)
    echo "unknown command: ${command}" >&2
    exit 2
    ;;
esac

#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${REPO_ROOT}"

PYTHONPATH_VALUE="packages/paa-core/src:packages/paa-producer/src:packages/paa-cli/src:packages/paa-consumer/src:."
export PYTHONPATH="${PYTHONPATH_VALUE}${PYTHONPATH:+:${PYTHONPATH}}"

python -m paa_cli queue ensure-topology --repo-root "${REPO_ROOT}" >/dev/null

exec python -m paa_cli runtime supervisor --repo-root "${REPO_ROOT}" "$@"

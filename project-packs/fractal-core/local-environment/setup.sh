#!/bin/sh
set -eu

CURRENT_ROOT="$(git rev-parse --show-toplevel)"

find_canonical_root() {
  git worktree list --porcelain | awk '/^worktree /{print substr($0,10)}' | while IFS= read -r path; do
    if [ "$path" != "$CURRENT_ROOT" ] && [ -d "$path/.project/data/paa" ]; then
      printf '%s\n' "$path"
      return 0
    fi
  done
}

CANONICAL_ROOT="$(find_canonical_root || true)"
if [ -z "${CANONICAL_ROOT:-}" ]; then
  CANONICAL_ROOT="$CURRENT_ROOT"
fi

mkdir -p "$CANONICAL_ROOT/.project/data" \
  "$CANONICAL_ROOT/.project/data/paa/automation-memory" \
  "$CANONICAL_ROOT/.project/data/paa/logs/automations" \
  "$CANONICAL_ROOT/.codex-work/uv-cache"

if [ "$CURRENT_ROOT" != "$CANONICAL_ROOT" ]; then
  mkdir -p "$CURRENT_ROOT/.project/data"
  rm -rf "$CURRENT_ROOT/.project/data/paa"
  ln -s "$CANONICAL_ROOT/.project/data/paa" "$CURRENT_ROOT/.project/data/paa"

  if [ ! -e "$CURRENT_ROOT/.venv" ] && [ -e "$CANONICAL_ROOT/.venv" ]; then
    ln -s "$CANONICAL_ROOT/.venv" "$CURRENT_ROOT/.venv"
  fi
fi

BOOTSTRAP_PYTHON=""
if [ -x "$CANONICAL_ROOT/.venv/bin/python" ]; then
  BOOTSTRAP_PYTHON="$CANONICAL_ROOT/.venv/bin/python"
elif [ -x "/opt/homebrew/opt/python@3.13/bin/python3" ]; then
  BOOTSTRAP_PYTHON="/opt/homebrew/opt/python@3.13/bin/python3"
elif command -v python3.12 >/dev/null 2>&1; then
  BOOTSTRAP_PYTHON="$(command -v python3.12)"
elif command -v python3 >/dev/null 2>&1; then
  BOOTSTRAP_PYTHON="$(command -v python3)"
fi

if [ -z "$BOOTSTRAP_PYTHON" ]; then
  echo "Codex local environment bootstrap requires Python 3.12+ or the canonical repo .venv." >&2
  exit 1
fi

export UV_CACHE_DIR="$CANONICAL_ROOT/.codex-work/uv-cache"
export FRACTAL_CORE_HANDOFF_STATE_DIR="$CANONICAL_ROOT/.project/data/paa/queue-state/fractal-core-handoff"
export PAA_AUTOMATION_LOG_ROOT="$CANONICAL_ROOT/.project/data/paa/logs/automations"
export PAA_AUTOMATION_SHARED_REPO_ROOT="$CANONICAL_ROOT"

CANONICAL_PYTHONPATH=""
if [ -d "$CANONICAL_ROOT/.codex/paa/vendor" ] && [ -d "$CANONICAL_ROOT/.codex/paa/lib" ]; then
  CANONICAL_PYTHONPATH="$CANONICAL_ROOT/.codex/paa/vendor:$CANONICAL_ROOT/.codex/paa/lib"
fi

if [ "$CURRENT_ROOT" != "$CANONICAL_ROOT" ]; then
  if [ -n "$CANONICAL_PYTHONPATH" ]; then
    PYTHONPATH="$CANONICAL_PYTHONPATH${PYTHONPATH:+:$PYTHONPATH}" \
      "$BOOTSTRAP_PYTHON" - <<'PY' "$CURRENT_ROOT"
from pathlib import Path
import sys
from paa_core.install import install_consumer_runtime

install_consumer_runtime(Path(sys.argv[1]))
PY
  fi
fi

mkdir -p "$CURRENT_ROOT/.codex-work"
cat > "$CURRENT_ROOT/.codex-work/local-environment.env" <<EOF
PAA_AUTOMATION_SHARED_REPO_ROOT=$CANONICAL_ROOT
FRACTAL_CORE_HANDOFF_STATE_DIR=$FRACTAL_CORE_HANDOFF_STATE_DIR
PAA_AUTOMATION_LOG_ROOT=$PAA_AUTOMATION_LOG_ROOT
UV_CACHE_DIR=$UV_CACHE_DIR
EOF

echo "codex_setup_ok"

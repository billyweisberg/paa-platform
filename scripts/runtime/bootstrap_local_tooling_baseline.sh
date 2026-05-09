#!/usr/bin/env bash
set -euo pipefail

# Bootstrap the local tooling baseline used by the current proven role set.
#
# Goals:
# - keep a modern default python available for lightweight local scripting
# - keep a dedicated shared uv tools environment for repeatable test tooling
# - provide tomli fallback for older interpreters when tomllib is unavailable

TOOLS_VENV="${TOOLS_VENV:-$HOME/.codex/venvs/paa-tools}"
DEFAULT_PYTHON="${DEFAULT_PYTHON:-}"
TOOLS_PYTHON_VERSION="${TOOLS_PYTHON_VERSION:-3.12}"

REQUIRED_USER_PACKAGES=(
  PyYAML
  jsonschema
  tomli
)

REQUIRED_TOOLS_PACKAGES=(
  tomli
  PyYAML
  jsonschema
  pytest
  ruff
  mypy
  types-PyYAML
  packaging
)

echo "== Fractal Core local tooling baseline =="
echo "tools venv: ${TOOLS_VENV}"
echo "tools python version: ${TOOLS_PYTHON_VERSION}"

if [ -z "${DEFAULT_PYTHON}" ]; then
  if [ -x "/opt/homebrew/opt/python@3.13/bin/python3" ]; then
    DEFAULT_PYTHON="/opt/homebrew/opt/python@3.13/bin/python3"
  else
    DEFAULT_PYTHON="python3"
  fi
fi

echo "default python command: ${DEFAULT_PYTHON}"

if ! command -v uv >/dev/null 2>&1; then
  echo "error: uv is required but not found on PATH" >&2
  exit 1
fi

if ! command -v "${DEFAULT_PYTHON}" >/dev/null 2>&1; then
  echo "error: ${DEFAULT_PYTHON} is required but not found on PATH" >&2
  exit 1
fi

echo
echo "== Default python =="
"${DEFAULT_PYTHON}" --version

echo
echo "== Installing user-level compatibility packages for default python =="
"${DEFAULT_PYTHON}" -m pip install --user --break-system-packages --upgrade "${REQUIRED_USER_PACKAGES[@]}"

echo
echo "== Creating/updating shared uv tools environment =="
uv venv "${TOOLS_VENV}" --python "${TOOLS_PYTHON_VERSION}"
uv pip install --python "${TOOLS_VENV}/bin/python" --upgrade "${REQUIRED_TOOLS_PACKAGES[@]}"

echo
echo "== Verifying imports =="
"${DEFAULT_PYTHON}" - <<'PY'
import sys
print(f"default_python={sys.executable}")
print(f"default_python_version={sys.version.split()[0]}")
try:
    import tomllib  # noqa: F401
    print("tomllib=stdlib")
except Exception:
    import tomli  # noqa: F401
    print("tomli=fallback")
import yaml  # noqa: F401
import jsonschema  # noqa: F401
print("default_python_imports=ok")
PY

"${TOOLS_VENV}/bin/python" - <<'PY'
import sys
import tomli  # noqa: F401
import yaml  # noqa: F401
import jsonschema  # noqa: F401
import pytest  # noqa: F401
import mypy  # noqa: F401
import packaging  # noqa: F401
print(f"tools_python={sys.executable}")
print(f"tools_python_version={sys.version.split()[0]}")
print("tools_python_imports=ok")
PY

echo
echo "== Recommended PATH entries for fresh shells =="
cat <<'EOF'
export PATH="/opt/homebrew/opt/python@3.13/bin:$PATH"
export PATH="$PATH:$HOME/.codex/venvs/paa-tools/bin"
export PATH="$PATH:$HOME/Library/Python/3.13/bin"
export PATH="$PATH:$HOME/Library/Python/3.9/bin"
EOF

echo
echo "baseline_status=ok"

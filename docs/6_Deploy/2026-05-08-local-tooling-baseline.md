# Local Tooling Baseline

## Purpose

Define the local Python and test-tooling baseline for:
- current-role-set runtime work
- current-role-set test execution
- lightweight local scripting around PAA

This exists to stop repeated missing-module churn such as:
- `tomllib` / `tomli`
- `yaml`
- `jsonschema`

## Desired interpreter model

### Default local scripting interpreter

Prefer a modern `python3` from Homebrew:
- target:
  - `/opt/homebrew/opt/python@3.13/bin/python3`

This gives:
- stdlib `tomllib`
- modern packaging behavior
- fewer compatibility surprises than the Apple system Python

### Shared test/tooling environment

Use one shared `uv` tools environment:
- path:
  - `$HOME/.codex/venvs/paa-tools`
- target python:
  - `3.12`

This environment is the stable home for:
- `pytest`
- `ruff`
- `mypy`
- `jsonschema`
- shared import verification during testing

### Older interpreter compatibility

Some commands or host tools may still reach an older system Python such as `3.9`.

For that case:
- prefer `tomllib` when available
- fall back to `tomli` when `tomllib` is missing

## Required baseline packages

### Default python user-level compatibility packages
- `PyYAML`
- `jsonschema`
- `tomli`

### Shared `uv` tools environment packages
- `tomli`
- `PyYAML`
- `jsonschema`
- `pytest`
- `ruff`
- `mypy`
- `types-PyYAML`
- `packaging`

## Bootstrap script

Use:

```bash
/Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/runtime/bootstrap_local_tooling_baseline.sh
```

What it does:
- installs the default-python user-level compatibility packages
- creates or refreshes the shared `uv` tools environment
- verifies imports for both layers
- prints the recommended PATH entries

## PATH contract

Fresh shells should make these layers available:

```bash
export PATH="/opt/homebrew/opt/python@3.13/bin:$PATH"
export PATH="$PATH:$HOME/.codex/venvs/paa-tools/bin"
export PATH="$PATH:$HOME/Library/Python/3.13/bin"
export PATH="$PATH:$HOME/Library/Python/3.9/bin"
```

## Runtime usage guidance

### Use default `python3` for
- quick local validation scripts
- lightweight tooling checks
- import verification

### Use the shared `uv` tools env for
- `pytest`
- `ruff`
- `mypy`
- `jsonschema` CLI
- repeatable test-tool command execution

### Use repo-local PAA wrappers for
- consumer runtime work:
  - `.codex/paa/bin/paa-consumer`
- producer runtime work:
  - `.codex/paa/bin/paa-producer`

Do not replace repo-local wrapper usage with the shared tools env.

## Success criteria

The baseline is considered healthy when:
- `python3` resolves to a modern interpreter
- `yaml` and `jsonschema` import in the default interpreter
- `tomllib` is available in modern python, or `tomli` fallback is available in older python
- `pytest`, `ruff`, `mypy`, and `jsonschema` resolve from the shared tools environment in fresh shells

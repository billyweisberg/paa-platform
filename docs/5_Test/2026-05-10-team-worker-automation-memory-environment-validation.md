# Team Worker Automation Memory And Environment Validation

## Purpose

Record the root cause and fix for two app-launched automation environment defects observed during `Stage W7 Phase 4` setup:
- home-folder automation memory was not readable through the repo-scoped filesystem MCP view
- `CODEX_HOME` was unset in the app-launched shell context

## Observed defects

### 1. Home-folder automation memory boundary

Observed behavior:
- the automation attempted to use a memory file under `/Users/billyweisberg/.codex/automations/<automation_id>/memory.md`
- that path sits outside the repo tree and is not a reliable MCP filesystem surface for repo-scoped automation work

Impact:
- the automation had to fall back to shell-based file reads instead of using the normal repo-visible file path

### 2. Unset `CODEX_HOME`

Observed behavior:
- the automation attempted a memory write through logic that assumed `$CODEX_HOME` was set
- app-launched local-mode runs did not guarantee that variable in the shell environment

Impact:
- the first memory write path failed until an explicit path was substituted manually

## Root cause

The Team Worker automation contract had already standardized repo-local logs, wrappers, queue state, and runtime artifacts, but it had not explicitly standardized automation memory.

That left the automations drifting back to Codex home-folder memory conventions:
- `/Users/billyweisberg/.codex/automations/<automation_id>/memory.md`
- `$CODEX_HOME`

Those assumptions were not compatible with the repo-local PAA runtime boundary we are testing.

## Fix applied

### Contract fix

Authoritative memory path is now repo-local:
- `{{REPO_ROOT}}/.project/data/paa/automation-memory/<automation_id>.md`

This path is now documented in:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/6_Deploy/2026-05-09-team-worker-automation-contract.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/6_Deploy/2026-05-09-automation-logging-contract.md`

### Bootstrap fix

Updated source helper:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/runtime/bootstrap_automation_logging.sh`

Updated installed consumer helper:
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/scripts/runtime/bootstrap_automation_logging.sh`

New behavior:
- creates repo-local automation memory root
- ensures `<automation_id>.md` exists
- exports `PAA_AUTOMATION_MEMORY_FILE`
- records `memory_file` in `summary.json`

### Launcher prompt fix

Updated Team Worker-aware automation definitions so they now instruct the model to:
- use the repo-local automation memory file directly
- stop relying on `$CODEX_HOME`
- stop treating home-folder automation memory as authoritative

Updated surfaces:
- project-pack automation definitions in `/Users/billyweisberg/Repos/billyweisberg/paa-platform/project-packs/fractal-core/automations/`
- installed consumer automation definitions in `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/automations/`
- active home-level UI registrations in `/Users/billyweisberg/.codex/automations/`

## Validation

Validated with the installed consumer helper:
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/scripts/runtime/run_automation_preflight_with_logging.sh`

Observed for `docs-dev-automation`:
- `summary.json` includes:
  - `memory_file = /Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.project/data/paa/automation-memory/docs-dev-automation.md`
- repo-local memory file exists
- no dependency on `CODEX_HOME` was required for the helper/bootstrap path

## Result

The two environment defects are now understood and corrected at the contract and launcher level.

Remaining boundary:
- this does not by itself convert the automations to the final Codex-native worktree/environment model
- it does remove the specific repo-boundary and `CODEX_HOME` failures that surfaced in the current Team Worker pilot

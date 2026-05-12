# 2026-05-11 Codex-Native Worktree Local Environment Validation

## Goal

Validate that Team Worker automations can launch from a Codex-managed git worktree with:

- a pinned Python environment
- shared PAA runtime state
- a worktree-local `.codex/paa` install
- no fallback to ambient macOS `python3`

## Changes Under Test

- consumer repo Local Environment bootstrap:
  - `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/setup.sh`
- project-pack bootstrap source:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/project-packs/fractal-core/local-environment/setup.sh`
- consumer runtime installer:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/install.py`
- Team Worker automation definitions switched to:
  - `execution_environment = "worktree"`

## Disposable validation surface

Created disposable git worktree:

- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex-work/test-codex-native-worktree`

Then copied and executed:

```bash
./.codex/setup.sh
```

## Observed bootstrap result

The bootstrap completed successfully:

- `codex_setup_ok`

The disposable worktree then contained:

- worktree-local wrapper:
  - `.codex/paa/bin/paa-consumer`
- shared runtime-state link:
  - `.project/data/paa -> /Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.project/data/paa`
- shared virtualenv link:
  - `.venv -> /Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.venv`
- pinned environment file:
  - `.codex-work/local-environment.env`

The generated environment file recorded:

- `PAA_AUTOMATION_SHARED_REPO_ROOT=/Users/billyweisberg/Repos/billyweisberg/fractal-core-python`
- `FRACTAL_CORE_HANDOFF_STATE_DIR=/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.project/data/paa/queue-state/fractal-core-handoff`
- `PAA_AUTOMATION_LOG_ROOT=/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.project/data/paa/logs/automations`
- `UV_CACHE_DIR=/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex-work/uv-cache`

## Preflight proof

Executed from the disposable worktree:

```bash
./.codex/paa/scripts/runtime/run_automation_preflight_with_logging.sh \
  --repo-root /Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex-work/test-codex-native-worktree \
  --automation-id python-team-automation \
  --role-key python-team \
  --role-display-name "Python Dev" \
  --target-role python-team
```

Result:

- `ok = true`
- `should_invoke_model = false`
- `skip_model_invocation = true`
- `gate_reason = no_role_work_detected`

Most important outcome:

- the worktree-local preflight succeeded from the Codex-style worktree surface
- it did not fall back to ambient macOS `python3`
- it used the pinned environment prepared by `.codex/setup.sh`

## Conclusion

The Team Worker automation surface is now reconciled enough to run as a true Codex-native worktree automation model:

- Codex owns the execution worktree
- `.codex/setup.sh` owns environment bootstrap
- PAA still owns routing, packets, lineage, and shared runtime state

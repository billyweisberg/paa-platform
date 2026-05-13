# Team Worker Repo-Local Worktree Root Correction

## Purpose

Record the correction made after the live `Stage W7 Phase 4` Python Dev run proved that home-folder Team Worker worktrees were not writable from app-launched Codex automations.

## Observed failure

The Python Team automation could:
- claim the assignment
- prepare, inspect, and enter the role worktree

But it could not write there because the prepared worktree lived under:
- `<codex_home>/worktrees/paa/fractal-core-python/issue-108-dev`

The app-launched sandbox for the automation allowed writes only under the consumer repo root:
- `<consumer_repo_root>`

## Root cause

The runtime helper `default_role_worktree_path()` still hard-coded the default worktree root to the home-folder Codex path.

That path worked for shell-driven experiments but violated the writable boundary for app-launched local-mode automations.

## Fix

Updated runtime default:
- repo-local root:
  - `<repo_root>/.codex-work/worktrees/paa/<role_branch>`
- optional override:
  - `$PAA_ROLE_WORKTREE_ROOT/<role_branch>`

Updated source runtime:
- `packages/paa-consumer/src/paa_consumer/techlead.py`

Updated installed consumer runtime:
- `<consumer_repo_root>/.codex/paa/lib/paa_consumer/techlead.py`

Updated active docs:
- `docs/2_Design/2026-05-09-team-worker-roles-design-spec.md`
- `docs/6_Deploy/2026-05-07-phase-i2-automation-execution-environment-contract.md`
- `docs/6_Deploy/2026-05-09-team-worker-automation-contract.md`

## Live pilot cleanup

To keep the active issue `108` slice coherent:
- removed the obsolete home-folder worktree:
  - `<codex_home>/worktrees/paa/fractal-core-python/issue-108-dev`
- cleared the obsolete blocked Python result packet
- re-sent the Python assignment packet to `fractal-core-python`

The current assignment now waits on the queue with no registered default worktree yet.
That is expected under the corrected model: the next Python run should prepare or reuse the repo-local default worktree itself.

## Result

The Team Worker default worktree root is now aligned with the writable repo boundary of app-launched Codex automations.

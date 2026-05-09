# Automation Logging Contract

## Purpose

Define the logging contract for PAA automations so we can:
- observe no-work polling without spending tokens
- trace app-launched automation behavior coherently
- preserve run evidence in the consumer repo
- debug launch, preflight, worktree, and return-path failures without relying on UI memory

This contract is intentionally repo-local and durable.

## Scope

This contract applies to:
- `TechLead`
- `Delivery Architect`
- `QA`
- all `Team Worker Roles`

It covers:
- log root placement
- run directory layout
- minimum event fields
- bootstrap behavior
- event append behavior
- stdout/stderr capture expectations
- retention boundary for the current pilot stage

## Canonical log root

Consumer-side automation logs must live under:
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.project/data/paa/logs/automations/`

Why here:
- same durability boundary as queue state, reports, claims, artifacts, and evidence
- local to the consumer repo
- not hidden in machine-global UI state
- available for pilot debugging and later reporting

Do not use:
- `/tmp`
- home-folder automation directories
- ad hoc scratch folders outside the repo

## Run directory layout

For each automation run, create:
- `<log_root>/<automation_id>/<run_id>/events.jsonl`
- `<log_root>/<automation_id>/<run_id>/stdout.log`
- `<log_root>/<automation_id>/<run_id>/stderr.log`
- `<log_root>/<automation_id>/<run_id>/summary.json`
- `<log_root>/<automation_id>/<run_id>/env.sh`

Example:
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.project/data/paa/logs/automations/docs-dev-automation/2026-05-09T18-38-45Z-79585/events.jsonl`

## Run id contract

Run ids should be stable enough to correlate logs across files and simple enough to read manually.

Current bootstrap pattern:
- `<utc timestamp>-<pid>`

Example:
- `2026-05-09T18-38-45Z-79585`

## Required environment variables

The logging bootstrap must define at least:
- `PAA_AUTOMATION_LOG_ROOT`
- `PAA_AUTOMATION_RUN_DIR`
- `PAA_AUTOMATION_RUN_ID`
- `PAA_AUTOMATION_REPO_ROOT`
- `PAA_AUTOMATION_AUTOMATION_ID`
- `PAA_AUTOMATION_ROLE_KEY`
- `PAA_AUTOMATION_ROLE_DISPLAY_NAME`
- `PAA_AUTOMATION_EVENTS_FILE`
- `PAA_AUTOMATION_STDOUT_LOG`
- `PAA_AUTOMATION_STDERR_LOG`
- `PAA_AUTOMATION_SUMMARY_FILE`
- `PAA_AUTOMATION_LOG_LEVEL`
- `PAA_AUTOMATION_LOG_FORMAT`

Recommended defaults:
- `PAA_AUTOMATION_LOG_LEVEL=INFO`
- `PAA_AUTOMATION_LOG_FORMAT=jsonl`

## Bootstrap helper

Current helper:
- source:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/runtime/bootstrap_automation_logging.sh`
- installed consumer path:
  - `.codex/paa/scripts/runtime/bootstrap_automation_logging.sh`

Purpose:
- create the run directory
- create `stdout.log`, `stderr.log`, `events.jsonl`, and `summary.json`
- emit shell `export` lines so a launcher can bring the logging env into scope

Usage shape:

```bash
/Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/runtime/bootstrap_automation_logging.sh \
  --repo-root /Users/billyweisberg/Repos/billyweisberg/fractal-core-python \
  --automation-id docs-dev-automation \
  --role-key docs-dev \
  --role-display-name "Docs Dev" \
  --phase stage-w7-phase2 \
  --issue-number 106 \
  --package-id-external fcore-stage1-2026-05-02-issue106-retirement-boundary-diagnostics \
  --brief-id-external fcore-coder-2026-05-02-issue106-retirement-boundary-diagnostics
```

## Event append helper

Current helper:
- source:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/runtime/log_automation_event.py`
- installed consumer path:
  - `.codex/paa/scripts/runtime/log_automation_event.py`

Purpose:
- append one JSONL event to the current run log
- use the already-bootstrapped environment variables

Example:

```bash
/Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/runtime/log_automation_event.py \
  --event preflight_check \
  --phase stage-w7-phase2 \
  --status ok \
  --message "no work present" \
  --extra-json '{"should_invoke_model": false}'
```

## Logged preflight helper

Current helper:
- source:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/scripts/runtime/run_automation_preflight_with_logging.sh`
- installed consumer path:
  - `.codex/paa/scripts/runtime/run_automation_preflight_with_logging.sh`

Purpose:
- bootstrap a run log
- execute `automation-preflight`
- persist the raw preflight JSON
- append a structured preflight event
- print the preflight JSON back to stdout for the caller

## Minimum event fields

Each event line should include:
- `ts`
- `run_id`
- `automation_id`
- `role_key`
- `role_display_name`
- `phase`
- `event`
- `status`
- `repo_root`

When available, also include:
- `cwd`
- `worktree_path`
- `queue`
- `message_id`
- `duration_ms`
- `model_invoked`
- `message`
- `extra`

## Minimum phases to log

Every automation run should log these phase families when applicable:

1. launcher
- run bootstrap
- launch cwd
- resolved repo root

2. preflight
- queue checked
- target role
- `should_invoke_model`
- `gate_reason`

3. worktree
- lineage resolved
- branch selected
- worktree prepared or reused
- cwd transitioned

4. execution
- model invoked or skipped
- key role milestones
- packet compile/send steps

5. completion
- success/failure
- cleanup result
- blocking error if any

## No-work polling rule

No-work polling must still create a run envelope and at least one preflight event.

That gives us durable proof that:
- the automation ran
- no work existed
- no model invocation was needed

This is especially important for `Stage W7 Phase 2`.

## Current practical boundary

This contract currently starts at the first runtime-controlled step the automation can execute.

That means:
- we can now log the no-work preflight path and later runtime steps
- we can read those repo-local logs after a UI-launched automation run

It does not mean:
- we can observe a hidden pre-model scheduler hook inside the Codex app itself

So the current logging truth begins when the automation executes the installed logged-preflight helper, not before.

## Stdout and stderr capture

Automation launchers should append command stdout and stderr to:
- `stdout.log`
- `stderr.log`

The logging contract does not require every PAA command to become a structured logger immediately.
The initial acceptable model is:
- JSONL event log for lifecycle markers
- stdout/stderr capture for raw command output

## Retention policy for current stage

Current pilot-stage rule:
- keep logs by default
- do not add aggressive cleanup yet

Reason:
- during pilot and Team Worker rollout, debug visibility is more valuable than automatic pruning

A later lifecycle/ops slice can add:
- age-based cleanup
- run-count caps
- compression or archival

## Relationship to the Team Worker pilot

We paused after:
- `Stage W7 Phase 1: UI visibility validation`

The next live test remains:
- `Stage W7 Phase 2: no-work poll and non-invocation validation`

This logging contract exists so that when we resume Phase 2, we do it with:
- durable run directories
- preflight event logs
- stdout/stderr capture

## Acceptance state

This logging contract is complete enough for the current stage when:
- a reusable bootstrap helper exists
- a reusable event append helper exists
- the Team Worker pilot can resume with logging in place
- logs are written under the repo-local consumer runtime state tree

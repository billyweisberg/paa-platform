# Phase I2 Automation Execution Environment Contract

## Purpose

Define the explicit execution-environment contract for the current proven consumer role set:
- `TechLead`
- `Delivery Architect`
- `Python Dev`
- `QA`

This contract exists so the automations do not infer their runtime environment ad hoc.
A current automation is only considered runnable when it follows this contract exactly.

## Scope

This contract covers:
- canonical consumer repo root
- launch cwd
- deterministic role worktree root and execution cwd
- repo-local PAA wrapper usage
- repo-local `uv` usage
- required and optional environment variables
- forbidden deprecated runtime roots
- fail-closed rules when the environment is not aligned

This contract does not yet define:
- the full role execution skill behavior
- multi-worker family expansion
- broad unpause policy by itself

## Canonical consumer repo root

For the current proven role set, all consumer-side automations must treat this path as the canonical repo root:
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python`

All role automations must start from this repo identity even when they later execute inside a prepared role worktree.

## Launch cwd contract

At automation launch time, the cwd must be the canonical consumer repo root:
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python`

Why:
- repo-local PAA wrappers are installed relative to this root
- authority install, queue state, reports, claims, and artifacts all hang off this root
- pre-run no-work gating must be able to inspect repo-local runtime state before any worktree transition

Required launch behavior:
- UI-visible automation registrations must point `cwds` at the canonical consumer repo root
- pre-run no-work gating must run from the canonical consumer repo root
- repo-local wrapper resolution must happen from the canonical consumer repo root

## Worktree root contract

Deterministic role worktrees live under:
- default repo-local root:
  - `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex-work/worktrees/paa/<role_branch>`
- optional override root:
  - `$PAA_ROLE_WORKTREE_ROOT/<role_branch>`

Current deterministic role branch forms:
- `issue-<issue_number>-delivery`
- `issue-<issue_number>-dev`
- `issue-<issue_number>-qa`

Canonical branch form:
- `issue-<issue_number>`

Ownership model:
- `TechLead` owns lineage and branch authorization
- role automation owns create-or-reuse of its deterministic role worktree beneath that authorization

## Execution cwd contract

There are two allowed execution cwd states.

### 1. Preflight / routing / queue inspection

Use the canonical consumer repo root:
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python`

Allowed commands from this cwd:
- `.codex/paa/bin/paa-consumer automation-preflight`
- `.codex/paa/bin/paa-consumer techlead-*`
- `.codex/paa/bin/paa-consumer queue-*`
- `.codex/paa/bin/paa-producer authority *` when compiling packets against the canonical repo state

### 2. Role execution after worktree preparation

After the role worktree is prepared and inspected, the role automation must switch its execution cwd to the prepared worktree path returned by:
- `techlead-prepare-role-worktree`
- `techlead-inspect-role-worktree`
- `techlead-role-entry`

Examples:
- `/Users/billyweisberg/.codex/worktrees/paa/fractal-core-python/issue-106-delivery`
- `/Users/billyweisberg/.codex/worktrees/paa/fractal-core-python/issue-106-dev`
- `/Users/billyweisberg/.codex/worktrees/paa/fractal-core-python/issue-106-qa`

Role work must execute there, not back in the canonical consumer repo root.

## Repo-local PAA wrapper contract

All automations must use repo-local wrappers, not direct module invocation and not deprecated home-folder runtime entrypoints.

Consumer wrapper:
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/bin/paa-consumer`

Producer wrapper:
- `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/bin/paa-producer`

Required rules:
- use repo-local wrappers for PAA queue, TechLead, and packet compilation actions
- do not call deprecated home-folder Fractal Core skills or runtime scripts directly
- do not hardcode system Python module entrypoints in the automation prompt

## `uv` contract

### PAA wrapper layer

The repo-local PAA wrappers are the required bootstrap path.
They already prefer:
- `uv run --python 3.12`

and only fall back to:
- `python3 >= 3.12`

Automation rule:
- call the repo-local wrappers first
- do not reimplement their bootstrap behavior in automation prompts

### Role execution layer

When a role automation needs to run repo work directly inside its prepared worktree:
- prefer `uv run` from the prepared worktree cwd
- use the worktree-local project configuration and lockfile
- fail closed if `uv` is unavailable rather than silently switching to an unrelated interpreter

That means the role execution skill should eventually emit exact role-local commands shaped like:
- `uv run ...` from the prepared worktree
- or repo-local PAA wrapper commands that themselves resolve through the installed wrapper bootstrap

## Environment variable contract

### Required

These environment variables must be correct when the automation runs.

`FRACTAL_CORE_HANDOFF_STATE_DIR`
- required durable queue state root
- expected value pattern:
  - `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.project/data/paa/queue-state/fractal-core-handoff`
- reason:
  - ensures claims and queue-runtime state stay repo-local and durable

### Optional but supported

RabbitMQ connection variables may be provided when defaults are not correct:
- `FRACTAL_CORE_RABBITMQ_HOST`
- `FRACTAL_CORE_RABBITMQ_MANAGEMENT_PORT`
- `FRACTAL_CORE_RABBITMQ_AMQP_PORT`
- `FRACTAL_CORE_RABBITMQ_USER`
- `FRACTAL_CORE_RABBITMQ_PASSWORD`
- `FRACTAL_CORE_RABBITMQ_VHOST`
- `FRACTAL_CORE_RABBITMQ_EXCHANGE`

PAA DB variables may be provided when defaults are not correct:
- `PAA_DB_CONTAINER`
- `PAA_DB_NAME`
- `PAA_DB_USER`

### Wrapper-managed

These should be treated as wrapper-managed, not automation-authored:
- `PYTHONPATH`

Reason:
- the repo-local wrapper sets the correct vendor/lib path bootstrap already
- automation prompts should not try to reconstruct it manually

## Forbidden runtime roots and fallback behavior

Automations must not use deprecated home-folder runtime surfaces as operational dependencies.

Forbidden as runtime roots:
- `/Users/billyweisberg/.codex/skills/fractal-core-*`
- `/Users/billyweisberg/.codex/skills/fractal-core-handoff-common/`
- deprecated home-folder automation prompts as execution truth

Allowed home-folder usage in this phase:
- global UI registration entries under `/Users/billyweisberg/.codex/automations/`
- deterministic worktree root under `/Users/billyweisberg/.codex/worktrees/`

Important distinction:
- home-folder automations are UI registration surfaces
- repo-local installs are runtime execution surfaces

## Fail-closed rules

An automation must not invoke the model when any of these are false:
- pre-run gate says no work is present
- canonical consumer repo root is not the active launch cwd for preflight
- required repo-local wrapper path is missing
- required installed authority package is missing
- required deterministic worktree cannot be resolved for role execution
- `FRACTAL_CORE_HANDOFF_STATE_DIR` is not pointing at the repo-local durable queue state root
- role execution requires `uv` but `uv` is not available

An automation must stop and report a blocker instead of guessing when:
- the role worktree exists but is on the wrong branch
- the prepared worktree path does not match deterministic ownership/lineage rules
- required environment variables point at deprecated or unrelated runtime roots

## Role-specific execution summary

### TechLead
- launch cwd: canonical consumer repo root
- execution cwd: canonical consumer repo root for this phase
- primary wrapper: `.codex/paa/bin/paa-consumer`
- no-work gate required before model invocation: yes

### Delivery Architect
- launch cwd: canonical consumer repo root
- preflight cwd: canonical consumer repo root
- execution cwd after preparation: deterministic delivery role worktree
- primary wrappers:
  - `.codex/paa/bin/paa-consumer`
  - `.codex/paa/bin/paa-producer`
- no-work gate required before model invocation: yes

### Python Dev
- launch cwd: canonical consumer repo root
- preflight cwd: canonical consumer repo root
- execution cwd after preparation: deterministic Python role worktree
- primary wrappers:
  - `.codex/paa/bin/paa-consumer`
  - `.codex/paa/bin/paa-producer`
- direct repo work should prefer `uv run` from the prepared worktree
- no-work gate required before model invocation: yes

### QA
- launch cwd: canonical consumer repo root
- preflight cwd: canonical consumer repo root
- execution cwd after preparation: deterministic QA role worktree
- primary wrappers:
  - `.codex/paa/bin/paa-consumer`
  - `.codex/paa/bin/paa-producer`
- direct repo work should prefer `uv run` from the prepared worktree when repo commands are needed
- no-work gate required before model invocation: yes

## Acceptance state for this slice

This slice is complete when:
- the execution environment is documented as one explicit contract
- the contract names repo root, worktree root, cwd transitions, wrapper usage, `uv` behavior, and env vars
- later automation-skill work can implement against this contract instead of guessing

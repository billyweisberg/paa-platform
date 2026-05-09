# Stage W7 Team Worker Automation Pilot Test Plan

Supersedes:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/5_Test/2026-05-09-phase-i4-automation-pilot-test-plan.md`

## Purpose

Re-baseline the paused automation pilot work against the `Team Worker Roles` target model.

This plan exists so we stop testing a temporary automation surface and instead validate the actual target implementation shape:
- Team Worker-aware automation registrations
- Team Worker-aware launcher prompts
- repo-local installed runtime wrappers
- deterministic no-work preflight
- deterministic role worktree transition

## Pilot scope

### Always in scope
- `TechLead`
- `Delivery Architect`
- `Python Dev`
- `QA`

### Added Team Worker proving scope
- `Docs Dev`

### Present but deferred for first pilot execution
- `Frontend Dev`
- `Backend Dev`
- `Infra Dev`

These are now part of the launch surface and registry model, but the first resumed pilot should still stay narrow enough to be supervised coherently.

## Why this plan replaces the older pilot plan

The older pilot plan assumed only the current proven role set.
That is no longer the target implementation.

Since Team Worker Roles are now first-class project data, the pilot must validate:
- the expanded launcher surface
- the generalized worker execution contract
- the new Team Worker role vocabulary

without widening immediately into every possible worker lane at once.

## Fixed inputs

- consumer repo root:
  - `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python`
- platform repo root:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform`
- producer repo root:
  - `/Users/billyweisberg/Repos/Individual-Centricity/appdev`
- consumer wrapper:
  - `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/bin/paa-consumer`
- producer wrapper:
  - `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/bin/paa-producer`
- authority manifest:
  - `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.project/data/paa/authority/current/authority/fractal-core-python-authority.json`
- Team Worker role registry:
  - `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/team-worker-roles.json`
- home-level UI registration root:
  - `/Users/billyweisberg/.codex/automations`

Default proving fixture:
- issue: `106`
- PR: `107`
- package id external:
  - `fcore-stage1-2026-05-02-issue106-retirement-boundary-diagnostics`
- brief id external:
  - `fcore-coder-2026-05-02-issue106-retirement-boundary-diagnostics`

## Test sequence

1. `Phase 0` Team Worker pilot readiness snapshot
2. `Phase 1` UI visibility validation for Team Worker-aware launch surfaces
3. `Phase 2` no-work poll and non-invocation validation
4. `Phase 3` Team Worker single-role launch environment validation
5. `Phase 4` supervised Team Worker live pilot slice
6. `Phase 5` final deliberate unpause decision

## Phase 0: Team Worker pilot readiness snapshot

### Goal
Confirm that the pilot starts from a Team Worker-aware installed and registered baseline.

### Inputs
- Team Worker launcher/bootstrap validation
- installed consumer runtime
- home-level UI registrations
- Team Worker registry file
- queue state

### Expected outputs
- all queues empty or explained
- installed consumer runtime present
- `techlead-status --validate-schema` passes
- all eight home-level Team Worker-aware registrations present
- Team Worker registry file present

### Success
- the pilot is testing the target Team Worker model, not a stale launcher layer

### Evaluation
- queue checks
- file existence checks
- runtime validation checks

### Knobs
- queue cleanup timing
- runtime reinstall before pilot
- pilot fixture ids

## Phase 1: UI visibility validation

### Goal
Confirm visible app/UI presence of the Team Worker-aware launch surfaces.

### Inputs
- Codex UI automation list
- home-level UI registrations

### Steps
1. verify visible presence of:
   - `Fractal Core TechLead Automation`
   - `Fractal Core Delivery Architect Automation`
   - `Python Team Automation`
   - `Fractal Core QA Automation`
2. verify visible presence of:
   - `Docs Dev Automation`
3. optionally note whether the new Team Worker registrations are also visible for:
   - `Frontend Dev Automation`
   - `Backend Dev Automation`
   - `Infra Dev Automation`

### Expected outputs
- current proven role set remains visible
- `Docs Dev Automation` is visible

### Success
- app-layer visibility covers the target pilot roles

### Evaluation
- user UI confirmation

### Knobs
- app refresh timing
- whether to require all new Team Worker roles visible before first resumed pilot or only `Docs Dev`

## Phase 2: No-work poll and non-invocation validation

### Goal
Confirm that Team Worker-aware automations still honor the deterministic no-work gate.

### Inputs
- empty queue baseline
- app-launched no-work automation runs
- `automation-preflight` runtime behavior

### Expected outputs
- no model invocation for:
  - `TechLead`
  - `Delivery Architect`
  - `Python Dev`
  - `QA`
  - `Docs Dev`
- no worktree side effects

### Success
- generalized Team Worker launcher prompts did not break non-model preflight behavior

### Evaluation
- user-visible app behavior
- runtime preflight checks
- queue checks

### Knobs
- which role to test first
- whether to include one or all expanded Team Worker roles in no-work validation

## Phase 3: Team Worker single-role launch environment validation

### Goal
Validate one app-launched Team Worker automation against the real runtime/environment contract.

### Recommended role
- `Docs Dev`

### Inputs
- one disposable Team Worker assignment packet for `Docs Dev`
- app-launched `Docs Dev Automation`
- execution environment contract

### Expected outputs
- automation wakes only because work exists
- correct repo root launch context
- correct no-work bypass behavior when no packet exists
- deterministic Team Worker role worktree path
- correct `worker_result_packet` role identity

### Success
- one non-Python Team Worker automation launches coherently from the app boundary

### Evaluation
- user-visible app behavior
- runtime queue/worktree/result verification

### Knobs
- chosen Team Worker proving role
- send versus compile-only return behavior
- whether to use disposable issue fixture or historical issue fixture

## Phase 4: Supervised Team Worker live pilot slice

### Goal
Run one supervised live slice through the Team Worker-aware automation surface.

### Recommended slice
- `TechLead -> Delivery Architect -> TechLead -> Docs Dev -> TechLead -> QA -> TechLead`

### Expected outputs
- app-launched automations wake in the correct sequence
- no hidden queue-order reasoning is required
- top-level `techlead-status` remains coherent
- disposable worktrees are created only when work exists
- queues return cleanly to zero after cleanup

### Success
- the Team Worker model is proven from the actual app/UI launcher boundary, not only from CLI/runtime surfaces

### Evaluation
- UI observation
- queue checks
- worktree checks
- packet validation and acknowledgment checks
- top-level TechLead status checks

### Knobs
- whether to keep the pilot on `Docs Dev` first or revert to `Python Dev` for a control comparison
- whether to keep packets pending during intermediate checks
- cleanup timing after each step

## Phase 5: Final deliberate unpause decision

### Goal
Decide whether the current Team Worker-aware automation surface is ready for deliberate unpause.

### Expected outputs
One of:
- `not ready`
- `ready for additional supervised pilot only`
- `ready for deliberate unpause`

### Success
- the decision is grounded in the Team Worker-aware pilot evidence, not the older current-role-set-only pilot assumptions

### Evaluation
- aggregate pass/fail status of Phases 0 through 4
- unresolved defects still open after the pilot

### Knobs
- whether visibility-only or execution defects are treated as blocking
- whether all Team Worker roles must be visible before unpause or only the pilot scope roles

## Current decision before pilot execution

At the moment this plan is written:
- pilot execution remains paused
- the launcher/bootstrap layer is now aligned enough to resume the pilot
- no final unpause decision should be made until this W7 plan is executed

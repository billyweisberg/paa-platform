Superseded by:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/5_Test/2026-05-09-stage-w7-team-worker-automation-pilot-test-plan.md`

# Phase I4 Automation Pilot Test Plan

## Purpose

Define the supervised app/UI-launched automation pilot plan for the current proven role set before deliberate unpause.

Current proven role set:
- `TechLead`
- `Delivery Architect`
- `Python Dev`
- `QA`

This plan exists to answer, explicitly and repeatably:
- what we test from the actual app/UI boundary
- in what order we run the pilot
- what you do versus what I verify
- what inputs are required
- what success looks like
- how results are evaluated
- what knobs can be adjusted if a pilot phase fails or needs a controlled variant

## Scope

This plan validates the actual automation launcher path for the current proven role set only.

It covers:
- UI-visible automation presence
- app-launched no-work polling behavior
- app-launched model invocation gating
- app-launched runtime environment adherence
- app-launched role worktree behavior
- app-launched packet return behavior
- supervised live pilot through the current proven role set
- final deliberate unpause decision after the pilot

It does not cover:
- broader worker-family expansion
- broader Delivery Architect outcome expansion beyond the current supported path
- unsupervised cutover on first contact
- broad operatorless productionization beyond the current proven role set

## Test strategy

The pilot sequence moves from cheapest user-observable UI checks to the most integrated live supervised slice.

Order matters:
1. confirm app/UI visibility and launch surfaces
2. confirm no-work polling does not wake the model
3. confirm one role can launch with the correct runtime context
4. confirm one supervised current-role-set live slice through the app boundary
5. make the final unpause decision

This keeps us from treating UI presence as equivalent to runnable automation behavior.

## Collaboration model for this plan

This is a human-in-the-loop pilot.

### What you do
- open the app UI
- confirm what appears on screen
- launch the automations from the actual UI surface when the plan says to do so
- report visible UI behavior when it cannot be observed from the repo/runtime side alone

### What I do
- prepare runtime state
- provide exact commands and expected observations
- verify queue/worktree/packet/runtime behavior behind the scenes
- classify each phase as pass/fail/blocked
- update the written record after each phase

## Global test inputs

### Fixed inputs for the current plan
- consumer repo root:
  - `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python`
- platform repo root:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform`
- producer repo root:
  - `/Users/billyweisberg/Repos/Individual-Centricity/appdev`
- canonical consumer wrapper:
  - `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/bin/paa-consumer`
- canonical producer wrapper:
  - `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/bin/paa-producer`
- canonical authority manifest path:
  - `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.project/data/paa/authority/current/authority/fractal-core-python-authority.json`
- queue state root:
  - `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.project/data/paa/queue-state/fractal-core-handoff`
- home-level automation registration root:
  - `/Users/billyweisberg/.codex/automations`
- canonical issue branch pattern:
  - `issue-<issue_number>`
- deterministic role branch patterns:
  - `issue-<issue_number>-delivery`
  - `issue-<issue_number>-dev`
  - `issue-<issue_number>-qa`

### Default live pilot data set
- package id external:
  - `fcore-stage1-2026-05-02-issue106-retirement-boundary-diagnostics`
- brief id external:
  - `fcore-coder-2026-05-02-issue106-retirement-boundary-diagnostics`
- issue number:
  - `106`
- PR number:
  - `107`
- canonical branch:
  - `issue-106`

### Queue names
- `fractal-core-architecture`
- `fractal-core-python`
- `fractal-core-qa`

## Phase 0: Pilot Readiness Snapshot

### Goal
Prove that the pilot starts from a known-clean, known-installed state before using the app launcher.

### Inputs
- Phase I3 results
- current installed runtime
- current installed skills
- current installed automations
- home-level UI registrations
- queue state

### Steps
1. verify all three queues are empty or in a known acceptable state
2. verify installed consumer wrapper and authority manifest still exist
3. verify installed role skills still exist for:
   - `fractal-core-techlead`
   - `fractal-core-delivery-review`
   - `fractal-core-dev-result`
   - `fractal-core-qa-review`
4. verify home-level UI registration files still exist for:
   - `fractal-core-techlead-automation`
   - `fractal-core-delivery-architect-automation`
   - `python-team-automation`
   - `fractal-core-qa-automation`
5. confirm no unexpected dirty repo state would confuse the pilot

### Expected outputs
- clean queue baseline
- installed runtime present
- installed skills present
- UI registration files present
- clean repo baseline

### Success criteria
- we start from a controlled baseline
- no hidden state ambiguity exists before the app/UI steps begin

### Evaluation method
- queue checks
- file existence checks
- repo status checks

### Adjustable variables / knobs
- queue cleanup before pilot
- repo choice
- runtime revision
- pilot issue/package/brief selection

## Phase 1: UI Visibility And Launch Surface Validation

### Goal
Prove that the current proven role set actually appears in the app UI as launchable automations.

### Inputs
- app UI
- home-level UI registrations under `/Users/billyweisberg/.codex/automations`
- current automation display names

### Steps
1. open the app UI area where automations are listed
2. confirm visible presence of:
   - `Fractal Core TechLead Automation`
   - `Fractal Core Delivery Architect Automation`
   - `Python Team Automation`
   - `Fractal Core QA Automation`
3. attempt to open each automation surface without running work yet
4. confirm the displayed automation identity matches the intended role

### Expected outputs
- all four automations are visible in the UI
- each automation is individually selectable/openable
- no role is missing or mislabeled

### Success criteria
- the UI shows the current proven role set as real launch surfaces
- there is no missing-role gap between registration files and the visible app layer

### Evaluation method
- user-visible UI confirmation
- optional screenshot capture or written confirmation from the app

### Adjustable variables / knobs
- app refresh/reload timing
- registration file names/display names
- whether we validate all four roles at once or one by one

## Phase 2: No-Work Poll And Non-Invocation Validation

### Goal
Prove that app-launched automations can poll for work without waking the model when no work exists.

### Inputs
- app-launched automation runs
- empty queue state
- `automation-preflight` runtime behavior

### Steps
1. confirm all queues are empty
2. launch one no-work poll cycle for:
   - `TechLead`
   - `Delivery Architect`
   - `Python Dev`
   - `QA`
3. observe whether the app UI triggers a real model run or exits quietly
4. verify behind the scenes that preflight would return:
   - `should_invoke_model = false`
5. confirm no queue or worktree side effects were created

### Expected outputs
- each automation exits quietly on no-work state
- no model invocation occurs for empty queues
- no accidental role worktree mutation occurs

### Success criteria
- app-launched no-work polling is cheap and non-chatty
- the launcher honors the deterministic preflight gate behavior

### Evaluation method
- user-visible app behavior
- runtime preflight checks
- queue checks
- worktree ownership/staleness spot checks if needed

### Adjustable variables / knobs
- which role to test first
- single-role versus all-role no-work polling
- wait timing between poll attempts
- whether to inspect one queue or all queues after each no-work attempt

## Phase 3: Single-Role Launch Environment Validation

### Goal
Prove that one app-launched automation can start with the correct runtime context.

### Inputs
- app-launched automation run
- one disposable assignment packet for one target role
- execution environment contract

### Steps
1. send one disposable assignment packet for a chosen target role
2. launch that role’s automation from the app UI
3. verify the role actually wakes because work exists
4. verify the role uses the intended runtime context:
   - canonical consumer repo root as launch base
   - correct wrapper path
   - correct queue state root
   - correct deterministic role worktree preparation or reuse
   - correct worktree cwd transition for execution
5. verify the role can reach the expected return surface without hidden manual path correction

### Expected outputs
- model invocation occurs only for the intended role
- runtime context matches the documented execution contract
- no wrong cwd/worktree/env fallback appears

### Success criteria
- the app launcher preserves the same runtime contract already proven via CLI/runtime validation
- the launched role does not require ad hoc path fixes to run correctly

### Evaluation method
- user-visible launch behavior
- runtime output / logs
- worktree ownership queries
- queue state inspection

### Adjustable variables / knobs
- target role under test
- assignment packet family
- disposable branch/worktree suffixes
- whether the assignment is compile-only or fully sent

## Phase 4: Supervised Live Automation Pilot Slice

### Goal
Prove one actual supervised pilot slice through the app/UI launcher path for the current proven role set.

### Inputs
- canonical issue/package/brief set
- current proven packet families
- current role skills and automations
- live queues
- app UI launcher

### Steps
1. `TechLead` is launched from the app/UI and picks up the pilot assignment path
2. `Delivery Architect` is launched from the app/UI and returns `delivery_review_packet`
3. `TechLead` is launched from the app/UI and routes to `Python Dev`
4. `Python Dev` is launched from the app/UI and returns `worker_result_packet`
5. `TechLead` is launched from the app/UI and routes to `QA`
6. `QA` is launched from the app/UI and returns `qa_verification_packet`
7. `TechLead` is launched from the app/UI and records or derives the next decision
8. cleanup disposable queue/worktree state if the pilot was run with disposable overrides

### Expected outputs
- all four roles launch from the app/UI successfully
- no-work gating and real-work invocation both behave correctly
- correct packet family is used on each leg
- worktree and queue state remain coherent throughout
- top-level `techlead-status` remains coherent during the pilot

### Success criteria
- no hidden manual queue reasoning is needed
- no hidden path/env repair is needed after the UI launcher starts the role
- no role disappears or misfires at the app boundary
- current-role-set loop behaves the same through the app launcher as it did through the supervised CLI/runtime proof

### Evaluation method
- user-visible app behavior
- queue checks before, during, after
- worktree ownership/staleness checks during the run
- `techlead-status --validate-schema`
- written validation note against observed live outputs

### Adjustable variables / knobs
- whether the pilot is run with disposable branch/worktree suffixes
- whether roles are launched manually one by one or through the app’s natural scheduling cadence
- target role launch order for troubleshooting
- whether return packets are immediately acknowledged or left pending until the full pilot path is observed

## Phase 5: Final Deliberate Unpause Decision

### Goal
Decide, based on the supervised app/UI pilot, whether the current proven role set is ready for deliberate unpause.

### Inputs
- outputs from Phases 0 through 4 of this pilot plan
- Phase I3 cutover-readiness decision
- consistency/unpause gate

### Steps
1. summarize pass/fail per pilot phase
2. list any blockers that remain after the app/UI pilot
3. classify blockers as:
   - hard blocker
   - operational note
   - post-unpause follow-up
4. decide one of:
   - ready for deliberate unpause
   - ready only for another supervised pilot
   - not ready

### Expected outputs
- one explicit readiness verdict
- one explicit blocker list
- one explicit next action

### Success criteria
- no ambiguity remains about whether we deliberately unpause
- the final decision reflects actual app/UI launcher behavior, not only CLI/runtime behavior

### Evaluation method
- written verdict against checklist and actual pilot evidence

### Adjustable variables / knobs
- allowed blocker severity threshold
- whether unpause is role-by-role or full current proven role set
- whether a second supervised pilot is required before unpause

## Test sequence summary

Run pilot phases in this order:
1. Phase 0 pilot readiness snapshot
2. Phase 1 UI visibility and launch surface validation
3. Phase 2 no-work poll and non-invocation validation
4. Phase 3 single-role launch environment validation
5. Phase 4 supervised live automation pilot slice
6. Phase 5 final deliberate unpause decision

## Minimum pass gate before deliberate unpause

The current proven role set is ready for deliberate cutover/unpause only if:
- Phases 0 through 4 pass with no hard blockers
- Phase 5 yields `ready for deliberate unpause`
- any remaining issues are documented as operational notes, not active launcher/runtime defects

# Phase I3 Current Proven Role Set Test Plan

## Purpose

Define the full test plan to validate the current proven role set before executing the deliberate cutover/unpause sequence.

Current proven role set:
- `TechLead`
- `Delivery Architect`
- `Python Dev`
- `QA`

This plan exists to answer, explicitly and repeatably:
- what we test
- in what order
- with what inputs
- what success looks like
- how results are evaluated
- what variables can be tuned when a phase fails or needs a controlled variant

## Scope

This plan validates the current proven role set only.

It covers:
- UI-visible automation registration
- prompt and skill alignment
- no-work preflight gating
- execution-environment contract adherence
- packet emission and return behavior
- queue behavior
- branch/worktree behavior
- lifecycle query and cleanup safety
- supervised canonical end-to-end loop
- cutover readiness decision

It does not cover:
- broader worker-family expansion
- new packet family invention
- broader Delivery Architect outcome expansion beyond the current supported path

## Test strategy

The test sequence moves from cheapest and most deterministic to most integrated and stateful.

Order matters:
1. static contract and installation checks
2. non-model gating checks
3. role-environment and skill checks
4. packet and queue transport checks
5. supervised canonical live slice
6. lifecycle and cleanup safety checks
7. cutover decision

This prevents us from spending live queue/worktree effort before the local contracts are known-good.

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
- canonical issue branch pattern:
  - `issue-<issue_number>`
- deterministic role branch patterns:
  - `issue-<issue_number>-delivery`
  - `issue-<issue_number>-dev`
  - `issue-<issue_number>-qa`

### Default live test data set
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

## Phase 0: Baseline And Installation Sanity

### Goal
Prove that the installed runtime, installed authority, installed skills, installed automations, and home-level UI registrations are present and coherent before any behavior tests.

### Inputs
- current installed runtime in consumer repo
- project-pack automation and skill sources in `paa-platform`
- home-level UI registration entries under `/Users/billyweisberg/.codex/automations/`

### Steps
1. verify consumer wrapper help surfaces
2. verify authority manifest exists
3. verify installed consumer skills exist for:
   - `fractal-core-techlead`
   - `fractal-core-delivery-review`
   - `fractal-core-dev-result`
   - `fractal-core-qa-review`
4. verify installed consumer automations exist for:
   - `fractal-core-techlead-automation`
   - `fractal-core-delivery-architect-automation`
   - `python-team-automation`
   - `fractal-core-qa-automation`
5. verify home-level UI registration entries exist for the same four automations

### Expected outputs
- wrapper commands are visible
- authority manifest exists
- installed skill files exist
- installed automation TOML files exist
- home-level UI registration TOML files exist

### Success criteria
- all required files and command surfaces are present
- no required automation or skill is missing from the current role set

### Evaluation method
- file existence checks
- `paa-consumer help`
- optional TOML parse validation

### Adjustable variables / knobs
- repo root
- project pack name
- consumer runtime revision
- home-level automation registration paths

## Phase 1: Prompt And Skill Contract Alignment

### Goal
Prove that the active guidance teaches the same system the runtime implements.

### Inputs
- project-pack automation TOMLs
- installed consumer automation TOMLs
- project-pack skills
- installed consumer skills

### Steps
1. verify active prompts no longer teach:
   - shared full-cycle branch as the only model
   - human-only TechLead routing behavior
2. verify active prompts do teach:
   - TechLead-owned lineage and routing
   - authorized role worktrees
   - correct packet families per role
3. verify role skills contain:
   - preflight
   - role worktree intake
   - role return surfaces

### Expected outputs
- no stale shared-branch-only language
- no stale “do not auto-send” TechLead language
- role skills contain the execution-contract markers

### Success criteria
- prompts and skills match the current packet model and role-worktree model
- no known stale guidance remains on active surfaces

### Evaluation method
- grep/content validation against expected markers
- spot review of current installed consumer copies

### Adjustable variables / knobs
- prompt wording
- skill wording
- pack manifest selection
- installed consumer refresh timing

## Phase 2: Non-Model Preflight Gate

### Goal
Prove that each automation can poll without invoking the model when there is no work, and will invoke the model only when work is actually present.

### Inputs
- `automation-preflight` command
- empty queue state
- disposable assignment packet for positive-path validation

### Steps
1. run `automation-preflight` for:
   - `techlead`
   - `delivery-architect`
   - `python-team`
   - `qa`
   with empty queues
2. send a disposable assignment packet to one role queue
3. rerun `automation-preflight` for that role
4. claim and acknowledge the packet
5. rerun `automation-preflight`

### Expected outputs
- empty queue path:
  - `should_invoke_model = false`
- queued work path:
  - `should_invoke_model = true`
- post-cleanup path:
  - `should_invoke_model = false`

### Success criteria
- no-work path never wakes the model
- positive path wakes exactly the intended role
- queue cleanup returns the gate to false

### Evaluation method
- inspect JSON output fields:
  - `should_invoke_model`
  - `skip_model_invocation`
  - `gate_reason`
  - `queue_candidates`

### Adjustable variables / knobs
- target role
- queue packet family
- queue preview depth
- role-specific queue selection
- `claimed_by` value for disposable claim cleanup

## Phase 3: Execution Environment Contract Adherence

### Goal
Prove that the current automations can start from the canonical consumer repo root, transition to deterministic role worktrees when required, and use the correct wrappers and environment roots.

### Inputs
- execution environment contract doc
- canonical consumer repo root
- role worktree root
- wrapper paths
- environment variables

### Steps
1. verify automation `cwds` point to the canonical consumer repo root
2. verify role worktree paths resolve under the deterministic worktree root
3. verify wrapper paths exist:
   - `.codex/paa/bin/paa-consumer`
   - `.codex/paa/bin/paa-producer`
4. verify queue state root is repo-local
5. verify no active path depends on deprecated home-folder runtime skills
6. verify role skills explicitly call out worktree cwd transition and `uv` preference where required

### Expected outputs
- all paths resolve to the contract-defined roots
- wrapper paths exist
- queue state root is repo-local
- role skills reflect the contract

### Success criteria
- no environment ambiguity remains for the current role set
- cwd transition and worktree execution model are explicit and internally consistent

### Evaluation method
- path existence checks
- content inspection
- optional env dump for real automation runs later

### Adjustable variables / knobs
- `FRACTAL_CORE_HANDOFF_STATE_DIR`
- `FRACTAL_CORE_RABBITMQ_*`
- `PAA_DB_*`
- explicit `--repo-root`
- explicit `--worktree-path`
- explicit `--role-branch`

## Phase 4: Packet And Queue Transport Validation

### Goal
Prove that each active packet family for the current role set validates, resolves to the correct queue, and can be sent/claimed/acknowledged cleanly.

### Inputs
- active packet families:
  - `techlead_assignment_packet`
  - `techlead_decision_packet`
  - `delivery_review_packet`
  - `worker_result_packet`
  - `qa_verification_packet`
- queue commands
- disposable packet files

### Steps
1. validate representative packet files through the installed wrapper
2. send them to the expected queue
3. inspect queue preview and resolved queue
4. claim and acknowledge disposable packets
5. recheck queue state after cleanup

### Expected outputs
- validation passes
- resolved queue matches expectation
- send succeeds
- claim succeeds
- ack succeeds
- reconciled queue state returns to zero after cleanup

### Success criteria
- no queue-resolution ambiguity
- no queue cleanup drift beyond transient reconciled/raw lag already documented
- packet family to queue mapping is stable

### Evaluation method
- command JSON outputs
- queue check previews
- queue claim/ack outputs

### Adjustable variables / knobs
- message file path
- queue name
- `--send`
- `claimed_by`
- queue preview depth
- disposable packet contents

## Phase 5: Role Bridge Surface Validation

### Goal
Prove that each current role can move through the bounded receive/execute/return bridge correctly before a supervised live automation cutover.

### Inputs
- `techlead-handoff-to-role-worktree`
- `techlead-inspect-role-worktree`
- `techlead-role-entry`
- `techlead-role-result-assist`
- `techlead-role-return`
- deterministic role branch/worktree surfaces

### Steps
1. hand off to `Delivery Architect`
2. inspect worktree and role entry
3. validate role result assist and return path
4. repeat for `Python Dev`
5. repeat for `QA`

### Expected outputs
- worktree preparation succeeds or reuse is correctly reported
- role-entry shows aligned branch and assignment artifact
- role-result-assist shows correct result family and input contract
- role-return validates and sends the correct packet family

### Success criteria
- no role requires ad hoc queue reasoning
- no role requires hidden branch/worktree conventions
- no role returns the wrong packet family

### Evaluation method
- command JSON outputs
- assignment/result artifact paths
- worktree ownership and stale-state queries if needed

### Adjustable variables / knobs
- target role
- branch action (`ensure` vs `reset`)
- explicit `--role-branch`
- explicit `--worktree-path`
- explicit `--assignment-path`
- `--send`

## Phase 6: Canonical Supervised End-To-End Slice

### Goal
Prove the full current-role-set loop under supervised live conditions.

### Inputs
- canonical issue/package/brief set
- current proven packet families
- current role skills and automations
- live queues

### Steps
1. `TechLead -> Delivery Architect`
2. `Delivery Architect -> TechLead`
3. `TechLead -> Python Dev`
4. `Python Dev -> TechLead`
5. `TechLead -> QA`
6. `QA -> TechLead`
7. `TechLead` records or derives the next decision
8. cleanup disposable branches/worktrees and queue messages

### Expected outputs
- all role transitions succeed
- correct packet family is used on each leg
- queue state remains coherent throughout
- top-level `techlead-status` reflects active work coherently
- cleanup returns queues to zero

### Success criteria
- no manual queue-order reasoning is needed
- no prompt/runtime contradiction appears on active paths
- no role/worktree ownership ambiguity appears
- no legacy `slice_result_packet` is required on the active Python lane

### Evaluation method
- canonical E2E runbook execution
- queue checks before, during, after
- `techlead-status --validate-schema`
- validation notes recorded against observed live outputs

### Adjustable variables / knobs
- package id
- brief id
- issue/PR selection
- target role overrides for explicit handoff testing
- use of disposable branch/worktree suffixes
- `--send` on assignment and return phases

## Phase 7: Lifecycle Safety Validation

### Goal
Prove that lifecycle query and cleanup behavior remains safe and fail-closed for the current role set.

### Inputs
- lineage state
- worktree ownership state
- stale-worktree state
- lifecycle commands:
  - `techlead-reset-required`
  - `techlead-reset-cleanup`
  - `techlead-superseded-cleanup`
  - `techlead-closed-cleanup`

### Steps
1. validate fail-closed behavior on ineligible live state
2. validate positive-path synthetic fixtures where applicable
3. verify cleanup removes worktree but preserves branches in the documented scope

### Expected outputs
- ineligible live state returns explicit refusal
- positive synthetic state returns successful cleanup result
- cleanup result reports preserved branches correctly

### Success criteria
- lifecycle cleanup follows lineage state rather than guesswork
- no branch deletion occurs in the current cutover scope
- no cleanup command mutates ambiguous worktree state

### Evaluation method
- lifecycle command JSON output
- synthetic fixture harness output
- git worktree inspection after cleanup

### Adjustable variables / knobs
- target role
- synthetic fixture selection
- `--send-decision`
- role branch override
- worktree path override
- reset reason / superseded branch / worktree hint fields

## Phase 8: Cutover Readiness Decision

### Goal
Decide, based on evidence from Phases 0-7, whether the current proven role set is ready for deliberate unpause.

### Inputs
- outputs from all prior phases
- cutover checklist
- consistency/unpause gate

### Steps
1. summarize pass/fail per prior phase
2. list any blockers
3. classify blockers as:
   - hard blocker
   - operational note
   - post-cutover follow-up
4. decide one of:
   - ready for deliberate unpause
   - ready only for additional supervised pilot
   - not ready

### Expected outputs
- one explicit readiness verdict
- one explicit blocker list
- one explicit next action

### Success criteria
- no ambiguity about whether we proceed
- no hidden assumption that “good enough” means unpause

### Evaluation method
- written verdict against checklist and actual phase evidence

### Adjustable variables / knobs
- allowed blocker severity threshold
- whether the next run is supervised only or actual unpause
- whether a role is unpaused one-at-a-time or as the full current proven role set

## Test sequence summary

Run phases in this order:
1. Phase 0 baseline and installation sanity
2. Phase 1 prompt and skill contract alignment
3. Phase 2 non-model preflight gate
4. Phase 3 execution environment contract adherence
5. Phase 4 packet and queue transport validation
6. Phase 5 role bridge surface validation
7. Phase 6 canonical supervised end-to-end slice
8. Phase 7 lifecycle safety validation
9. Phase 8 cutover readiness decision

## Minimum pass gate before deliberate unpause

The current proven role set is ready for deliberate cutover/unpause only if:
- Phases 0 through 7 all pass with no hard blockers
- Phase 8 yields `ready for deliberate unpause`
- any remaining issues are documented as operational notes, not active routing or environment defects

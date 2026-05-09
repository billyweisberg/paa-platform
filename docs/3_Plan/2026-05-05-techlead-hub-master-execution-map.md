# TechLead Hub Master Execution Map

## Purpose

This note re-establishes one authoritative execution map for the TechLead-centered hub-and-spoke migration.

It exists because the work has been proceeding through a mix of:
- core design notes
- a delta plan
- narrow mini-plans
- deploy/runtime slices

That produced real progress, but it also made it too easy to lose the overall map.

This document is now the planning spine for the hub-and-spoke completion effort.
When deciding the next slice, start here first.

## Planning Sources

This map is synthesized from:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-04-current-mesh-vs-techlead-hub-spoke.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-04-techlead-hub-packet-and-decision-vocabulary.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-04-techlead-hub-state-and-routing-contract.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/3_Plan/2026-05-04-techlead-hub-implementation-delta-plan.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/3_Plan/2026-05-05-phase-c-decision.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/3_Plan/2026-05-05-phase-d-mini-plan-branch-worktree-lineage.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/3_Plan/2026-05-05-phase-e-decision-lineage-query-helper.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/6_Deploy/2026-05-05-techlead-role-branch-mutation.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/6_Deploy/2026-05-05-techlead-role-worktree-mutation.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/6_Deploy/2026-05-05-techlead-handoff-to-role-worktree.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/6_Deploy/2026-05-05-techlead-inspect-role-worktree.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/6_Deploy/2026-05-05-techlead-role-entry.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/3_Plan/2026-05-09-target-worker-family-expansion-implementation-plan.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-09-team-worker-roles-design-spec.md`

## Target Model

The target consumer-side workflow is:

- `TechLead` is the routing hub
- `TechLead` owns the canonical issue branch
- spoke roles do bounded work only
- spoke roles do not route other spokes
- spoke roles return constrained result packets only to `TechLead`
- `TechLead` decides the next assignment every time
- role branches and worktrees are disposable execution surfaces beneath canonical issue lineage

### Canonical branch model

- canonical branch: `issue-<issue_number>`
- optional role branches:
  - `issue-<issue_number>-delivery`
  - `issue-<issue_number>-dev`
  - `issue-<issue_number>-qa`

### Current role model in scope

Producer-side:
- `Authority Architect`

Consumer-side hub:
- `TechLead`

Consumer-side spoke roles:
- `Delivery Architect`
- `Python Dev`
- `QA`

The pattern must remain extensible to future worker roles such as:
- `Frontend Dev`
- `Backend Dev`
- `Infra Dev`
- `Docs Dev`

## Current Status

### We are not off the architecture map

The hub-and-spoke design itself is still intact.
What drifted was planning visibility.

### Current phase

Current phase is:
- `Phase I: Operational Hardening, E2E Acceptance, And Automation Unpause`

Meaning:
- the hub loop has now been executed end-to-end for the current proven role set
- lifecycle depth through reset, superseded, and closed cleanup is implemented for the narrow `python-team` path
- remaining work is now hardening, reporting coherence, and Team Worker Roles expansion

### What is complete vs incomplete

Complete enough to count as done:
- Phases `A` through `H` for the current proven role set

Active and not yet complete:
- Phase `I`

Deferred future requirement:
- broader Team Worker Roles expansion after Phase I hardening

## Phase Map

## Phase A: Reroute Through TechLead

### Goal
Make `TechLead` the required interception point for consumer-side results without a full packet-family rewrite.

### Completed slices
- `slice_result_packet` rerouted from `Python Dev -> QA` to `Python Dev -> TechLead`
- `qa_verification_packet` rerouted from `QA -> Architect` to `QA -> TechLead`
- queue/runtime route-policy tightened to reject the old direct mesh routes for new sends
- TechLead reporting updated to understand:
  - `techlead_dev_review_pending`
  - `techlead_qa_review_pending`
- prompts and skills updated so Dev and QA return to `TechLead`, not to each other or directly to `Architect`

### Acceptance state
- complete

## Phase B: First-Class TechLead Packet Families

### Goal
Make TechLead-issued control traffic first-class in the control spine.

### Completed slices
- added `techlead_assignment_packet`
- added `techlead_decision_packet`
- added schemas and examples
- added compiler entrypoints
- added queue/runtime validation and persistence support
- added TechLead reporting support for issued assignments and recorded decisions
- added explicit dispatch helpers so compile, validate, and send do not depend on hidden queue knowledge
- made the DB role model decision:
  - packet/runtime vocabulary keeps `Delivery Architect` and `Authority Architect`
  - DB persistence remains aliased to `Architect` for now

### Acceptance state
- complete

## Phase C: TechLead Assignment Emission

### Goal
Give TechLead the first real supported emission path for next assignments.

### Completed slices
- added `techlead-emit-next-assignment`
- supported explicit `Python Dev` emission path
- supported derived `QA` emission path from `techlead_dev_review_pending`
- reused existing compile, validate, and send primitives rather than inventing a parallel send path
- validated live dispatch through the existing queue/control spine
- tightened queue-state accounting so `messages_ready` and preview cannot drift silently

### Acceptance state
- complete

## Phase D: Lineage Persistence And Visibility

### Goal
Make branch and worktree lineage explicit and persisted before branch automation grows.

### Completed slices
- added lineage fields to:
  - `techlead_assignment_packet`
  - `techlead_decision_packet`
- persisted lineage metadata through the existing control spine
- surfaced lineage in `techlead-status`
- implemented first branch-aware TechLead decision paths:
  - `reset_required`
  - `superseded`
  - `closed`

### Acceptance state
- complete

## Phase E: Role Execution Bridge

### Goal
Bridge TechLead assignment emission into a prepared, inspectable, role-specific execution workspace without auto-running role work.

### Completed slices
- added `techlead-lineage` as the required lineage precursor
- added `techlead-prepare-role-branch`
- added `techlead-prepare-role-worktree`
- added `techlead-handoff-to-role-worktree`
- added `techlead-inspect-role-worktree`
- added `techlead-role-entry`
- added `techlead-role-result-assist`
- added `techlead-role-return`

### Current state
This phase is complete enough to treat the bridge as real.

The hub can now:
- emit assignment intent
- prepare branch context
- prepare worktree context
- inspect the receive side
- produce a role-entry view with exact manual execution surfaces
- compile, validate, and optionally send a role result back toward `TechLead`

### Validation result
- one clean Python Dev round trip has been run through:
  - TechLead emit
  - branch/worktree prep
  - role entry
  - result compile/send return
- the returned `slice_result_packet` validated and sent successfully
- the returned packet appeared on the expected transitional queue

### Remaining slices
- make Dev and QA return flow use the same structured entry/exit model as the TechLead handoff side
- confirm the bridge is generic enough for future worker roles, not only `Python Dev`

### Acceptance criteria
Phase E is complete when a role can:
- receive a prepared worktree context
- see the exact assignment artifact and expected result vocabulary
- be guided to the exact result compilation surface
- hand control back into the hub path without ad hoc queue/branch reasoning
- complete one clean round trip through the bridge

### Acceptance state
- complete

## Phase F: Role Result Return Path

### Goal
Make the spoke-to-hub return path first-class and symmetrical with the TechLead-to-spoke handoff path.

### Scope
This is the first phase that should complete the round trip.

### Completed foundation
- role-result assist helper exists
- exact compile surfaces exist for:
  - Dev result return
  - QA result return
- validate/send bridge exists for the result packet
- one clean Python Dev round trip has been validated

### Remaining slices
- tighten the worker-result contract if `slice_result_packet` remains too Python-specific
- decide whether `worker_result_packet` is actually required before multi-role expansion
- stop short of broad autonomous execution of the role itself

### Acceptance criteria
- a prepared role can return to `TechLead` through one narrow guided path
- no ad hoc queue selection is required
- no role invents its own branch or routing semantics
- result return path is reusable by future worker-role families

### Status
- complete

### Decision
- the current return bridge shape is generic enough to keep
- `slice_result_packet` is still too Python-specific to be the final multi-worker contract
- defer `worker_result_packet` to Phase G

## Phase G: Multi-Role Generalization And Delivery Architect Integration

### Goal
Finish the hub model so it is not effectively a Python-only special case.

### Completed foundation
- `worker_result_packet` contract defined
- `delivery_review_packet` contract defined
- schema files added for both packet families
- example packets added for both packet families
- runtime validator acceptance added for both packet families
- producer compiler support added for both packet families
- TechLead runtime interpretation added for both packet families
- explicit Delivery Architect assignment/return bridge added
- legacy `slice_result_packet` support deliberately kept intact during migration
- active Python bridge validated on `worker_result_packet`
- `delivery_review_packet` can now drive the supported `ready_for_dev -> Python Dev` TechLead decision path

### Planned slices
- demote `slice_result_packet` to legacy compatibility after the generic worker lane is proven
- finish the Delivery Architect -> TechLead -> Python Dev decision lane before broadening worker-role expansion
- ensure route policy remains spoke-to-TechLead only

### Deferred required expansion
Worker-role family expansion is a real requirement, not optional future polish.

Defer it until the hub loop is fully hardened, but keep it explicitly on the plan for a later return:
- `Frontend Dev`
- `Backend Dev`
- `Infra Dev`
- `Docs Dev`

### Acceptance criteria
- TechLead can route at least one non-Python spoke cleanly
- the packet model is generic enough for future worker-role expansion
- Delivery Architect is no longer only a design concept in docs

### Status
- complete for the current proven role set

## Phase H: Lifecycle Hygiene And Worktree Cleanup Automation

### Goal
Automate the safe parts of branch/worktree lifecycle after lineage and query/reporting are proven.

### Planned slices
- Phase H1 worktree ownership contract:
  - `TechLead` owns lineage and branch authorization
  - role automation owns create-or-reuse of its own deterministic role worktree
  - `TechLead` worktree helpers remain admin/recovery surfaces, not the normal runtime owner
- Phase H1 worktree ownership metadata/reporting:
  - owning role is queryable through runtime reporting
  - ownership remains deterministic and cleanup-free
- Phase H2 stale worktree detection:
  - obvious stale conditions are queryable
  - absence is not misclassified as stale
  - no cleanup mutation yet
- Phase H3 reset-required lifecycle mutation:
  - first cleanup-safe mutation slice
  - marks reset-required execution surfaces as cleanup candidates
  - does not delete worktrees or branches yet
- Phase H4 physical reset cleanup:
  - first physical cleanup slice
  - retires a stale `python-team` worktree after reset-required has been recorded
  - preserves the role branch
- Phase H5 superseded cleanup:
  - next narrow physical cleanup slice
  - retires a stale superseded `python-team` worktree
  - preserves the superseded role branch
- Phase H6 closed cleanup:
  - first terminal cleanup slice
  - retires a stale closed `python-team` worktree
  - preserves both the role branch and canonical branch in this slice
- branch reset automation on top of `techlead-lineage`
- supersede-lineage cleanup flow
- close-slice cleanup flow
- safe worktree retirement and deletion
- stale role-branch retirement
- evidence-first cleanup rules
- fail-closed protections if active worktree state is ambiguous

### Acceptance criteria
- worktree ownership is explicit and consistent with the hub model
- reset, supersede, and close actions can mutate execution surfaces safely
- cleanup is driven by lineage state, not guesswork
- no branch/worktree mutation happens without a queryable lineage precursor

### Status
- complete for the current narrow lifecycle family

## Phase I: Operational Hardening, E2E Acceptance, And Automation Unpause

### Goal
Turn the working hub model into a reliable operating system for agents, not a promising prototype.

### Planned slices
- full end-to-end slice test plan for the hub workflow
- automation prompt hardening and consistency review
- global UI registration vs project-local deployed content finalization
- project-pack deployment boundary finalization
- runtime/config/bootstrap final checks
- automation visibility and install/update hygiene
- unpause criteria for real automations
- cutover checklist for live use

### Acceptance criteria
- one slice can run end-to-end through the hub model cleanly
- the queue, branch, worktree, and packet flows stay aligned under repeated runs
- prompts teach the same system the runtime actually implements
- automations are reliable enough to unpause deliberately

### Status
- active

### Current hardening result
- canonical E2E transport loop: proven for the current proven role set
- hardening rerun resolved:
  - queue-order masking in TechLead derivation
  - Delivery Architect result-assist contract mismatch on `result_type`
  - top-level `techlead-status` active-work inference/reporting drift
- automation unpause gate: satisfied for the current proven role set
- operational note:
  - raw broker `messages_ready` may lag briefly after cleanup, so reconciled runtime queue state remains the correct control-plane source

### Phase I spine
- canonical E2E runbook:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/5_Test/2026-05-07-phase-i-canonical-e2e-runbook.md`
- consistency checklist and unpause gate:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/6_Deploy/2026-05-07-phase-i-consistency-and-unpause-gate.md`
- Phase I entry plan:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/3_Plan/2026-05-07-phase-i1-hardening-and-acceptance-plan.md`
- canonical E2E validation note:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/5_Test/2026-05-07-phase-i-canonical-e2e-validation.md`
- cutover checklist for the current proven role set:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/6_Deploy/2026-05-07-phase-i-cutover-checklist-current-role-set.md`
- automation creation/readiness plan:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/3_Plan/2026-05-07-phase-i2-automation-creation-and-readiness-plan.md`
- UI registration alignment note:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/5_Test/2026-05-07-phase-i2-ui-registration-alignment.md`
- prompt alignment validation note:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/5_Test/2026-05-07-phase-i2-prompt-alignment-validation.md`
- automation preflight validation note:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/5_Test/2026-05-07-phase-i2-automation-preflight-validation.md`
- execution-environment contract:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/6_Deploy/2026-05-07-phase-i2-automation-execution-environment-contract.md`
- local tooling baseline:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/6_Deploy/2026-05-08-local-tooling-baseline.md`
- role skill hardening validation note:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/5_Test/2026-05-07-phase-i2-role-skill-hardening-validation.md`
- current proven role set test plan:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/5_Test/2026-05-08-phase-i3-current-role-set-test-plan.md`
- Phase I3 Phase 0 baseline validation:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/5_Test/2026-05-08-phase-i3-phase0-baseline-validation.md`
- Phase I3 Phase 1 prompt and skill alignment validation:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/5_Test/2026-05-08-phase-i3-phase1-prompt-skill-alignment-validation.md`
- Phase I3 Phase 2 preflight gate validation:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/5_Test/2026-05-09-phase-i3-phase2-preflight-gate-validation.md`
- Phase I3 Phase 3 execution environment validation:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/5_Test/2026-05-09-phase-i3-phase3-execution-environment-validation.md`
- Phase I3 Phase 4 packet transport validation:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/5_Test/2026-05-09-phase-i3-phase4-packet-transport-validation.md`
- Phase I3 Phase 5 role bridge surface validation:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/5_Test/2026-05-09-phase-i3-phase5-role-bridge-validation.md`
- Phase I3 Phase 6 canonical supervised end-to-end slice validation:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/5_Test/2026-05-09-phase-i3-phase6-canonical-e2e-validation.md`
- Phase I3 Phase 7 lifecycle safety validation:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/5_Test/2026-05-09-phase-i3-phase7-lifecycle-safety-validation.md`
- Phase I3 Phase 8 cutover readiness decision:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/5_Test/2026-05-09-phase-i3-phase8-cutover-readiness-decision.md`
- Phase I4 automation pilot test plan:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/5_Test/2026-05-09-phase-i4-automation-pilot-test-plan.md`
- Phase I4 Phase 0 pilot readiness snapshot validation:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/5_Test/2026-05-09-phase-i4-phase0-pilot-readiness-validation.md`
- Phase I4 Phase 1 UI visibility and launch surface validation:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/5_Test/2026-05-09-phase-i4-phase1-ui-visibility-validation.md`

### Roadmap decision after Phase I gate pass
- the prior defer-until-after-cutover rule is superseded
- Team Worker Roles expansion is now promoted before further automation cutover work
- use `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-09-team-worker-roles-design-spec.md` as the active design authority for that expansion
- use `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/3_Plan/2026-05-09-target-worker-family-expansion-implementation-plan.md` as the sequencing plan beneath that authority
- resume automation cutover and pilot work only after automation surfaces are reconciled with the target worker-family model

## Completed Slices Ledger

This is the short completed ledger we should carry forward instead of relying on thread memory.

### Completed
- Phase A reroute to `TechLead`
- Phase B first-class TechLead packet families
- Phase B dispatch primitives
- Phase C next-assignment emission
- queue-state accounting fix
- Phase D lineage fields and lineage reporting
- branch-aware decision emission for `reset_required`, `superseded`, `closed`
- Phase E lineage query helper
- Phase E role-branch preparation
- Phase E role-worktree preparation
- Phase E handoff from emitted assignment to prepared role worktree
- Phase E receive-side worktree inspection
- Phase E role-entry helper
- Phase E role-result assist helper
- Phase E role-return bridge
- Phase E clean Python Dev round-trip validation
- Phase F clean QA return-bridge validation
- Phase H1 worktree ownership reporting
- Phase H2 stale worktree detection
- Phase H3 reset-required lifecycle mutation
- Phase H3 positive synthetic reset fixture validation
- Phase H4 physical reset cleanup
- Phase H4 positive synthetic physical cleanup validation
- Phase H5 superseded cleanup
- Phase H5 positive synthetic superseded cleanup validation
- Phase H6 closed cleanup
- Phase H6 positive synthetic closed cleanup validation
- Phase I canonical E2E validation for the current proven role set
- Phase I3 Phase 0 baseline and installation sanity validation
- Phase I3 Phase 1 prompt and skill contract alignment validation
- Phase I3 Phase 2 non-model preflight gate validation
- Phase I3 Phase 3 execution environment contract adherence validation
- Phase I3 Phase 4 packet and queue transport validation
- Phase I3 Phase 5 role bridge surface validation
- Phase I3 Phase 6 canonical supervised end-to-end slice validation
- Phase I3 Phase 7 lifecycle safety validation
- Phase I3 Phase 8 cutover readiness decision

### Still open inside active flow
- broader Team Worker Roles expansion beyond the proven `Python Dev` generic lane
- additional Delivery Architect result outcomes beyond `ready_for_dev`
- `queue-check` preview depth remains shallow on architecture-queue history; routing/status now tolerate it, but operator visibility is still incomplete and should be hardened before broader scale-out

## Remaining Slices By Priority

### Immediate next slices
1. finish the remaining launcher/bootstrap details inside Stage W5 from `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/3_Plan/2026-05-09-target-worker-family-expansion-implementation-plan.md`
2. then execute Stage W6 from `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/3_Plan/2026-05-09-target-worker-family-expansion-implementation-plan.md`
3. keep the remaining Phase I4 pilot work paused until automation surfaces are reconciled with the Team Worker Roles model

## Guardrails

These rules exist to keep future slices on track.

### 1. Do not invent new flows outside this map
If a next slice is not clearly inside one phase here, update this map first.

### 2. Keep the hub model explicit
The target is not a soft preference.
The target is:
- `TechLead` routes
- spoke roles execute bounded work
- spoke roles return constrained results only to `TechLead`

### 3. No hidden truth
Each of these must have one declared home:
- packet schema truth
- route-policy truth
- lineage truth
- role prompt truth
- queue-dispatch truth
- branch/worktree mutation truth

### 4. No branch mutation without lineage query
Future branch/worktree mutation automation must keep `techlead-lineage` as the required precursor.

### 5. Finish the round trip before broadening scope
Do not jump to wide automation or many-role expansion before the `TechLead -> role -> TechLead` round trip is clean and repeatable.

## Recommended Next Step

The next slice should be:
- finish the remaining launcher/bootstrap details for Team Worker Roles

Immediately after that:
- prove one additional non-Python Team Worker Roles lane with `Docs Dev`
- then return to the paused automation pilot work once the launch surfaces match the target model

That keeps the system moving toward the target implementation instead of re-hardening a temporary worker shape.

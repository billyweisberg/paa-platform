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
  - `issue-<issue_number>-python-team`
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
- `Phase F: Role Result Return Path`

Meaning:
- `TechLead` can emit assignment intent
- lineage can be queried and persisted
- branch/worktree preparation can be done in narrow steps
- handoff into a prepared role execution context exists
- one clean Python Dev round trip has been validated through the bridge
- the remaining work is now about making that return path generic and stable enough for broader worker-role use

### What is complete vs incomplete

Complete enough to count as done:
- Phases `A` through `E`

Started and partially complete:
- Phase `F`

Not yet complete:
- Phases `G` through `I`

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
- confirm the current return bridge is generic enough for future worker-role families
- tighten the worker-result contract if `slice_result_packet` remains too Python-specific
- decide whether `worker_result_packet` is actually required before multi-role expansion
- validate the same bridge shape for `QA`
- stop short of broad autonomous execution of the role itself

### Acceptance criteria
- a prepared role can return to `TechLead` through one narrow guided path
- no ad hoc queue selection is required
- no role invents its own branch or routing semantics
- result return path is reusable by future worker-role families

### Status
- active

## Phase G: Multi-Role Generalization And Delivery Architect Integration

### Goal
Finish the hub model so it is not effectively a Python-only special case.

### Planned slices
- decide whether `slice_result_packet` remains transitional or becomes `worker_result_packet`
- add or finalize `delivery_review_packet`
- add Delivery Architect assignment emission path
- add Delivery Architect result return path
- confirm the hub contract works for multiple worker-role families:
  - `Python Dev`
  - `Frontend Dev`
  - `Backend Dev`
  - `Infra Dev`
  - `Docs Dev`
- ensure route policy remains spoke-to-TechLead only

### Acceptance criteria
- TechLead can route at least one non-Python spoke cleanly
- the packet model is generic enough for future worker-role expansion
- Delivery Architect is no longer only a design concept in docs

### Status
- not started

## Phase H: Lifecycle Hygiene And Worktree Cleanup Automation

### Goal
Automate the safe parts of branch/worktree lifecycle after lineage and query/reporting are proven.

### Planned slices
- branch reset automation on top of `techlead-lineage`
- supersede-lineage cleanup flow
- close-slice cleanup flow
- safe worktree retirement and deletion
- stale role-branch retirement
- evidence-first cleanup rules
- fail-closed protections if active worktree state is ambiguous

### Acceptance criteria
- reset, supersede, and close actions can mutate execution surfaces safely
- cleanup is driven by lineage state, not guesswork
- no branch/worktree mutation happens without a queryable lineage precursor

### Status
- not started

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
- not started

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

### Still open inside active flow
- generic worker-role proof beyond the Python Dev path
- QA return-path proof through the same bridge

## Remaining Slices By Priority

### Immediate next slices
1. continue Phase F by validating the same return bridge shape for `QA`
2. decide whether the current Python Dev return path is generic enough for future worker roles
3. validate one full round trip through:
   - TechLead emit
   - branch/worktree prep
   - role entry
   - result return to `TechLead`
   - TechLead-visible follow-up interpretation for the returned result

### After that
4. generalize the role model beyond Python-only execution assumptions
5. integrate Delivery Architect as a real spoke
6. automate lifecycle hygiene only after lineage query/reporting remains trustworthy under repeated runs
7. run full end-to-end acceptance and automation hardening before unpausing real automations

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
- validate the same narrow return bridge for `QA`

Immediately after that:
- tighten the generic worker return contract only if the `QA` pass shows a real asymmetry

That keeps the system on the shortest path to a real functioning round trip.

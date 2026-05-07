# Phase I Cutover Checklist For The Current Proven Role Set

This is the deliberate cutover checklist for the currently proven hub loop role set:
- `TechLead`
- `Delivery Architect`
- `Python Dev`
- `QA`

It applies only to the current proven role set.
It does not authorize later worker-family expansion by implication.

## Purpose

This checklist exists to move from:
- proven prototype behavior

to:
- deliberate live use with paused automations being unpaused intentionally

The point is to make cutover explicit, reversible, and auditable.

## Scope boundary

This checklist covers:
- queue/runtime behavior
- packet-family alignment
- branch/worktree ownership expectations
- installed runtime / prompt / skill consistency
- operational rollback readiness

This checklist does not cover:
- future worker-role family expansion
- broader Delivery Architect outcome expansion beyond current supported cases
- new packet-family invention

## Required preconditions

Before cutover, all of the following must be true:

1. canonical E2E transport loop is proven
- reference:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/5_Test/2026-05-07-phase-i-canonical-e2e-validation.md`

2. automation unpause gate is satisfied for the current proven role set
- reference:
  - `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/6_Deploy/2026-05-07-phase-i-consistency-and-unpause-gate.md`

3. current runtime command surface is installed in the consumer repo
- required wrapper:
  - `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.codex/paa/bin/paa-consumer`

4. authority mirror is aligned in the consumer repo
- expected authority path:
  - `/Users/billyweisberg/Repos/billyweisberg/fractal-core-python/.project/data/paa/authority/current/authority/fractal-core-python-authority.json`

## Cutover checklist

### A. Runtime and wrapper sanity

- `paa-consumer help` lists the active TechLead command surface
- `paa-consumer techlead-status --validate-schema` passes
- queue commands are available from the top-level wrapper:
  - `queue-check`
  - `queue-validate`
  - `queue-send`
  - `queue-claim-next`
  - `queue-ack`

### B. Prompt and skill sanity

- active guidance teaches:
  - `delivery_review_packet` for Delivery Architect
  - `worker_result_packet` for Python Dev
  - `qa_verification_packet` for QA
- no active guidance teaches `slice_result_packet` as the default Python lane
- active TechLead guidance matches the runtime command surface

### C. Queue-state sanity

- all three queues can be checked through the installed wrapper
- reconciled queue state is trusted as the operational control-plane source
- if raw broker `messages_ready` lags briefly after cleanup, operators and automations rely on:
  - reconciled `messages_ready`
  - queue preview
  - follow-up queue check
not raw broker count alone

### D. Branch and worktree sanity

- lineage is queryable via:
  - `techlead-lineage`
- worktree ownership is queryable via:
  - `techlead-worktree-ownership`
- stale-worktree state is queryable via:
  - `techlead-worktree-stale`
- role automation ownership model is understood:
  - `TechLead` owns lineage and routing
  - role automation owns create-or-reuse of its deterministic worktree

### E. Lifecycle safety sanity

- lifecycle commands fail closed when ineligible:
  - `techlead-reset-required`
  - `techlead-reset-cleanup`
  - `techlead-superseded-cleanup`
  - `techlead-closed-cleanup`
- no lifecycle cleanup command deletes branches in the current cutover scope

### F. Live-use boundary sanity

- cutover remains limited to the current proven role set
- no assumption is made that future worker families are already proven
- no hidden spoke-to-spoke routing is required
- no manual queue reasoning is required on active routing paths

## Unpause action sequence

When the checklist is satisfied, unpause deliberately in this order:

1. confirm queues are empty or in a known acceptable state
2. confirm installed runtime revision in the consumer repo is the intended one
3. confirm active authority mirror alignment
4. unpause `TechLead`
5. unpause `Delivery Architect`
6. unpause `Python Dev`
7. unpause `QA`
8. run one supervised live slice through the current proven role set
9. verify queue cleanup and top-level `techlead-status` after that slice

## Rollback trigger conditions

Re-pause immediately if any of the following occurs:

- a live slice requires hidden manual queue reasoning
- top-level `techlead-status` diverges from issue-scoped runtime interpretation on an active path
- packet-family guidance and runtime behavior diverge again
- role worktree ownership becomes ambiguous
- lifecycle cleanup behavior contradicts queryable lineage state

## Cutover decision for the roadmap

For the roadmap, the next step should remain inside `Phase I`.

Reason:
- the current proven role set is now technically proven
- the next remaining value is operational cutover discipline
- future worker-family expansion is a real requirement, but it should resume after cutover hygiene is explicit rather than implied

So the recommended sequence is:
1. finish current-role-set cutover hygiene
2. deliberately unpause for the current proven role set
3. then return to deferred multi-worker expansion

# Phase I Consistency Checklist And Unpause Gate

## Consistency checklist

Before unpausing real automations, verify:

### Prompt and skill consistency
- active TechLead guidance teaches:
  - `worker_result_packet` for Python
  - `delivery_review_packet` for Delivery Architect
  - `qa_verification_packet` for QA
- no active guidance teaches `slice_result_packet` as the default Python lane
- lifecycle cleanup guidance matches implemented commands:
  - `reset`
  - `superseded`
  - `closed`

### Wrapper and runtime consistency
- installed consumer wrapper exposes the current command surface
- installed TechLead skill matches the current runtime
- queue validate/send helpers are available from the top-level CLI

### Routing consistency
- `TechLead` is the only routing hub for consumer-side roles
- no active flow depends on direct:
  - `Python Dev -> QA`
  - `QA -> Architect`
- Delivery Architect follow-up behavior matches the current implemented cases

### Branch and worktree consistency
- lineage is queryable
- worktree ownership is queryable
- stale-worktree state is queryable
- lifecycle cleanup commands fail closed when state is ineligible

### Legacy compatibility boundaries
- `slice_result_packet` still validates for legacy overlap
- but is not taught as an active default

## Automation unpause gate

Real automations should remain paused until all of the following are true:

1. one canonical end-to-end slice passes through the current role set
2. no queue-state drift appears during that run
3. no branch/worktree ownership ambiguity appears during that run
4. no prompt/runtime mismatch is found on an active path
5. no active path requires hidden manual queue reasoning
6. lifecycle cleanup commands remain consistent with lineage state during the run

## Still-blocking conditions even after a mostly successful E2E run

Do not unpause real automations yet if:
- the E2E pass depends on ad hoc manual intervention outside documented runtime surfaces
- the installed wrappers and project-pack guidance are out of sync
- Delivery Architect routing still needs unplanned manual reinterpretation
- repeated runs produce inconsistent queue or worktree observations

## Exit condition for this gate

The gate is satisfied only when the current role set is:
- coherent
- repeatable
- documented
- and safe enough to unpause deliberately rather than experimentally


## Residual visibility limitation

- `queue-check` preview on `fractal-core-architecture` can stay shallow and may show only the oldest visible packet while newer pending packets still influence TechLead derivation and top-level status correctly.
- Current assessment:
  - not a blocker for the current proven role set
  - still a real observability defect
- Required follow-up before broader scale-out:
  - improve queue preview/reporting depth so operators and future automations can inspect pending architecture-queue history without ambiguity

## Current gate result

Canonical Phase I E2E result:
- transport loop: pass for the current proven role set
- automation unpause gate: not yet final for the current proven role set

Phase I3 cutover decision:
- readiness verdict: ready only for additional supervised pilot
- final deliberate unpause remains blocked on actual app/UI automation visibility and launcher-path proof

Resolved in the hardening rerun:
- queue-order masking in TechLead derivation
- Delivery Architect result-assist contract mismatch on `result_type`
- top-level `techlead-status` active-work inference/reporting drift

Operational note:
1. raw broker `messages_ready` may lag briefly after cleanup, but reconciled queue state and follow-up broker checks returned to zero across all three queues

Reference validation note:
- `docs/5_Test/2026-05-07-phase-i-canonical-e2e-validation.md`

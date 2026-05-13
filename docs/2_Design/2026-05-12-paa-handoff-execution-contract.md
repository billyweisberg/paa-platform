# PAA Handoff Execution Contract

Date: 2026-05-12

## Purpose

Define the handoff process in one place.

This note consolidates the parts that are currently spread across:
- packet vocabulary
- route matrix
- queue transport behavior
- role-return behavior
- lineage/worktree behavior
- DB reporting surfaces
- repo-local runtime artifacts

The goal is to make one thing explicit:
- what the handoff runtime is supposed to do
- what state is authoritative
- which parts live in the DB
- which parts live in repo-local files
- what invariants must hold at every transition

## Scope

This contract covers the consumer-side TechLead hub workflow:
- `TechLead`
- `Delivery Architect`
- Team Worker roles such as `Python Dev`, `Docs Dev`, `Frontend Dev`, `Backend Dev`, `Infra Dev`
- `QA`

It does not redefine producer-side authority publication.

## Related Notes

This note consolidates and should be read alongside:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-04-techlead-hub-packet-and-decision-vocabulary.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-04-techlead-hub-state-and-routing-contract.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-09-paa-service-contracts.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-09-paa-sequence-diagrams.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/6_Deploy/2026-05-03-worktree-branch-strategy.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-12-paa-messaging-simplification-note.md`

## Core Model

The consumer-side system is hub-and-spoke.

Only `TechLead` may assign the next consumer-side role.
All spoke roles return only to `TechLead`.
No spoke role routes directly to another spoke role.

Allowed route families:
1. `TechLead -> spoke assignment`
2. `spoke -> TechLead result`
3. `TechLead -> terminal decision`
4. `TechLead -> producer-side escalation`

Disallowed route families:
1. spoke -> spoke
2. spoke -> terminal closeout
3. spoke -> next issue selection
4. spoke -> independent branch-lineage invention

## Packet Families

### 1. Assignment packets

Used when `TechLead` assigns bounded work to a spoke role.

Current schema family:
- `techlead_assignment_packet`

Required semantics:
- target role
- assignment type
- issue / PR / branch context
- canonical branch
- optional role branch / worktree hint
- source package / brief context
- allowed result types

### 2. Result packets

Used when a spoke role returns its work result to `TechLead`.

Current schema families:
- `delivery_review_packet`
- `worker_result_packet`
- `qa_verification_packet`

Required semantics:
- source role
- issue / PR / branch context
- bounded result type
- evidence / findings / summary
- recommendation to `TechLead`
- source assignment reference

### 3. Decision packets

Used when `TechLead` records a durable workflow decision.

Current schema family:
- `techlead_decision_packet`

Required semantics:
- decision type
- source packet/result reference
- rationale
- next assignment target if any
- merge/reset/close state if terminal

## Queues

Current queue topology:
- `fractal-core-architecture`
- `fractal-core-python`
- `fractal-core-qa`

Current queue responsibilities:
- `fractal-core-architecture`
  - `TechLead` assignments to `Delivery Architect`
  - `Delivery Architect` returns to `TechLead`
  - `TechLead` decision packets
- `fractal-core-python`
  - Team Worker assignments
  - future Team Worker wakeups
- `fractal-core-qa`
  - `QA` assignments

Current design limitation:
- queue topology is still static
- Team Worker queue binding is broader than per-role routing and still needs future simplification if scale requires it

## Handoff Lifecycle

Every active handoff should follow one lifecycle.

### A. Assignment creation

1. `TechLead` derives next target role and assignment type
2. runtime compiles the assignment packet
3. runtime validates packet and route
4. runtime sends packet to the target queue
5. runtime persists queue / handoff evidence

### B. Role claim and execution

1. role preflight detects claimable work
2. role claims the packet from the queue
3. role prepares or reuses its authorized role worktree
4. role performs bounded work inside that surface
5. role prepares result input

### C. Role return

1. runtime compiles the result packet
2. runtime validates the result packet
3. runtime sends the result packet back to `TechLead`
4. runtime closes the source assignment packet

### D. TechLead transition

1. `TechLead` inspects the returned result packet
2. runtime derives the allowed next decision
3. if the decision is another assignment:
   - compile next assignment
   - send next assignment
   - close the source result packet
4. if the decision is terminal:
   - persist decision
   - optionally send decision packet
   - close the source result packet if appropriate

## Mandatory Invariants

These are the most important rules.

### Invariant 1: one active source packet per transition
A role or `TechLead` transition should act on one explicit source packet.

### Invariant 2: send and close belong to one runtime path
If a runtime path sends the next packet, it must also close the source packet in the same controlled flow.

This now applies to:
- `techlead-role-return --send`
- `techlead-emit-next-assignment --send`

### Invariant 3: wrong packet must never be acknowledged
If the queue head is not the expected source packet, the runtime must fail closed rather than acking the wrong message.

### Invariant 4: queue residue must not change workflow interpretation
Workflow truth should not depend on whether a stale packet preview still exists.

### Invariant 5: branch/worktree lineage is hub-owned
Only `TechLead`-governed runtime paths may define the canonical lineage and the role worktree contract.

## What Is Authoritative Today

The honest answer is: the system is hybrid.

### Authoritative enough in DB today

These are real control-plane sources:
- `paa.roles`
- `paa.handoffs`
- `paa.queue_messages`
- `paa.automation_runs`
- `paa.design_packages`
- `paa.coder_run_briefs`
- reporting views such as `paa.v_work_item_full_chain_traceability`

Key DB anchors:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/migrations/postgres/001-step1-control-plane.sql:117`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/migrations/postgres/001-step1-control-plane.sql:206`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/migrations/postgres/001-step1-control-plane.sql:230`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/sql/full_chain_reporting_view.sql:15`

### Still file-backed today

These remain repo-local file artifacts:
- installed authority package and overlay files
- compiled packet JSON / markdown review files
- repo-local logs
- repo-local automation memory
- repo-local queue claim JSON
- installed runtime payload under `.codex/paa`

Examples:
- `.project/data/paa/reports/`
- `.project/data/paa/logs/`
- `.project/data/paa/automation-memory/`
- `.project/data/paa/queue-state/`
- `.project/data/paa/authority/current/`

## Why It Is Not All In The DB

There are four reasons.

### 1. Installed authority packages are repo-scoped execution inputs
The consumer repo needs an installed, versioned, inspectable authority package to execute against.
That naturally lives as files.

### 2. Packet artifacts are treated as evidence, not just transport payloads
Packet JSON and review markdown are meant to be inspectable and durable at the repo boundary.
That pushed compilation output into files.

### 3. Queue claim state evolved as repo-local runtime state
The queue claim/ack layer was implemented as local runtime state rather than as a purely DB-driven lease model.
That is why claim JSON exists.

### 4. The architecture is still hybrid
PAA has not fully committed to either:
- DB/state-first orchestration
or
- queue/message-first workflow truth

So both file artifacts and DB records carry meaningful pieces of workflow state.

## What Should Be Authoritative In The Target Model

Target-state preference:
- DB/runtime state owns owner/stage truth
- queue owns wakeup/transport only
- files own installable artifacts, evidence, logs, and local execution context

That means:
- current owner should be queryable from durable state
- current workflow stage should be queryable from durable state
- a lingering queue packet should be an operational residue problem, not a truth problem

This aligns with:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-12-paa-messaging-simplification-note.md`

## Current Known Weaknesses

1. queue lifecycle and workflow lifecycle are still too tightly coupled
2. app-launched automation behavior and runtime state still require careful end-to-end proof
3. too much workflow understanding is split across multiple docs instead of one consolidated contract
4. DB truth and file truth boundaries are still not strict enough

## Practical Interpretation For Today

Until the architecture is simplified further, the safe rule is:

- DB is the best durable reporting/control-plane spine we have
- queue packets are live handoff signals
- repo-local files are required runtime evidence and execution context
- no single one of those three layers is sufficient by itself

That is why operators still have to reason across:
- DB-backed reports
- queue state
- repo-local packet/report artifacts

## Immediate Runtime Expectations

When evaluating a live handoff, the runtime should make these things true:

1. source packet is explicit
2. next packet is explicit
3. source packet closeout is part of the same runtime path
4. postcondition queue state is inspectable
5. branch/worktree context is explicit and bounded
6. packet/report artifacts remain visible in the repo

## Conclusion

The handoff process exists in design docs, but it has been spread across too many notes.
This document is intended to be the single contract for:
- packet families
- queue roles
- transition lifecycle
- closeout invariants
- DB truth vs file truth boundaries

It should become the primary reference when the runtime, prompts, or automation surfaces are changed.

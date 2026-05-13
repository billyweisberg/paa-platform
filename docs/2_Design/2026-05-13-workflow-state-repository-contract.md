# Workflow State Repository Contract

Date: 2026-05-13

## Purpose

Define the concrete Data Access Layer contract for:
- `Workflow State Repository`

This repository is the structured access boundary for DB-primary workflow truth.

Its purpose is to give higher-level components a stable way to:
- read current workflow state
- persist and inspect workflow transition history
- manage DB-primary queue-claim lifecycle records
- perform atomic workflow-state write groups

without reconstructing workflow truth from queue residue, repo-local reports, or projection artifacts.

## Related Notes

Read alongside:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-data-access-layer-design.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-final-workflow-state-entity-design.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-workflow-state-machine-data-contract.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-stable-table-classification-and-ownership-map.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-final-runtime-input-and-run-event-entity-design.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-final-projection-boundary-policy.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-12-paa-handoff-execution-contract.md`

## Role

Provide structured access to:
1. the single current workflow-state row for each work item
2. append-only workflow transition history
3. DB-primary queue-claim lifecycle records
4. workflow-state repair and consistency metadata

## Repository Boundary

The repository owns structured access to these DB tables:
- `paa.workflow_states`
- `paa.workflow_transitions`
- `paa.queue_claims`

It may join supporting identity tables only as needed for lookup resolution:
- `paa.projects`
- `paa.roles`
- `paa.work_items`

It does **not** own primary access to:
- `paa.handoffs`
- `paa.queue_messages`
- `paa.automation_runs`
- `paa.acceptance_events`
- projections or report views

Those remain outside this repository boundary.

## Non-Goals

The repository does not:
- decide whether a transition is legal
- compute business semantics for routing or acceptance
- infer workflow truth from queue state
- author projections
- manage packet payload content
- replace the `Runtime Event Repository`

## Primary Consumers

The main consumers are:
- `Workflow State Machine`
- `Runtime Lifecycle Engine`
- `Reporting And Traceability Projection`
- future operator and repair tooling

## Canonical Read Models

The repository provides structured access to four logical read models.

### 1. Current Workflow State View

Represents the current authoritative workflow truth for one work item.

Includes:
- current workflow stage
- current owner role
- lineage state
- blocking and terminal state
- active execution context
- active transport context
- consistency state

Backed by:
- `paa.workflow_states`

### 2. Workflow Transition History View

Represents the authoritative append-only workflow history for one work item.

Includes:
- transition type and status
- from/to stage and owner
- supporting source and result references
- reason and notes
- application timestamps

Backed by:
- `paa.workflow_transitions`

### 3. Active Queue Claim View

Represents the current active or most recent queue-claim lifecycle for a queue message or work item.

Includes:
- claim status
- claimant role and agent
- source attempt context
- ack outcome
- claim timing

Backed by:
- `paa.queue_claims`

### 4. Workflow Consistency And Repair View

Represents the workflow state's current self-assessment and repair history.

Includes:
- `state_consistency`
- blocking reason codes
- manual repair transitions
- claim status that may require compensation

Backed by:
- `paa.workflow_states`
- `paa.workflow_transitions`
- `paa.queue_claims`

## Required Repository Capabilities

## A. Current Workflow State Access

### Read capabilities
- get current workflow state by `workflow_state_id`
- get current workflow state by `work_item_id`
- get current workflow state by `(project_id, current_issue_number)`
- list active workflow states for a project
- list workflow states by `workflow_stage`
- list workflow states by `current_owner_role_id`
- list workflow states by `lineage_state`
- list workflow states by `state_consistency`

### Write capabilities
- create initial workflow state row for a work item
- update current workflow state after an applied transition
- set blocking state and blocking reason
- set terminal decision and close timestamps
- update active transport and execution context references
- mark state consistency and repair metadata

### Invariants
- exactly one `workflow_states` row exists per `work_item_id`
- current-state reads must come from `paa.workflow_states`, not reconstructed transition scans
- closed or superseded states remain queryable as the canonical current terminal snapshot

## B. Workflow Transition Access

### Read capabilities
- list workflow transitions for a `work_item_id` in applied order
- get workflow transition by `workflow_transition_id`
- list transitions by `transition_type`
- list transitions by `transition_status`
- list transitions for a `workflow_state_id`
- list transitions involving a given role

### Write capabilities
- append transition row
- record transition failure row
- record compensated or cancelled transition row
- attach reason, notes, and error metadata

### Invariants
- `workflow_transitions` is append-only
- transitions are never rewritten to impersonate the current state row
- every successful state mutation must have a corresponding applied transition row

## C. Queue Claim Lifecycle Access

### Read capabilities
- get queue claim by `queue_claim_id`
- list claims for a `queue_message_id`
- get active claim for a `queue_message_id`
- list claims for a `work_item_id`
- list claims by `claim_status`
- list claims by `ack_outcome`

### Write capabilities
- create active claim row
- release claim
- expire claim
- mark acked claim and ack outcome
- mark abandoned or superseded claim
- attach claim-source and repair metadata

### Invariants
- queue claim truth is DB-primary and must not be reconstructed from claim files
- only one active claim may exist for the same queue message at a time
- ack outcomes belong to queue-claim lifecycle records, not to ad hoc file markers

## D. Lookup And Resolution Support

### Read capabilities
- resolve `role_id` from role key or name for workflow-state operations
- resolve project-scoped work item linkage for state lookup
- resolve whether a work item already has a workflow-state row

### Non-goal
- this repository does not become a general identity service
- it may only perform the minimum identity resolution required to manage workflow-state records correctly

## E. Repair And Recovery Support

### Read capabilities
- list workflow states requiring manual repair
- list transitions with failed or compensated status
- list stale active claims

### Write capabilities
- persist `manual_repair` transition rows
- set consistency state to `manual_repair_required`
- clear repair-required state after successful compensation

### Invariants
- repair actions must be visible in authoritative DB history
- repair metadata must not live only in markdown or local JSON artifacts

## Contract Shape

The repository should expose bounded access groups rather than one flat method set.

Recommended contract groups:
- `states`
- `transitions`
- `claims`
- `repairs`
- `lookups`

This can still be implemented as one concrete repository component internally.

The important design rule is that consumers see explicit workflow-state access boundaries.

## Transaction Boundaries

The repository should support atomic write groups for these cases.

### Case 1: initial workflow-state creation
- create `workflow_states` row
- append initial `workflow_transitions` row

### Case 2: normal applied transition
- append `workflow_transitions` row
- mutate `workflow_states` current row
- optionally update active claim linkage when the transition consumes or closes a claim

### Case 3: claim lifecycle closeout
- update `queue_claims`
- update `workflow_states.active_queue_claim_id` when needed
- append repair or closeout transition when claim lifecycle changes workflow truth

### Case 4: manual repair
- append `manual_repair` transition
- mutate `workflow_states.state_consistency`
- close or supersede invalid active claim rows as part of the same unit when appropriate

## Prohibited Access Patterns

Consumers of this repository must not:
- derive current workflow stage by scanning `paa.queue_messages`
- derive current owner by inspecting packet payload JSON only
- treat repo-local status reports as workflow truth
- write `workflow_states` without also recording the corresponding transition history when the state changed
- treat queue claim files as canonical claim truth when DB claim records exist

## Reporting Implication

This repository is the data source for future workflow reports such as:
- current owner and stage summaries
- blocked or repair-required slice lists
- transition audit trails
- stale-claim reports
- acceptance and closeout lineage views

Reporting tools should query through this repository or through a projection layer built from it.

## Final Conclusion

The `Workflow State Repository` is the second concrete DAL contract because it owns the part of the old hybrid model that caused the most operational confusion.

It gives PAA a structured access layer for:
- current workflow truth
- transition history
- claim lifecycle truth
- repair visibility

That is the correct boundary for stopping workflow state from being reconstructed out of:
- queue residue
- repo-local reports
- claim JSON
- partial runtime artifacts.

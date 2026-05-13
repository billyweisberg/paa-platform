# Workflow State Machine Data Contract

Superseded for final entity-shape decisions by:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-final-workflow-state-entity-design.md`

Date: 2026-05-13

## Purpose

Define the proposed canonical data contract for the V2 `Workflow State Machine`.

This note is written from the stance of an Authority Architect authoring the next durable contract layer for PAA itself.

It answers five questions:
1. what canonical records the `Workflow State Machine` should own
2. how those records map to the DB
3. what transitions the component owns
4. what existing records it consumes but does not own
5. what projections must stop pretending to be primary truth

## Related Notes

Read alongside:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-workflow-state-machine-foundation-mapping.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-component-design-foundation-and-derivation-baseline.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-db-primary-data-consolidation-audit.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-12-paa-handoff-execution-contract.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-09-paa-data-contracts.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-v2-component-relationships.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-final-workflow-state-entity-design.md`

## Executive Summary

The `Workflow State Machine` should own two new canonical DB-primary records:
- `workflow_state`
- `workflow_transition`

And one adjacent runtime-support record if claim lifecycle remains operationally meaningful:
- `queue_claim`

These records should become the authoritative owner of:
- current workflow stage
- current owner role
- current blocking/terminal state
- the transition history that explains how the slice reached its current state

These records should **not** replace:
- design packages
- coder briefs
- queue message payloads
- acceptance events
- automation runs

Instead, they should normalize workflow truth across those existing sources.

## Core Design Rule

The `Workflow State Machine` owns semantic workflow truth.

That means:
- `paa.handoffs` owns transport handoff records
- `paa.queue_messages` owns packet transport records
- `paa.automation_runs` owns runtime execution history
- `paa.acceptance_events` owns acceptance decisions
- `workflow_state` owns current workflow truth
- `workflow_transition` owns the authoritative transition history of that workflow truth

## Canonical Records

## 1. `workflow_state`

### Purpose

Represent the current authoritative workflow state for one active or recently closed slice.

### Ownership

Owned by:
- `Workflow State Machine`

Written by:
- runtime lifecycle entry points that successfully complete a workflow transition

Read by:
- TechLead status and routing
- role preflight
- traceability projection
- acceptance/closeout paths
- future operator tooling

### Proposed fields

#### Identity and scoping
- `workflow_state_id`
- `project_id`
- `work_item_id`
- `design_package_id`
- `coder_run_brief_id`
- `authority_version_id`

#### Current workflow truth
- `workflow_stage`
- `current_owner_role_id`
- `lineage_state`
- `state_consistency`
- `blocking_reason`
- `terminal_decision`

#### Active source-transition context
- `active_handoff_id`
- `active_queue_message_id`
- `active_message_id_external`
- `active_assignment_role_id`
- `active_result_role_id`

#### Execution context
- `current_issue_number`
- `current_pr_number`
- `canonical_branch`
- `active_role_branch`

#### Timestamps
- `state_entered_at`
- `last_transition_at`
- `closed_at`
- `created_at`
- `updated_at`

#### Extension / metadata
- `metadata_json`

### Semantics

This record answers these questions directly:
- who owns the slice now
- what stage it is in now
- whether it is blocked, active, waiting, or closed
- which handoff/message is currently active, if any
- whether the state is internally consistent

### Proposed enumerations

#### `workflow_stage`
Initial useful values:
- `authorized_not_assigned`
- `delivery_review_pending`
- `worker_assignment_pending`
- `worker_execution_in_progress`
- `techlead_worker_review_pending`
- `qa_assignment_pending`
- `qa_execution_in_progress`
- `techlead_qa_review_pending`
- `acceptance_in_progress`
- `techlead_decision_recorded`
- `blocked`
- `superseded`
- `closed`

#### `lineage_state`
Initial useful values:
- `not_started`
- `active`
- `awaiting_result`
- `awaiting_acceptance`
- `closed`
- `superseded`

#### `state_consistency`
Initial useful values:
- `consistent`
- `missing_upstream_context`
- `missing_transport_record`
- `missing_execution_record`
- `conflicting_transition_evidence`
- `manual_repair_required`

#### `terminal_decision`
Initial useful values:
- `accepted`
- `rejected`
- `needs_changes`
- `blocked`
- `needs_human_review`
- `superseded`
- `none`

## 2. `workflow_transition`

### Purpose

Represent one authoritative workflow-state transition event.

### Ownership

Owned by:
- `Workflow State Machine`

Written by:
- runtime lifecycle paths that attempt a transition

Read by:
- traceability projection
- debugging and audit tools
- status derivation
- repair/compensation tooling

### Proposed fields

#### Identity
- `workflow_transition_id`
- `workflow_state_id`
- `project_id`
- `work_item_id`

#### Transition request
- `transition_type`
- `from_workflow_stage`
- `to_workflow_stage`
- `from_owner_role_id`
- `to_owner_role_id`
- `transition_status`

#### Source references
- `source_handoff_id`
- `source_queue_message_id`
- `source_message_id_external`
- `source_packet_schema_type`
- `source_packet_role_id`

#### Resulting references
- `result_handoff_id`
- `result_queue_message_id`
- `result_message_id_external`
- `result_packet_schema_type`
- `result_role_id`

#### Execution context
- `performed_by_agent_id`
- `performed_by_role_id`
- `automation_run_id`
- `reason`
- `notes`
- `error_code`
- `error_details`

#### Timing
- `transition_requested_at`
- `transition_applied_at`
- `created_at`

#### Metadata
- `metadata_json`

### Semantics

This record answers these questions directly:
- what transition was attempted
- what state it started from
- what state it moved to
- which packet or result caused it
- who performed it
- whether it succeeded, failed, or was compensated

### Proposed enumerations

#### `transition_type`
Initial useful values:
- `assignment_emitted`
- `assignment_claimed`
- `role_result_returned`
- `delivery_review_returned`
- `qa_result_returned`
- `techlead_assignment_advanced`
- `techlead_decision_recorded`
- `accept_and_merge_completed`
- `slice_closed`
- `slice_blocked`
- `slice_superseded`
- `manual_repair`

#### `transition_status`
Initial useful values:
- `requested`
- `applied`
- `failed`
- `compensated`
- `cancelled`

## 3. `queue_claim`

### Purpose

Represent a DB-primary queue claim/lease if queue claiming continues to affect workflow truth.

### Ownership

Owned by:
- queue claim / transport support layer

Consumed by:
- `Workflow State Machine`
- runtime lifecycle engine

### Proposed fields
- `queue_claim_id`
- `queue_message_id`
- `project_id`
- `work_item_id`
- `claimed_by_agent_id`
- `claimed_by_role_id`
- `claim_status`
- `claimed_at`
- `acked_at`
- `released_at`
- `expires_at`
- `metadata_json`

### Why this is separate

Claims are transport-support state, not core workflow-state identity.
But they should still be DB-primary if they determine whether a packet is considered actively in flight.

## DB Mapping

## New tables

The cleanest next DB mapping is:
- `paa.workflow_states`
- `paa.workflow_transitions`
- `paa.queue_claims`

## Existing tables consumed but not replaced

### Upstream context
- `paa.projects`
- `paa.roles`
- `paa.work_items`
- `paa.authority_versions`
- `paa.design_packages`
- `paa.coder_run_briefs`
- `paa.coder_brief_sequence_states`

### Runtime event sources
- `paa.handoffs`
- `paa.queue_messages`
- `paa.automation_runs`
- `paa.acceptance_events`

### Execution record context
- `paa.execution_records`

## Transition Ownership Rules

### Rule 1
Only the runtime lifecycle engine may request a state transition.

### Rule 2
A transition is authoritative only after:
- source validation passes
- required runtime side effects complete
- the `workflow_state` row is updated
- the `workflow_transition` row is persisted

### Rule 3
Queue send/claim/ack events do not become workflow truth by themselves.
They become workflow truth only when committed through the `Workflow State Machine`.

### Rule 4
Acceptance and merge outcomes do not become current workflow truth by themselves.
They become workflow truth only when persisted into the workflow-state record.

### Rule 5
Projection surfaces may not invent workflow stage.
They must read it from `workflow_state`.

## Consumed Data Contracts

The `Workflow State Machine` consumes, but does not own:

### Authority and slice-definition context
- `paa.design_packages.package_json`
- `paa.coder_run_briefs.brief_json`
- installed authority package metadata

### Readiness context
- `paa.coder_brief_sequence_states.readiness_state`
- dependency blocking data derived from `paa.component_dependency_edges`

### Runtime event context
- `paa.queue_messages.payload_json`
- `paa.handoffs.status`
- `paa.automation_runs.status`
- `paa.acceptance_events.decision`
- `paa.execution_records.status`

## Projection Boundaries

The following surfaces must become projections only.

### Must stop acting as primary truth
- `techlead-status-report.json`
- queue preview plus local report synthesis in TechLead status
- role preflight logic that infers current owner/stage from queue residue alone
- repo-local memory and report artifacts used for workflow recovery

### May remain as projections/evidence
- report JSON in `.project/data/paa/reports/`
- human-readable markdown exports
- repo-local logs
- automation memory markdown used only for narrative/operator context

## Authority-Authoring Gap

We already have canonical schemas for:
- authority package config and metadata
- handoff packets
- one runtime status report

We do **not** yet have canonical schema artifacts for:
- `workflow_state`
- `workflow_transition`
- `queue_claim`

That means this note is the design contract precursor to those schemas.

## Hard Conclusions

1. The `Workflow State Machine` should own DB-primary current workflow truth.
2. It needs one state record and one transition record to do that cleanly.
3. Queue claim must become DB-primary if it remains part of the lifecycle contract.
4. Existing transport, design, and execution tables remain important, but they are inputs and evidence, not the owner of workflow truth.
5. Status reports and repo-local evidence files must be demoted to projections.

## Recommended Immediate Next Step

Create the first concrete schema artifacts for:
- `workflow_state.schema.json`
- `workflow_transition.schema.json`
- `queue_claim.schema.json`

Then map them into a migration note for:
- `paa.workflow_states`
- `paa.workflow_transitions`
- `paa.queue_claims`

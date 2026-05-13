# Runtime Event Repository Contract

Date: 2026-05-13

## Purpose

Define the concrete Data Access Layer contract for:
- `Runtime Event Repository`

This repository is the structured access boundary for DB-primary runtime transport, execution, evidence, acceptance, and structured run-event history.

Its purpose is to give higher-level components a stable way to:
- read and write runtime event history
- resolve transport and handoff provenance
- access structured transition inputs and automation run milestones
- persist acceptance and evidence records

without promoting runtime history into workflow truth or forcing consumers to parse raw logs and packet artifacts directly.

## Related Notes

Read alongside:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-data-access-layer-design.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-final-runtime-input-and-run-event-entity-design.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-workflow-state-repository-contract.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-final-workflow-state-entity-design.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-final-projection-boundary-policy.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-12-paa-handoff-execution-contract.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-stable-table-classification-and-ownership-map.md`

## Role

Provide structured access to:
1. handoff and queue transport records
2. runtime execution and automation run history
3. structured transition inputs and automation run events
4. evidence and verification history
5. acceptance and closeout event history

## Repository Boundary

The repository owns structured access to these DB tables:
- `paa.handoffs`
- `paa.queue_messages`
- `paa.automation_runs`
- `paa.transition_inputs`
- `paa.automation_run_events`
- `paa.acceptance_events`
- `paa.execution_records`
- `paa.evidence`
- `paa.verification_obligations`

It may join supporting identity tables only as needed for lookup resolution:
- `paa.projects`
- `paa.roles`
- `paa.work_items`
- `paa.agents`

It does **not** own primary access to:
- `paa.workflow_states`
- `paa.workflow_transitions`
- `paa.queue_claims`
- stable component-design tables
- read-model projections or report views

Those remain outside this repository boundary.

## Non-Goals

The repository does not:
- define current workflow truth
- decide legal workflow transitions
- replace the `Workflow State Repository`
- author projections
- own stable Component Design identity
- interpret repo-local markdown or raw logs as canonical runtime truth

## Primary Consumers

The main consumers are:
- `Runtime Lifecycle Engine`
- `Workflow State Machine`
- `Reporting And Traceability Projection`
- future operator, recovery, and analytics tooling

## Canonical Read Models

The repository provides structured access to six logical read models.

### 1. Handoff And Queue Transport View

Represents transport-level runtime history.

Includes:
- handoff identity and direction
- queue message identity and payload registration
- sender and recipient role context
- queue timing and delivery state

Backed by:
- `paa.handoffs`
- `paa.queue_messages`

### 2. Automation Run History View

Represents the run-level execution history for one automation run.

Includes:
- run identity and status
- role and agent context
- execution outcome
- run-level timing

Backed by:
- `paa.automation_runs`

### 3. Transition Input View

Represents structured runtime inputs that materially participated in a transition.

Includes:
- input type and source surface
- source queue or report linkage
- payload registration
- structured summaries and hashes

Backed by:
- `paa.transition_inputs`

### 4. Automation Run Event View

Represents structured, append-only milestone and outcome history for a run.

Includes:
- event type, phase, and status
- queue, handoff, and claim linkage when available
- event summaries and evidence pointers

Backed by:
- `paa.automation_run_events`

### 5. Evidence And Verification View

Represents runtime evidence and verification obligations relevant to execution and review.

Includes:
- evidence references
- verification requirement state
- validation and proof linkage

Backed by:
- `paa.evidence`
- `paa.verification_obligations`
- `paa.execution_records`

### 6. Acceptance And Closeout Event View

Represents recorded acceptance and closeout event history.

Includes:
- acceptance decision records
- decision provenance
- closeout timing and actor context

Backed by:
- `paa.acceptance_events`

## Required Repository Capabilities

## A. Handoff And Queue Message Access

### Read capabilities
- get handoff by `handoff_id`
- get queue message by `queue_message_id`
- get queue message by external message id
- list handoffs for a `work_item_id`
- list queue messages for a `work_item_id`
- list queue messages by queue name
- list queue messages by packet schema type

### Write capabilities
- create handoff record
- create queue message record
- update queue message delivery or acknowledgement metadata
- attach provenance metadata to a handoff or queue message row

### Invariants
- transport history remains queryable even after workflow state advances
- queue payload registration belongs here, not in workflow-state records
- transport rows do not define current workflow truth by themselves

## B. Automation Run Access

### Read capabilities
- get automation run by `automation_run_id`
- list automation runs for a `work_item_id`
- list automation runs by role
- list automation runs by status
- list most recent automation run for a work item and role

### Write capabilities
- create automation run row
- update automation run status and summary metadata
- mark run completion or failure

### Invariants
- run-level history is append-friendly and audit-friendly
- automation run summaries are structured runtime history, not workflow truth

## C. Transition Input Access

### Read capabilities
- get transition input by `transition_input_id`
- list transition inputs for a `work_item_id`
- list transition inputs for an `automation_run_id`
- list transition inputs for a `workflow_transition_id`
- find transition input by `(input_type, input_key, input_hash)` when provenance repair is needed

### Write capabilities
- create transition input record
- attach workflow transition linkage after the transition is known
- update structured summaries and source linkage metadata

### Invariants
- `payload_json` in `transition_inputs` is the canonical structured transition-input registration
- file paths or report paths are secondary pointers only
- transition inputs must remain queryable even if repo-local artifacts disappear

## D. Automation Run Event Access

### Read capabilities
- get run event by `automation_run_event_id`
- list run events for an `automation_run_id` in event order
- list run events for a `work_item_id`
- list run events by `event_type`
- list run events by `event_phase`
- list run events by `event_status`

### Write capabilities
- append automation run event row
- append failure or compensated event row
- attach event summaries, evidence refs, and raw-log pointers

### Invariants
- `automation_run_events` is append-only
- structured milestone history belongs here, not only in `summary.json` or `events.jsonl`
- raw logs are evidence pointers, not the only runtime event record

## E. Evidence And Verification Access

### Read capabilities
- get evidence rows for a `work_item_id`
- list evidence by evidence type or source
- list verification obligations for a `work_item_id`
- list unmet or blocked verification obligations
- get execution record by `execution_record_id`

### Write capabilities
- create or update evidence records
- create or update verification obligations
- create or update execution records when runtime evidence requires them

### Invariants
- evidence and verification state remain runtime/history concerns until promoted by projection or workflow logic
- this repository persists proof context, not acceptance semantics

## F. Acceptance Event Access

### Read capabilities
- get acceptance event by `acceptance_event_id`
- list acceptance events for a `work_item_id`
- list acceptance events by decision
- get most recent acceptance event for a work item

### Write capabilities
- create acceptance event
- update acceptance-event provenance or metadata when late evidence must be attached

### Invariants
- acceptance event history remains queryable independent of current workflow state
- acceptance events contribute to workflow and reporting logic, but do not replace workflow-state records

## G. Lookup And Resolution Support

### Read capabilities
- resolve runtime event rows by `message_id_external`
- resolve run/event records for a given work item and role
- resolve whether structured transition input already exists for a given input hash or key

### Non-goal
- this repository does not become a general identity service
- it only provides the minimum lookup support needed for runtime history and provenance operations

## Contract Shape

The repository should expose bounded access groups rather than one flat method set.

Recommended contract groups:
- `handoffs`
- `queue_messages`
- `automation_runs`
- `transition_inputs`
- `run_events`
- `evidence`
- `verification`
- `acceptance`
- `lookups`

This can still be implemented as one concrete repository component internally.

The important design rule is that consumers see explicit runtime-history access boundaries.

## Transaction Boundaries

The repository should support atomic write groups for these cases.

### Case 1: packet send registration
- create handoff row
- create queue message row
- append relevant run event row when part of the same send unit

### Case 2: role-return or decision-input registration
- create transition input row
- append relevant run event row
- attach source queue or handoff provenance in the same unit

### Case 3: automation run milestone recording
- append `automation_run_events` row
- update `automation_runs` summary/status when needed
- attach evidence pointer or metadata in the same unit when available

### Case 4: acceptance closeout event recording
- create acceptance event
- append closeout-related run event when applicable
- update linked evidence metadata when part of the same closeout unit

## Prohibited Access Patterns

Consumers of this repository must not:
- treat queue message rows as the current workflow state
- treat handoff history as the only acceptance history
- parse repo-local report JSON or raw logs directly when normalized runtime-event rows exist
- write workflow-state rows through this repository
- treat verification projections as if they replace evidence and obligation records

## Reporting Implication

This repository is the data source for future runtime-history reports such as:
- transport and queue activity timelines
- automation run milestone reports
- transition-input provenance reports
- evidence and verification coverage reports
- acceptance and closeout event timelines

Reporting tools should query through this repository or through a projection layer built from it.

## Final Conclusion

The `Runtime Event Repository` is the third concrete DAL contract because it owns the other half of the old hybrid boundary: runtime history and operational evidence.

It gives PAA a structured access layer for:
- transport records
- execution history
- structured transition inputs
- automation run milestones
- evidence and acceptance history

That is the correct boundary for stopping runtime history from being reconstructed out of:
- raw logs
- repo-local report files
- ad hoc packet inspection
- unstructured event artifacts.

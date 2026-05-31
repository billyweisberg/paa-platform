Title: PAA Methodology Execution Object Model
Doc-ID: paa-methodology-execution-object-model
Doc-Type: design-note
Status: active
Lifecycle-Stage: design
Created: 2026-05-30
Last-Edited: 2026-05-30
Author: Billy Weisberg
Repo: paa-platform
Component: PAAMethodologyExecution
Domain: methodology-execution
Keywords: paa, methodology, execution, object-model, pointer, lane, stage, step
Depends-On: 2026-05-30-paa-methodology-execution-state-model.md, 2026-05-30-paa-methodology-execution-component-family.md, 2026-05-30-paa-methodology-lane-and-command-model.md, 2026-05-13-paa-domain-object-model-and-oo-component-decomposition.md
Supersedes:
Superseded-By:
Canonical: true
Review-After: 2026-06-30
Summary: Defines the concrete domain object model for the methodology-execution pointer family, including owned objects, related external truth, and object lifecycle boundaries.

# PAA Methodology Execution Object Model

## Purpose

Define the domain object model for the methodology-execution pointer family before repository and service contracts are finalized.

This note exists to answer:
- which objects the pointer family really owns
- which objects it only binds to or projects from
- how lane, stage, step, status, and owner semantics fit together
- which relationships are append-only history versus mutable current truth

## Design Rule

The methodology-execution family should own:
- pointer truth
- transition history for pointer truth
- typed bindings to related authority and runtime records
- operator-facing projection records derived from pointer truth and related records

It should not absorb ownership of:
- implementation-plan internals
- workflow internals
- packet transport internals
- coder-brief internals
- queue-claim internals

## Core Object Set

## 1. `MethodologyExecution`

### Meaning
The mutable current pointer for one governed execution thread.

### Owns
- active lane
- active stage
- active step
- current status
- current owner role
- next action key
- blocked reason
- primary binding references for the active execution thread

### Identity
- `methodology_execution_id`

### Scope
One record per active governed execution thread.

### Important rule
This is the DB-primary current-truth object for “where are we in the methodology right now?”

## 2. `MethodologyExecutionEvent`

### Meaning
Append-only transition history for `MethodologyExecution`.

### Owns
- prior lane/stage/step snapshot
- next lane/stage/step snapshot
- transition kind
- actor context
- notes and evidence
- event creation time

### Identity
- `methodology_execution_event_id`

### Important rule
This object is immutable history.
It explains how current pointer truth changed.

## 3. `MethodologyExecutionBinding`

### Meaning
A typed relationship from one methodology execution thread to one related authority or runtime record.

### Owns
- binding kind
- bound record identity
- primary vs secondary binding semantics
- optional notes and metadata

### Identity
- `methodology_execution_binding_id`

### Important rule
Bindings prevent the root pointer record from turning into a giant nullable foreign-key bag.
Direct bindings may still exist for the most common high-value references, but the general-purpose relationship model should live here.

## 4. `MethodologyExecutionProjection`

### Meaning
An operator-facing read model summarizing the current methodology position and next valid action.

### Owns
- projection snapshot for CLI and reporting
- resolved display values for lane, stage, step, owner, and next action
- summarized related-record identities
- rendered explanation hints

### Identity
- `methodology_execution_id`
- optional projection version or refresh timestamp

### Important rule
This is a read model, not primary mutable truth.

## Value Object Set

## 5. `MethodologyLane`

### Meaning
A closed vocabulary value representing the active methodology lane.

### Canonical values
- `authority_derivation`
- `component_realization`
- `runtime_execution`
- `acceptance_closeout`

### Important rule
This is value vocabulary, not an entity.

## 6. `MethodologyStage`

### Meaning
A coarse-grained lifecycle position inside one lane.

### Canonical initial values
- `vision`
- `design`
- `stage1_package`
- `derivation_readiness`
- `implementation_plan_derivation`
- `brief_assembly`
- `brief_target_authoring`
- `brief_review`
- `packet_preparation`
- `component_materialization`
- `slice_execution`
- `runtime_handoff`
- `verification`
- `acceptance`
- `closed`

### Important rule
Stage must be broad enough for reporting and narrow enough for preflight.

## 7. `MethodologyStep`

### Meaning
The exact bounded action currently active or next in line.

### Examples
- `derive_design_package`
- `evaluate_derivation_readiness`
- `materialize_component_spec`
- `derive_next_activity_bundle`
- `run_worker_packet`
- `accept_slice`

### Important rule
A step should map to a concrete operator action or one CLI command, not a vague narrative label.

## 8. `MethodologyExecutionStatus`

### Meaning
A closed vocabulary value expressing whether the current step is executable, running, blocked, waiting, or terminal.

### Canonical initial values
- `not_started`
- `ready`
- `active`
- `blocked`
- `waiting`
- `completed`
- `superseded`
- `closed`

## 9. `MethodologyOwnerRole`

### Meaning
The current owner of the next methodology transition.

### Canonical initial values
- `Authority Architect`
- `Delivery Architect`
- `TechLead`
- `Python Dev`
- `QA`
- `Operator`
- `System`

## 10. `MethodologyTransitionKind`

### Meaning
A value object classifying why one execution-state event occurred.

### Canonical initial values
- `manual_progression`
- `automated_progression`
- `preflight_block`
- `handoff_claim`
- `handoff_result`
- `verification_outcome`
- `acceptance_outcome`
- `repair`
- `supersede`
- `closeout`

## 11. `MethodologyBindingKind`

### Meaning
A value object classifying what sort of related record is bound to a methodology execution thread.

### Canonical initial values
- `project`
- `work_item`
- `component`
- `design_package`
- `implementation_plan`
- `implementation_plan_activity`
- `coder_run_brief`
- `coder_brief_target`
- `workflow`
- `queue_claim`
- `handoff_packet`
- `handoff_record`
- `automation_run`
- `acceptance_event`
- `published_execution_package`
- `installed_execution_package`
- `execution_overlay`

## Relationship Model

### `MethodologyExecution` -> `Project`
- required reference
- the methodology thread must always belong to one project

### `MethodologyExecution` -> `WorkItem`
- usually required for real execution threads
- may be absent only for early meta-authority or bootstrap threads if explicitly allowed later

### `MethodologyExecution` -> `MethodologyExecutionEvent`
- one-to-many
- append-only history

### `MethodologyExecution` -> `MethodologyExecutionBinding`
- one-to-many
- typed related-record references

### `MethodologyExecution` -> `MethodologyExecutionProjection`
- one-to-one or one-to-many versioned projection depending on later storage choice

## External Related Objects Not Owned Here

The following objects are related but remain externally owned:
- `DesignPackage`
- derivation-readiness result surfaces
- `ImplementationPlan`
- `ImplementationPlanActivity`
- `Workflow`
- `WorkflowTransition`
- `QueueClaim`
- `HandoffPacket`
- `HandoffRecord`
- `AutomationRun`
- `AcceptanceEvent`
- `PublishedExecutionPackage`
- `InstalledExecutionPackage`
- `ExecutionOverlay`

## Ownership Boundary Table

| object | ownership | reason |
|---|---|---|
| `MethodologyExecution` | owned | current pointer truth belongs to this family |
| `MethodologyExecutionEvent` | owned | pointer transition history belongs to this family |
| `MethodologyExecutionBinding` | owned | typed binding registry belongs to this family |
| `MethodologyExecutionProjection` | owned | operator-facing projection belongs to this family |
| `ImplementationPlan` | external | already owned by implementation-plan substrate |
| `Workflow` | external | already owned by workflow-lifecycle substrate |
| `QueueClaim` | external | transport/runtime support truth, not methodology pointer truth |
| `HandoffPacket` | external | transport payload truth, not pointer truth |
| `AcceptanceEvent` | external | acceptance outcome truth, not pointer truth |

## Lifecycle Rules

### Rule 1. One current pointer per governed execution thread
At any moment, one execution thread should have one current `MethodologyExecution` root record.

### Rule 2. Current truth plus append-only history
Current pointer truth lives in `MethodologyExecution`.
History lives in `MethodologyExecutionEvent`.

### Rule 3. Bind, do not absorb
Related record identities should be bound and summarized, not absorbed as duplicated state owners.

### Rule 4. Projection is downstream
Operator-facing status, next-step, and explain surfaces should read from `MethodologyExecutionProjection`, not reconstruct from scattered records every time.

### Rule 5. Lane vocabulary is closed
Lane values should remain strict and intentionally expanded only through explicit authority updates.

## Immediate Repository Implications

The repository layer will need to support at least:
- upsert current `MethodologyExecution`
- append `MethodologyExecutionEvent`
- upsert or replace `MethodologyExecutionBinding` entries
- read current execution by primary identity and by bound records
- load projection-oriented snapshots for CLI-facing queries

## Immediate Service Implications

The service family will need to support at least:
- current-state transition application
- next-step derivation
- projection refresh
- lane-aware preflight evaluation against current pointer truth

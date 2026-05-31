Title: Methodology Execution Repository Contract And Persistence Mapping
Doc-ID: methodology-execution-repository-contract-and-persistence-mapping
Doc-Type: design-note
Status: active
Lifecycle-Stage: design
Created: 2026-05-30
Last-Edited: 2026-05-30
Author: Billy Weisberg
Repo: paa-platform
Component: MethodologyExecutionRepository
Domain: methodology-execution
Keywords: paa, methodology, execution, repository, persistence, mapping, contract
Depends-On: 2026-05-30-paa-methodology-execution-object-model.md, 2026-05-30-paa-methodology-execution-state-model.md, 2026-05-30-paa-methodology-execution-component-family.md, 2026-05-13-component-design-repository-contract.md
Supersedes:
Superseded-By:
Canonical: true
Review-After: 2026-06-30
Summary: Defines the repository boundary and first persistence mapping for methodology execution current truth, transition history, bindings, and projection-oriented retrieval.

# Methodology Execution Repository Contract And Persistence Mapping

## Purpose

Define the initial repository boundary and persistence mapping for the methodology-execution pointer family.

This note exists to make the next implementation lane concrete by specifying:
- what the repository must read and write
- which records are DB-primary truth versus projection-oriented retrieval
- how the object model maps into relational tables and queries

## Repository Role

`MethodologyExecutionRepository` should provide DB-primary persistence for:
- `MethodologyExecution`
- `MethodologyExecutionEvent`
- `MethodologyExecutionBinding`

It should also support projection-oriented reads sufficient for:
- `MethodologyExecutionProjectionService`
- CLI pointer commands such as future `paa status`, `paa next`, and `paa explain`

## Non-Role

The repository should not:
- derive next valid transitions itself
- perform lane-aware preflight policy itself
- render CLI output
- own implementation-plan or workflow repositories
- directly mutate external related-record truth

## Repository Contract Surface

### Write operations

#### `upsert_methodology_execution`
Purpose:
- create or update the current pointer record for one execution thread

Carries:
- root identity
- lane, stage, step, status
- owner role
- next action key
- blocked reason
- optional direct reference ids
- metadata

#### `append_methodology_execution_event`
Purpose:
- append one immutable pointer transition event

Carries:
- execution id
- from/to lane
- from/to stage
- from/to step
- transition kind
- actor context
- notes
- evidence

#### `replace_methodology_execution_bindings`
Purpose:
- replace the binding set for one execution thread and one binding scope or category

Carries:
- execution id
- binding entries
- optional scope semantics such as `replace_all` or `replace_kind`

### Read operations

#### `get_methodology_execution`
Purpose:
- load one current pointer record by `methodology_execution_id`

#### `find_methodology_execution_by_primary_ref`
Purpose:
- resolve the current pointer from primary business anchors such as:
  - `project_id`
  - `work_item_id`
  - optional `component_id`

#### `list_methodology_execution_events`
Purpose:
- load append-only transition history for one execution thread

#### `list_methodology_execution_bindings`
Purpose:
- load the typed related-record bindings for one execution thread

#### `load_methodology_execution_projection_inputs`
Purpose:
- load the repository-side stitched view needed by projection and pointer-status services

## Owned Persistence Tables

### `paa.methodology_executions`
DB-primary current truth.

#### Key columns
- `methodology_execution_id`
- `project_id`
- `work_item_id`
- `lane`
- `stage`
- `step`
- `status`
- `current_owner_role`
- `next_action_key`
- `blocked_reason`
- `component_id` nullable
- `design_package_id` nullable
- `implementation_plan_id` nullable
- `coder_run_brief_id` nullable
- `packet_id` nullable
- `workflow_state_id` nullable
- `active_authority_ref`
- `active_artifact_ref`
- `metadata_json`
- `created_at`
- `updated_at`

#### Important rule
This table is the canonical current-pointer table.

### `paa.methodology_execution_events`
Append-only history table.

#### Key columns
- `methodology_execution_event_id`
- `methodology_execution_id`
- `from_lane`
- `to_lane`
- `from_stage`
- `to_stage`
- `from_step`
- `to_step`
- `from_status`
- `to_status`
- `transition_kind`
- `actor_role_id` nullable
- `actor_name`
- `notes`
- `evidence_json`
- `created_at`

#### Important rule
This table must never be updated in place except for rare repair tooling with explicit authority.

### `paa.methodology_execution_bindings`
Typed many-to-one binding registry.

#### Key columns
- `methodology_execution_binding_id`
- `methodology_execution_id`
- `binding_kind`
- `bound_record_id`
- `bound_record_key`
- `bound_record_ref`
- `is_primary`
- `notes`
- `metadata_json`
- `created_at`
- `updated_at`

#### Important rule
This table should support heterogeneous bindings without forcing every relationship into the root table.

## Projection-Oriented Read Model

The first repository contract does not need to own a materialized projection table yet.

It may initially provide `load_methodology_execution_projection_inputs` as a stitched query over:
- `paa.methodology_executions`
- `paa.methodology_execution_bindings`
- and selected external tables by id reference

A dedicated materialized projection table can be introduced later if query complexity or reporting load justifies it.

## Persistence Mapping Table

| object | primary table | write shape | read shape |
|---|---|---|---|
| `MethodologyExecution` | `paa.methodology_executions` | upsert | current-state row |
| `MethodologyExecutionEvent` | `paa.methodology_execution_events` | append-only insert | ordered event rows |
| `MethodologyExecutionBinding` | `paa.methodology_execution_bindings` | replace or upsert by execution/kind | binding rows |
| `MethodologyExecutionProjection` | derived query initially | none | stitched projection inputs |

## Key Query Paths

### Query path 1. Load current pointer by execution id
Used by:
- CLI status and next-step inspection
- state service transition logic

### Query path 2. Resolve pointer by project/work item
Used by:
- operator commands that begin from issue or work-item identity
- runtime orchestration flows that need to locate current methodology state

### Query path 3. Load full event history
Used by:
- audits
- explain surfaces
- repair and diagnostics

### Query path 4. Load projection inputs
Used by:
- future `paa status`
- future `paa next`
- future `paa explain`

## Integrity Rules

### Rule 1. One active root per execution thread
The persistence model should prevent duplicate current-root records for the same primary execution anchor set.

### Rule 2. Event history is append-only
Pointer history should not be rewritten as a normal update path.

### Rule 3. Binding kinds are vocabulary-controlled
`binding_kind` must come from explicit controlled vocabulary.

### Rule 4. External refs are references only
The repository may point to external truth, but it must not duplicate ownership of that truth.

### Rule 5. Projection reads may join external truth
Projection-oriented reads may stitch from external tables, but write ownership stays local to this family.

## First Slice Recommendation

The first governed implementation slice should target:
1. repository interface contract
2. DTOs for root row, event row, and binding row
3. minimal Postgres adapter for:
- upsert current execution
- append execution event
- get current execution by id
- find execution by project/work item

That is enough to start the pointer family without overcommitting to the later projection and preflight surfaces.

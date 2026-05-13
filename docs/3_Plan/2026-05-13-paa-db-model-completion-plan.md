# PAA DB Model Completion Plan

Date: 2026-05-13

## Purpose

Sequence the work required to complete the PAA DB model before moving into Data Access Layer implementation or deeper component implementation.

This plan exists because the V2 System Design work established two things clearly:
1. the DB is the primary operational truth surface for PAA
2. the current model is substantial, but incomplete in the specific places that matter most for workflow truth, installed execution-package truth, and normalized Component Design structure

This note is an execution plan.
It is not the top-level design authority.

## Design Authority

Use these design notes as the governing authority for this plan:
- `docs/2_Design/2026-05-13-paa-system-component-diagram-v2.md`
- `docs/2_Design/2026-05-13-paa-v2-component-relationships.md`
- `docs/2_Design/2026-05-13-paa-runtime-consolidation-design-correction.md`
- `docs/2_Design/2026-05-13-paa-schema-and-data-surface-audit.md`
- `docs/2_Design/2026-05-13-paa-db-primary-data-consolidation-audit.md`
- `docs/2_Design/2026-05-13-existing-component-design-model-audit.md`
- `docs/2_Design/2026-05-13-component-design-foundation-and-derivation-baseline.md`
- `docs/2_Design/2026-05-13-workflow-state-machine-foundation-mapping.md`
- `docs/2_Design/2026-05-13-workflow-state-machine-data-contract.md`
- `docs/2_Design/2026-05-13-paa-db-model-diagram-and-gap-analysis.md`
- `docs/2_Design/2026-05-13-final-component-element-entity-design.md`

## Planning Rule

Do not implement the Data Access Layer against the current transitional data model.

Finish the DB model first, then design and implement the Data Access Layer against the completed model.

That means this plan ends when:
- the target DB-primary entities are defined
- existing tables are classified and normalized
- file-primary operational truth is demoted or replaced
- projection-only surfaces are clearly identified

## Completion Objective

At the end of this plan, PAA should have a DB model with these properties:

1. current workflow truth is DB-primary
2. transition history is DB-primary
3. queue claim / lease truth is DB-primary
4. installed execution-package registration and overlay state are DB-primary
5. stable Component Design records are clearly separated from derivative slice records
6. runtime-event history is clearly separated from workflow state
7. reporting and local artifacts are projections, not truth
8. the Data Access Layer can be designed against stable data boundaries instead of transitional ones

## Classification Framework

Each current or proposed data surface falls into one of these plan actions:
- `keep`: retain as a stable part of the target model
- `extend`: keep, but add fields, constraints, or stronger invariants
- `add`: create as a missing DB-primary entity family
- `demote`: retain only as projection, cache, export, or local package artifact

## Work Area Checklist

- [ ] workflow-state layer
  - status: entity design complete, migration implemented, runtime adoption not started
  - action: `add`
  - target entities:
    - `paa.workflow_states`
    - `paa.workflow_transitions`
    - `paa.queue_claims` or equivalent lease model

- [ ] execution-package registration DB entity layer
  - status: entity design complete, migration implemented, runtime adoption not started
  - action: `add`
  - target entities:
    - `paa.execution_package_installs`
    - `paa.execution_package_overlays`

- [x] component-design foundation normalization
  - status: normalization rules complete, stable component element schema implemented, runtime adoption not started
  - action: `keep`, `extend`, and `add`
  - target tables:
    - `paa.components`
    - `paa.component_surfaces`
    - `paa.component_relationships`
    - `paa.component_element_types`
    - `paa.component_elements`
    - `paa.component_dependency_edges`

- [ ] derivative slice-artifact normalization
  - status: normalization rules complete, schema extensions implemented, runtime adoption not started
  - action: `keep` and `extend`
  - target tables:
    - `paa.design_packages`
    - `paa.design_package_signoffs`
    - `paa.coder_run_briefs`
    - `paa.coder_brief_sequence_states`

- [ ] runtime-event and execution-history alignment
  - status: entity design complete, migration implemented, runtime adoption not started
  - action: `keep` and `extend`
  - target tables:
    - `paa.handoffs`
    - `paa.queue_messages`
    - `paa.automation_runs`
    - `paa.execution_records`
    - `paa.acceptance_events`
    - `paa.evidence`
    - `paa.verification_obligations`

- [ ] projection and file-surface demotion
  - status: boundary policy complete, schema baseline implemented, runtime demotion not started
  - action: `demote`
  - target surfaces:
    - repo-local report JSON
    - automation-memory markdown
    - queue-state files
    - claim JSON
    - markdown report companions

## Current DB Model Decision Table

## Keep As Stable Foundations

These should remain part of the target DB model:
- `paa.projects`
- `paa.roles`
- `paa.authority_versions`
- `paa.work_items`
- `paa.agents`
- `paa.execution_records`
- `paa.handoffs`
- `paa.queue_messages`
- `paa.automation_runs`
- `paa.verification_obligations`
- `paa.evidence`
- `paa.acceptance_events`
- `paa.source_artifacts`
- `paa.source_statements`
- `paa.requirements`
- `paa.requirement_sources`
- `paa.design_decisions`
- `paa.decision_requirements`
- `paa.spec_fragments`
- `paa.spec_fragment_requirements`
- `paa.spec_fragment_decisions`
- `paa.implementation_targets`
- `paa.authority_version_fragments`
- `paa.authority_version_targets`
- `paa.components`
- `paa.component_surfaces`
- `paa.component_relationships`
- `paa.component_element_types`
- `paa.component_elements`
- `paa.design_packages`
- `paa.design_package_signoffs`
- `paa.coder_run_briefs`
- `paa.component_dependency_edges`
- `paa.coder_brief_sequence_states`

## Keep And Extend

These exist, but need stronger semantics or alignment rules:

### Runtime execution and transport
- `paa.handoffs`
  - extend with clearer lifecycle relationship to workflow transitions and queue claims
- `paa.queue_messages`
  - extend with clearer linkage to workflow transitions, queue claims, and packet provenance
- `paa.automation_runs`
  - extend to absorb structured run milestones now stranded in file-only logs
- `paa.acceptance_events`
  - extend to align consistently with closed workflow transitions and decision records
- `paa.execution_records`
  - extend only if needed to distinguish operational execution evidence from workflow transitions

### Stable component foundation
- `paa.components`
  - extend so newer V2 components and stable PAA components are first-class, not just historical retirement components
- `paa.component_surfaces`
  - extend if needed to model stable execution, data, and configuration surfaces explicitly
- `paa.component_relationships`
  - extend if needed to separate structural relationships from runtime sequencing dependencies
- `paa.component_dependency_edges`
  - extend so it becomes a current, maintained dependency model instead of a narrow historical one

### Derivative slice-artifact model
- `paa.design_packages`
  - extend with stricter alignment rules to stable component identity
- `paa.coder_run_briefs`
  - extend with stricter alignment rules to stable component identity and execution-package provenance
- `paa.coder_brief_sequence_states`
  - extend only as needed after upstream workflow-state and dependency normalization

## Add As Missing DB-Primary Entities

These are the mandatory additions before the data model is considered complete.

### Workflow state
- `paa.workflow_states`
  - one authoritative current workflow-state row per active slice
- `paa.workflow_transitions`
  - append-only transition history
- `paa.queue_claims`
  - claim / lease truth for queue lifecycle

### Execution-package install state
- `paa.execution_package_installs`
  - installed package registration for each consumer execution surface
- `paa.execution_package_overlays`
  - overlay activation / removal history and active state

### Structured transition and run metadata
- `paa.transition_inputs`
  - canonical DB record for structured transition inputs when they matter operationally
- `paa.automation_run_events`
  - structured milestones and outcomes now trapped in `summary.json` or `events.jsonl`

### Projection layer, if explicit DB projection records are chosen
- `paa.workflow_status_projections`
- `paa.lineage_projections`
- `paa.accepted_chain_projections`

Important note:
- explicit projection tables are a design option, not yet a mandatory migration commitment
- they remain in-scope for the completed model because the projection boundary must be explicit even if implemented through views or materialized views

## Demote To Projection Or Local Artifact Only

These must stop acting like operational truth.

### Repo-local report artifacts
- `.project/data/paa/reports/techlead-status-report.json`
- `.project/data/paa/reports/techlead-assignment.*.json`
- `.project/data/paa/reports/worker-result.*.json`
- `.project/data/paa/reports/delivery-review.*.json`
- `.project/data/paa/reports/qa-verification.*.json`
- `.project/data/paa/reports/techlead-decision.*.json`
- `.project/data/paa/reports/role-result-input.*.json`

Correct role after this plan:
- export
- local inspection artifact
- reproducible projection

### Queue and claim files
- `.project/data/paa/claims/*.json`
- `.project/data/paa/queue-state/**`

Correct role after this plan:
- removed as primary truth
- at most transient cache if still technically necessary

### Automation memory and markdown exports
- `.project/data/paa/automation-memory/*.md`
- markdown report companions under `.project/data/paa/reports/`

Correct role after this plan:
- human narrative only
- never recovery-critical truth

### Installed package artifact metadata as sole truth
- `.project/data/paa/authority/current/package-metadata.json`
- `.project/data/paa/authority/current/overlays/**/overlay-metadata.json`
- `.project/data/paa/authority/current/overlays/**/manifest-task.json`
- `.codex/paa/install-metadata.json`

Correct role after this plan:
- installed local artifact view only
- DB registration records hold canonical install and overlay truth

## Execution Sequence

## Phase 1: Lock The Existing Foundation

Goal:
- explicitly declare which existing tables remain foundational and which do not

Deliverables:
- stable table classification matrix
- derivative table classification matrix
- runtime-event table classification matrix
- projection-only surface list

Completed artifacts:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-stable-table-classification-and-ownership-map.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-db-model-diagram-and-gap-analysis.md`

Exit criteria:
- no ambiguity remains about whether a given surface is foundational, derivative, event, or projection-only

## Phase 2: Complete The Workflow-State Layer

Goal:
- introduce a canonical DB-primary workflow-state model

Deliverables:
- schema contract for `workflow_states`
- schema contract for `workflow_transitions`
- schema contract for `queue_claims`
- mapping from current runtime lifecycle to those entities

Completed entity-design artifacts:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-workflow-state-machine-data-contract.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-final-workflow-state-entity-design.md`

Implemented migration baseline:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/migrations/postgres/006-step6-workflow-install-runtime-normalization.sql`

Exit criteria:
- current owner, current stage, transition history, and claim state can be answered from DB without depending on repo-local files

## Phase 3: Complete Execution-Package Registration DB Entity Design

Goal:
- make installed execution-package truth queryable in DB

Deliverables:
- schema contract for `execution_package_installs`
- schema contract for `execution_package_overlays`
- provenance and activation rules

Completed entity-design artifact:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-final-execution-package-registration-entity-design.md`

Implemented migration baseline:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/migrations/postgres/006-step6-workflow-install-runtime-normalization.sql`

Exit criteria:
- active installed package and active overlays can be determined from DB without relying only on local metadata files

## Phase 4: Normalize Structured Runtime Inputs And Run History

Goal:
- stop losing operationally meaningful transition and run facts into file-only artifacts

Deliverables:
- schema contract for `transition_inputs`
- schema contract for `automation_run_events`
- event-classification rules for which run facts remain raw logs versus DB facts

Completed entity-design artifact:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-final-runtime-input-and-run-event-entity-design.md`

Implemented migration baseline:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/migrations/postgres/006-step6-workflow-install-runtime-normalization.sql`

Exit criteria:
- major transition inputs and major automation milestones are DB-queryable

## Phase 5: Regularize Stable Component Design Foundations

Goal:
- bring stable component records back into alignment with active package/brief usage

Deliverables:
- V2 stable component population plan
- alignment rules between `paa.components` and `paa.design_packages` / `paa.coder_run_briefs`
- decision on which glossary-level Component Design elements need first-class stable records now versus later

Completed normalization-rule artifact:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-component-design-normalization-rules.md`

Implemented schema baseline:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/migrations/postgres/006-step6-workflow-install-runtime-normalization.sql`

Exit criteria:
- new slice artifacts cannot silently outrun the stable component catalog in the same way as the current Team Worker drift

## Phase 6: Finalize Projection Boundary

Goal:
- define exactly what is projection-only and how it is generated

Deliverables:
- status projection policy
- lineage projection policy
- accepted-chain projection policy
- file-export policy

Completed policy artifact:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-final-projection-boundary-policy.md`

Implemented schema baseline:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/migrations/postgres/006-step6-workflow-install-runtime-normalization.sql`

Exit criteria:
- report files, markdown exports, and status summaries are explicitly downstream of DB truth

## Specific Design Questions To Resolve During This Plan

1. should `queue_claims` be a dedicated table or a normalized extension of `queue_messages` and `handoffs`
2. should `workflow_states` be one row per active work item only, or also preserve terminal snapshots
3. should projection surfaces remain views, become materialized views, or become explicit projection tables
4. how strict should `primary_component_id` resolution become for `design_packages` and `coder_run_briefs`
5. which glossary-level Component Design elements require new stable tables now versus later
6. where should `transition_inputs` stop and `evidence` begin
7. how much of automation run event history belongs in DB versus raw file logs

## Explicit Non-Goals

This plan does not yet do these things:
- implement the Data Access Layer
- implement repository classes or query services
- redesign RabbitMQ transport
- redesign GitHub integration
- redesign installed package file layouts
- replace source-controlled schema files with DB records

Those can proceed after the DB model is complete.

## Acceptance Criteria For Plan Completion

This plan is complete when all of the following are true:

1. every currently important data surface is classified as `keep`, `extend`, `add`, or `demote`
2. the workflow-state layer has a final target schema decision
3. the execution-package registration DB entity layer has a final target schema decision
4. the runtime-event layer is separated cleanly from workflow state
5. the stable component foundation is separated cleanly from derivative slice artifacts
6. file-primary operational truth is eliminated from the target model
7. the Data Access Layer can be designed against the completed target model without assuming transitional file truth

## Plan Status Decision

The DB model is now complete enough for Data Access Layer design.

That means:
- entity-design baselines are complete for the missing DB-primary families
- normalization rules are complete for stable versus derivative component truth
- the projection boundary is complete

What is not complete yet:
- applying the new migration to live databases
- runtime adoption of the new DB-primary entities
- projection-demotion implementation in runtime code
- Data Access Layer implementation

## Recommended Next Moves After This Plan

After this plan baseline is accepted, execute in this order:
1. apply and validate the new migration against the target database
2. resume detailed Data Access Layer design against the completed model
3. implement repository/Data Access Components against the migrated model
4. implement runtime migration away from file-primary operational truth
5. then remove obsolete file-primary recovery paths

## Hard Conclusion

The current DB model is already rich enough that this completion effort should be additive and normalizing, not a reinvention.

The main job is to stop allowing operational truth to live outside the DB and to stop allowing stable component structure, derivative slice artifacts, runtime events, and projections to blur together.

That is the completion standard for the PAA DB model.

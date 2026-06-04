# Workflow State Machine Foundation Mapping

Date: 2026-05-13

## Purpose

Define the pre-Component-Design foundation mapping for the V2 `Workflow State Machine`.

This note is written from the stance of an **Authority Architect** preparing an authority-quality design baseline for PAA itself.

It answers six questions for the `Workflow State Machine`:
1. stable records
2. derivative records
3. runtime records
4. missing records
5. derivation inputs
6. derivation outputs

It also records the current **authority authoring schemas and tools** available to us for doing this work properly.

## Related Notes

Read alongside:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/terminology/paa-engineering-terminology-glossary.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-system-component-diagram-v2.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-v2-component-relationships.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-existing-component-design-model-audit.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-component-design-foundation-and-derivation-baseline.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-db-primary-data-consolidation-audit.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-03-coder-brief-derivation-method.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-03-stage1-design-package-contract.md`

## Executive Summary

The `Workflow State Machine` should not be designed as a fresh abstraction.
It should be derived from existing PAA authority and runtime records.

The current system already contains enough structured data to define the foundation of this component, but the data is split across:
- authority package and brief artifacts
- execution runtime records
- queue and handoff persistence
- acceptance and reporting records

The design correction is:
- make workflow truth explicit and DB-primary
- stop reconstructing workflow truth from queue residue and repo-local evidence files
- derive workflow transitions from valid runtime events and authority-scoped slice records

## Authority Authoring Schemas We Already Have

### Canonical schema bundles in `paa-platform`

These are the current platform-owned canonical schema bundles:

#### Authority-package schemas
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/schemas/authority-package/package-metadata.schema.json`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/schemas/authority-package/project-config.producer.schema.json`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/schemas/authority-package/project-config.consumer.schema.json`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/schemas/authority-package/project-config.producer-consumer.schema.json`

These define:
- authority package metadata
- producer repo config
- consumer repo config
- unified producer-consumer config

#### Handoff packet schemas
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/schemas/handoff-packets/architect_cycle_packet.schema.json`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/schemas/handoff-packets/techlead_assignment_packet.schema.json`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/schemas/handoff-packets/worker_result_packet.schema.json`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/schemas/handoff-packets/delivery_review_packet.schema.json`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/schemas/handoff-packets/qa_verification_packet.schema.json`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/schemas/handoff-packets/techlead_decision_packet.schema.json`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/schemas/handoff-packets/slice_result_packet.schema.json`

These define the transport payloads that the `Workflow State Machine` must interpret, but should no longer treat as the sole owner of workflow truth.

#### Runtime record schemas
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/schemas/runtime-records/techlead-status-report.schema.json`

This defines an operator-facing projection, not primary workflow truth.

### Source authority artifact schemas still outside `paa-platform`

These still exist in the producer authority repo and remain part of the effective authority-authoring toolchain:
- `/Users/billyweisberg/Repos/Individual-Centricity/appdev/docs/architecture/tom-baby7-fractal-core/project-authority/project-authority.schema.json`
- `/Users/billyweisberg/Repos/Individual-Centricity/appdev/docs/architecture/tom-baby7-fractal-core/artifact-schemas/stage1_design_package.schema.json`
- `/Users/billyweisberg/Repos/Individual-Centricity/appdev/docs/architecture/tom-baby7-fractal-core/artifact-schemas/dependency_graph_slice.schema.json`

Important note:
- this means authority authoring is real, but still not fully consolidated into a single platform-owned schema family
- we should treat this as an active design constraint, not ignore it

## Authority Authoring Tools We Already Have

### Producer-side CLI surfaces

Current producer-side authority authoring tools include:

- `paa-producer publish-authority-package`
- `paa-producer load-issue-into-paa`
- `paa-producer materialize-readiness`
- `paa-producer materialize-verification-obligations`
- `paa-producer derive-artifacts`
- `paa-producer authority ...`

Within `paa-producer authority`, current useful subcommands include:
- `summary`
- `current`
- `task`
- `next`
- `verify-issue`
- `authoring-check`
- `materialize-task`
- `materialize-next`
- `sync-issue`
- `create-issue`
- `advance-after-merge`
- `record-acceptance`
- `record-decision`
- `materialize-coder-brief`
- `materialize-architect-packet`

Relevant code surfaces:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_producer/__main__.py`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_producer/authority_runtime.py`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_producer/publish.py`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_producer/issue_loader.py`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/readiness.py`

### Consumer-side install tool

Current install/update entry point:
- `paa-consumer install-authority-package`

Relevant code surface:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-consumer/src/paa_consumer/authority_install.py`

### Runtime install tooling

Current runtime install toolchain:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/install.py`

This installs:
- repo-local runtime payload under `.codex/paa/`
- schema bundles under `.codex/paa/schemas/`
- selected project-pack skills and automations

## Authority-Architect Interpretation

If we behave like an Authority Architect for PAA itself, the existing tooling already implies a disciplined process:

1. define source authority records and schemas
2. derive Stage 1 design-package artifacts
3. derive coder-brief artifacts and readiness state
4. publish a versioned authority package
5. install that package into an execution repo
6. allow runtime components to execute only against the installed package and DB-backed execution records

That is the mindset this note uses.

## Workflow State Machine Foundation Mapping

## 1. Stable Records

These are the records the future `Workflow State Machine` should rely on as stable foundational context.

### Work identity and project context
- `paa.projects`
- `paa.work_items`
- `paa.roles`
- `paa.agents`

These define:
- project identity
- slice identity
- role identity
- runtime actor identity

### Stable design context
- `paa.design_packages`
- `paa.coder_run_briefs`

These are not workflow-state tables, but they define the bounded execution context the workflow operates on.

The `Workflow State Machine` should treat them as stable upstream context for:
- what slice is being executed
- what brief/package pair is active
- what authority version the execution belongs to

## 2. Derivative Records

These are derivative records that shape or constrain workflow state without being the workflow state table itself.

### Sequencing / readiness projections
- `paa.component_dependency_edges`
- `paa.coder_brief_sequence_states`

These define whether a slice is:
- derivation-ready
- execution-ready
- blocked
- parallel-safe

They should be treated as workflow preconditions and workflow annotations, not as the workflow state store itself.

### Authority package install context
- installed authority package under:
  - `.project/data/paa/authority/current/`
- package metadata from:
  - `package-metadata.json`

This defines what the consumer runtime is allowed to execute against.

The `Workflow State Machine` should not own this data, but it must consume it as execution-time authority context.

## 3. Runtime Records

These are the existing records most closely tied to workflow execution today.

### Current runtime persistence surfaces
- `paa.handoffs`
- `paa.queue_messages`
- `paa.automation_runs`
- `paa.acceptance_events`

These already represent parts of runtime execution truth:
- packets sent
- queue-message status
- automation execution history
- acceptance decisions

### Current projections and evidence
These should be treated as downstream evidence or projections, not primary state:
- `techlead-status-report.json`
- compiled packet report JSON
- queue claim JSON
- automation memory markdown
- repo-local logs

The `Workflow State Machine` should replace these as primary state sources.

## 4. Missing Records

These are the missing DB-primary records the component still needs.

### Explicit workflow-state record

We do not yet have a clean DB-primary record that says, for one active slice:
- current owner role
- current workflow stage
- active source packet if any
- active transition status
- terminal state if closed
- workflow consistency state

This should become the core state owned by the `Workflow State Machine`.

### Explicit workflow-transition record

We also lack a clean transition log that says:
- what transition was attempted
- from which state
- to which state
- by which runtime entry point
- against which work item / package / brief
- whether it succeeded, failed, or was compensated

`paa.handoffs` and `paa.queue_messages` partly cover transport transitions, but not the full workflow-state transition model.

### Explicit queue-lease / queue-claim DB record

Today queue claim state is still file-primary.
That is incompatible with a DB-primary workflow model.

A DB-backed lease/claim record is needed if queue claim affects workflow truth.

## 5. Derivation Inputs

From an Authority Architect perspective, the `Workflow State Machine` should be derived from the following upstream structured inputs.

### Authority-defined slice context
- authority manifest task identity
- Stage 1 design package identity
- coder brief identity
- issue/PR identity when materialized

### Sequencing and readiness context
- readiness state from `paa.coder_brief_sequence_states`
- blocking causes and parallel group data
- dependency graph implications from `paa.component_dependency_edges`

### Runtime event context
- queue messages sent, claimed, acknowledged
- automation run outcomes
- QA verification results
- acceptance decisions
- merge and issue-close outcomes

These are the raw ingredients from which workflow truth should be computed and persisted.

## 6. Derivation Outputs

The `Workflow State Machine` should produce these outputs.

### Primary outputs
- authoritative current workflow stage
- authoritative current owner role
- authoritative active/blocked/closed lineage state
- authoritative terminal decision state

### Secondary outputs
- transition history
- operator-facing summary state
- readiness-to-assign decisions
- consistency/error flags when runtime events are contradictory

### Projection outputs
These should be downstream projections from the workflow state, not hand-built summaries:
- TechLead top-level status
- lineage summary
- accepted-chain reporting
- automation-facing preflight status

## Workflow-State Interpretation Rules

As an Authority Architect, the interpretation rules should be strict.

### Rule 1
Queue messages are transport events, not workflow truth.

### Rule 2
Design packages and coder briefs are authority-scoped execution inputs, not workflow-state records.

### Rule 3
Readiness records constrain workflow transitions, but do not replace workflow-state ownership.

### Rule 4
Repo-local files may persist evidence, but they must not remain primary sources for workflow owner or workflow stage.

### Rule 5
The installed authority package defines what work is executable.
The DB-backed workflow model defines what work is currently active.

## Current Authoring Gaps Relevant To This Component

The current authority authoring toolkit is usable, but incomplete for this component.

### Gap 1: no canonical workflow-state schema bundle yet
We have:
- authority-package schemas
- handoff-packet schemas
- one runtime-record schema

We do not yet have a canonical schema for:
- workflow-state record
- workflow-transition record
- queue-lease record

### Gap 2: Stage 1 package schema still lives partly outside platform ownership
The source schemas for:
- `stage1_design_package`
- `dependency_graph_slice`
- producer `project-authority`

still live in `appdev`.
That is workable, but not the fully consolidated end state.

### Gap 3: authority authoring tools do not yet materialize workflow-state artifacts directly
Current tools materialize:
- authority packages
- design packages
- coder briefs
- readiness
- verification obligations

They do not yet materialize the explicit DB-primary workflow-state model we now want.

## Hard Design Conclusions

1. The `Workflow State Machine` already has enough upstream structured inputs to be designed rigorously.
2. It should be derived from existing authority, package, brief, readiness, and runtime event records.
3. It should not be derived from repo-local reports, queue residue, or prompt memory.
4. The current schema/tooling set is sufficient to ground the design, but not yet sufficient to fully author and materialize the component.
5. The next design move should add explicit workflow-state authoring schemas and DB records, not another layer of file-primary reports.

## Recommended Immediate Next Step

Before full detailed Component Design, create one more short authority-style note:
- `Workflow State Machine Data Contract`

That note should define:
1. proposed canonical workflow-state schema
2. proposed workflow-transition schema
3. DB table mapping
4. transition ownership rules
5. projection boundaries to status/reporting surfaces

That is the right next move because the foundation mapping is now explicit and the authoring toolkit is now inventoried.

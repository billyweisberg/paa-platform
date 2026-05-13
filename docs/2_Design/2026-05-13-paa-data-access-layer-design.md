# PAA Data Access Layer Design

Date: 2026-05-13

## Purpose

Define the `Data Access Layer` for the PAA System Design.

This layer introduces a set of **Data Access Components** that provide structured access to the PAA data model and execution-package surfaces.

The purpose of this layer is to stop runtime and design components from:
- querying raw tables ad hoc
- reading installed authority artifacts directly in many places
- reconstructing state from report files
- mixing transport/history access with workflow-state access

This note adds the Data Access Layer to the PAA System Design as a first-class component group.

## Related Notes

Read alongside:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-system-component-diagram-v2.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-v2-component-relationships.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-schema-and-data-surface-audit.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-existing-component-design-model-audit.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-workflow-state-machine-foundation-mapping.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-workflow-state-machine-data-contract.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-db-primary-data-consolidation-audit.md`

## Why A Data Access Layer Is Needed

The current system already has rich data, but access to that data is still too spread out.

Today, logic reaches into a mixture of:
- Postgres tables
- Postgres views
- installed authority package files
- packet payload JSON
- repo-local report artifacts
- queue claim files
- GitHub runtime state

That access pattern is part of the current hybrid problem.

A Data Access Layer is needed so that:
- stateful components read and write data through explicit contracts
- stable component-design data is accessed differently from runtime-event history
- projections stop becoming accidental sources of truth
- data ownership becomes visible in the System Design

## Design Principle

The Data Access Layer does **not** own business semantics.

It owns:
- structured access to durable records
- structured access to installed execution-package records
- query boundaries
- write boundaries
- repository-level invariants

Business semantics remain owned by higher-level components such as:
- `Workflow State Machine`
- `Runtime Lifecycle Engine`
- `Reporting And Traceability Projection`

## Data Access Components

## 1. `Workflow State Repository`

### Role

Provide structured read/write access to authoritative workflow state and workflow transition history.

### Owns access to
- `paa.workflow_states` (future)
- `paa.workflow_transitions` (future)
- `paa.queue_claims` (future, if claims remain DB-primary)

### Primary consumers
- `Workflow State Machine`
- `Runtime Lifecycle Engine`
- `Reporting And Traceability Projection`

### Non-goals
- does not compute workflow semantics
- does not decide legal transitions
- does not interpret queue transport directly outside repository contract

## 2. `Execution Package Repository`

### Role

Provide structured access to installed execution-package content and install metadata.

### Owns access to
- installed authority manifest
- installed design package artifacts
- installed coder brief artifacts
- install metadata
- overlay activation metadata

### Primary consumers
- `Runtime Lifecycle Engine`
- `Workflow State Machine` when package/brief identity must be resolved
- `Reporting And Traceability Projection`

### Non-goals
- does not publish authority packages
- does not derive packages from source authority
- does not own package semantics

## 3. `Component Design Repository`

### Role

Provide structured access to stable component-design records and slice-derivation design records.

### Owns access to
- `paa.components`
- `paa.component_surfaces`
- `paa.component_relationships`
- `paa.design_packages`
- `paa.design_package_signoffs`
- `paa.coder_run_briefs`
- `paa.component_dependency_edges`
- `paa.coder_brief_sequence_states`

### Primary consumers
- Authority publication and derivation flows
- `Runtime Lifecycle Engine`
- future Component Design tools
- future Component Design reporting tools

### Non-goals
- does not author source authority itself
- does not own runtime event history
- does not own current workflow state

## 4. `Runtime Event Repository`

### Role

Provide structured access to transport, execution, acceptance, and execution-record history.

### Owns access to
- `paa.handoffs`
- `paa.queue_messages`
- `paa.automation_runs`
- `paa.acceptance_events`
- `paa.execution_records`
- `paa.evidence`
- `paa.verification_obligations`

### Primary consumers
- `Runtime Lifecycle Engine`
- `Workflow State Machine`
- `Reporting And Traceability Projection`

### Non-goals
- does not define current workflow truth
- does not define component design structure

## 5. `Projection Repository`

### Role

Provide structured access to read models, reporting views, and projection records.

### Owns access to
- reporting views such as `paa.v_work_item_full_chain_traceability`
- future materialized reporting tables
- operator-summary read models
- status and lineage projection records

### Primary consumers
- `Reporting And Traceability Projection`
- operator/admin tooling
- future analytics tools

### Non-goals
- does not define primary state
- does not replace workflow-state or event repositories

## Repository Boundaries

### Stable design data boundary

Stable design data belongs behind:
- `Component Design Repository`

That includes:
- component identity
- component surfaces
- stable relationships
- design packages
- coder briefs
- dependency edges
- readiness state

### Runtime-state boundary

Current workflow truth belongs behind:
- `Workflow State Repository`

That includes:
- current owner
- current workflow stage
- transition history
- current blocking/terminal state

### Runtime-event boundary

Execution and transport history belongs behind:
- `Runtime Event Repository`

That includes:
- handoffs
- queue messages
- automation runs
- acceptance events
- evidence
- execution records

### Execution-package boundary

Installed execution-time authority belongs behind:
- `Execution Package Repository`

That includes:
- installed manifest
- installed package artifacts
- installed brief artifacts
- package metadata
- overlays

### Projection boundary

Read-only operator/reporting surfaces belong behind:
- `Projection Repository`

That includes:
- lineage views
- accepted-chain views
- status views
- future analytics read models

## Why This Matters For Component Design

This layer is especially important because we already know:
- PAA has a partial DB-backed Component Design model
- newer slice artifacts outran the stable component catalog
- workflow truth has been reconstructed from the wrong surfaces

Without a Data Access Layer, the next Component Design phase would still risk:
- raw-table coupling
- file-surface coupling
- duplicate derivation logic
- reporting surfaces acting as state

## Immediate Design Impact On PAA Components

### `Workflow State Machine`
Should depend on:
- `Workflow State Repository`
- `Runtime Event Repository`
- `Execution Package Repository`

Should not query:
- raw `paa.queue_messages`
- raw installed package files
- local report JSON

directly.

### `Runtime Lifecycle Engine`
Should depend on:
- `Workflow State Repository`
- `Execution Package Repository`
- `Component Design Repository`
- `Runtime Event Repository`

Should not query raw tables ad hoc across those domains.

### `Reporting And Traceability Projection`
Should depend on:
- `Workflow State Repository`
- `Runtime Event Repository`
- `Projection Repository`
- `Execution Package Repository` when execution-time package context is needed

Should not synthesize state directly from queue plus file residue.

## Future Tooling Implication

Once these Data Access Components exist, they become the natural foundation for:
- Component Design authoring tools
- Component Design query tools
- authority publication/reporting tools
- operator reporting tools
- DB-backed audits and dashboards

That is why this layer belongs in System Design, not just implementation planning.

## Hard Conclusions

1. PAA needs a first-class Data Access Layer.
2. The Data Access Layer should be composed of multiple repositories, not one generic DB helper.
3. Stable component-design data, workflow-state data, runtime-event data, execution-package data, and projection data must be accessed through different components.
4. This layer is required if we want the PAA data model to become usable as a designed system instead of a collection of reachable tables and files.

## Recommended Next Step

Use this layer as the basis for the next question:
- what tools already exist, or should exist, for designing and accessing Component designs in the DB and generating reports from those records

That question now has a clean architectural home:
- primarily `Component Design Repository`
- supported by `Projection Repository`

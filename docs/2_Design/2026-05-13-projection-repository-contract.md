# Projection Repository Contract

Date: 2026-05-13

## Purpose

Define the concrete Data Access Layer contract for:
- `Projection Repository`

This repository is the structured access boundary for DB-backed and file-exported derived read models.

Its purpose is to give higher-level components a stable way to:
- read operator-friendly derived status and lineage views
- materialize and access reporting projections
- expose summarized read models without confusing them for primary truth

while enforcing the projection boundary that was missing in the old hybrid model.

## Related Notes

Read alongside:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-data-access-layer-design.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-final-projection-boundary-policy.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-workflow-state-repository-contract.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-runtime-event-repository-contract.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-component-design-repository-contract.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-execution-package-repository-contract.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-db-model-diagram-and-gap-analysis.md`

## Role

Provide structured access to:
1. DB-backed projection views and read models
2. projection-oriented summary records derived from primary truth
3. optional generated report-export inputs and outputs
4. projection regeneration workflows and health checks

## Repository Boundary

The repository owns structured access to projection-only surfaces such as:
- `paa.coder_brief_sequence_states`
- `paa.v_work_item_full_chain_traceability`
- future materialized projection tables such as:
  - `paa.workflow_status_projections`
  - `paa.lineage_projections`
  - `paa.accepted_chain_projections`

It may also own structured generation and access of file-backed projection exports such as:
- `.project/data/paa/reports/*.json`
- `.project/data/paa/reports/*.md`

But only as derived/export surfaces.

It does **not** own primary access to:
- workflow truth tables
- runtime event history tables
- stable component-design tables
- execution-package registration tables
- source-authority tables

Those remain outside this repository boundary and are inputs only.

## Non-Goals

The repository does not:
- mutate workflow truth
- mutate runtime history truth
- mutate stable component-design truth
- mutate execution-package registration truth
- invent state from file exports
- replace the primary repositories that own truth surfaces

## Primary Consumers

The main consumers are:
- `Reporting And Traceability Projection`
- operator and admin tooling
- future analytics tooling
- export-generation tooling

## Canonical Read Models

The repository provides structured access to six logical read models.

### 1. Workflow Status Projection View

Represents current operator-facing status summaries.

Includes:
- current owner summary
- current stage summary
- blocking summary
- queue/assignment summary where that summary is derived

Backed by:
- future `paa.workflow_status_projections`
- or equivalent DB-backed status view materialization

### 2. Lineage And Full-Chain Traceability View

Represents end-to-end lineage and traceability summaries for one work item or accepted chain.

Includes:
- lineage stage summary
- chain-state summary
- acceptance summary
- package/brief/component summary

Backed by:
- `paa.v_work_item_full_chain_traceability`
- future lineage-specific projection tables or materialized views

### 3. Readiness And Sequencing Projection View

Represents derivative readiness and sequence summaries.

Includes:
- readiness state
- blocking cause
- parallel-group summary
- execution-readiness summary

Backed by:
- `paa.coder_brief_sequence_states`

### 4. Accepted-Chain Projection View

Represents accepted or closed-chain rollups for reporting.

Includes:
- latest accepted work item per component or project
- acceptance decision summaries
- closeout timing summaries

Backed by:
- future `paa.accepted_chain_projections`
- or derived read views from workflow, runtime, and acceptance truth

### 5. Projection Health View

Represents projection freshness and rebuild state.

Includes:
- projection generated-at timestamps
- source-input version references
- stale or rebuild-required indicators

Backed by:
- future projection metadata tables or materialized-view metadata conventions

### 6. File Export View

Represents exported report surfaces generated from projection inputs.

Includes:
- export path
- export type
- export generation timestamp
- source projection identity

Backed by:
- projection generation metadata
- repo-local exported projection files when present

## Required Repository Capabilities

## A. Projection Read Access

### Read capabilities
- get full-chain traceability projection for a `work_item_id`
- list active workflow-status summaries for a project
- list readiness summaries for a package or brief
- list accepted-chain summaries for a project or component
- list projection rows by freshness or stale status when supported

### Invariants
- projection reads must never be the only path to primary truth
- if a projection is missing, the system must still be able to recover from primary repositories

## B. Projection Regeneration Support

### Read capabilities
- resolve which primary-truth inputs feed a given projection
- determine whether a projection is stale relative to its source truth

### Write capabilities
- refresh or rebuild projection rows or materialized views
- persist projection generation metadata when explicit projection tables exist
- mark projection rows stale or regenerated when metadata support exists

### Invariants
- projection rebuild must be deterministic from primary truth inputs
- projection regeneration may not invent independent business semantics

## C. File Export Access

### Read capabilities
- resolve exported JSON or markdown report locations for a given projection
- read exported report content when a consumer explicitly needs the export form rather than the projection row

### Write capabilities
- generate JSON report export from a projection
- generate markdown companion export from a projection
- update export generation metadata or pointers

### Invariants
- exported report files are disposable and reproducible
- file exports may never become the only surviving copy of a summary that should be reproducible from DB-backed projections and primary truth

## D. Projection Health And Integrity Access

### Read capabilities
- list missing projections expected for active work items
- list stale projections older than their source truth
- list exports whose projection source no longer exists or is out of date

### Write capabilities
- record projection repair or regeneration metadata when explicit metadata support exists

### Invariants
- projection health is about freshness and reproducibility, not primary truth ownership
- projection repair may never mutate the upstream truth repositories to “fix” the projection

## Contract Shape

The repository should expose bounded access groups rather than one flat method set.

Recommended contract groups:
- `workflow_status`
- `lineage`
- `readiness`
- `accepted_chains`
- `health`
- `exports`
- `regeneration`

This can still be implemented as one concrete repository component internally.

The important design rule is that consumers see explicit projection-only access boundaries.

## Transaction Boundaries

The repository should support atomic write groups for these cases.

### Case 1: projection row rebuild
- rebuild one projection row or materialized read-model record
- persist regeneration metadata for that projection when supported

### Case 2: report export generation
- generate exported JSON or markdown file
- update export metadata or pointers in the same unit when supported

### Case 3: stale projection repair
- mark projection stale or regenerated
- rebuild dependent export metadata when part of the same repair unit

## Prohibited Access Patterns

Consumers of this repository must not:
- write workflow-state rows through the projection repository
- write runtime-event rows through the projection repository
- infer primary state from exported JSON or markdown when primary repositories are available
- treat `paa.coder_brief_sequence_states` as stable component truth
- mutate primary repositories to “fix” a projection discrepancy without going through the owning truth repository

## Reporting Implication

This repository is itself the data source for reporting and export tooling.

It should support:
- operator dashboards
- traceability and lineage exports
- accepted-chain reporting
- readiness and sequencing reporting
- projection-health reporting

while remaining explicitly downstream from primary truth.

## Final Conclusion

The `Projection Repository` is the fifth concrete DAL contract because it completes the separation between:
- truth repositories
- and summary/export repositories

It gives PAA a structured access layer for:
- DB-backed derived read models
- file-exported summaries
- projection health and regeneration

That is the correct boundary for keeping reports useful without letting them quietly become the system of record again.

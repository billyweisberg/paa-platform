# Component Design Normalization Rules

Date: 2026-05-13

## Purpose

Define the normalization rules that bring the stable Component Design model back into alignment with the active derivative slice-artifact model.

This note exists because the DB already has a real component-design-related substrate, but newer slices have outrun the stable component catalog.

The goal here is not to invent a new component model from scratch.
The goal is to regularize the existing one so that:
- stable reusable Component Designs live in stable records
- slice-specific design artifacts live in derivative records
- sequencing and readiness live in projection records
- the runtime stops treating these layers as interchangeable

## Related Notes

Read alongside:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-existing-component-design-model-audit.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-component-design-foundation-and-derivation-baseline.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-stable-table-classification-and-ownership-map.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-13-paa-db-model-diagram-and-gap-analysis.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/terminology/paa-engineering-terminology-glossary.md`

## Normalization Goal

The normalized Component Design model must preserve this separation:

1. stable reusable Component Design
- owned in stable component records

2. slice-specific reviewed design package
- owned in derivative package records

3. slice-specific execution brief
- owned in derivative coder-brief records

4. slice-specific dependency sequencing and readiness
- owned in derivative dependency edges and projection records

If one layer starts impersonating another, the model drifts.
That is what happened.

## Final Normalization Rules

## Rule 1: Reusable components must exist in stable component records

If a named thing is a reusable PAA system component, it must exist in the stable component layer:
- `paa.components`
- and any future stable component extension tables

It must not exist only as:
- `design_packages.primary_component_name`
- `coder_run_briefs.component_assignment_json`
- embedded `component_model_slice` JSON

Practical consequence:
- newer V2 components such as `Workflow State Machine`, `Installed Execution Package Manager`, `Runtime Lifecycle Engine`, and future DAL components must be first-class stable components before derivative slices may claim them as primary components

## Rule 2: Derivative artifacts may reference stable components, but may not replace them

`paa.design_packages` and `paa.coder_run_briefs` may:
- reference stable components
- scope a slice to one or more stable components
- add slice-specific shaping, constraints, and execution detail

They may not become the only place where a reusable component exists.

Practical consequence:
- a package or brief may enrich a component assignment
- but it may not be used as a substitute for a missing `paa.components` row

## Rule 3: `primary_component_id` resolution must become strict for reusable-component slices

The current model has allowed package and brief rows to load even when `primary_component_id` cannot be resolved.
That is how newer slices outran the stable component catalog.

New rule:
- if a slice claims a reusable stable component as its primary component, `primary_component_id` resolution must succeed
- otherwise the slice must be explicitly marked as one of:
  - `component_not_yet_normalized`
  - `multi_component_slice`
  - `artifact_only_transitional`

Practical consequence:
- silent null `primary_component_id` drift should stop
- transitional exceptions may still exist, but only explicitly and visibly

## Rule 4: package-scoped dependency edges remain derivative unless explicitly promoted

`paa.component_dependency_edges` currently carries package-scoped sequencing semantics.
That is useful, but it is not yet the same thing as a stable reusable component dependency graph.

New rule:
- package-scoped edges remain derivative by default
- only explicitly reviewed and promoted dependency relationships may move into the stable structural component model

Practical consequence:
- we do not accidentally treat slice-specific sequencing as permanent architecture
- but we preserve a path for repeated derivative relationships to become stable architectural relationships later

## Rule 5: readiness and sequencing state is projection, not design authority

`paa.coder_brief_sequence_states` is useful and should remain.
But it must remain a projection layer derived from:
- stable components
- derivative packages
- derivative coder briefs
- derivative dependency edges

It is not a stable design-authority surface.

Practical consequence:
- readiness records may never be the only place where component structure or dependency meaning exists

## Rule 6: the 15 Component Design elements attach to the stable component layer first

Per the glossary, reusable component design includes 15 elements.
Those elements should be normalized against the stable component layer first, not the derivative slice layer.

At minimum, these missing areas should be treated as stable-component concerns:
- Component State Model
- Service Contract
- Data Contract
- Injected Services
- Interfaces
- Messages Received
- Messages Published
- Message Data Contracts
- Event Subscriptions
- Events Published
- Event Data Contracts
- Component Lifecycle
- Component Configuration

Practical consequence:
- if we later add stable extension tables such as service contracts, state models, or event contracts, they belong under stable component identity, not under per-slice package rows

## Rule 7: derivative slices may specialize stable components, but must declare the specialization boundary

A derivative slice may:
- narrow scope
- add implementation constraints
- bind verification obligations
- define execution sequencing

But it must do so as a specialization of stable component identity, not as an implicit rewrite of component identity.

Practical consequence:
- the component boundary remains stable
- the slice boundary remains slice-specific

## Rule 8: stable component population is now a gating concern, not a deferred cleanup

The old model allowed newer work to proceed while the stable component catalog lagged behind.
That is no longer acceptable for V2.

New rule:
- if a new reusable component enters the active PAA system design, stable component population is part of the design-authority workflow, not optional future cleanup

Practical consequence:
- stable component catalog upkeep becomes a first-class design responsibility

## Required Transitional Statuses

To avoid pretending everything is normalized before it is, the model needs explicit transitional statuses.

At minimum, derivative package/brief loading should support a visible normalization status such as:
- `normalized`
- `component_not_yet_normalized`
- `artifact_only_transitional`
- `multi_component_slice`
- `repair_required`

This can be represented by:
- new columns on `paa.design_packages` and `paa.coder_run_briefs`
- or a small adjunct normalization-status table

The exact storage choice can be decided later.
The requirement itself is now locked.

## Required Alignment Checks

The normalized model should enforce these checks.

### Check 1: primary-component alignment
If a package or brief declares one primary reusable component, that component must resolve to `paa.components`.

### Check 2: surface alignment
If a package claims specific owned surfaces for a reusable component, those surfaces must align with the stable component surface model or be explicitly marked as provisional slice-only surfaces.

### Check 3: dependency-edge classification
Each dependency edge must be classifiable as one of:
- stable structural relationship
- derivative slice dependency
- provisional relationship awaiting architectural review

### Check 4: readiness derivation provenance
Every readiness/projection record must be traceable back to:
- stable component identity
- derivative package
- derivative brief
- derivative dependency edge set

## What Must Change In Practice

From this point forward, these behaviors are no longer acceptable:
- introducing a new reusable component only in package JSON
- allowing null `primary_component_id` silently for reusable-component slices
- using derivative package content as if it were the stable component catalog
- letting readiness state carry architectural meaning that is absent upstream

These behaviors are required instead:
- populate stable reusable component records first
- then derive packages and briefs against them
- then compute dependency edges and readiness projections from that aligned base

## What This Means For Existing Tables

### `paa.components`
Must become the maintained catalog of active reusable PAA components, not just historical retirement components.

### `paa.component_surfaces`
Must become the maintained catalog of stable owned surfaces for active reusable components.

### `paa.component_relationships`
Must remain structural and stable, not overloaded with slice-specific sequencing.

### `paa.design_packages`
Must carry explicit normalization status when stable-component alignment is incomplete.

### `paa.coder_run_briefs`
Must carry explicit normalization status when stable-component alignment is incomplete.

### `paa.component_dependency_edges`
Must remain derivative by default, with an explicit promotion path if recurring relationships deserve stable status.

### `paa.coder_brief_sequence_states`
Must remain a projection layer only.

## Hard Conclusion

The component-design problem is not that the DB lacks component-related tables.
The problem is that the system allowed derivative slice artifacts to advance faster than the stable reusable component catalog.

These normalization rules stop that drift.

From here forward:
- reusable component truth belongs in stable component records
- slice-specific truth belongs in derivative artifacts
- sequencing truth belongs in derivative edges and projections
- runtime truth belongs in workflow and runtime-event entities

That is the normalization baseline for the remaining PAA data-model work.

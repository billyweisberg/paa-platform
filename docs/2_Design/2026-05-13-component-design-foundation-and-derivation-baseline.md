# Component Design Foundation And Derivation Baseline

Date: 2026-05-13

## Purpose

Define the design baseline we must use **before** starting new V2 Component Design work for PAA.

This note answers two questions:
1. what existing DB-backed tables should be treated as the starting foundation for Component Design
2. what the PAA system and its future V2 components are derived from, and how that derivation should flow

This note exists because the system already has a real derivation model.
We should build on that model, not pretend the V2 components emerge from freeform architecture prose or from empty schema space.

## Related Notes

Read alongside:
- `docs/terminology/paa-engineering-terminology-glossary.md`
- `docs/2_Design/2026-05-03-coder-brief-derivation-method.md`
- `docs/2_Design/2026-05-03-coder-brief-field-derivation-matrix.md`
- `docs/2_Design/2026-05-03-stage1-design-package-contract.md`
- `docs/2_Design/2026-05-03-stage1-schema-and-record-shape.md`
- `docs/2_Design/2026-05-03-component-dependency-graph-contract.md`
- `docs/2_Design/2026-05-13-existing-component-design-model-audit.md`
- `docs/2_Design/2026-05-13-paa-system-component-diagram-v2.md`
- `docs/2_Design/2026-05-13-paa-v2-component-relationships.md`

## Executive Summary

The next round of PAA V2 Component Design should start from this rule set:

1. stable component definitions should be modeled as stable component records
2. per-slice derivative artifacts should be modeled as design-package and coder-brief records
3. sequencing and readiness should be modeled as derived projection state
4. V2 components must be derivable from structured Stage 1 authority inputs, not from narrative interpretation at execution time

That means the foundation is already partly present:
- `paa.components`
- `paa.component_surfaces`
- `paa.component_relationships`
- `paa.design_packages`
- `paa.coder_run_briefs`
- `paa.component_dependency_edges`
- `paa.coder_brief_sequence_states`

The problem is not that we lack a model.
The problem is that the existing model is only partially regularized, and newer slices have outrun the stable component catalog.

## Existing Foundation We Should Reuse

### Stable component foundation

These tables are the right starting point for stable Component Design identity:
- `paa.components`
- `paa.component_surfaces`
- `paa.component_relationships`

These already represent:
- stable component identity
- surface ownership
- stable collaboration / dependency shape

This is the right foundation for glossary-level Component Design elements such as:
- Role
- partial Data Contract context
- partial Interfaces / collaboration context
- component-level boundary placement

### Derivative slice-design foundation

These tables are the right starting point for slice-level derivative artifacts:
- `paa.design_packages`
- `paa.design_package_signoffs`
- `paa.coder_run_briefs`

These already represent:
- Stage 1 reviewed design-package authority
- Stage 2 coder-facing derived execution briefs
- package and brief provenance
- package signoff state

This is the right foundation for:
- slice-scoped design intent
- per-slice construction packets
- per-slice authorization and signoff
- per-slice execution shaping

### Derived sequencing foundation

These tables are the right starting point for operational sequencing state:
- `paa.component_dependency_edges`
- `paa.coder_brief_sequence_states`

These already represent:
- typed dependency edges
- blocking and parallelism metadata
- computed readiness state

This is the right foundation for:
- Project Design sequencing
- derivation-readiness checks
- execution-readiness checks
- dependency-aware orchestration

## What The System And Its Components Are Derived From

Per `docs/2_Design/2026-05-03-coder-brief-derivation-method.md`, the current derivation method says a `coder_run_brief` is derived from four primary upstream sources:
- Product / Architect / Designer authority
- spec fragments
- implementation targets
- component model

That method should now be generalized as the design rule for PAA V2 too.

### V2 derivation principle

A V2 component design should not be invented ad hoc.
It should be derived from structured upstream authority in the same spirit as coder-brief derivation.

For PAA system design, that means each V2 component should be derived from:
- system-intent authority
- bounded scope statements
- execution/runtime target definition
- stable component model

Using current PAA terminology, the derivation chain is:

1. system authority and design intent
2. Stage 1 design package
3. stable component model and dependency graph
4. derived runtime-facing execution artifacts
5. runtime execution and workflow projection

## Current Structured Derivation Chain

The current design docs already imply this chain.

### Layer 1: System-intent authority

From `docs/2_Design/2026-05-03-coder-brief-derivation-method.md` and `docs/2_Design/2026-05-03-stage1-design-package-contract.md`:
- Product / Architect / Designer authority defines why the slice exists
- spec fragments define the bounded change
- implementation targets define desired state and expected touch surfaces
- component model defines structure and seams

This is the upstream design-authority layer.

### Layer 2: Stage 1 design package

From `docs/2_Design/2026-05-03-stage1-design-package-contract.md` and `docs/2_Design/2026-05-03-stage1-schema-and-record-shape.md`:
- authority context
- product and source basis
- requirement set
- design decision set
- spec fragment
- implementation target
- architectural authority constraints
- component model slice
- component surfaces
- dependency graph slice
- verification contract basis
- failure and recovery context
- signoff

This is the reviewed design bundle from which deterministic derivation is supposed to happen.

### Layer 3: Stable component and dependency model

From `docs/2_Design/2026-05-03-component-dependency-graph-contract.md` and the existing DB schema:
- stable components exist as nodes
- stable surfaces define where responsibility lives
- stable relationships define collaboration shape
- dependency edges add execution-governing sequencing semantics

This is the structural layer that makes derivation mechanical instead of interpretive.

### Layer 4: Derived execution artifacts

From `docs/2_Design/2026-05-03-coder-brief-field-derivation-matrix.md` and current runtime implementation:
- `paa.design_packages` persist the Stage 1 slice package
- `paa.coder_run_briefs` persist the execution-facing derived brief
- `paa.coder_brief_sequence_states` persist readiness computations

This is the execution-construction layer.

### Layer 5: Runtime lifecycle and workflow execution

From the current runtime and V2 design correction:
- packets, assignments, results, and closeout are runtime lifecycle concerns
- queue traffic is transport only
- workflow truth should ultimately live in the DB-backed workflow model

This is the execution and projection layer.

## Design Implication For V2 Components

The V2 components:
- `Workflow State Machine`
- `Installed Execution Package`
- `Runtime Lifecycle Engine`

should be derived from the existing structured layers above.

They should **not** be treated as free-floating architectural abstractions.

### `Installed Execution Package`

Should be derived from:
- published authority artifacts
- Stage 1 design-package content
- derived coder-brief content
- execution-time policy views

It is the installed runtime package view of reviewed upstream authority.

### `Runtime Lifecycle Engine`

Should be derived from:
- execution artifact shapes
- packet schemas
- sequencing/readiness state
- worktree policy
- allowed lifecycle transitions implied by design-package and brief execution

It is the runtime executor of already-derived authority, not a design-authority component.

### `Workflow State Machine`

Should be derived from:
- work-item lifecycle
- handoff and queue lifecycle
- acceptance and closeout state
- derived execution transitions

It should not derive design intent.
It should only derive and persist workflow truth from valid runtime transitions.

## Foundation Mapping For Future Component Design

Before detailed Component Design begins, we should treat the existing surfaces as follows.

### Stable component definition layer

Owns:
- component identity
- role
- surfaces
- stable relationships

Current tables:
- `paa.components`
- `paa.component_surfaces`
- `paa.component_relationships`

### Slice-derivation layer

Owns:
- Stage 1 package content
- package signoff state
- derived coder brief content
- artifact provenance

Current tables:
- `paa.design_packages`
- `paa.design_package_signoffs`
- `paa.coder_run_briefs`

### Dependency and sequencing layer

Owns:
- dependency edges
- blocking/parallelism semantics
- readiness projection

Current tables:
- `paa.component_dependency_edges`
- `paa.coder_brief_sequence_states`

### Runtime execution layer

Owns:
- packet lifecycle
- workflow transitions
- automation runs
- acceptance events
- queue-message state

Current and adjacent tables:
- `paa.handoffs`
- `paa.queue_messages`
- `paa.automation_runs`
- `paa.acceptance_events`
- plus the future DB-primary workflow-state layer identified in the consolidation audit

## The Current Break In The Derivation Chain

The audit result from `docs/2_Design/2026-05-13-existing-component-design-model-audit.md` shows the current break clearly:
- newer slices are being persisted as design packages and coder briefs
- but they are not consistently aligned to the stable component catalog and dependency graph

That means the derivation chain currently breaks between:
- Layer 2: Stage 1 design package
and
- Layer 3: stable component model

The immediate design consequence is:
- V2 Component Design must repair this break
- not bypass it with new standalone documents or runtime-only logic

## Hard Baseline Rules

### Rule 1: Stable components must be stable records

If a concept is a reusable system component, it belongs in the stable component model.
It should not exist only inside package JSON.

### Rule 2: Slice-specific construction belongs in derivative artifacts

If a concept is slice-scoped, issue-scoped, or execution-scoped, it belongs in:
- design package records
- coder brief records
- sequencing/projection records

It should not be mistaken for a stable component definition.

### Rule 3: Derivation must stay deterministic

A runtime or coder agent should not reconstruct design intent from prose or GitHub history when the structured derivation chain already exists.

### Rule 4: New V2 components must map to the chain

Every V2 component design should explicitly state:
- which upstream structured records it is derived from
- which stable tables define it
- which derivative tables instantiate it per slice
- which runtime tables record its execution consequences

## What This Means For The Next Design Step

The next Component Design work should begin with a foundation decision table for each V2 component:
- what stable DB records define the component
- what derivative records instantiate slice-specific behavior for it
- what existing records are insufficient
- what missing glossary-level Component Design elements need first-class representation

That is the right next move because it keeps V2 grounded in:
- the glossary
- the existing derivation model
- the already-modeled DB substrate
- the DB-primary direction already established in the data audit

## Recommended Next Step

Before detailed Component Design for `Workflow State Machine`, create a foundation mapping note that answers for each V2 component:
1. stable records
2. derivative records
3. runtime records
4. missing records
5. derivation inputs
6. derivation outputs

That will let the next Component Design phase start from the real system instead of from abstractions.

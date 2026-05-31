Title: PAA Methodology Execution Component Family
Doc-ID: paa-methodology-execution-component-family
Doc-Type: design-note
Status: active
Lifecycle-Stage: design
Created: 2026-05-30
Last-Edited: 2026-05-30
Author: Billy Weisberg
Repo: paa-platform
Component: PAAMethodologyExecution
Domain: methodology-execution
Keywords: paa, methodology, execution, component-family, pointer, lane, stage, step, preflight
Depends-On: 2026-05-30-paa-methodology-execution-state-model.md, 2026-05-30-paa-methodology-lane-and-command-model.md, 2026-05-28-paa-cli-system-architecture.md, 2026-05-28-paa-operator-system-implementation-plan.md
Supersedes:
Superseded-By:
Canonical: true
Review-After: 2026-06-30
Summary: Starts the governed design lane for the methodology-execution substrate by naming the first component family, ownership boundaries, and intended slice order.

# PAA Methodology Execution Component Family

## Purpose

Start the governed design lane for the methodology execution pointer as a real component family rather than an informal future idea.

This family exists to make the full PAA lifecycle explicit and machine-readable across:
- authority derivation
- component realization
- runtime execution
- acceptance and closeout

## Core Decision

The methodology pointer should not be a hidden CLI convention and should not be owned entirely by `TechLead`.

It should become a distinct governed substrate family with its own repository, state service, projection, and preflight surfaces.

## Proposed Initial Component Family

### `MethodologyExecutionRepository`
Owns:
- persistence for `MethodologyExecution`
- persistence for `MethodologyExecutionEvent`
- typed bindings to linked records

Does not own:
- implementation-plan truth
- workflow truth
- queue truth
- coder-brief truth

### `MethodologyExecutionStateService`
Owns:
- current lane/stage/step state transitions
- next valid transition derivation
- blocked and waiting state calculation

Does not own:
- CLI rendering
- worker execution policy
- acceptance policy itself

### `MethodologyExecutionProjectionService`
Owns:
- operator-facing summary projection
- `paa status` / `paa next` / `paa explain`-style projection data
- cross-record stitching for the methodology pointer

Does not own:
- mutating transitions
- primary persistence

### `MethodologyExecutionPreflightService`
Owns:
- lane-aware command validation
- preflight outcomes: `allowed`, `warn`, `blocked`, `redirect`
- mapping requested CLI actions to valid methodology transitions

Does not own:
- command execution itself
- output rendering

## Relationship To `PAAOperatorCLI`

`PAAOperatorCLI` should consume this family, not absorb it.

That means:
- the current Typer root may stay thin and command-family oriented
- the richer pointer-driven operator experience should arrive by injecting this family later
- the CLI should not invent lane truth locally once this family exists

## First Intended Slice Order

1. `MethodologyExecutionRepository`
- interface contract
- persistence shape
- minimal read/write slice

2. `MethodologyExecutionStateService`
- state model contract
- next-step derivation for one narrow lane

3. `MethodologyExecutionProjectionService`
- minimal `status` projection slice

4. `MethodologyExecutionPreflightService`
- minimal command-family preflight slice for `component` and `plan`

## Immediate Design Follow-ups

The next design artifacts for this lane should be:
- methodology execution object model
- repository contract and persistence mapping
- transition/state-machine table
- projection shape for `status`, `next`, and `explain`
- preflight rule table for the first command families

## Boundary Rule

Until this family is implemented:
- `PAAOperatorCLI` may bridge from existing planning and runtime surfaces
- but it should not pretend to have a unified persisted methodology pointer

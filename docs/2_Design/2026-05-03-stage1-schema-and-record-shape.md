# 84. Stage 1 Schema and Record Shape

## Purpose
This document defines the concrete record shape for the Stage 1 design package and the dependency graph slice it contains.

It turns the Stage 1 contract into a schema-level artifact suitable for:
- documentation
- review
- persistence in PAA
- tool-driven completeness checks
- parent input to coder-brief derivation

## Artifacts defined
The concrete Stage 1 record shape is now represented by:
- `appdev/docs/architecture/tom-baby7-fractal-core/artifact-schemas/stage1_design_package.schema.json`
- `appdev/docs/architecture/tom-baby7-fractal-core/artifact-schemas/dependency_graph_slice.schema.json`

## Design choice
The Stage 1 package is modeled as:
- one top-level package record
- containing strongly named section objects
- including an embedded dependency graph slice

This is deliberate.

Why:
- the package is reviewed as a unit
- derivation consumes a single coherent parent artifact
- provenance and signoff can attach to the package as a whole
- dependency sequencing lives inside the package, not as an afterthought

## Top-level package shape
The Stage 1 package schema contains these top-level sections:
- `authority_context`
- `product_and_source_basis`
- `requirement_set`
- `design_decision_set`
- `spec_fragment`
- `implementation_target`
- `architectural_authority_constraints`
- `component_model_slice`
- `component_surfaces`
- `dependency_graph_slice`
- `verification_contract_basis`
- `failure_and_recovery_context`
- `signoff`

This mirrors the Stage 1 contract directly.

## Dependency graph slice shape
The embedded graph slice is intentionally explicit.

It contains:
- `nodes`
- `edges`
- `blocking_dependencies`
- `parallelizable_dependencies`
- `sequencing_constraints`

### Nodes
Each node identifies:
- component id
- component name
- role
- system layer
- optional tier
- status
- surface set

### Edges
Each edge identifies:
- source component
- target component
- dependency type
- dependency strength
- sequencing requirement
- blocking scope
- dependency status
- optional complexity/duration/run-count metadata
- shared-surface conflict marker

This is where the future node diagram and execution planner get their real structure.

## Why the graph is embedded
The graph should exist independently in PAA too.
But for Stage 1 package review, embedding the local graph slice is the right move.

It keeps the package self-sufficient for:
- derivation review
- dependency review
- sequencing review
- future artifact export

## Record-shape implications for PAA
The schema implies two separate persistence concerns:

### 1. Stable normalized records
Already largely covered or planned in PAA:
- authority tasks
- requirements
- design decisions
- spec fragments
- implementation targets
- components
- component surfaces
- verification obligations

### 2. Package and dependency artifacts
Need explicit support:
- Stage 1 design package records
- dependency graph edges with sequencing metadata
- package signoff state
- package provenance

## Recommended DB direction
The next DB layer should add:
- `paa.design_packages`
- `paa.design_package_signoffs`
- `paa.component_dependency_edges`

This is better than forcing all dependency metadata into generic relationships.

## Package review consequence
Because the package now has a real shape, we can automate checks like:
- package completeness
- missing signoffs
- missing primary component
- undefined blocking dependency
- illegal parallelism assumption
- missing verification basis

That is exactly the kind of simple tool support we want.

## Immediate consequence for derivation
Once a package validates against the Stage 1 schema and has the required signoffs, Stage 2 can consume it deterministically.

That means derivation can stop reaching back into scattered design records ad hoc.
Instead it can consume:
- one approved design package record
- plus normalized supporting records as needed for provenance

## Next step
The next useful move is to formalize how coder-brief sequencing is computed from the dependency graph slice and authority order.

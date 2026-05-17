# ImplementationPlanRepository Contract

Date: 2026-05-17

## Purpose

Define `ImplementationPlanRepository` strictly using the existing PAA model.

This note does **not** introduce a new artifact family.

It uses only:
- `Component`
- `Component Elements`
- `Code Artifact Target Taxonomy`
- `ImplementationPlan`
- `CoderBrief`

The objective is to make the engineering bridge explicit:

- implementation-plan activities carry:
  - component
  - component elements
  - code artifact targets
- that structured information is then added into a `CoderBrief`
- the coder agent receives the full context needed to render working code

## Core Decision

`ImplementationPlanRepository` is modeled as a normal PAA component.

It is:
- not a special note type
- not a separate design-artifact family
- not a `CoderBrief`

It is a component whose design can be fully expressed through the current PAA model.

## PAA Model Placement

### Component
- `ImplementationPlanRepository`

### Layer
- `Infrastructure Ports`

### Primary role
- provide structured persistence access to `ImplementationPlan` project-design truth

### Downstream adapter expectation
- `PostgresImplementationPlanRepository`

Important rule:
- the repository contract is the persistence boundary
- the repository implementation is a code artifact target derived from that boundary

## Repository Boundary

`ImplementationPlanRepository` owns structured access to:

- `paa.implementation_plans`
- `paa.implementation_plan_activities`
- `paa.implementation_plan_activity_dependencies`
- `paa.implementation_plan_artifacts`
- `paa.implementation_plan_verification_surfaces`
- `paa.implementation_plan_authority_events`

It also reads supporting identity from:

- `paa.projects`
- `paa.work_items`
- `paa.design_packages`
- `paa.implementation_targets`
- `paa.components`
- `paa.component_elements`
- `paa.component_element_realizations`

Important rule:
- this repository owns persistence access to implementation-plan truth
- it does not own derivation logic
- it does not own project delivery projections
- it does not own coder-brief assembly

## Non-Goals

`ImplementationPlanRepository` does not:

- derive plans from design packages
- decide build sequencing policy
- compute current / next / blocked activities
- infer workflow truth
- assemble `CoderBrief` payloads
- publish packets

Those belong downstream to services or projections.

## Primary Consumers

- `Implementation Plan Derivation Service`
- `Project Delivery Projection`
- future `Brief Assembly Service`
- future operator reporting / project views

## Required Repository Capabilities

### Plan root reads
- get implementation plan by `implementation_plan_id`
- get implementation plan by `(project_id, plan_id_external)`
- get implementation plan by `(design_package_id, consumer_context_key)`
- list implementation plans by `work_item_id`

### Plan root writes
- create implementation plan root
- update implementation plan root
- change plan status / authority state
- append implementation-plan authority event

### Activity reads
- list implementation-plan activities
- get activity by `(implementation_plan_id, activity_key)`
- list activities by state

### Activity writes
- create activity
- update activity
- change activity state

### Dependency reads
- list activity dependencies for a plan
- list predecessors for an activity
- list successors for an activity

### Dependency writes
- create activity dependency
- update dependency metadata / notes

### Artifact reads
- list implementation-plan artifacts
- list artifacts for an activity

### Artifact writes
- create artifact
- update artifact

### Verification-surface reads
- list verification surfaces for a plan
- list verification surfaces for an activity

### Verification-surface writes
- create verification surface
- update verification surface status / metadata

## Component-Element Mapping

This repository component can be expressed directly through current `Component Element` types.

### 1. `Role`
Meaning:
- persistence boundary for implementation-plan truth

### 2. `Service Contract`
Meaning:
- the public repository contract and its method surface

### 3. `Data Contract`
Meaning:
- repository DTOs / record shapes for:
  - plan root
  - activity
  - dependency
  - artifact
  - verification surface
  - authority event

### 4. `Interfaces`
Meaning:
- the repository interface itself
- collaborator-facing method definitions

### 5. `Functions`
Meaning:
- concrete Postgres implementation methods

### 6. `Verification Surfaces`
Meaning:
- unit tests for contract behavior
- clean-db validation of basic persistence paths

Important rule:
- we do not need a separate modeled thing called `repository_contract_note`
- the repository contract is already expressible through:
  - `Service Contract`
  - `Interfaces`
  - `Data Contract`
  - `Functions`

## Code Artifact Target Mapping

The repository component implies these code artifact targets.

### Required targets
- `repository_interface`
- `concrete_repository_class`
- `dto`
- `test_module`
- `package_export`

### Optional later targets
- `query_object`
- `projection_view`

Important rule:
- code artifact targets are the concrete implementation forms
- they are not new design categories

## Explicit Mapping: Component -> Elements -> Targets

## Component
- `ImplementationPlanRepository`

## Component Elements

### `Service Contract`
- defines the aggregate boundary and required capabilities
- code artifact targets:
  - `repository_interface`

### `Data Contract`
- defines repository DTOs and aggregate record shapes
- code artifact targets:
  - `dto`

### `Interfaces`
- defines callable repository methods and collaborator-facing contract
- code artifact targets:
  - `repository_interface`
  - `package_export`

### `Functions`
- defines concrete Postgres persistence behavior
- code artifact targets:
  - `concrete_repository_class`

### `Verification Surfaces`
- defines repository test coverage and validation expectations
- code artifact targets:
  - `test_module`

## Implementation-Plan Activity Mapping

The implementation plan for this component should express activities using the current PAA model.

Each activity should carry:
- `component`
- `component_element`
- `code_artifact_target`

## Example first-slice activities

### Activity 1
- title:
  - define repository interface
- component:
  - `ImplementationPlanRepository`
- component element:
  - `Interfaces`
- code artifact target:
  - `repository_interface`

### Activity 2
- title:
  - define repository DTOs
- component:
  - `ImplementationPlanRepository`
- component element:
  - `Data Contract`
- code artifact target:
  - `dto`

### Activity 3
- title:
  - implement Postgres repository class
- component:
  - `ImplementationPlanRepository`
- component element:
  - `Functions`
- code artifact target:
  - `concrete_repository_class`

### Activity 4
- title:
  - export repository package surface
- component:
  - `ImplementationPlanRepository`
- component element:
  - `Interfaces`
- code artifact target:
  - `package_export`

### Activity 5
- title:
  - add repository unit tests
- component:
  - `ImplementationPlanRepository`
- component element:
  - `Verification Surfaces`
- code artifact target:
  - `test_module`

## Dependency Shape For The First Slice

Recommended first-slice dependency order:

1. `Interfaces -> repository_interface`
2. `Data Contract -> dto`
3. `Functions -> concrete_repository_class`
4. `Interfaces -> package_export`
5. `Verification Surfaces -> test_module`

Important sequencing rule:
- `dto` and `repository_interface` may be parallel-safe if the contract is already stable
- `concrete_repository_class` should follow both
- `test_module` should follow the concrete implementation surface it is proving

## Relationship To `CoderBrief`

`ImplementationPlanRepository` contract definition is **not** itself a `CoderBrief`.

Instead, the flow is:

1. define the component using:
   - component
   - component elements
   - code artifact targets

2. derive implementation-plan activities from that structure

3. add those structured activities into a `CoderBrief`

4. the coder agent receives:
   - the selected component
   - the relevant component elements
   - the code artifact targets
   - the activity sequence
   - constraints and proving instructions

That is the engineering bridge.

## First-Slice Success Criteria

This repository definition step is successful when:

1. `ImplementationPlanRepository` is clearly modeled as a component
2. its component elements are explicit
3. its code artifact targets are explicit
4. its first implementation-plan activities are explicit
5. the path from those activities into a later `CoderBrief` is direct and unambiguous

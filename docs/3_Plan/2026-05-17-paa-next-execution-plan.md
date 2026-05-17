# PAA Next Execution Plan

Date: 2026-05-17
Status: active

## Purpose

Unify the current active work into one ordered execution plan.

This plan consolidates three previously separate threads:
- `ImplementationPlan` schema and activity-derivation work
- `Component Design Planning Service` planning work
- the duplicate `Component Design Planning Service` implementation thread

The goal is to eliminate ambiguity about what is next, what is already done, and what must happen before implementation resumes in earnest.

## Consolidated Workstreams

### Workstream A. `ImplementationPlan` project-design backbone

This is the newly discovered primary truth layer for:
- project design
- implementation planning
- authoritative activity sequencing
- project visibility / projection

### Workstream B. `Component Design Planning Service`

This is still the dependency-graph-selected next Stratum 2 service to implement.

However, it now sits downstream of the `ImplementationPlan` backbone, because project-design truth and implementation-plan derivation should exist before the planning service is implemented deeply against an incomplete planning model.

### Workstream C. Duplicate planning-service thread

This is not a separate workstream.
It is now merged into Workstream B.

## Current Status Snapshot

### Completed already

#### `ImplementationPlan` design and schema
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-17-implementation-plan-entity-design.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-17-implementation-plan-activity-derivation-policy.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/migrations/postgres/013-step13-implementation-plans.sql`

#### `ImplementationPlan` migration validation
- applied and validated on the PAA-local DB
- local DB:
  - container: `paa-postgres-db`
  - database: `paa_dev`

#### `Component Design Planning Service` design
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-component-design-planning-service-component-spec.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-component-design-planning-service-pre-spec.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/3_Plan/2026-05-17-component-design-planning-service-implementation-plan.md`

#### DB infrastructure cutover
- PAA-local Postgres service exists
- shared DB helper is the runtime path
- remaining legacy direct DB callers have been migrated

### Not yet implemented

#### `ImplementationPlan` runtime/code layer
- `ImplementationPlanRepository`
- `Implementation Plan Derivation Service`
- `Project Delivery Projection` contract

#### `Component Design Planning Service` code
- service contract
- DTOs
- default service shell
- read/planning logic
- tests

## Dependency Logic

The next implementation target remains:
- `Component Design Planning Service`

But the next execution priority is:
- finish enough of the `ImplementationPlan` backbone that project-design truth exists as code-level infrastructure before the service implementation expands.

This means:
- `ImplementationPlan` repository/service/projection design comes first
- then initial `Component Design Planning Service` implementation begins

## Ordered Execution Plan

## Step 1. Define `ImplementationPlanRepository`

### Why first
This is the first code-level infrastructure boundary for the new project-design truth layer.

### Deliverables
- design note or repository contract update for `ImplementationPlanRepository`
- repository package layout under `paa-core`
- initial repository methods identified and sequenced

### Target files
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-17-implementation-plan-repository-contract.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/repositories/implementation_plan/__init__.py`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/repositories/implementation_plan/contracts.py`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/repositories/implementation_plan/models.py`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/repositories/implementation_plan/postgres.py`

### Minimum repository scope
- load implementation plan by id / external id
- list implementation-plan activities
- list activity dependencies
- list verification surfaces
- create/update plan root
- create/update activities
- create/update dependencies

## Step 2. Define `Implementation Plan Derivation Service`

### Why second
Once the repository boundary exists, we need the domain service that derives a consumer-specific implementation plan from approved slice authority.

### Deliverables
- component pre-spec or direct component spec
- service responsibility boundary
- upstream/downstream dependency mapping
- first implementation slice definition

### Target files
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-17-implementation-plan-derivation-service-pre-spec.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-17-implementation-plan-derivation-service-component-spec.md`

### Expected responsibility
- consume approved slice authority and consumer context
- produce authoritative `ImplementationPlan` records and activities
- not absorb coder-brief assembly
- not absorb workflow/runtime ownership

## Step 3. Define `Project Delivery Projection` contract

### Why third
Once project-design truth exists, we need the contract for how the operator-facing “Project” view is derived from it.

### Deliverables
- projection contract note
- explicit derivation inputs for:
  - current activity
  - next activity
  - completed activities
  - blocked activities
- projection boundary statement

### Target files
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-17-project-delivery-projection-contract.md`

### Required output semantics
- project view is projection-only
- implementation plan remains primary truth
- workflow/runtime state refines activity state but does not replace plan ownership

## Step 4. Scaffold `ImplementationPlan` code packages

### Why fourth
After repository/service/projection design is stable, create the code skeletons before implementation.

### Deliverables
- repository package scaffold
- service package scaffold
- tests scaffold

### Target files
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/repositories/implementation_plan/`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/implementation_plan_derivation/`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/tests/unit/test_implementation_plan_repository.py`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/tests/unit/test_implementation_plan_derivation_service.py`

## Step 5. Implement `ImplementationPlanRepository` first slice

### Why fifth
This finishes the minimum persistence layer for project-design truth.

### Deliverables
- DTOs
- repository contract
- Postgres implementation
- focused unit tests

### First slice scope
- read plan root
- read activities
- read dependencies
- read verification surfaces
- upsert plan root
- upsert activities
- upsert dependencies

## Step 6. Implement `Implementation Plan Derivation Service` first slice

### Why sixth
With persistence ready, implement the first project-design derivation path.

### Deliverables
- service contract
- DTOs
- default implementation
- unit tests

### First slice scope
- derive plan root from design package + implementation target + consumer context
- derive activity list for the proof slice
- derive activity dependencies
- derive verification surfaces
- persist the result through `ImplementationPlanRepository`

## Step 7. Re-materialize proof slice into `ImplementationPlan`

### Why seventh
Use the validated `Component Design Planning Service` proof slice again, this time as the first real `ImplementationPlan` consumer.

### Deliverables
- proof-slice implementation-plan artifact or record set
- validation note showing plan root and activities persisted in the PAA-local DB

### Proof target
- `Component Design Planning Service`

## Step 8. Begin `Component Design Planning Service` code implementation

### Why eighth
At this point the planning backbone exists strongly enough to support service implementation.

### Deliverables
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/component_design_planning/contracts.py`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/component_design_planning/models.py`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/component_design_planning/default.py`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/packages/paa-core/src/paa_core/services/component_design_planning/__init__.py`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/tests/unit/test_component_design_planning_service.py`

### Initial scope
Implement only Phase 1 and Phase 2 from:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/3_Plan/2026-05-17-component-design-planning-service-implementation-plan.md`

Meaning:
- service contract
- planning DTOs
- default service shell

## Step 9. Implement `Component Design Planning Service` read/planning slice

### Why ninth
This is the first useful service behavior after the contract/shell exists.

### Deliverables
- component planning reads
- element planning views
- realization option views
- gap detection
- brief-planning payload assembly

### Scope source
Use Phases 3-6 from:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/3_Plan/2026-05-17-component-design-planning-service-implementation-plan.md`

## Step 10. Validate planning bridge alignment

### Why tenth
Before moving on, confirm that:
- `ImplementationPlan` derivation
- `Component Design Planning Service`
- coder-brief derivation

all align without a new methodology gap.

### Deliverables
- validation note comparing:
  - component spec
  - implementation plan
  - implementation-plan records
  - service outputs
  - coder-brief inputs

## Priority Summary

### Immediate priority
1. `ImplementationPlanRepository`
2. `Implementation Plan Derivation Service`
3. `Project Delivery Projection` contract

### Next priority
4. scaffold and implement `ImplementationPlan` code layer
5. re-materialize the proof slice into the new plan layer

### Then
6. implement `Component Design Planning Service`

## Success Condition

This execution plan is successful when:
1. `ImplementationPlan` exists as real repo/service/projection-backed code-level infrastructure
2. `Component Design Planning Service` begins implementation against that stronger backbone
3. the proof slice is represented not only as a design package and coder brief, but also as a real implementation plan with authoritative activities

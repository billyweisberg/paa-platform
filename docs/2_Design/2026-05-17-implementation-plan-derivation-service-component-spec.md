Title: Implementation Plan Derivation Service Component Spec
Doc-ID: paa-implementation-plan-derivation-service-component-spec
Doc-Type: component-spec
Status: active
Lifecycle-Stage: design
Created: 2026-05-18
Last-Edited: 2026-05-18
Author: Billy Weisberg
Repo: paa-platform
Component: ImplementationPlanDerivationService
Domain: implementation-plan
Keywords: implementation, plan, derivation, service, activities, planning
Depends-On: 2026-05-17-implementation-plan-entity-design.md, 2026-05-17-implementation-plan-repository-contract.md
Supersedes: 
Superseded-By: 
Canonical: true
Review-After: 2026-06-15
Owners: 
Expires: 
Issue: 
PR: 
Authority-Source: 
Implementation-Status: 
Summary: Defines the service boundary that derives authoritative implementation plans and activities from approved slice authority.

# Implementation Plan Derivation Service Component Spec

Date: 2026-05-17

## Purpose

Define the full `Component Spec` for `Implementation Plan Derivation Service` using the current PAA methodology and model.

This service is the project-design bridge between:
- approved slice authority
- consumer context
- structured component/code-artifact modeling

and:
- authoritative `ImplementationPlan` records
- authoritative implementation-plan activities

It exists so the system can derive a real implementation plan before coder briefing begins.

## Related Notes

Read alongside:
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-17-implementation-plan-entity-design.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-17-implementation-plan-activity-derivation-policy.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-17-implementation-plan-repository-contract.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-component-design-planning-service-component-spec.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-16-paa-producer-derivation-subsystem.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-15-paa-layered-architecture-proposal.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/2_Design/2026-05-15-paa-layered-component-dependency-graph.md`
- `/Users/billyweisberg/Repos/billyweisberg/paa-platform/docs/terminology/paa-engineering-terminology-glossary.md`

## Architecture Placement

Layer:
- `Domain Services`

Dependency stratum:
- `Stratum 2`

Primary upstream dependencies:
- `ImplementationPlanRepository`
- `ComponentDesignPlanningService`
- `StructuredLogger`

Primary downstream consumers:
- `Brief Assembly Service`
- `Project Delivery Projection`
- future project-design authoring tools

## 1. Role

`Implementation Plan Derivation Service` derives a consumer-specific, slice-scoped `ImplementationPlan` from approved design authority and component/code-artifact planning structure.

Authority boundary:
- owns derivation of implementation-plan root data
- owns derivation of implementation-plan activities
- owns derivation of activity dependencies
- owns derivation of verification surfaces
- owns persistence of derived implementation-plan truth through `ImplementationPlanRepository`
- does not own coder-brief assembly
- does not own workflow/runtime state
- does not own project delivery projection

## 2. Component State Model

The service should be stateless between calls.

### Persistent state
This component owns no persistent state directly.

It creates and updates persistent planning truth through:
- `ImplementationPlanRepository`

### In-memory working state
During one call, the service may hold:
- loaded design package context
- loaded implementation target context
- loaded component planning payload
- derived activity list
- derived activity dependency list
- derived verification-surface list
- derivation warnings and gap summaries

### State rule
Derived implementation-plan structures become primary truth only after persistence through `ImplementationPlanRepository`.

## 3. Service Contract

The service provides a derivation-oriented contract over approved slice authority.

### Inputs
- design package identity or design package record
- implementation target identity or implementation target record
- consumer context key
- optional primary component override when governance allows it
- optional derivation mode flags for:
  - dry-run
  - persist
  - replace-existing-draft-plan

### Outputs
- implementation-plan root DTO
- implementation-plan activity DTO set
- implementation-plan activity dependency DTO set
- implementation-plan verification-surface DTO set
- derivation warnings
- derivation gaps
- persisted implementation-plan identity when persistence is requested

### Guarantees
- implementation-plan activities are derived from explicit component / element / target structure
- the service does not invent activity lists from loose prose alone
- each activity carries explicit association to:
  - component
  - component element
  - code artifact target
- the service stops before coder-brief assembly

### Non-guarantees
- this service does not guarantee final workflow readiness
- this service does not dispatch packets
- this service does not create queue/runtime state
- this service does not decide project projection display state

## 4. Data Contract

The service consumes approved authority structures and emits structured plan DTOs.

### Primary consumed records
- `DesignPackage`
- `ImplementationTarget`
- `ComponentPlanningView`
- `ComponentElementPlanningView`
- `RealizationOptionView`
- `PlanningGap`

### Primary emitted DTOs

#### `ImplementationPlanDerivationRequest`
Carries:
- `project_id`
- `design_package_id`
- `implementation_target_id`
- `consumer_context_key`
- optional `primary_component_id`
- optional `persist`
- optional `replace_existing_draft`
- optional `metadata`

#### `ImplementationPlanRootDraft`
Carries:
- project identity
- work-item identity
- design-package identity
- implementation-target identity
- primary component identity
- plan title
- consumer context key
- build-sequence summary
- proving summary
- protected constraint summary

#### `ImplementationPlanActivityDraft`
Carries:
- activity key
- activity title
- component id
- component element id
- code artifact target key
- activity kind
- sequence order
- target path or module hint
- assigned role hint
- metadata

#### `ImplementationPlanActivityDependencyDraft`
Carries:
- predecessor activity key
- successor activity key
- sequencing requirement
- dependency strength
- notes

#### `ImplementationPlanVerificationSurfaceDraft`
Carries:
- related activity key
- surface kind
- surface ref
- required flag
- sequence order
- metadata

#### `ImplementationPlanDerivationResult`
Carries:
- plan root draft
- activity drafts
- dependency drafts
- verification-surface drafts
- warnings
- gaps
- persisted implementation plan id when available

### Data contract rule
Outputs must be structured enough that downstream `Brief Assembly Service` can consume them without reconstructing engineering intent from prose.

## 5. Injected Services

### Required injected services
- `ImplementationPlanRepository`
- `ComponentDesignPlanningService`
- `StructuredLogger`

### Optional injected services
- `Clock`
- future `ImplementationPlanPolicyHelper`

### Important non-injected collaborators
This service should not depend directly on:
- `MessageBus`
- `GitProvider`
- `WorkflowStateRepository`
- `RuntimeEventRepository`
- `ExecutionPackageRepository`

If those become necessary, the component boundary should be reconsidered.

## 6. Interfaces

### Provided interface
- `ImplementationPlanDerivationService`

### Required interfaces
- `ImplementationPlanRepository`
- `ComponentDesignPlanningService`
- `StructuredLogger`

### Recommended code realization
- interface / contract:
  - `implementation_plan_derivation_service_interface`
- default implementation:
  - `default_implementation_plan_derivation_service`

## 7. Functions

Minimum public functions:
- `derive_plan(request)`
- `derive_plan_for_design_package(project_id, design_package_id, consumer_context_key)`
- `derive_activity_set(component_id, consumer_context_key)`
- `derive_activity_dependencies(component_id, consumer_context_key)`
- `derive_verification_surfaces(component_id, consumer_context_key)`

Likely internal helper functions:
- `load_derivation_context(...)`
- `load_component_planning_payload(...)`
- `derive_plan_root(...)`
- `derive_activity_drafts(...)`
- `derive_dependency_drafts(...)`
- `derive_verification_surface_drafts(...)`
- `detect_derivation_gaps(...)`
- `persist_plan_bundle(...)`

## 8. Messages Received

This component receives service-level commands and queries, not queue packets.

### Primary command
- `DeriveImplementationPlan`

### Supporting query-like operations
- `DeriveActivitySet`
- `DeriveActivityDependencies`
- `DeriveVerificationSurfaces`

## 9. Messages Published

This service should remain request/response oriented in the first slice.

If internal events are emitted later, they should remain narrow and domain-level, such as:
- `ImplementationPlanDerived`
- `ImplementationPlanActivitiesDerived`
- `ImplementationPlanDerivationGapDetected`

For the first implementation, returning structured results is sufficient.

## 10. Message Data Contracts

### `DeriveImplementationPlan`
Carries:
- design-package binding
- implementation-target binding
- consumer-context key
- optional persistence mode

### `ImplementationPlanDerived`
Carries:
- implementation-plan identity
- primary component identity
- activity count
- dependency count
- verification-surface count
- warning count

## 11. Event Subscriptions

This service subscribes to no queue or runtime event stream in the first slice.

Its invocation should come from:
- producer-side project-design flows
- future Delivery Architect tools
- future implementation-plan authoring commands

## 12. Events Published

No required durable events in the first slice.

Durable authority progression for plan approval belongs later through:
- `ImplementationPlanRepository`
- `implementation_plan_authority_events`

## 13. Event Data Contracts

Not required in the first implementation slice.

## 14. Component Lifecycle

Lifecycle phases:
- input resolution
- component-planning resolution
- activity derivation
- dependency derivation
- verification-surface derivation
- optional persistence
- structured result return

Lifecycle rule:
- if required authority input is incomplete, fail closed with explicit gaps
- do not silently emit a partial implementation plan and claim it is ready for coder briefing

## 15. Component Configuration

Required configuration:
- default consumer context resolution policy
- persistence mode default

Optional configuration:
- activity sequencing heuristics that remain within approved policy
- default role-assignment hints for activity generation

Configuration rule:
- configuration may tune derivation behavior
- configuration may not change the primary truth boundary

## Responsibility Summary

Owns:
- deriving structured implementation-plan truth
- mapping component planning outputs into activity-level project-design records
- ensuring activities explicitly carry:
  - component
  - component element
  - code artifact target

Does not own:
- coder brief construction
- packet preparation
- workflow state
- queue dispatch
- projection rendering

## Explicit Mapping To Existing PAA Model

This service is fully expressible through the current model.

### Component
- `Implementation Plan Derivation Service`

### Component Elements
- `Role`
- `Service Contract`
- `Data Contract`
- `Injected Services`
- `Interfaces`
- `Functions`
- `Verification Surfaces`

### Code Artifact Targets
- `service_interface`
- `service_implementation`
- `dto`
- `test_module`
- `package_export`

### Implementation-plan activity usage
This service exists to derive activities that later feed `CoderBrief` construction.

Each derived activity must carry:
- component
- component element
- code artifact target

That is the direct bridge to:
- `CoderBrief -> Working Code`

## Invariants

1. every derived activity belongs to one implementation plan
2. every derived activity must map back to explicit component-planning structure
3. no activity may be emitted without a code artifact target
4. the service must stop before coder-brief assembly
5. dry-run and persisted derivation should produce equivalent structural outputs

## Failure Model

Fail closed when:
- design package is missing or not approved
- implementation target is missing
- primary component cannot be resolved
- component-planning payload is too incomplete to derive a trustworthy plan

Return warnings or gaps when:
- optional realization choices are incomplete
- verification surfaces are partially defined
- sequencing hints are weak but not fatal

## First-Slice Scope

The first implementation slice should:
- derive a single-component implementation plan for the proof slice
- persist plan root
- persist activities
- persist dependencies
- persist verification surfaces
- return a structured result for downstream brief assembly

The first implementation slice should not:
- derive multi-component project plans
- own packet-ready authority transitions
- own review/approval governance for the plan
- replace `Brief Assembly Service`

## Success Criteria

This component spec is successful when:

1. the service boundary is explicit and narrow
2. it is clear how the service consumes existing PAA model structures
3. it is clear how it produces implementation-plan activities
4. it is clear that coder briefing is downstream from this service, not merged into it
